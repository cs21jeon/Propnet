#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VWorld 정비구역 SHP → redevelopment_zones.geometry 업데이트

LSMD_CONT_UD602_*.zip SHP 파일에서 폴리곤 좌표를 추출하여
기존 DB 레코드와 중심좌표 근접 매칭 → geometry 업데이트.
매칭 안 되는 구역은 새로 INSERT.

사용:
  python load_vworld_shp.py --shp-dir /home/webapp/goldenrabbit/data/propvalue_shp
  python load_vworld_shp.py --shp-dir /home/webapp/goldenrabbit/data/propvalue_shp --dry-run
"""
import argparse
import glob
import json
import logging
import os
import sys
import zipfile

import psycopg2
import psycopg2.extras
import shapefile
from pyproj import Transformer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('load_vworld_shp')

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'dbname': os.environ.get('DB_NAME', 'goldenrabbit_db'),
    'user': os.environ.get('DB_USER', 'goldenrabbit_user'),
    'password': os.environ.get('DB_PASSWORD', ''),
}

# EPSG:5186 (GRS80 TM중부) → EPSG:4326 (WGS84)
_transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)

# 시도코드 → 시/도명
SIDO_MAP = {
    '11': '서울특별시', '26': '부산광역시', '27': '대구광역시',
    '28': '인천광역시', '29': '광주광역시', '30': '대전광역시',
    '31': '울산광역시', '36': '세종특별자치시',
    '41': '경기도', '42': '강원특별자치도', '43': '충청북도',
    '44': '충청남도', '45': '전북특별자치도', '46': '전라남도',
    '47': '경상북도', '48': '경상남도', '50': '제주특별자치도',
}


def tm_to_wgs84(x, y):
    lon, lat = _transformer.transform(x, y)
    return round(lon, 7), round(lat, 7)


def shape_to_geojson(shape):
    """SHP shape → GeoJSON Polygon (WGS84 변환)"""
    if shape.shapeType == 0 or not shape.points:
        return None, None, None

    parts = list(shape.parts) + [len(shape.points)]
    rings = []
    all_lats = []
    all_lons = []

    for i in range(len(parts) - 1):
        ring_pts = shape.points[parts[i]:parts[i + 1]]
        ring_wgs = []
        for x, y in ring_pts:
            lon, lat = tm_to_wgs84(x, y)
            ring_wgs.append([lon, lat])
            all_lats.append(lat)
            all_lons.append(lon)
        rings.append(ring_wgs)

    geojson = {'type': 'Polygon', 'coordinates': rings}
    center_lat = (min(all_lats) + max(all_lats)) / 2
    center_lon = (min(all_lons) + max(all_lons)) / 2

    return geojson, round(center_lat, 7), round(center_lon, 7)


def extract_shp_from_zip(zip_path, extract_dir):
    """ZIP에서 SHP 파일 추출, SHP 경로 반환"""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)

    shp_files = glob.glob(os.path.join(extract_dir, '**', '*.shp'), recursive=True)
    return shp_files


def load_shp_file(shp_path):
    """SHP 파일에서 정비구역 데이터 추출"""
    sf = shapefile.Reader(shp_path, encoding='euc-kr', encodingErrors='replace')
    fields = [f[0] for f in sf.fields[1:]]
    log.info("  Fields: %s, Records: %d", fields, len(sf))

    zones = []
    for rec in sf.iterShapeRecords():
        r = rec.record.as_dict()
        geojson, center_lat, center_lon = shape_to_geojson(rec.shape)
        if not geojson:
            continue

        alias = r.get('ALIAS', '').strip()
        remark = r.get('REMARK', '').strip()
        col_adm = r.get('COL_ADM_SE', '').strip()
        mnum = r.get('MNUM', '').strip()

        # 시도코드 추출 (COL_ADM_SE 앞 2자리 또는 MNUM에서)
        sido_code = ''
        if len(col_adm) >= 2:
            sido_code = col_adm[:2]
        elif len(mnum) >= 10:
            # MNUM 형식에서 시도코드 추출 시도
            for code in SIDO_MAP:
                if code in mnum[:10]:
                    sido_code = code
                    break

        zones.append({
            'alias': alias,
            'remark': remark,
            'col_adm_se': col_adm,
            'mnum': mnum,
            'sido_code': sido_code,
            'city': SIDO_MAP.get(sido_code, ''),
            'geometry': geojson,
            'center_lat': center_lat,
            'center_lon': center_lon,
            'num_points': len(rec.shape.points),
        })

    return zones


def match_and_save(zones, dry_run=False):
    """DB 레코드와 중심좌표 근접 매칭 → geometry 업데이트 (1:N 허용)"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # geometry 없는 DB 레코드만 대상
    cur.execute("""
        SELECT id, zone_name, zone_code, city, district, center_lat, center_lon
        FROM redevelopment_zones
        WHERE geometry IS NULL AND center_lat IS NOT NULL
    """)
    db_zones = cur.fetchall()
    log.info("geometry 없는 DB 레코드: %d건", len(db_zones))

    # 1:N 매칭 — 하나의 SHP 폴리곤을 여러 DB 구역에 매칭 허용
    # 500m 이내(≈ 0.005도)
    MATCH_THRESHOLD = 0.005
    matched = 0
    skipped = 0

    for z in zones:
        if not z['geometry']:
            continue

        geo_json = json.dumps(z['geometry'])

        # 이 SHP 폴리곤과 가까운 DB 구역 모두 찾기
        nearby = []
        for db in db_zones:
            dist = abs(float(db['center_lat']) - z['center_lat']) + abs(float(db['center_lon']) - z['center_lon'])
            if dist < MATCH_THRESHOLD:
                nearby.append((db, dist))

        if nearby:
            for db, dist in nearby:
                if not dry_run:
                    cur.execute(
                        "UPDATE redevelopment_zones SET geometry = %s, updated_at = NOW() WHERE id = %s AND geometry IS NULL",
                        (geo_json, db['id'])
                    )
                matched += 1
        else:
            skipped += 1

        if matched % 200 == 0 and matched > 0:
            if not dry_run:
                conn.commit()
            log.info("  진행: matched=%d, skipped=%d", matched, skipped)

    if not dry_run:
        conn.commit()

    cur.close()
    conn.close()
    log.info("완료: matched=%d, skipped=%d (total SHP=%d)", matched, skipped, len(zones))


def main():
    parser = argparse.ArgumentParser(description='VWorld 정비구역 SHP → DB geometry')
    parser.add_argument('--shp-dir', required=True, help='SHP zip 파일 디렉토리')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--regions', default='서울,경기,인천', help='처리할 지역 (쉼표 구분)')
    args = parser.parse_args()

    if not DB_CONFIG['password'] and not args.dry_run:
        log.error("DB_PASSWORD 환경변수 필요")
        sys.exit(1)

    regions = [r.strip() for r in args.regions.split(',')]
    all_zones = []

    for region in regions:
        pattern = os.path.join(args.shp_dir, f'LSMD_CONT_UD602_{region}.zip')
        zips = glob.glob(pattern)
        if not zips:
            log.warning("파일 없음: %s", pattern)
            continue

        for zip_path in zips:
            log.info("처리: %s", os.path.basename(zip_path))
            extract_dir = zip_path.replace('.zip', '')
            os.makedirs(extract_dir, exist_ok=True)
            shp_files = extract_shp_from_zip(zip_path, extract_dir)

            for shp in shp_files:
                log.info("  SHP: %s", os.path.basename(shp))
                zones = load_shp_file(shp)
                log.info("  → %d 구역 추출", len(zones))
                all_zones.extend(zones)

    log.info("총 %d 구역 추출 완료", len(all_zones))

    if all_zones:
        if args.dry_run:
            log.info("[DRY-RUN] 매칭 시뮬레이션")
        match_and_save(all_zones, dry_run=args.dry_run)

    log.info("완료!")


if __name__ == '__main__':
    main()
