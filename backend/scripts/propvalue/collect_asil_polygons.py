#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
아실(asil.kr) 정비구역 폴리곤 수집 → redevelopment_zones.geometry 업데이트

아실의 data_redevelop.jsp API에서 구역별 폴리곤 좌표를 수집하여
기존 redevelopment_zones 테이블의 geometry 컬럼에 저장.

사용:
  python collect_asil_polygons.py --dry-run
  python collect_asil_polygons.py
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
log = logging.getLogger('collect_asil')

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'dbname': os.environ.get('DB_NAME', 'goldenrabbit_db'),
    'user': os.environ.get('DB_USER', 'goldenrabbit_user'),
    'password': os.environ.get('DB_PASSWORD', ''),
}

ASIL_URL = 'https://asil.kr/json/data_redevelop.jsp'

# 수도권 영역을 격자로 분할 (서울+경기+인천)
# 각 격자: 약 0.1도 ≈ 11km
def generate_grid():
    """수도권 영역을 0.08도 격자로 분할"""
    grids = []
    # 서울+경기+인천: 위도 37.0~37.9, 경도 126.3~127.4
    lat_start, lat_end = 37.0, 37.9
    lon_start, lon_end = 126.3, 127.4
    step = 0.08

    lat = lat_start
    while lat < lat_end:
        lon = lon_start
        while lon < lon_end:
            grids.append((lat, lon, lat + step, lon + step))
            lon += step
        lat += step

    return grids


def fetch_asil_area(s_lat, s_lng, e_lat, e_lng, dev_type=0, step=0):
    """아실 API에서 해당 영역의 정비구역 데이터 수집"""
    params = urllib.parse.urlencode({
        'os': 'pc',
        'user': '1',
        'type': str(dev_type),
        'step': str(step),
        'zoom': '14',
        'code': '',
        's_lat': f'{s_lat:.6f}',
        's_lng': f'{s_lng:.6f}',
        'e_lat': f'{e_lat:.6f}',
        'e_lng': f'{e_lng:.6f}',
    })
    url = f'{ASIL_URL}?{params}'
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
    req.add_header('Referer', 'https://asil.kr/asil/index.jsp')

    resp = urllib.request.urlopen(req, timeout=30)
    raw = resp.read()
    text = raw.decode('euc-kr', errors='replace')

    if len(text.strip()) <= 2:  # "[]" or "["
        return []

    return json.loads(text)


def collect_all_polygons():
    """수도권 전체 격자에서 폴리곤 수집"""
    grids = generate_grid()
    all_zones = {}  # key -> zone data (중복 제거)

    log.info("격자 수: %d개", len(grids))

    for i, (s_lat, s_lng, e_lat, e_lng) in enumerate(grids):
        for dev_type in [0, 1, 2, 3]:
            try:
                zones = fetch_asil_area(s_lat, s_lng, e_lat, e_lng, dev_type=dev_type)
                for z in zones:
                    key = z.get('key', '')
                    if key and key not in all_zones and z.get('polygon'):
                        all_zones[key] = z
            except Exception as e:
                log.debug("격자 %d type=%d 실패: %s", i, dev_type, e)

            time.sleep(0.1)  # rate limit

        if (i + 1) % 20 == 0:
            log.info("격자 %d/%d 완료 (구역 %d건)", i + 1, len(grids), len(all_zones))

    return list(all_zones.values())


def parse_title(title):
    """아실 title에서 사업유형과 구역명 분리"""
    # "재개발 한남3재정비촉진구역" → ("재개발", "한남3재정비촉진구역")
    # "재건축 신속통합기획<BR>압구정3구역" → ("재건축", "압구정3구역")
    title = title.replace('<BR>', ' ').replace('<br>', ' ')
    parts = title.split(' ', 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return '', title.strip()


def polygon_to_geojson(polygon_data):
    """아실 polygon 데이터 → GeoJSON Polygon"""
    if not polygon_data or not isinstance(polygon_data, list):
        return None

    # 아실 형식: [{"coordinates": [[[lon, lat], ...], ...]}]
    for item in polygon_data:
        coords = item.get('coordinates')
        if coords:
            return {
                'type': 'Polygon',
                'coordinates': coords,
            }
    return None


def save_polygons(zones, dry_run=False):
    """폴리곤 데이터를 DB에 저장/업데이트"""
    if dry_run:
        log.info("[DRY-RUN] %d건 폴리곤 저장 예정", len(zones))
        for z in zones[:5]:
            ptype, name = parse_title(z.get('title', ''))
            poly = z.get('polygon', [])
            coord_count = sum(len(p.get('coordinates', [[]])[0]) for p in poly) if poly else 0
            log.info("  %s | %s | %s | coords=%d", z.get('key'), ptype, name, coord_count)
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 기존 zone_name으로 매칭하여 geometry 업데이트
    # 또는 새로운 구역이면 INSERT
    upsert_sql = """
        INSERT INTO redevelopment_zones
            (zone_name, zone_code, city, district, project_type, stage,
             geometry, center_lat, center_lon, source, raw_data, updated_at)
        VALUES
            (%(zone_name)s, %(zone_code)s, %(city)s, '', %(project_type)s, %(stage)s,
             %(geometry)s, %(center_lat)s, %(center_lon)s, 'asil', %(raw_data)s, NOW())
        ON CONFLICT (zone_code) DO UPDATE SET
            geometry = EXCLUDED.geometry,
            center_lat = COALESCE(EXCLUDED.center_lat, redevelopment_zones.center_lat),
            center_lon = COALESCE(EXCLUDED.center_lon, redevelopment_zones.center_lon),
            updated_at = NOW()
    """

    # 기존 DB 데이터의 zone_name → id 매핑 (geometry 업데이트용)
    cur.execute("SELECT id, zone_name, zone_code FROM redevelopment_zones WHERE geometry IS NULL")
    existing = {row[1]: (row[0], row[2]) for row in cur.fetchall()}

    updated = 0
    inserted = 0

    for z in zones:
        ptype, name = parse_title(z.get('title', ''))
        geojson = polygon_to_geojson(z.get('polygon'))
        if not geojson:
            continue

        lat = float(z.get('lat', 0)) if z.get('lat') else None
        lon = float(z.get('lng', 0)) if z.get('lng') else None
        stage = z.get('desc', '').strip()

        # 기존 DB에서 이름으로 매칭 시도
        matched_id = None
        for db_name, (db_id, db_code) in existing.items():
            # 부분 매칭: 아실 이름이 DB 이름에 포함되거나 역
            if name in db_name or db_name in name:
                matched_id = db_id
                break

        if matched_id:
            # geometry만 업데이트
            cur.execute(
                "UPDATE redevelopment_zones SET geometry = %s, updated_at = NOW() WHERE id = %s",
                (json.dumps(geojson), matched_id)
            )
            updated += 1
        else:
            # 새 구역 INSERT
            zone_code = f"asil-{z.get('key', name)}"
            params = {
                'zone_name': name,
                'zone_code': zone_code,
                'city': '',  # 좌표로 역추론 가능
                'project_type': ptype,
                'stage': stage,
                'geometry': json.dumps(geojson),
                'center_lat': lat,
                'center_lon': lon,
                'raw_data': json.dumps({
                    'key': z.get('key'),
                    'title': z.get('title'),
                    'desc': z.get('desc'),
                }, ensure_ascii=False),
            }
            try:
                cur.execute(upsert_sql, params)
                inserted += 1
            except Exception as e:
                log.error("INSERT 실패 (%s): %s", name, e)
                conn.rollback()

        if (updated + inserted) % 50 == 0 and (updated + inserted) > 0:
            conn.commit()
            log.info("  %d건 처리 (updated=%d, inserted=%d)", updated + inserted, updated, inserted)

    conn.commit()
    cur.close()
    conn.close()
    log.info("총 %d건 처리 (updated=%d, inserted=%d)", updated + inserted, updated, inserted)


def main():
    parser = argparse.ArgumentParser(description='아실 정비구역 폴리곤 수집')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    if not DB_CONFIG['password'] and not args.dry_run:
        log.error("DB_PASSWORD 환경변수 필요")
        sys.exit(1)

    log.info("아실 정비구역 폴리곤 수집 시작")
    zones = collect_all_polygons()
    log.info("총 %d건 폴리곤 수집 완료", len(zones))

    if zones:
        save_polygons(zones, dry_run=args.dry_run)

    log.info("완료!")


if __name__ == '__main__':
    main()
