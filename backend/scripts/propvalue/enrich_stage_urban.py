#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PropValue stage_urban 보강 — ArcGIS PROPEL_CD → 추진단계 raw 텍스트

urban.seoul.go.kr ArcGIS 전 레이어(94~122)에서 PRESENT_SN + PROPEL_CD를 수집하고,
PROPEL 코드 매핑 API로 "공사중 - 착공" 형태의 추진단계 텍스트를 생성하여
redevelopment_zones.stage_urban 컬럼에 저장.

실행:
  source /home/webapp/goldenrabbit/backend/venv/bin/activate
  export $(grep -v '^#' /home/webapp/goldenrabbit/backend/.env | xargs)
  cd /home/webapp/goldenrabbit/backend/scripts/propvalue
  python3 enrich_stage_urban.py
  python3 enrich_stage_urban.py --dry-run
"""
import argparse
import json
import logging
import os
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
log = logging.getLogger('enrich_stage_urban')

DB_CFG = dict(
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    port=int(os.environ.get("DB_PORT", 5432)),
    dbname=os.environ.get("DB_NAME", "goldenrabbit_db"),
    user=os.environ.get("DB_USER", "goldenrabbit_user"),
    password=os.environ.get("DB_PASSWORD", ""),
)

ARCGIS_BASE = (
    "https://urban.seoul.go.kr/proxy/proxy.jsp?"
    "http://98.33.2.225:6080/arcgis/rest/services/UPIS/20200526_WMS/MapServer"
)

# ArcGIS 레이어 ID 범위 (94~122)
LAYER_IDS = list(range(94, 123))


def fetch_propel_mapping():
    """urban.seoul.go.kr API에서 PROPEL_CD → (그룹명, 단계명) 매핑 가져오기"""
    url = 'https://urban.seoul.go.kr/bsns/getPropelCdByCd.json'
    data = json.dumps({'propelCd': ''}).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (PropValue)')
    req.add_header('Referer', 'https://urban.seoul.go.kr/')

    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode('utf-8'))

    mapping = {}
    for item in result:
        cd = item.get('propelCd', '')
        nm = item.get('propelCdNm', '')
        grp = item.get('propelGrpNm', '')
        if cd and nm:
            mapping[cd] = (grp, nm)

    log.info("PROPEL 코드 매핑: %d건 로드", len(mapping))
    return mapping


def propel_to_text(propel_cd, mapping):
    """PROPEL_CD → "공사중 - 착공" 형태 텍스트 변환"""
    if not propel_cd or propel_cd not in mapping:
        return propel_cd or ''
    grp, nm = mapping[propel_cd]
    if grp and grp != nm:
        return f"{grp} - {nm}"
    return nm


def fetch_layer_propel(layer_id):
    """ArcGIS 레이어에서 PRESENT_SN + PROPEL_CD 수집"""
    where = urllib.parse.quote("1=1")
    url = (f"{ARCGIS_BASE}/{layer_id}/query?where={where}"
           f"&outFields=PRESENT_SN,DGM_NM,PROPEL_CD"
           f"&returnGeometry=false&f=json")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (PropValue)"})

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
    except Exception as e:
        log.debug("Layer %d fetch 실패: %s", layer_id, e)
        return {}

    results = {}
    for f in data.get("features", []):
        attrs = f.get("attributes", {})
        sn = (attrs.get("PRESENT_SN") or "").strip()
        propel = (attrs.get("PROPEL_CD") or "").strip()
        if sn and propel:
            results[sn] = propel

    return results


def ensure_column(conn):
    """stage_urban 컬럼이 없으면 추가"""
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'redevelopment_zones' AND column_name = 'stage_urban'
    """)
    if not cur.fetchone():
        log.info("stage_urban 컬럼 추가 중...")
        cur.execute("ALTER TABLE redevelopment_zones ADD COLUMN stage_urban TEXT DEFAULT ''")
        conn.commit()
        log.info("stage_urban 컬럼 추가 완료")
    cur.close()


def main():
    parser = argparse.ArgumentParser(description='ArcGIS PROPEL_CD → stage_urban 보강')
    parser.add_argument('--dry-run', action='store_true', help='DB 업데이트 없이 확인만')
    args = parser.parse_args()

    if not DB_CFG['password'] and not args.dry_run:
        log.error("DB_PASSWORD 환경변수 필요")
        sys.exit(1)

    # 1) PROPEL 코드 매핑 로드
    log.info("=== 1단계: PROPEL 코드 매핑 로드 ===")
    mapping = fetch_propel_mapping()

    # 2) ArcGIS 전 레이어에서 PRESENT_SN → PROPEL_CD 수집
    log.info("=== 2단계: ArcGIS PROPEL_CD 수집 (레이어 %d~%d) ===",
             LAYER_IDS[0], LAYER_IDS[-1])
    all_propel = {}  # PRESENT_SN → PROPEL_CD
    for lid in LAYER_IDS:
        results = fetch_layer_propel(lid)
        if results:
            # 기존 매핑이 없는 경우에만 추가 (첫 매칭 우선이 아닌, 더 상세한 코드 우선)
            for sn, propel in results.items():
                if sn not in all_propel:
                    all_propel[sn] = propel
                else:
                    # 기존 코드가 "추진중" 계열(01,03 등)이고 새 코드가 더 상세하면 교체
                    old = all_propel[sn]
                    old_grp = mapping.get(old, ('', ''))[0]
                    new_grp = mapping.get(propel, ('', ''))[0]
                    # "공사중", "완료" 등 더 진행된 단계 우선
                    priority = {'완료': 4, '공사중': 3, '추진중': 2, '기타': 1, '': 0}
                    if priority.get(new_grp, 0) > priority.get(old_grp, 0):
                        all_propel[sn] = propel
            log.info("  Layer %d: %d건 (누적 %d건)", lid, len(results), len(all_propel))
        time.sleep(0.3)

    log.info("ArcGIS 총 %d개 구역의 PROPEL_CD 수집 완료", len(all_propel))

    # 3) DB 업데이트
    log.info("=== 3단계: DB 업데이트 ===")

    if args.dry_run:
        # 샘플 출력
        count = 0
        for sn, propel in list(all_propel.items())[:20]:
            text = propel_to_text(propel, mapping)
            log.info("  [DRY-RUN] %s → %s → %s", sn[:30], propel, text)
            count += 1
        log.info("[DRY-RUN] 총 %d건 업데이트 예정", len(all_propel))
        return

    conn = psycopg2.connect(**DB_CFG)
    ensure_column(conn)
    cur = conn.cursor()

    # DB에서 urban.seoul.go.kr 소스 구역의 zone_code 목록 로드
    cur.execute("""
        SELECT id, zone_code FROM redevelopment_zones
        WHERE source = 'urban.seoul.go.kr'
    """)
    db_zones = {row[1]: row[0] for row in cur.fetchall()}
    log.info("DB urban 구역: %d건", len(db_zones))

    updated = 0
    for zone_code, zone_id in db_zones.items():
        propel = all_propel.get(zone_code)
        if propel:
            text = propel_to_text(propel, mapping)
            cur.execute(
                "UPDATE redevelopment_zones SET stage_urban = %s WHERE id = %s",
                (text, zone_id)
            )
            updated += 1

        if updated % 200 == 0 and updated > 0:
            conn.commit()
            log.info("  %d건 커밋...", updated)

    conn.commit()
    cur.close()
    conn.close()
    log.info("총 %d건 stage_urban 업데이트 완료 (DB urban 구역 %d건 중)", updated, len(db_zones))


if __name__ == '__main__':
    main()
