#!/usr/bin/env python3
"""
PropValue stage 보강 v3 -- PP0101 "추진중" 68건 정보몽땅 재매칭

배경:
  - fix_bz101_stage_mapping.py 실행 후 PP0101(추진중, 상세불명) 구역 중
    정보몽땅 등에서 보강되지 못한 66건 재개발 + 2건 재건축이 stage 빈값
  - 이전 enrich_stage_from_cleanup.py에서 매칭 실패 (이름 형식 차이)
  - 이번 스크립트에서는 더 완화된 기준으로 재매칭 시도

매칭 전략 (단계적, 앞 단계에서 매칭된 건은 이후 단계에서 제외):
  1. 정규화 정확 매칭 (공백/특수문자/접미어 제거 후 동일)
  2. 포함 매칭 (한쪽이 다른쪽을 포함, 최소 2글자, 숫자 경계 확인)
  3. 동+번지 매칭 ("사당동305-35" <-> "사당동 305-35 일대")
  4. 주소 기반 매칭 (정보몽땅 address에서 동+번호 추출 -> DB zone_name 비교)
  5. 핵심단어 매칭 (동이름 + 숫자 조합이 일치하면 매칭)

검증:
  - 1:1 매칭 확인 (중복 매칭 금지)
  - 역방향 검증 (동일 DB 구역에 여러 정보몽땅 구역 매칭 방지)
  - stage 유효성 검증 (STAGE_MAP에 없는 값은 경고)
  - 이미 stage가 있는 구역은 건너뜀

사용:
  python enrich_stage_v3_cleanup.py --dry-run     # DB 변경 없이 확인
  python enrich_stage_v3_cleanup.py               # 실행
  python enrich_stage_v3_cleanup.py --verbose      # 매칭 실패 구역도 상세 출력
"""
import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('enrich_v3')

DB_PARAMS = {
    "dbname": "goldenrabbit_db",
    "user": "goldenrabbit_user",
    "password": os.environ.get("DB_PASSWORD", ""),
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
}

CLEANUP_BASE_URL = 'https://cleanup.seoul.go.kr'
CLEANUP_LIST_URL = f'{CLEANUP_BASE_URL}/cleanup/bsnssttus/lsubBsnsSttus.do'

# 정보몽땅 진행단계 -> DB stage 정규화
STAGE_MAP = {
    '추진주체구성전': '구역지정',
    '추진위원회구성': '추진위',
    '추진위원회승인': '추진위',
    '조합설립인가': '조합설립',
    '조합설립': '조합설립',
    '사업시행인가': '사업시행',
    '사업시행자지정': '사업시행',
    '사업계획승인': '사업시행',
    '관리처분인가': '관리처분',
    '관리처분': '관리처분',
    '착공': '착공',
    '철거': '착공',
    '분양': '착공',
    '준공인가': '준공',
    '이전고시': '준공',
    '조합해산': '조합해산',
    '조합청산': '조합해산',
    '정비구역지정': '구역지정',
    '정비계획 수립': '구역지정',
    '안전진단': '구역지정',
    '조합원 모집신고': '조합설립',
    '조합규약작성': '조합설립',
    '조합창립총회': '조합설립',
    '도시계획심의': '구역지정',
    '지구단위계획수립': '사업시행',
    '신속통합기획': '구역지정',
    '후보지선정': '구역지정',
    '정비예정구역': '구역지정',
    '추진위원회': '추진위',
    '시공자선정': '사업시행',
    '건축심의': '사업시행',
    '사업시행': '사업시행',
    '공사중': '착공',
    '입주': '준공',
}

VALID_STAGES = {
    '구역지정', '추진위', '조합설립', '사업시행', '관리처분',
    '착공', '준공', '조합해산', '해제',
}

# 정보몽땅 project_type -> DB project_type 호환 그룹
# 같은 그룹 내에서만 매칭 허용
# 재개발/재건축은 ArcGIS에서 BZ101(재개발)로 분류되었지만
# 정보몽땅에서는 재건축으로 등록된 경우가 많음 (아파트 단지) -> 상호 허용
TYPE_COMPAT = {
    '재개발': {'재개발', '재건축'},        # ArcGIS 재개발 <-> 정보몽땅 재건축 허용
    '주택재개발': {'재개발', '재건축'},
    '재건축': {'재건축', '재개발'},        # 역방향도 허용
    '주택재건축': {'재건축', '재개발'},
    '도시환경': {'도시환경'},
    '도시환경정비': {'도시환경'},
    '가로주택': {'가로주택'},
    '가로주택정비': {'가로주택'},
    '소규모재건축': {'소규모재건축', '재건축'},
    '주거환경개선': {'주거환경개선'},
}

# 명백히 다른 유형끼리의 매칭을 차단하기 위한 불호환 그룹
TYPE_INCOMPAT = {
    '도시환경': {'재개발', '재건축'},
    '도시환경정비': {'재개발', '재건축'},
    '가로주택': {'재개발', '재건축'},
    '가로주택정비': {'재개발', '재건축'},
}


def types_compatible(cleanup_type, db_type):
    """정보몽땅 사업유형과 DB 사업유형이 호환되는지"""
    if not cleanup_type or not db_type:
        return True  # 유형 정보 없으면 허용
    # 불호환 체크 (명백히 다른 유형)
    incompat = TYPE_INCOMPAT.get(cleanup_type)
    if incompat and db_type in incompat:
        return False
    # 호환 체크
    compat_set = TYPE_COMPAT.get(cleanup_type)
    if compat_set is None:
        return True  # 알 수 없는 유형은 허용
    return db_type in compat_set


def normalize_stage(raw):
    """정보몽땅 진행단계 정규화"""
    raw = raw.strip()
    for key, val in STAGE_MAP.items():
        if key in raw:
            return val
    return raw if raw else ""


def normalize_name(name):
    """구역명 정규화 (매칭용): 공백/특수문자/접미어 제거"""
    name = re.sub(r'[·\s\-\_\(\)（）\[\]【】「」『』\u3000]', '', name)
    # 사업 종류 접미어 제거
    name = re.sub(r'정비구역$', '', name)
    name = re.sub(r'구역$', '', name)
    name = re.sub(r'주택재건축정비사업.*', '', name)
    name = re.sub(r'주택재개발정비사업.*', '', name)
    name = re.sub(r'재건축정비사업.*', '', name)
    name = re.sub(r'재개발정비사업.*', '', name)
    name = re.sub(r'도시환경정비사업.*', '', name)
    name = re.sub(r'가로주택정비사업.*', '', name)
    name = re.sub(r'주거환경개선사업.*', '', name)
    name = re.sub(r'소규모재건축사업.*', '', name)
    name = re.sub(r'정비사업.*', '', name)
    name = re.sub(r'조합$', '', name)
    name = re.sub(r'일대$', '', name)
    return name.lower()


def extract_dong_number(text):
    """텍스트에서 동이름+번지 추출. "사당동305-35" -> ("사당동", "305-35")"""
    m = re.search(r'([가-힣]+동)\s*(\d+(?:-\d+)?)', text)
    if m:
        return m.group(1), m.group(2)
    return None, None


def extract_all_numbers(text):
    """텍스트에서 모든 숫자 추출 (번지 매칭용)"""
    return re.findall(r'\d+', text)


# ===== 정보몽땅 크롤링 =====

def fetch_cleanup_page(page_no=1):
    """정보몽땅 사업장 목록 한 페이지(10건)"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        log.error("beautifulsoup4 필요: pip install beautifulsoup4")
        sys.exit(1)

    data = urllib.parse.urlencode({
        'cpage': str(page_no),
        'pageSize': '10',
        'bsnsGubun': '',
        'jachiGubun': '',
        'bsnsNm': '',
        'jbeon': '',
    }).encode('utf-8')

    req = urllib.request.Request(CLEANUP_LIST_URL, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    req.add_header('User-Agent', 'Mozilla/5.0 (PropValue stage enrichment v3)')
    req.add_header('Referer', f'{CLEANUP_BASE_URL}/cleanup/bsnssttus/lscrMainIndx.do')

    resp = urllib.request.urlopen(req, timeout=30)
    html = resp.read().decode('utf-8')
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    rows = []
    table = soup.find('table')
    if not table:
        return rows
    tbody = table.find('tbody')
    if not tbody:
        return rows

    for tr in tbody.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 6:
            continue
        rows.append({
            'district': tds[1].get_text(strip=True),
            'project_type': tds[2].get_text(strip=True),
            'zone_name': tds[3].get_text(strip=True),
            'address': tds[4].get_text(strip=True),
            'stage': tds[5].get_text(strip=True),
        })
    return rows


def crawl_all_cleanup():
    """정보몽땅 전체 크롤링"""
    log.info("정보몽땅 크롤링 시작...")
    all_cleanup = []
    page = 1
    max_pages = 120
    seen_names = set()
    consecutive_dupes = 0

    while page <= max_pages:
        try:
            rows = fetch_cleanup_page(page_no=page)
        except Exception as e:
            log.warning("페이지 %d 실패: %s", page, e)
            page += 1
            time.sleep(1)
            continue

        if not rows:
            log.info("페이지 %d: 데이터 없음 -> 종료", page)
            break

        new_rows = [r for r in rows if r['zone_name'] not in seen_names]
        if not new_rows:
            consecutive_dupes += 1
            if consecutive_dupes >= 3:
                log.info("페이지 %d: 연속 3페이지 중복 -> 종료", page)
                break
        else:
            consecutive_dupes = 0
            for r in rows:
                seen_names.add(r['zone_name'])
            all_cleanup.extend(new_rows)

        if page % 20 == 0:
            log.info("  페이지 %d: 누적 %d건", page, len(all_cleanup))
        page += 1
        time.sleep(0.5)

    log.info("정보몽땅 총 %d건 수집", len(all_cleanup))
    return all_cleanup


# ===== 매칭 로직 =====

def match_cleanup_to_db(cleanup_zones, db_zones, verbose=False):
    """정보몽땅 구역을 DB 구역과 완화 기준으로 매칭

    db_zones: list of (id, zone_name, district, stage, project_type, zone_code)
    """
    # DB 구역을 구별로 인덱싱
    db_by_dist = {}
    for zid, zname, zdist, zstage, ztype, zcode in db_zones:
        if zdist not in db_by_dist:
            db_by_dist[zdist] = []
        znorm = normalize_name(zname)
        zdong, znum = extract_dong_number(zname)
        db_by_dist[zdist].append({
            'id': zid, 'name': zname, 'stage': zstage,
            'type': ztype, 'code': zcode,
            'norm': znorm, 'dong': zdong, 'num': znum,
        })

    matches = []
    matched_db_ids = set()       # DB 구역 중복 매칭 방지
    matched_cleanup_names = set()  # 정보몽땅 구역 중복 매칭 방지
    unmatched_cleanup = []

    for cz in cleanup_zones:
        cdist = cz['district']
        cname = cz['zone_name']
        cstage = normalize_stage(cz['stage'])
        if not cstage:
            continue

        cnorm = normalize_name(cname)
        cdong, cnum = extract_dong_number(cname)
        caddr = cz.get('address', '')
        ctype = cz.get('project_type', '')
        candidates = db_by_dist.get(cdist, [])

        best_match = None
        match_method = ''

        # --- 1단계: 정규화 정확 매칭 ---
        for db in candidates:
            if db['id'] in matched_db_ids:
                continue
            if not types_compatible(ctype, db['type']):
                continue
            if cnorm == db['norm']:
                best_match = db
                match_method = 'exact'
                break

        # --- 2단계: 포함 매칭 (최소 3글자, 숫자 경계 확인) ---
        if not best_match:
            for db in candidates:
                if db['id'] in matched_db_ids:
                    continue
                if not types_compatible(ctype, db['type']):
                    continue
                if len(cnorm) < 3 or len(db['norm']) < 3:
                    continue
                if cnorm in db['norm'] or db['norm'] in cnorm:
                    container = db['norm'] if cnorm in db['norm'] else cnorm
                    contained = cnorm if cnorm in db['norm'] else db['norm']
                    idx = container.find(contained)
                    end_idx = idx + len(contained)
                    # 숫자 경계: 포함된 문자열 끝이 숫자이고 바로 뒤도 숫자면 제외
                    if (contained[-1].isdigit() and end_idx < len(container)
                            and container[end_idx].isdigit()):
                        continue
                    # 시작도 마찬가지
                    if (idx > 0 and contained[0].isdigit()
                            and container[idx - 1].isdigit()):
                        continue
                    best_match = db
                    match_method = 'contains'
                    break

        # --- 3단계: 동+번지 매칭 ---
        if not best_match and cdong and cnum:
            for db in candidates:
                if db['id'] in matched_db_ids:
                    continue
                if not types_compatible(ctype, db['type']):
                    continue
                if db['dong'] == cdong and db['num'] == cnum:
                    best_match = db
                    match_method = 'dong+num'
                    break

        # --- 4단계: 주소 기반 매칭 (동+번지 정확 매칭만) ---
        if not best_match and caddr:
            adong, anum = extract_dong_number(caddr)
            if adong and anum:
                for db in candidates:
                    if db['id'] in matched_db_ids:
                        continue
                    if not types_compatible(ctype, db['type']):
                        continue
                    # DB zone_name에서도 동+번지 추출하여 정확 비교
                    if db['dong'] == adong and db['num'] == anum:
                        best_match = db
                        match_method = 'address'
                        break

        # --- 5단계: 핵심단어 매칭 (동이름 + 첫번째 숫자, 동일 유형만) ---
        if not best_match and cdong:
            cnums = extract_all_numbers(cnorm)
            if cnums:
                for db in candidates:
                    if db['id'] in matched_db_ids:
                        continue
                    if not types_compatible(ctype, db['type']):
                        continue
                    dnums = extract_all_numbers(db['norm'])
                    if db['dong'] and db['dong'] == cdong and dnums and dnums[0] == cnums[0]:
                        # 추가 확인: 두번째 숫자도 있으면 비교
                        if len(cnums) > 1 and len(dnums) > 1:
                            if cnums[1] != dnums[1]:
                                continue
                        best_match = db
                        match_method = 'keyword'
                        break

        if best_match:
            if best_match['id'] in matched_db_ids:
                continue  # 이미 매칭된 DB 구역 (안전장치)
            if cname in matched_cleanup_names:
                continue  # 이미 매칭된 정보몽땅 구역

            matched_db_ids.add(best_match['id'])
            matched_cleanup_names.add(cname)
            matches.append({
                'db_id': best_match['id'],
                'db_name': best_match['name'],
                'db_code': best_match['code'],
                'cleanup_name': cname,
                'new_stage': cstage,
                'existing_stage': best_match['stage'],
                'district': cdist,
                'project_type': best_match['type'],
                'method': match_method,
            })
        else:
            unmatched_cleanup.append(cz)

    return matches, unmatched_cleanup


def validate_matches(matches, db_zones):
    """매칭 결과 검증"""
    errors = []
    warnings = []

    # 1) DB ID 중복 체크
    id_counts = {}
    for m in matches:
        did = m['db_id']
        id_counts[did] = id_counts.get(did, 0) + 1
    for did, cnt in id_counts.items():
        if cnt > 1:
            names = [m['cleanup_name'] for m in matches if m['db_id'] == did]
            errors.append(f"DB id={did} 에 {cnt}건 중복 매칭: {names}")

    # 2) stage 유효성 확인
    for m in matches:
        if m['new_stage'] not in VALID_STAGES:
            warnings.append(
                f"비표준 stage '{m['new_stage']}' <- {m['cleanup_name']} [{m['district']}]")

    # 3) 기존 stage가 이미 있는 건 건너뛰기 확인
    overwrite_count = 0
    for m in matches:
        if m['existing_stage'] and m['existing_stage'].strip():
            overwrite_count += 1
            warnings.append(
                f"기존 stage 있음: {m['db_name']} ('{m['existing_stage']}' -> '{m['new_stage']}')")

    return errors, warnings, overwrite_count


def main():
    parser = argparse.ArgumentParser(
        description='PropValue stage 보강 v3 -- PP0101 68건 정보몽땅 재매칭')
    parser.add_argument('--dry-run', action='store_true',
                        help='DB 변경 없이 확인만')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='매칭 실패 구역도 상세 출력')
    args = parser.parse_args()

    if not DB_PARAMS['password']:
        log.error("DB_PASSWORD 환경변수가 필요합니다")
        sys.exit(1)

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # ===== 1단계: 현재 빈값 구역 목록 확인 =====
    log.info("===== 1단계: DB에서 stage 빈값 구역 조회 =====")
    cur.execute("""
        SELECT id, zone_name, district, stage, project_type, zone_code
        FROM redevelopment_zones
        WHERE source = 'urban.seoul.go.kr'
          AND (stage IS NULL OR stage = '')
        ORDER BY district, zone_name
    """)
    db_no_stage = cur.fetchall()
    log.info("stage 빈값 구역: %d건", len(db_no_stage))

    # 유형별 분포
    type_counts = {}
    for _, _, _, _, ptype, _ in db_no_stage:
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
    for ptype, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
        log.info("  %s: %d건", ptype, cnt)

    # 구별 분포
    dist_counts = {}
    for _, _, dist, _, _, _ in db_no_stage:
        dist_counts[dist] = dist_counts.get(dist, 0) + 1
    log.info("\n구별 분포:")
    for dist, cnt in sorted(dist_counts.items(), key=lambda x: -x[1]):
        log.info("  %s: %d건", dist, cnt)

    if not db_no_stage:
        log.info("보강 대상 없음. 종료.")
        cur.close()
        conn.close()
        return

    # ===== 2단계: 정보몽땅 크롤링 =====
    log.info("\n===== 2단계: 정보몽땅 크롤링 =====")
    all_cleanup = crawl_all_cleanup()

    # 정보몽땅 stage 분포
    stage_counts = {}
    for r in all_cleanup:
        s = normalize_stage(r['stage'])
        stage_counts[s] = stage_counts.get(s, 0) + 1
    log.info("정보몽땅 stage 분포:")
    for s, c in sorted(stage_counts.items(), key=lambda x: -x[1]):
        log.info("  %s: %d건", s or "(빈)", c)

    # 정보몽땅 구별 분포
    cleanup_dist = {}
    for r in all_cleanup:
        cleanup_dist[r['district']] = cleanup_dist.get(r['district'], 0) + 1
    log.info("정보몽땅 구별 분포 (대상 구 기준):")
    for dist in sorted(dist_counts.keys()):
        log.info("  %s: 정보몽땅 %d건, DB빈값 %d건",
                 dist, cleanup_dist.get(dist, 0), dist_counts.get(dist, 0))

    # ===== 3단계: 매칭 =====
    log.info("\n===== 3단계: 매칭 (완화 기준) =====")
    matches, unmatched = match_cleanup_to_db(all_cleanup, db_no_stage, verbose=args.verbose)
    log.info("매칭 결과: %d건 성공, %d건 미매칭 (정보몽땅 기준)", len(matches), len(unmatched))

    # 매칭 방법별 분포
    method_counts = {}
    for m in matches:
        method_counts[m['method']] = method_counts.get(m['method'], 0) + 1
    log.info("매칭 방법별:")
    for method, cnt in sorted(method_counts.items(), key=lambda x: -x[1]):
        log.info("  %s: %d건", method, cnt)

    # ===== 4단계: 검증 =====
    log.info("\n===== 4단계: 검증 =====")
    errors, warnings, overwrite_count = validate_matches(matches, db_no_stage)

    if errors:
        log.error("검증 실패 (%d건 오류):", len(errors))
        for e in errors:
            log.error("  [ERROR] %s", e)
        log.error("DB 업데이트를 중단합니다.")
        cur.close()
        conn.close()
        sys.exit(1)

    if warnings:
        log.warning("검증 경고 (%d건):", len(warnings))
        for w in warnings[:20]:
            log.warning("  [WARN] %s", w)
        if len(warnings) > 20:
            log.warning("  ... 외 %d건", len(warnings) - 20)

    # 기존 stage 덮어쓰기 건 필터링 (빈값만 업데이트)
    applicable = [m for m in matches
                  if not m['existing_stage'] or not m['existing_stage'].strip()]
    skipped = [m for m in matches
               if m['existing_stage'] and m['existing_stage'].strip()]
    log.info("적용 대상: %d건 (기존 stage 있어 스킵: %d건)", len(applicable), len(skipped))

    # ===== 매칭 결과 출력 =====
    log.info("\n===== 매칭 상세 =====")
    for m in applicable:
        log.info("  [%s] %-30s <- %-40s -> %s (%s)",
                 m['district'], m['db_name'][:30], m['cleanup_name'][:40],
                 m['new_stage'], m['method'])

    # 매칭 실패한 DB 구역 (가장 중요한 정보)
    matched_db_ids = set(m['db_id'] for m in matches)
    unmatched_db = [(zid, zname, zdist, ztype)
                    for zid, zname, zdist, _, ztype, _ in db_no_stage
                    if zid not in matched_db_ids]

    log.info("\n===== 매칭 실패 DB 구역: %d건 (수동 확인 필요) =====", len(unmatched_db))
    for zid, zname, zdist, ztype in unmatched_db:
        log.info("  [%s] %s (%s) id=%d", zdist, zname, ztype, zid)

    # ===== 5단계: 적용 =====
    if args.dry_run:
        log.info("\n[DRY-RUN] DB 변경을 수행하지 않습니다.")
        log.info("적용 예정: %d건", len(applicable))
    else:
        log.info("\n===== 5단계: DB 업데이트 =====")
        updated = 0
        for m in applicable:
            cur.execute("UPDATE redevelopment_zones SET stage = %s WHERE id = %s",
                        (m['new_stage'], m['db_id']))
            if cur.rowcount > 0:
                updated += 1
                log.info("  UPDATE id=%d %s -> '%s'", m['db_id'], m['db_name'], m['new_stage'])

        conn.commit()
        log.info("DB 업데이트 완료: %d건", updated)

    # ===== 6단계: 최종 통계 =====
    log.info("\n===== 6단계: 최종 통계 =====")
    cur.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN stage IS NOT NULL AND stage != '' THEN 1 ELSE 0 END)
        FROM redevelopment_zones
    """)
    total, with_stage = cur.fetchone()
    pct = with_stage * 100.0 / total if total else 0
    log.info("총 %d건, stage 보유 %d건 (%.1f%%)", total, with_stage, pct)

    # 남은 빈값 유형별
    cur.execute("""
        SELECT project_type, COUNT(*)
        FROM redevelopment_zones
        WHERE stage IS NULL OR stage = ''
        GROUP BY project_type
        ORDER BY COUNT(*) DESC
    """)
    remaining = cur.fetchall()
    if remaining:
        remaining_total = sum(c for _, c in remaining)
        log.info("남은 stage 빈값: %d건", remaining_total)
        for pt, cnt in remaining:
            log.info("  %s: %d건", pt, cnt)
    else:
        log.info("stage 빈값 없음! (100%% 커버)")

    # stage 분포
    cur.execute("""
        SELECT stage, COUNT(*) FROM redevelopment_zones
        WHERE stage IS NOT NULL AND stage != ''
        GROUP BY stage ORDER BY COUNT(*) DESC
    """)
    log.info("\nstage 분포:")
    for s, c in cur.fetchall():
        log.info("  %s: %d건", s, c)

    cur.close()
    conn.close()
    log.info("\n완료.")


if __name__ == "__main__":
    main()
