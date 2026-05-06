#!/usr/bin/env python3
"""
PropValue stage 보강 스크립트 — ArcGIS PROPEL_CD 필드 활용

ArcGIS 29개 레이어의 PROPEL_CD 필드에 진행단계 코드가 포함되어 있음.
이를 추출하여 DB의 stage 컬럼을 업데이트.

PROPEL_CD 코드 체계:
  - PP{type_prefix}{stage_suffix} 형식
  - type_prefix: 01(재개발), 02(재건축/도시환경/주거환경개선/소규모재건축),
                 03(가로주택), 08(재정비촉진지구), 10(도시재생), 18(뉴타운재개발) 등
  - stage_suffix 공통 매핑:
    04=구역지정, 05=추진위, 06=조합설립, 07=사업시행인가,
    08=관리처분, 09=착공, 10=준공, 11=이전고시, 12=조합해산

  - BZ101 (주택재개발, Layer 94) 특수: PP0101=추진중(상세불명), PP0103=완료(준공)

사용:
  python enrich_stage_from_arcgis.py          # 실행
  python enrich_stage_from_arcgis.py --dry-run  # DB 변경 없이 확인만
"""
import argparse
import json
import logging
import os
import sys
import time
import urllib.request

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('enrich_stage')

DB_PARAMS = {
    "dbname": "goldenrabbit_db",
    "user": "goldenrabbit_user",
    "password": os.environ.get("DB_PASSWORD", ""),
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
}

ARCGIS_BASE = "https://urban.seoul.go.kr/proxy/proxy.jsp?http://98.33.2.225:6080/arcgis/rest/services/UPIS/20200526_WMS/MapServer"

# Layer ID → (BZ code, project_type)
LAYERS = {
    94: ("BZ101", "재개발"),
    95: ("BZ102", "재건축"),
    96: ("BZ103", "도시환경"),
    97: ("BZ104", "주거환경개선"),
    98: ("BZ105", "소규모재건축"),
    99: ("BZ107", "가로주택"),
    100: ("BZ108", "기타"),
    101: ("BZ201", "택지개발"),
    102: ("BZ202", "지구단위계획"),
    103: ("BZ203", "도시개발"),
    104: ("BZ204", "도시계획시설"),
    105: ("BZ205", "시가지조성"),
    106: ("BZ301", "재정비촉진"),
    107: ("BZ302", "재개발"),
    108: ("BZ303", "재건축"),
    109: ("BZ304", "도시환경"),
    110: ("BZ305", "주거환경개선"),
    111: ("BZ306", "가로주택"),
    112: ("BZ401", "도시재생"),
    113: ("BZ402", "도시재생"),
    114: ("BZ403", "도시재생"),
    115: ("BZ404", "도시재생"),
    116: ("BZ501", "역세권"),
    117: ("BZ502", "역세권"),
    118: ("BZ601", "혁신도시"),
    119: ("BZ602", "기업도시"),
    120: ("BZ603", "경제자유구역"),
    121: ("BZ604", "국토부"),
    122: ("BZ606", "신도시"),
}

# PROPEL_CD suffix → stage 매핑 (공통)
# suffix는 뒤 2자리
STAGE_SUFFIX_MAP = {
    "01": "",           # BZ101 전용: PP0101 = 추진중(상세불명) → 빈값
    "02": "구역지정",   # 일부 레이어에서 사용
    "03": "준공",       # BZ101 전용: PP0103 = 완료(준공/이전고시 이후)
    "04": "구역지정",   # 정비구역 지정 단계
    "05": "추진위",     # 추진위원회 승인
    "06": "조합설립",   # 조합설립인가
    "07": "사업시행",   # 사업시행인가
    "08": "관리처분",   # 관리처분인가
    "09": "착공",       # 착공
    "10": "준공",       # 준공인가
    "11": "준공",       # 이전고시 (= 준공 이후)
    "12": "조합해산",   # 조합해산 (= 사업 완전 종료)
}

# BZ101 (주택재개발) Layer 94 특수 처리
# PP0101 = 추진중(구역지정~관리처분 등 진행 중, 상세 불명) → 빈값
# PP0103 = 완료(준공/이전고시 이후) → "준공"
BZ101_SPECIAL = {
    "PP0101": "",      # 추진중 (세부 단계 불명 → 빈값, 정보몽땅에서 보강)
    "PP0103": "준공",  # 완료 (준공/이전고시 이후)
}


def fetch_layer_propel_codes(layer_id):
    """ArcGIS 레이어에서 PRESENT_SN과 PROPEL_CD 쌍 수집"""
    url = (f"{ARCGIS_BASE}/{layer_id}/query?where=OBJECTID%3E0"
           f"&outFields=PRESENT_SN,DGM_NM,PROPEL_CD&returnGeometry=false&f=json")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (PropValue)"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        log.error("Layer %d fetch 실패: %s", layer_id, e)
        return []

    results = []
    for f in data.get("features", []):
        attrs = f.get("attributes", {})
        present_sn = (attrs.get("PRESENT_SN") or "").strip()
        propel_cd = (attrs.get("PROPEL_CD") or "").strip()
        dgm_nm = (attrs.get("DGM_NM") or "").strip()

        if present_sn and propel_cd:
            results.append({
                "present_sn": present_sn,
                "propel_cd": propel_cd,
                "dgm_nm": dgm_nm,
            })

    return results


def propel_to_stage(propel_cd, layer_id):
    """PROPEL_CD → stage 변환"""
    if not propel_cd or len(propel_cd) < 4:
        return ""

    # BZ101 (Layer 94) 특수 처리
    if layer_id == 94:
        if propel_cd in BZ101_SPECIAL:
            return BZ101_SPECIAL[propel_cd]
        # fallback: suffix 기반
        suffix = propel_cd[-2:]
        return STAGE_SUFFIX_MAP.get(suffix, "")

    # 일반 레이어: suffix 2자리로 매핑
    suffix = propel_cd[-2:]
    return STAGE_SUFFIX_MAP.get(suffix, "")


def main():
    parser = argparse.ArgumentParser(description='ArcGIS PROPEL_CD → stage 보강')
    parser.add_argument('--dry-run', action='store_true', help='DB 변경 없이 확인만')
    args = parser.parse_args()

    if not DB_PARAMS['password']:
        log.error("DB_PASSWORD 환경변수가 필요합니다")
        sys.exit(1)

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # 현재 상태 확인
    cur.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN stage IS NOT NULL AND stage != '' THEN 1 ELSE 0 END)
        FROM redevelopment_zones
    """)
    total, with_stage = cur.fetchone()
    log.info("현재 상태: 총 %d건, stage 보유 %d건 (%d%%)",
             total, with_stage, with_stage * 100 // total if total else 0)

    # ArcGIS에서 PROPEL_CD 수집
    all_mappings = {}  # present_sn → stage
    layer_stats = {}

    for layer_id, (bz_code, type_name) in LAYERS.items():
        log.info("Layer %d (%s %s) 수집 중...", layer_id, bz_code, type_name)
        features = fetch_layer_propel_codes(layer_id)

        mapped = 0
        for f in features:
            stage = propel_to_stage(f["propel_cd"], layer_id)
            if stage:
                all_mappings[f["present_sn"]] = {
                    "stage": stage,
                    "propel_cd": f["propel_cd"],
                    "dgm_nm": f["dgm_nm"],
                }
                mapped += 1

        layer_stats[bz_code] = {
            "total": len(features),
            "mapped": mapped,
            "type": type_name,
        }
        log.info("  → %d건 중 %d건 stage 매핑 가능", len(features), mapped)
        time.sleep(0.3)

    log.info("\n=== ArcGIS PROPEL_CD 수집 완료 ===")
    log.info("총 매핑 가능: %d건", len(all_mappings))

    # stage 분포 확인
    stage_dist = {}
    for v in all_mappings.values():
        s = v["stage"]
        stage_dist[s] = stage_dist.get(s, 0) + 1
    log.info("Stage 분포:")
    for s, cnt in sorted(stage_dist.items(), key=lambda x: -x[1]):
        log.info("  %s: %d건", s, cnt)

    if args.dry_run:
        log.info("\n[DRY-RUN] DB 업데이트를 건너뜁니다")
        # 매칭률 예상
        cur.execute("""
            SELECT zone_code FROM redevelopment_zones
            WHERE source = 'urban.seoul.go.kr'
              AND (stage IS NULL OR stage = '')
        """)
        empty_zones = set(r[0] for r in cur.fetchall())
        matched = len(empty_zones.intersection(all_mappings.keys()))
        log.info("stage 없는 구역 %d건 중 %d건 매칭 예상", len(empty_zones), matched)
        cur.close()
        conn.close()
        return

    # DB 업데이트
    log.info("\n=== DB 업데이트 시작 ===")
    updated = 0
    skipped_has_stage = 0
    skipped_no_match = 0

    # zone_code = PRESENT_SN인 구역만 대상
    cur.execute("""
        SELECT id, zone_code, stage FROM redevelopment_zones
        WHERE source = 'urban.seoul.go.kr'
    """)
    db_zones = cur.fetchall()

    for zid, zone_code, current_stage in db_zones:
        if zone_code not in all_mappings:
            skipped_no_match += 1
            continue

        new_stage = all_mappings[zone_code]["stage"]

        # 이미 정보몽땅에서 더 정확한 stage가 있으면 덮어쓰지 않음
        if current_stage and current_stage.strip():
            skipped_has_stage += 1
            continue

        cur.execute(
            "UPDATE redevelopment_zones SET stage = %s WHERE id = %s",
            (new_stage, zid)
        )
        if cur.rowcount > 0:
            updated += 1

    conn.commit()

    log.info("업데이트 완료:")
    log.info("  - 새로 stage 설정: %d건", updated)
    log.info("  - 이미 stage 있어 건너뜀: %d건", skipped_has_stage)
    log.info("  - zone_code 매칭 안 됨: %d건", skipped_no_match)

    # 최종 상태
    cur.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN stage IS NOT NULL AND stage != '' THEN 1 ELSE 0 END)
        FROM redevelopment_zones
    """)
    total_after, with_stage_after = cur.fetchone()
    log.info("\n=== 최종 상태 ===")
    log.info("총 %d건, stage 보유 %d건 (%d%%)",
             total_after, with_stage_after,
             with_stage_after * 100 // total_after if total_after else 0)
    log.info("개선: %d건 → %d건 (+%d건)",
             with_stage, with_stage_after, with_stage_after - with_stage)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
