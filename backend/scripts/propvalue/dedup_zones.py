#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PropValue 구역 중복 정리 + project_type 유형 통일 스크립트

1) duplicates_check.csv 367건 로드
2) 정비+비정비 155건: 정비 유지, 비정비 삭제
3) 정비+정비 101건: 적절한 쪽 유지, 다른 쪽 삭제
4) 비정비+비정비 111건: 건드리지 않음
5) project_type 새 유형으로 변환 (전체)
6) stage는 더 진행된 쪽으로 UPDATE
7) geometry/households/area_sqm 빈 필드 보강

사용법:
  python dedup_zones.py                 # dry-run
  python dedup_zones.py --execute       # 실제 실행
"""

import csv
import os
import sys
import argparse
import psycopg2
import psycopg2.extras

# -- project_type 매핑 --
TYPE_MAP = {
    '재건축': '재건축',
    '재개발': '재개발(주택정비형)',
    '도시환경': '재개발(도시정비형)',
    '주거환경개선': '재개발(주택정비형)',
    '가로주택': '가로주택정비',
    '소규모재건축': '소규모재건축',
}

JUNGBI_TYPES = set(TYPE_MAP.keys())
NON_JUNGBI_TYPES = {
    '도시재생', '지구단위계획', '재정비촉진', '택지개발',
    '도시계획시설', '기업도시', '도시개발', '국토부',
    '역세권', '경제자유구역', '신도시', '기타', '시가지조성', '혁신도시',
}

# -- stage 순서 --
STAGE_ORDER = ['구역지정', '추진위', '조합설립', '사업시행', '관리처분', '착공', '준공', '조합해산']
STAGE_RANK = {s: i for i, s in enumerate(STAGE_ORDER)}
STAGE_NORMALIZE = {
    '후보지선정': '구역지정', '용역착수': '구역지정', '신통착수': '구역지정',
    '신통 착수': '구역지정', '주민공람': '구역지정', '심의': '구역지정',
    '통심완료': '구역지정', '안전진단': '구역지정', '구의지정': '구역지정',
    '신탁시행자지정(신탁)': '구역지정',
    '추진위구성': '추진위', '추진위원회구성': '추진위', '추진위': '추진위',
    '조합설립': '조합설립', '조합설립인가': '조합설립', '조합': '조합설립',
    '사업시행': '사업시행', '사업시행인가': '사업시행', '사업계획승인': '사업시행',
    '시행자지정(조합)': '사업시행', '시행자지정(신탁)': '사업시행',
    '인가 완료': '사업시행', '신통자문': '사업시행',
    '관리처분': '관리처분', '관리처분인가': '관리처분',
    '착공': '착공', '철거': '착공', '분양': '착공',
    '준공': '준공', '준공인가': '준공', '이전고시': '준공', '통심완료+준공': '준공',
    '조합해산': '조합해산', '조합청산': '조합해산',
}


def get_stage_rank(stage):
    if not stage:
        return -1
    n = STAGE_NORMALIZE.get(stage, stage)
    return STAGE_RANK.get(n, -1)


def pick_later_stage(stage_a, stage_b):
    ra, rb = get_stage_rank(stage_a), get_stage_rank(stage_b)
    if ra >= rb:
        return stage_a if stage_a else stage_b
    return stage_b if stage_b else stage_a


def pick_jungbi_type(ta, tb):
    """정비+정비 중복 시 우선 유형 결정."""
    pair = {ta, tb}
    if '도시환경' in pair:
        return '도시환경'
    if '소규모재건축' in pair:
        return '소규모재건축'
    if '가로주택' in pair:
        return '가로주택'
    if '주거환경개선' in pair:
        return '주거환경개선'
    if pair == {'재개발', '재건축'}:
        return '재개발'
    if ta == tb:
        return ta
    return ta


def find_ultimate_keeper(zone_id, keeper_map):
    """zone_id가 삭제 대상이면, 그 zone_id의 최종 keeper를 찾아 반환."""
    visited = set()
    current = zone_id
    while current in keeper_map and current not in visited:
        visited.add(current)
        current = keeper_map[current]
    return current


def main():
    parser = argparse.ArgumentParser(description='PropValue 중복 구역 정리')
    parser.add_argument('--execute', action='store_true', help='실제 DB 실행')
    parser.add_argument('--csv', default=None, help='CSV 경로')
    args = parser.parse_args()

    # CSV 파일 찾기
    csv_path = args.csv
    if not csv_path:
        candidates = [
            '/home/webapp/goldenrabbit/backend/scripts/propvalue/duplicates_check.csv',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'propvalue', 'data', 'duplicates_check.csv'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'duplicates_check.csv'),
        ]
        for c in candidates:
            if os.path.exists(c):
                csv_path = c
                break
    if not csv_path or not os.path.exists(csv_path):
        print("ERROR: duplicates_check.csv not found")
        sys.exit(1)

    print(f"CSV: {csv_path}")

    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            rows.append(row)
    print(f"총 {len(rows)}개 중복 쌍 로드됨")

    # 분류
    cat1, cat2, cat3 = [], [], []
    for row in rows:
        ta, tb = row['type_a'], row['type_b']
        ja, jb = ta in JUNGBI_TYPES, tb in JUNGBI_TYPES
        na, nb = ta in NON_JUNGBI_TYPES, tb in NON_JUNGBI_TYPES
        if (ja and nb) or (na and jb):
            cat1.append(row)
        elif ja and jb:
            cat2.append(row)
        elif na and nb:
            cat3.append(row)

    print(f"\n분류: 1번(정비+비정비)={len(cat1)}, 2번(정비+정비)={len(cat2)}, 3번(비정비+비정비)={len(cat3)}")

    # ---- 2-pass 처리 ----
    # keeper_map: deleted_id -> keeper_id (누가 이 id를 대신 유지하는지)
    keeper_map = {}
    # keep_info: keeper_id -> {new_type, new_stage, merge_from}
    keep_info = {}
    delete_ids = set()

    def ensure_info(kid):
        if kid not in keep_info:
            keep_info[kid] = {'new_type': None, 'new_stage': None, 'merge_from': set()}
        return keep_info[kid]

    def merge_into(keeper_id, deleted_id, keeper_type, stage_a, stage_b):
        """deleted_id를 keeper_id에 병합."""
        # 만약 keeper_id 자체가 이전에 삭제 대상이 됐으면, 최종 keeper 찾기
        actual_keeper = find_ultimate_keeper(keeper_id, keeper_map)
        if actual_keeper in delete_ids:
            # 최종 keeper도 삭제 대상이면 모순 -- keeper_id를 그대로 사용
            actual_keeper = keeper_id

        info = ensure_info(actual_keeper)
        info['merge_from'].add(deleted_id)
        info['new_type'] = TYPE_MAP.get(keeper_type, keeper_type)

        better = pick_later_stage(stage_a, stage_b)
        if info['new_stage']:
            better = pick_later_stage(info['new_stage'], better)
        info['new_stage'] = better

        delete_ids.add(deleted_id)
        keeper_map[deleted_id] = actual_keeper

        # actual_keeper가 delete에 있으면 제거
        delete_ids.discard(actual_keeper)

    # -- Pass 1: 정비+비정비 (cat1) --
    for row in cat1:
        ia, ib = int(row['id_a']), int(row['id_b'])
        ta, tb = row['type_a'], row['type_b']
        sa, sb = row['stage_a'], row['stage_b']

        if ta in JUNGBI_TYPES:
            keep_id, del_id, keep_type = ia, ib, ta
        else:
            keep_id, del_id, keep_type = ib, ia, tb

        # del_id가 이미 삭제 대상이면 stage만 업데이트
        if del_id in delete_ids:
            actual_keeper = find_ultimate_keeper(del_id, keeper_map)
            info = ensure_info(keep_id)
            info['new_type'] = TYPE_MAP.get(keep_type, keep_type)
            better = pick_later_stage(sa, sb)
            if info['new_stage']:
                better = pick_later_stage(info['new_stage'], better)
            info['new_stage'] = better
            continue

        merge_into(keep_id, del_id, keep_type, sa, sb)

    print(f"  Cat1 처리 후: DELETE={len(delete_ids)}, KEEP={len(keep_info)}")

    # -- Pass 2: 정비+정비 (cat2) --
    for row in cat2:
        ia, ib = int(row['id_a']), int(row['id_b'])
        ta, tb = row['type_a'], row['type_b']
        sa, sb = row['stage_a'], row['stage_b']

        # 둘 다 이미 삭제 대상이면 스킵
        if ia in delete_ids and ib in delete_ids:
            continue

        # 한 쪽만 이미 삭제 대상이면 다른 쪽에 stage 업데이트만
        if ia in delete_ids:
            info = ensure_info(ib)
            info['new_type'] = TYPE_MAP.get(pick_jungbi_type(tb, ta), pick_jungbi_type(tb, ta))
            better = pick_later_stage(sa, sb)
            if info['new_stage']:
                better = pick_later_stage(info['new_stage'], better)
            info['new_stage'] = better
            info['merge_from'].add(ia)
            continue
        if ib in delete_ids:
            info = ensure_info(ia)
            info['new_type'] = TYPE_MAP.get(pick_jungbi_type(ta, tb), pick_jungbi_type(ta, tb))
            better = pick_later_stage(sa, sb)
            if info['new_stage']:
                better = pick_later_stage(info['new_stage'], better)
            info['new_stage'] = better
            info['merge_from'].add(ib)
            continue

        # 둘 다 살아있음 -- 한 쪽 삭제
        preferred = pick_jungbi_type(ta, tb)
        if preferred == ta:
            keep_id, del_id = ia, ib
        else:
            keep_id, del_id = ib, ia

        # keep_id가 이전 cat1에서 이미 keep_info에 등록된 경우, 그 info를 유지하면서 del_id를 추가 삭제
        # del_id가 cat1에서 keep_info에 등록된 경우, del_id의 merge_from들을 keep_id로 이전
        if del_id in keep_info:
            # del_id가 다른 레코드들의 keeper였음 -> keep_id로 이전
            old_info = keep_info.pop(del_id)
            info = ensure_info(keep_id)
            info['merge_from'].update(old_info['merge_from'])
            info['merge_from'].add(del_id)
            # keeper_map 갱신: del_id를 가리키던 것들 -> keep_id로
            for did, kid in list(keeper_map.items()):
                if kid == del_id:
                    keeper_map[did] = keep_id

        merge_into(keep_id, del_id, preferred, sa, sb)

    print(f"  Cat2 처리 후: DELETE={len(delete_ids)}, KEEP={len(keep_info)}")

    # ---- 무결성 검증 ----
    conflicts = set(keep_info.keys()) & delete_ids
    if conflicts:
        print(f"\n  ERROR: {len(conflicts)} IDs are both keep and delete!")
        for c in sorted(conflicts):
            print(f"    id={c}")
        # 자동 해결: keep_info에 있으면 delete에서 제거
        for c in conflicts:
            delete_ids.discard(c)
        print(f"  자동 해결 완료. DELETE={len(delete_ids)}")
    else:
        print(f"  무결성 검증 통과")

    # ---- DB 실행 ----
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        # Try individual DB_ env vars
        db_host = os.environ.get('DB_HOST', '')
        db_name = os.environ.get('DB_NAME', '')
        db_user = os.environ.get('DB_USER', '')
        db_pass = os.environ.get('DB_PASSWORD', '')
        db_port = os.environ.get('DB_PORT', '5432')
        if db_host and db_name:
            db_url = "postgresql://{}:{}@{}:{}/{}".format(
                db_user, db_pass, db_host, db_port, db_name
            )

    if not db_url:
        for env_path in [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env'),
            '/home/webapp/goldenrabbit/backend/.env',
        ]:
            if os.path.exists(env_path):
                env_vars = {}
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            k, v = line.split('=', 1)
                            env_vars[k.strip()] = v.strip().strip('"').strip("'")
                if 'DATABASE_URL' in env_vars:
                    db_url = env_vars['DATABASE_URL']
                elif 'DB_HOST' in env_vars:
                    db_url = "postgresql://{}:{}@{}:{}/{}".format(
                        env_vars.get('DB_USER', ''),
                        env_vars.get('DB_PASSWORD', ''),
                        env_vars.get('DB_HOST', '127.0.0.1'),
                        env_vars.get('DB_PORT', '5432'),
                        env_vars.get('DB_NAME', ''),
                    )
                if db_url:
                    break

    if not db_url:
        print("\nERROR: DATABASE_URL not found.")
        if not args.execute:
            _print_sql_only(keep_info, delete_ids)
            return
        sys.exit(1)

    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("SELECT COUNT(*) FROM redevelopment_zones")
        before_count = cur.fetchone()[0]
        print(f"\n현재 DB: {before_count}건")

        # 백업
        if args.execute:
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='redevelopment_zones_backup_v3')")
            if not cur.fetchone()[0]:
                print("백업 테이블 생성: redevelopment_zones_backup_v3")
                cur.execute("CREATE TABLE redevelopment_zones_backup_v3 AS SELECT * FROM redevelopment_zones")
                cur.execute("SELECT COUNT(*) FROM redevelopment_zones_backup_v3")
                print(f"  백업 완료: {cur.fetchone()[0]}건")

        # Step 1: geometry/households/area_sqm 보강
        merge_count = 0
        for kid, info in keep_info.items():
            for mid in (info['merge_from'] & delete_ids):
                cur.execute("""
                    UPDATE redevelopment_zones dst
                    SET geometry = COALESCE(dst.geometry, src.geometry),
                        households = COALESCE(dst.households, src.households),
                        area_sqm = COALESCE(dst.area_sqm, src.area_sqm)
                    FROM redevelopment_zones src
                    WHERE dst.id = %s AND src.id = %s
                      AND (dst.geometry IS NULL OR dst.households IS NULL OR dst.area_sqm IS NULL)
                """, (kid, mid))
                if cur.rowcount > 0:
                    merge_count += cur.rowcount
        print(f"  필드 보강: {merge_count}건")

        # Step 2: UPDATE project_type + stage
        update_count = 0
        for kid, info in keep_info.items():
            parts, params = [], []
            if info['new_type']:
                parts.append("project_type = %s")
                params.append(info['new_type'])
            if info['new_stage']:
                parts.append("stage = %s")
                params.append(info['new_stage'])
            if parts:
                params.append(kid)
                sql = f"UPDATE redevelopment_zones SET {', '.join(parts)} WHERE id = %s"
                if args.execute:
                    cur.execute(sql, params)
                    update_count += cur.rowcount
                else:
                    update_count += 1
        print(f"  UPDATE (중복 처리): {update_count}건")

        # Step 3: DELETE
        if delete_ids:
            dl = sorted(delete_ids)
            if args.execute:
                cur.execute("DELETE FROM redevelopment_zones WHERE id = ANY(%s)", (dl,))
                actual = cur.rowcount
            else:
                actual = len(dl)
            print(f"  DELETE: {actual}건")

        # Step 4: 전체 project_type 일괄 변환
        type_count = 0
        for old_t, new_t in TYPE_MAP.items():
            if old_t != new_t:
                if args.execute:
                    cur.execute("UPDATE redevelopment_zones SET project_type = %s WHERE project_type = %s", (new_t, old_t))
                    type_count += cur.rowcount
                else:
                    cur.execute("SELECT COUNT(*) FROM redevelopment_zones WHERE project_type = %s", (old_t,))
                    cnt = cur.fetchone()[0]
                    if cnt > 0:
                        print(f"  [DRY] '{old_t}' -> '{new_t}': {cnt}건")
                    type_count += cnt
        print(f"  유형 일괄 변환: {type_count}건")

        # 결과
        if args.execute:
            cur.execute("SELECT COUNT(*) FROM redevelopment_zones")
            after = cur.fetchone()[0]
            print(f"\n=== 결과 ===")
            print(f"  변경 전: {before_count}건")
            print(f"  삭제: {before_count - after}건")
            print(f"  변경 후: {after}건")

            cur.execute("SELECT project_type, COUNT(*) FROM redevelopment_zones GROUP BY project_type ORDER BY COUNT(*) DESC")
            print(f"\n유형별:")
            for r in cur.fetchall():
                print(f"  {r[0] or '(없음)'}: {r[1]}건")

            conn.commit()
            print("\nCOMMIT!")
        else:
            print(f"\n[DRY-RUN] 예상: {before_count} - {len(delete_ids)} = {before_count - len(delete_ids)}건")
            conn.rollback()

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


def _print_sql_only(keep_info, delete_ids):
    print("\n-- UPDATE --")
    for kid in sorted(keep_info.keys()):
        info = keep_info[kid]
        parts = []
        if info['new_type']:
            parts.append(f"project_type='{info['new_type']}'")
        if info['new_stage']:
            parts.append(f"stage='{info['new_stage']}'")
        if parts:
            print(f"UPDATE redevelopment_zones SET {', '.join(parts)} WHERE id={kid};")
    print(f"\n-- DELETE ({len(delete_ids)}) --")
    if delete_ids:
        print(f"DELETE FROM redevelopment_zones WHERE id IN ({','.join(str(x) for x in sorted(delete_ids))});")
    print(f"\n-- Bulk type --")
    for old_t, new_t in TYPE_MAP.items():
        if old_t != new_t:
            print(f"UPDATE redevelopment_zones SET project_type='{new_t}' WHERE project_type='{old_t}';")


if __name__ == '__main__':
    main()
