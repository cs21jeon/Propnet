#!/usr/bin/env python3
"""
BZ101 (주택재개발) PROPEL_CD 매핑 오류 수정 스크립트

문제:
  - PP0101 (87건): "준공"으로 잘못 입력됨. 실제 의미는 "추진중" (상세 단계 불명)
  - PP0103 (141건): 빈값('')으로 입력됨. 실제 의미는 "완료" (준공/이전고시 이후)

수정:
  - PP0101 구역 중 stage='준공'인 건 -> stage='' (정보몽땅 보강 데이터는 유지)
  - PP0103 구역 중 stage=''인 건 -> stage='준공'

사용:
  python fix_bz101_stage_mapping.py --dry-run     # 확인만
  python fix_bz101_stage_mapping.py               # 실행
"""
import argparse
import json
import logging
import os
import sys
import urllib.request

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('fix_bz101')

DB_PARAMS = {
    "dbname": "goldenrabbit_db",
    "user": "goldenrabbit_user",
    "password": os.environ.get("DB_PASSWORD", ""),
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
}

ARCGIS_BASE = ("https://urban.seoul.go.kr/proxy/proxy.jsp?"
               "http://98.33.2.225:6080/arcgis/rest/services/UPIS/"
               "20200526_WMS/MapServer")

LAYER_BZ101 = 94


def fetch_bz101_propel_codes():
    """ArcGIS Layer 94 (BZ101 주택재개발)에서 PRESENT_SN, PROPEL_CD 수집"""
    url = (f"{ARCGIS_BASE}/{LAYER_BZ101}/query?where=OBJECTID%3E0"
           f"&outFields=PRESENT_SN,DGM_NM,PROPEL_CD&returnGeometry=false&f=json")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (PropValue)"})

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    pp0101 = []  # 추진중 (잘못 "준공"으로 입력된 것들)
    pp0103 = []  # 완료 (빈값으로 남아있는 것들)
    other = []

    for f in data.get("features", []):
        attrs = f.get("attributes", {})
        present_sn = (attrs.get("PRESENT_SN") or "").strip()
        propel_cd = (attrs.get("PROPEL_CD") or "").strip()
        dgm_nm = (attrs.get("DGM_NM") or "").strip()

        if not present_sn:
            continue

        if propel_cd == "PP0101":
            pp0101.append({"zone_code": present_sn, "name": dgm_nm})
        elif propel_cd == "PP0103":
            pp0103.append({"zone_code": present_sn, "name": dgm_nm})
        else:
            other.append({"zone_code": present_sn, "propel_cd": propel_cd})

    return pp0101, pp0103, other


def main():
    parser = argparse.ArgumentParser(description='BZ101 PROPEL_CD 매핑 오류 수정')
    parser.add_argument('--dry-run', action='store_true', help='DB 변경 없이 확인만')
    args = parser.parse_args()

    if not DB_PARAMS['password']:
        log.error("DB_PASSWORD 환경변수가 필요합니다")
        sys.exit(1)

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # ===== 1단계: ArcGIS에서 PP0101/PP0103 구역 목록 가져오기 =====
    log.info("ArcGIS Layer 94 (BZ101) 조회 중...")
    pp0101_zones, pp0103_zones, other_zones = fetch_bz101_propel_codes()
    log.info("PP0101 (추진중): %d건", len(pp0101_zones))
    log.info("PP0103 (완료):   %d건", len(pp0103_zones))
    log.info("기타 PROPEL_CD:  %d건", len(other_zones))

    # ===== 2단계: 수정 전 현재 상태 확인 =====
    pp0101_codes = [z["zone_code"] for z in pp0101_zones]
    pp0103_codes = [z["zone_code"] for z in pp0103_zones]

    # PP0101 중 stage='준공'인 건 (잘못 입력된 건)
    if pp0101_codes:
        cur.execute("""
            SELECT id, zone_code, zone_name, stage
            FROM redevelopment_zones
            WHERE zone_code = ANY(%s) AND stage = '준공'
        """, (pp0101_codes,))
        pp0101_wrong = cur.fetchall()
    else:
        pp0101_wrong = []

    # PP0101 중 stage가 정보몽땅 등에서 보강된 건 (유지해야 함)
    if pp0101_codes:
        cur.execute("""
            SELECT id, zone_code, zone_name, stage
            FROM redevelopment_zones
            WHERE zone_code = ANY(%s) AND stage != '준공' AND stage IS NOT NULL AND stage != ''
        """, (pp0101_codes,))
        pp0101_preserved = cur.fetchall()
    else:
        pp0101_preserved = []

    # PP0103 중 stage=''인 건 (보강 대상)
    if pp0103_codes:
        cur.execute("""
            SELECT id, zone_code, zone_name, stage
            FROM redevelopment_zones
            WHERE zone_code = ANY(%s) AND (stage IS NULL OR stage = '')
        """, (pp0103_codes,))
        pp0103_empty = cur.fetchall()
    else:
        pp0103_empty = []

    # PP0103 중 이미 다른 stage가 있는 건 (덮어쓰지 않음)
    if pp0103_codes:
        cur.execute("""
            SELECT id, zone_code, zone_name, stage
            FROM redevelopment_zones
            WHERE zone_code = ANY(%s) AND stage IS NOT NULL AND stage != ''
        """, (pp0103_codes,))
        pp0103_preserved = cur.fetchall()
    else:
        pp0103_preserved = []

    log.info("")
    log.info("===== 수정 전 현황 =====")
    log.info("")
    log.info("[PP0101 - 추진중] ArcGIS %d건:", len(pp0101_zones))
    log.info("  - stage='준공' (잘못됨, 수정 대상): %d건", len(pp0101_wrong))
    log.info("  - stage=다른값 (정보몽땅 보강, 유지): %d건", len(pp0101_preserved))
    if pp0101_preserved:
        for zid, zc, zn, zs in pp0101_preserved[:10]:
            log.info("    [유지] %s (%s) stage='%s'", zn, zc, zs)
        if len(pp0101_preserved) > 10:
            log.info("    ... 외 %d건", len(pp0101_preserved) - 10)

    log.info("")
    log.info("[PP0103 - 완료] ArcGIS %d건:", len(pp0103_zones))
    log.info("  - stage='' (빈값, 수정 대상): %d건", len(pp0103_empty))
    log.info("  - stage=다른값 (이미 보강됨, 유지): %d건", len(pp0103_preserved))
    if pp0103_preserved:
        for zid, zc, zn, zs in pp0103_preserved[:10]:
            log.info("    [유지] %s (%s) stage='%s'", zn, zc, zs)
        if len(pp0103_preserved) > 10:
            log.info("    ... 외 %d건", len(pp0103_preserved) - 10)

    if args.dry_run:
        log.info("")
        log.info("[DRY-RUN] DB 변경을 수행하지 않습니다.")
        log.info("")
        log.info("수정 예정:")
        log.info("  1) PP0101 %d건: stage='준공' -> stage=''", len(pp0101_wrong))
        log.info("  2) PP0103 %d건: stage='' -> stage='준공'", len(pp0103_empty))

        if pp0101_wrong:
            log.info("")
            log.info("PP0101 수정 대상 샘플:")
            for zid, zc, zn, zs in pp0101_wrong[:20]:
                log.info("  %s (%s) '준공' -> ''", zn, zc)

        if pp0103_empty:
            log.info("")
            log.info("PP0103 수정 대상 샘플:")
            for zid, zc, zn, zs in pp0103_empty[:20]:
                log.info("  %s (%s) '' -> '준공'", zn, zc)

        cur.close()
        conn.close()
        return

    # ===== 3단계: DB 수정 =====
    log.info("")
    log.info("===== DB 수정 시작 =====")

    # PP0101: "준공" -> "" (잘못된 매핑 되돌리기)
    fix1_count = 0
    for zid, zc, zn, zs in pp0101_wrong:
        cur.execute("UPDATE redevelopment_zones SET stage = '' WHERE id = %s", (zid,))
        if cur.rowcount > 0:
            fix1_count += 1

    # PP0103: "" -> "준공" (올바른 매핑 적용)
    fix2_count = 0
    for zid, zc, zn, zs in pp0103_empty:
        cur.execute("UPDATE redevelopment_zones SET stage = '준공' WHERE id = %s", (zid,))
        if cur.rowcount > 0:
            fix2_count += 1

    conn.commit()

    log.info("")
    log.info("===== 수정 완료 =====")
    log.info("  PP0101: %d건 stage='준공' -> '' (추진중, 상세불명)", fix1_count)
    log.info("  PP0103: %d건 stage='' -> '준공' (완료)", fix2_count)

    # ===== 4단계: 수정 후 검증 =====
    cur.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN stage IS NOT NULL AND stage != '' THEN 1 ELSE 0 END)
        FROM redevelopment_zones
    """)
    total, with_stage = cur.fetchone()
    log.info("")
    log.info("===== 수정 후 전체 현황 =====")
    log.info("총 %d건, stage 보유 %d건 (%.1f%%)",
             total, with_stage, with_stage * 100.0 / total if total else 0)

    # stage 빈값 유형별 현황
    cur.execute("""
        SELECT project_type, COUNT(*)
        FROM redevelopment_zones
        WHERE stage IS NULL OR stage = ''
        GROUP BY project_type
        ORDER BY COUNT(*) DESC
    """)
    remaining = cur.fetchall()
    if remaining:
        log.info("")
        log.info("남은 stage 빈값:")
        for pt, cnt in remaining:
            log.info("  %s: %d건", pt, cnt)

    cur.close()
    conn.close()
    log.info("")
    log.info("완료.")


if __name__ == "__main__":
    main()
