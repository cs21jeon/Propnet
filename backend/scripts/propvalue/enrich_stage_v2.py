#!/usr/bin/env python3
"""
PropValue stage 보강 v2 — 지구단위계획 480건 + 도시재생 79건 + 재개발 89건

이전 enrich_stage_from_arcgis.py에서 누락된 PROPEL_CD 코드 체계를 보완:
- PP05xx: 지구단위계획 전용 코드 (이전 스크립트에서 suffix 00~06 → 미매핑)
- PP10xx/PP11xx/PP21xx: 도시재생/재정비촉진 전용 코드
- PP0101: 재개발 "추진중"(상세불명) → 정보몽땅 재매칭으로 보강
- PP0103: 재개발 "완료" → stage="준공"

=== PROPEL_CD 코드 체계 (전체) ===

1) 정비사업 (BZ101~BZ108, BZ301~BZ306) — suffix 기반:
   01=추진중(BZ101전용, 상세불명→빈값), 03=완료/준공(BZ101전용)
   04=구역지정, 05=추진위, 06=조합설립, 07=사업시행, 08=관리처분,
   09=착공, 10=준공, 11=이전고시(준공), 12=조합해산

2) 지구단위계획 (BZ202, Layer 102) — PP05xx:
   PP0500=결정(기본), PP0501=변경1, PP0502=변경2, PP0503=변경3,
   PP0504=변경4, PP0505=변경5, PP0506=변경6
   → 모두 "결정고시" 상태 (지구단위계획은 결정/변경/해제만 있음)

3) 도시재생 BZ401 (Layer 112) — PP10xx:
   PP1001=촉진지구 지정, PP1002=촉진지구 해제
   → 재정비촉진지구 단위의 전체 지정/해제 상태

4) 도시재생 BZ402 (Layer 113) — PP11xx:
   suffix 매핑은 정비사업과 동일 (04~12 + 13=해제완료)

5) 도시재생 BZ403/BZ404 (Layer 114~115) — PP21xx:
   PP2101=지정, PP2102=진행, PP2103=해제

사용:
  python enrich_stage_v2.py --dry-run     # DB 변경 없이 확인
  python enrich_stage_v2.py               # 실행
  python enrich_stage_v2.py --cleanup-retry  # 정보몽땅 재매칭도 실행
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
log = logging.getLogger('enrich_v2')

DB_PARAMS = {
    "dbname": "goldenrabbit_db",
    "user": "goldenrabbit_user",
    "password": os.environ.get("DB_PASSWORD", ""),
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
}

ARCGIS_BASE = ("https://urban.seoul.go.kr/proxy/proxy.jsp?"
               "http://98.33.2.225:6080/arcgis/rest/services/UPIS/"
               "20200526_WMS/MapServer")

# ========== PROPEL_CD → stage 매핑 (전체) ==========

# 공통 suffix 매핑 (정비사업 + 재정비촉진 구역)
COMMON_SUFFIX_MAP = {
    "01": "",           # BZ101 전용: 추진중(상세불명) → 빈값
    "02": "구역지정",
    "03": "준공",       # BZ101 전용: 완료(준공/이전고시 이후)
    "04": "구역지정",
    "05": "추진위",
    "06": "조합설립",
    "07": "사업시행",
    "08": "관리처분",
    "09": "착공",
    "10": "준공",
    "11": "준공",       # 이전고시
    "12": "조합해산",
    "13": "해제",       # 재정비촉진 구역에서 사용 (해제완료)
}

# 지구단위계획 전용 (PP05xx)
# 지구단위계획은 정비사업과 달리 결정/변경/해제만 있음
# ArcGIS에 폴리곤이 있다 = 이미 결정고시됨
JIGU_STAGE_MAP = {
    "PP0500": "결정",
    "PP0501": "결정",
    "PP0502": "결정",
    "PP0503": "결정",
    "PP0504": "결정",
    "PP0505": "결정",
    "PP0506": "결정",
}

# 도시재생 BZ401 (Layer 112) — 재정비촉진지구 단위
DOSIJAE_BZ401_MAP = {
    "PP1001": "지정",     # 촉진지구 지정
    "PP1002": "해제",     # 촉진지구 해제
}

# 도시재생 BZ403/BZ404 (Layer 114~115)
DOSIJAE_BZ403_MAP = {
    "PP2101": "지정",
    "PP2102": "진행",
    "PP2103": "해제",
}

# 대상 레이어 (stage 빈값 가능성이 높은 레이어만)
TARGET_LAYERS = {
    # 지구단위계획
    102: ("BZ202", "지구단위계획"),
    # 도시재생 4개 레이어
    112: ("BZ401", "도시재생"),
    113: ("BZ402", "도시재생"),
    114: ("BZ403", "도시재생"),
    115: ("BZ404", "도시재생"),
    # 재개발 BZ101 (PP0101 추진중 재확인용)
    94: ("BZ101", "재개발"),
}


def fetch_layer_all(layer_id):
    """ArcGIS 레이어에서 PRESENT_SN과 PROPEL_CD 수집"""
    url = (f"{ARCGIS_BASE}/{layer_id}/query?where=OBJECTID%3E0"
           f"&outFields=PRESENT_SN,DGM_NM,PROPEL_CD&returnGeometry=false&f=json")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (PropValue)"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        log.error("Layer %d fetch error: %s", layer_id, e)
        return []

    results = []
    for f in data.get("features", []):
        attrs = f.get("attributes", {})
        present_sn = (attrs.get("PRESENT_SN") or "").strip()
        propel_cd = (attrs.get("PROPEL_CD") or "").strip()
        dgm_nm = (attrs.get("DGM_NM") or "").strip()
        if present_sn:
            results.append({
                "present_sn": present_sn,
                "propel_cd": propel_cd,
                "dgm_nm": dgm_nm,
            })
    return results


def propel_to_stage(propel_cd, layer_id):
    """PROPEL_CD → stage 변환 (확장 매핑)"""
    if not propel_cd:
        return ""

    # 1) 지구단위계획 전용 매핑 (PP05xx)
    if propel_cd in JIGU_STAGE_MAP:
        return JIGU_STAGE_MAP[propel_cd]

    # 2) 도시재생 BZ401 전용 매핑 (PP10xx)
    if propel_cd in DOSIJAE_BZ401_MAP:
        return DOSIJAE_BZ401_MAP[propel_cd]

    # 3) 도시재생 BZ403/BZ404 전용 매핑 (PP21xx)
    if propel_cd in DOSIJAE_BZ403_MAP:
        return DOSIJAE_BZ403_MAP[propel_cd]

    # 4) 공통 suffix 매핑 (PP11xx 포함)
    if len(propel_cd) >= 4:
        suffix = propel_cd[-2:]

        # BZ101 (Layer 94) 특수 처리
        if layer_id == 94:
            if propel_cd == "PP0101":
                return ""      # 추진중이지만 상세 불명
            if propel_cd == "PP0103":
                return "준공"  # 완료 (준공/이전고시 이후)

        return COMMON_SUFFIX_MAP.get(suffix, "")

    return ""


# ========== 정보몽땅 재매칭 (재개발 89건 타겟) ==========

CLEANUP_BASE_URL = 'https://cleanup.seoul.go.kr'
CLEANUP_LIST_URL = f'{CLEANUP_BASE_URL}/cleanup/bsnssttus/lsubBsnsSttus.do'

CLEANUP_STAGE_MAP = {
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
}


def normalize_cleanup_stage(raw):
    """정보몽땅 진행단계 정규화"""
    raw = raw.strip()
    for key, val in CLEANUP_STAGE_MAP.items():
        if key in raw:
            return val
    return raw if raw else ""


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
    req.add_header('User-Agent', 'Mozilla/5.0 (PropValue stage enrichment v2)')
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


def normalize_name(name):
    """구역명 정규화 (매칭용)"""
    name = re.sub(r'[·\s\-\_\(\)（）\[\]【】]', '', name)
    name = re.sub(r'구역$', '', name)
    name = re.sub(r'정비구역$', '', name)
    name = re.sub(r'재건축정비사업.*', '', name)
    name = re.sub(r'재개발정비사업.*', '', name)
    name = re.sub(r'도시환경정비사업.*', '', name)
    name = re.sub(r'가로주택정비사업.*', '', name)
    name = re.sub(r'주거환경개선사업.*', '', name)
    name = re.sub(r'정비사업.*', '', name)
    name = re.sub(r'조합$', '', name)
    return name.lower()


def match_cleanup_to_db(cleanup_zones, db_zones):
    """정보몽땅 구역을 DB 구역과 완화 기준으로 매칭

    db_zones: list of (id, zone_name, district, stage, project_type)
    """
    db_by_dist = {}
    for zid, zname, zdist, zstage, ztype in db_zones:
        if zdist not in db_by_dist:
            db_by_dist[zdist] = []
        db_by_dist[zdist].append((zid, zname, zstage, ztype, normalize_name(zname)))

    matches = []
    matched_ids = set()

    for cz in cleanup_zones:
        cdist = cz['district']
        cname = cz['zone_name']
        cstage = normalize_cleanup_stage(cz['stage'])
        if not cstage:
            continue

        cnorm = normalize_name(cname)
        candidates = db_by_dist.get(cdist, [])

        best_match = None

        # 1) 정확 매칭
        for zid, zname, zstage, ztype, znorm in candidates:
            if zid in matched_ids:
                continue
            if cnorm == znorm:
                best_match = (zid, zname, zstage, ztype)
                break

        # 2) 포함 매칭 (완화: 최소 3글자)
        if not best_match:
            for zid, zname, zstage, ztype, znorm in candidates:
                if zid in matched_ids:
                    continue
                if len(cnorm) >= 3 and len(znorm) >= 3:
                    if cnorm in znorm or znorm in cnorm:
                        # 숫자 경계 확인
                        container = znorm if cnorm in znorm else cnorm
                        contained = cnorm if cnorm in znorm else znorm
                        idx = container.find(contained)
                        end_idx = idx + len(contained)
                        if (contained[-1].isdigit() and end_idx < len(container)
                                and container[end_idx].isdigit()):
                            continue
                        best_match = (zid, zname, zstage, ztype)
                        break

        # 3) 동+번호 매칭
        if not best_match:
            cm = re.search(r'([가-힣]+?)(\d+)', cnorm)
            if cm:
                cdong, cnum = cm.group(1), cm.group(2)
                for zid, zname, zstage, ztype, znorm in candidates:
                    if zid in matched_ids:
                        continue
                    zm = re.search(r'([가-힣]+?)(\d+)', znorm)
                    if zm and zm.group(1) == cdong and zm.group(2) == cnum:
                        z_end = zm.end()
                        if z_end < len(znorm) and znorm[z_end].isdigit():
                            continue
                        best_match = (zid, zname, zstage, ztype)
                        break

        # 4) 주소 기반 매칭 (새로 추가: "OO동 NNN" 패턴)
        if not best_match and cz.get('address'):
            addr = cz['address']
            addr_m = re.search(r'([가-힣]+동)\s*(\d+)', addr)
            if addr_m:
                adong, anum = addr_m.group(1), addr_m.group(2)
                for zid, zname, zstage, ztype, znorm in candidates:
                    if zid in matched_ids:
                        continue
                    if adong in zname and anum in zname:
                        best_match = (zid, zname, zstage, ztype)
                        break

        if best_match:
            zid, zname, existing_stage, ztype = best_match
            matched_ids.add(zid)
            matches.append({
                'db_id': zid,
                'db_name': zname,
                'cleanup_name': cname,
                'new_stage': cstage,
                'existing_stage': existing_stage,
                'district': cdist,
                'project_type': ztype,
            })

    return matches


def run_arcgis_enrichment(conn, dry_run=False):
    """ArcGIS PROPEL_CD 기반 stage 보강 (지구단위계획 + 도시재생)"""
    cur = conn.cursor()

    # 현재 상태
    cur.execute("""
        SELECT project_type,
               COUNT(*) as total,
               SUM(CASE WHEN stage IS NOT NULL AND stage != '' THEN 1 ELSE 0 END) as with_stage
        FROM redevelopment_zones
        WHERE source = 'urban.seoul.go.kr'
          AND project_type IN ('지구단위계획', '도시재생')
        GROUP BY project_type
        ORDER BY project_type
    """)
    log.info("=== 보강 전 상태 (대상 유형) ===")
    for ptype, total, ws in cur.fetchall():
        log.info("  %s: %d건 중 stage %d건 (%d%%)",
                 ptype, total, ws, ws * 100 // total if total else 0)

    # ArcGIS에서 PROPEL_CD 수집
    all_mappings = {}  # present_sn → {stage, propel_cd, dgm_nm}

    for layer_id, (bz_code, type_name) in TARGET_LAYERS.items():
        if layer_id == 94:
            continue  # 재개발은 별도 처리
        log.info("Layer %d (%s %s) 수집 중...", layer_id, bz_code, type_name)
        features = fetch_layer_all(layer_id)

        mapped = 0
        no_propel = 0
        for f in features:
            stage = propel_to_stage(f["propel_cd"], layer_id)
            if stage:
                all_mappings[f["present_sn"]] = {
                    "stage": stage,
                    "propel_cd": f["propel_cd"],
                    "dgm_nm": f["dgm_nm"],
                    "layer_id": layer_id,
                }
                mapped += 1
            elif not f["propel_cd"]:
                no_propel += 1

        log.info("  %d건 중 stage 매핑 %d건, PROPEL_CD 없음 %d건",
                 len(features), mapped, no_propel)
        time.sleep(0.3)

    log.info("총 매핑 가능: %d건", len(all_mappings))

    # stage 분포
    stage_dist = {}
    for v in all_mappings.values():
        s = v["stage"]
        stage_dist[s] = stage_dist.get(s, 0) + 1
    log.info("매핑 stage 분포:")
    for s, cnt in sorted(stage_dist.items(), key=lambda x: -x[1]):
        log.info("  %s: %d건", s, cnt)

    if dry_run:
        # 매칭률 예상
        cur.execute("""
            SELECT zone_code FROM redevelopment_zones
            WHERE source = 'urban.seoul.go.kr'
              AND (stage IS NULL OR stage = '')
        """)
        empty_codes = set(r[0] for r in cur.fetchall())
        matched = len(empty_codes.intersection(all_mappings.keys()))
        log.info("[DRY-RUN] stage 없는 %d건 중 %d건 매칭 예상", len(empty_codes), matched)

        # 유형별 매칭
        cur.execute("""
            SELECT zone_code, project_type FROM redevelopment_zones
            WHERE source = 'urban.seoul.go.kr'
              AND (stage IS NULL OR stage = '')
        """)
        by_type = {}
        for zc, pt in cur.fetchall():
            if zc in all_mappings:
                by_type[pt] = by_type.get(pt, 0) + 1
        log.info("유형별 매칭 예상:")
        for pt, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
            log.info("  %s: %d건", pt, cnt)

        return 0

    # DB 업데이트
    log.info("\n=== DB 업데이트 ===")
    updated = 0
    skipped_has = 0
    skipped_no = 0

    cur.execute("""
        SELECT id, zone_code, stage FROM redevelopment_zones
        WHERE source = 'urban.seoul.go.kr'
    """)
    for zid, zone_code, current_stage in cur.fetchall():
        if zone_code not in all_mappings:
            skipped_no += 1
            continue

        if current_stage and current_stage.strip():
            skipped_has += 1
            continue

        new_stage = all_mappings[zone_code]["stage"]
        cur.execute("UPDATE redevelopment_zones SET stage = %s WHERE id = %s",
                    (new_stage, zid))
        if cur.rowcount > 0:
            updated += 1

    conn.commit()
    log.info("ArcGIS 업데이트: +%d건 (이미 있음: %d, 매칭 안됨: %d)",
             updated, skipped_has, skipped_no)
    return updated


def run_cleanup_retry(conn, dry_run=False):
    """정보몽땅 재매칭 (재개발 PP0101 추진중 상세불명 건 타겟)"""
    cur = conn.cursor()

    log.info("\n=== 정보몽땅 재매칭 시작 ===")

    # 크롤링
    log.info("정보몽땅 크롤링...")
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

    # DB에서 stage 없는 구역
    cur.execute("""
        SELECT id, zone_name, district, stage, project_type
        FROM redevelopment_zones
        WHERE source = 'urban.seoul.go.kr'
          AND (stage IS NULL OR stage = '')
    """)
    db_no_stage = cur.fetchall()
    log.info("DB stage 없는 구역: %d건", len(db_no_stage))

    if not db_no_stage:
        log.info("보강 대상 없음")
        return 0

    matches = match_cleanup_to_db(all_cleanup, db_no_stage)
    log.info("매칭 결과: %d건", len(matches))

    if dry_run:
        log.info("[DRY-RUN] 매칭 샘플:")
        for m in matches[:30]:
            log.info("  [%s] %s <- %s -> %s (기존: %s)",
                     m['district'], m['db_name'], m['cleanup_name'],
                     m['new_stage'], m['existing_stage'] or '(없음)')
        return 0

    updated = 0
    for m in matches:
        cur.execute("UPDATE redevelopment_zones SET stage = %s WHERE id = %s",
                    (m['new_stage'], m['db_id']))
        if cur.rowcount > 0:
            updated += 1

    conn.commit()
    log.info("정보몽땅 재매칭 업데이트: +%d건", updated)
    return updated


def print_final_stats(conn):
    """최종 통계 출력"""
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN stage IS NOT NULL AND stage != '' THEN 1 ELSE 0 END)
        FROM redevelopment_zones
    """)
    total, with_stage = cur.fetchone()

    log.info("\n=== 최종 통계 ===")
    log.info("총 %d건, stage 보유 %d건 (%d%%)",
             total, with_stage, with_stage * 100 // total if total else 0)

    # 유형별 통계
    cur.execute("""
        SELECT project_type,
               COUNT(*) as total,
               SUM(CASE WHEN stage IS NOT NULL AND stage != '' THEN 1 ELSE 0 END) as with_stage
        FROM redevelopment_zones
        GROUP BY project_type
        ORDER BY total DESC
    """)
    log.info("\n유형별 stage 현황:")
    log.info("  %-16s %6s %8s %6s", "유형", "총건수", "stage有", "비율")
    log.info("  " + "-" * 40)
    for ptype, t, ws in cur.fetchall():
        log.info("  %-16s %6d %8d %5d%%", ptype, t, ws, ws * 100 // t if t else 0)

    # stage 분포
    cur.execute("""
        SELECT stage, COUNT(*) FROM redevelopment_zones
        WHERE stage IS NOT NULL AND stage != ''
        GROUP BY stage ORDER BY COUNT(*) DESC
    """)
    log.info("\nstage 분포:")
    for s, c in cur.fetchall():
        log.info("  %s: %d건", s, c)

    # 여전히 빈 값인 구역 샘플
    cur.execute("""
        SELECT project_type, COUNT(*)
        FROM redevelopment_zones
        WHERE stage IS NULL OR stage = ''
        GROUP BY project_type
        ORDER BY COUNT(*) DESC
    """)
    remaining = cur.fetchall()
    if remaining:
        log.info("\n남은 stage 빈값:")
        for pt, cnt in remaining:
            log.info("  %s: %d건", pt, cnt)

    cur.close()


def main():
    parser = argparse.ArgumentParser(description='PropValue stage 보강 v2')
    parser.add_argument('--dry-run', action='store_true', help='DB 변경 없이 확인만')
    parser.add_argument('--cleanup-retry', action='store_true',
                        help='정보몽땅 재매칭도 실행 (재개발 89건 타겟)')
    parser.add_argument('--skip-arcgis', action='store_true',
                        help='ArcGIS 보강 건너뜀 (정보몽땅만 실행)')
    args = parser.parse_args()

    if not DB_PARAMS['password']:
        log.error("DB_PASSWORD 환경변수가 필요합니다")
        sys.exit(1)

    conn = psycopg2.connect(**DB_PARAMS)

    try:
        # 1) ArcGIS PROPEL_CD 보강 (지구단위계획 + 도시재생)
        arcgis_updated = 0
        if not args.skip_arcgis:
            log.info("========== 1단계: ArcGIS PROPEL_CD 보강 ==========")
            arcgis_updated = run_arcgis_enrichment(conn, dry_run=args.dry_run)

        # 2) 정보몽땅 재매칭 (재개발 89건)
        cleanup_updated = 0
        if args.cleanup_retry:
            log.info("\n========== 2단계: 정보몽땅 재매칭 ==========")
            cleanup_updated = run_cleanup_retry(conn, dry_run=args.dry_run)

        # 3) 최종 통계
        print_final_stats(conn)

        if not args.dry_run:
            log.info("\n총 보강: ArcGIS +%d건, 정보몽땅 +%d건 = +%d건",
                     arcgis_updated, cleanup_updated,
                     arcgis_updated + cleanup_updated)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
