#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIS건물통합정보 SHP → building_dong_geometry 일괄 로드.

공공데이터포털 AL_D010_XX_YYYYMMDD.shp 파일을 읽어서
building_dong_geometry 테이블에 UPSERT.

좌표계: SHP는 EPSG:5174(TM) → EPSG:4326(WGS84) 변환.

사용:
  python load_shp_to_dong_geometry.py --shp-dir "D:/임시/shp"
  python load_shp_to_dong_geometry.py --shp-dir "D:/임시/shp" --dry-run
  python load_shp_to_dong_geometry.py --shp-dir "D:/임시/shp" --file AL_D010_11_20260409
"""
import argparse
import glob
import json
import logging
import os
import time

import psycopg2
import shapefile

# pyproj for coordinate transformation
try:
    from pyproj import Transformer
    _transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)
    def tm_to_wgs84(x, y):
        lon, lat = _transformer.transform(x, y)
        return lon, lat
except ImportError:
    # fallback: approximate conversion (less accurate)
    import math
    def tm_to_wgs84(x, y):
        # Very rough approximation for Korea TM → WGS84
        # Better to install pyproj: pip install pyproj
        lon = 126.0 + (x - 200000) / 89000
        lat = 33.0 + (y - 0) / 111000
        return lon, lat
    print("WARNING: pyproj not installed, using approximate coordinate conversion")
    print("         Install with: pip install pyproj")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('load_shp')

DB_CONFIG = {
    'host': '175.119.224.71',
    'port': 5432,
    'dbname': 'goldenrabbit_db',
    'user': 'goldenrabbit_user',
    'password': os.environ.get('DB_PASSWORD', '***REMOVED***'),
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def polygon_center_tm(shape):
    """SHP shape → TM 중심좌표"""
    pts = shape.points
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def shape_to_geojson_wgs84(shape):
    """SHP shape → GeoJSON (WGS84 변환)"""
    if shape.shapeType == 0:  # NULL
        return None

    parts = list(shape.parts) + [len(shape.points)]
    rings = []
    for i in range(len(parts) - 1):
        ring_pts = shape.points[parts[i]:parts[i+1]]
        ring_wgs = []
        for x, y in ring_pts:
            lon, lat = tm_to_wgs84(x, y)
            ring_wgs.append([round(lon, 7), round(lat, 7)])
        rings.append(ring_wgs)

    if len(rings) == 1:
        return {'type': 'Polygon', 'coordinates': rings}
    else:
        return {'type': 'Polygon', 'coordinates': rings}


def load_one_shp(shp_path, conn, batch_size=5000, dry_run=False, valid_pnus=None):
    """1개 SHP 파일 로드"""
    basename = os.path.basename(shp_path).replace('.shp', '')
    log.info('로드 시작: %s', basename)

    sf = shapefile.Reader(shp_path, encoding='euc-kr')
    total = len(sf)
    log.info('  레코드 수: %d', total)

    if dry_run:
        # 샘플 3건만 출력
        for i, (rec, shape) in enumerate(zip(sf.iterRecords(), sf.iterShapes())):
            if i >= 3:
                break
            cx, cy = polygon_center_tm(shape) or (0, 0)
            lon, lat = tm_to_wgs84(cx, cy)
            log.info('  sample: pnu=%s bld_nm=%s dong_nm=%s ufid=%s lat=%.6f lon=%.6f',
                     rec[2], rec[9], rec[24], rec[21], lat, lon)
        return 0

    cur = conn.cursor()
    inserted = 0
    skipped = 0
    batch_data = []
    batch_keys = set()  # 배치 내 bd_mgt_sn 중복 방지
    start = time.time()

    for i, (rec, shape) in enumerate(zip(sf.iterRecords(), sf.iterShapes())):
        # A21 = UFID (건물고유번호) — bd_mgt_sn
        bd_mgt_sn = rec[21] if rec[21] else None
        if not bd_mgt_sn or bd_mgt_sn in batch_keys:
            skipped += 1
            continue

        pnu = rec[2] if rec[2] else None  # A2 = PNU (19자리)
        if not pnu or len(str(pnu)) != 19:
            skipped += 1
            continue

        # complex_parcels에 있는 PNU만 로드
        if valid_pnus and pnu not in valid_pnus:
            skipped += 1
            continue

        bld_nm = rec[9] if rec[9] else None  # A9 = 건물명
        dong_nm = rec[24] if rec[24] else None  # A24 = 동명
        grnd_flr = int(rec[26]) if rec[26] else None  # A26 = 지상층수
        archarea = float(rec[12]) if rec[12] else None  # A12 = 건축면적

        # 좌표 변환
        center_tm = polygon_center_tm(shape)
        if not center_tm:
            skipped += 1
            continue

        lon, lat = tm_to_wgs84(center_tm[0], center_tm[1])

        # GeoJSON (좌표 변환된)
        geojson = shape_to_geojson_wgs84(shape)

        batch_keys.add(bd_mgt_sn)
        batch_data.append((
            bd_mgt_sn, pnu, dong_nm, bld_nm, lat, lon,
            json.dumps(geojson) if geojson else None,
            grnd_flr, archarea,
        ))

        if len(batch_data) >= batch_size:
            _upsert_batch(cur, batch_data)
            conn.commit()
            inserted += len(batch_data)
            batch_data = []
            batch_keys.clear()
            elapsed = time.time() - start
            log.info('  진행: %d/%d (%.1f%%), 저장 %d, skip %d (%.0f초)',
                     i + 1, total, (i + 1) / total * 100, inserted, skipped, elapsed)

    # 남은 배치
    if batch_data:
        _upsert_batch(cur, batch_data)
        conn.commit()
        inserted += len(batch_data)

    elapsed = time.time() - start
    log.info('  완료: %s — 저장 %d, skip %d (%.0f초)', basename, inserted, skipped, elapsed)
    return inserted


def _upsert_batch(cur, batch):
    """배치 UPSERT"""
    args_str = ','.join(
        cur.mogrify(
            "(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,NOW())",
            row
        ).decode('utf-8')
        for row in batch
    )
    cur.execute(f"""
        INSERT INTO building_dong_geometry
            (bd_mgt_sn, pnu, dong_nm, bld_nm, lat, lon, geometry, grnd_flr, archarea, updated_at)
        VALUES {args_str}
        ON CONFLICT (bd_mgt_sn) DO UPDATE SET
            pnu = EXCLUDED.pnu, dong_nm = EXCLUDED.dong_nm, bld_nm = EXCLUDED.bld_nm,
            lat = EXCLUDED.lat, lon = EXCLUDED.lon, geometry = EXCLUDED.geometry,
            grnd_flr = EXCLUDED.grnd_flr, archarea = EXCLUDED.archarea, updated_at = NOW()
    """)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--shp-dir', required=True, help='SHP 파일 디렉토리')
    parser.add_argument('--file', default=None, help='특정 파일만 (확장자 없이)')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--batch-size', type=int, default=5000)
    args = parser.parse_args()

    if args.file:
        shp_files = [os.path.join(args.shp_dir, args.file + '.shp')]
    else:
        shp_files = sorted(glob.glob(os.path.join(args.shp_dir, 'AL_D010_*.shp')))

    if not shp_files:
        log.error('SHP 파일 없음: %s', args.shp_dir)
        return

    log.info('SHP 파일 %d개 발견', len(shp_files))

    conn = get_conn()
    log.info('DB 접속 OK (%s)', DB_CONFIG['host'])

    # complex_parcels PNU set 로드 (단지에 속한 PNU만 필터링)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT pnu FROM complex_parcels")
    valid_pnus = {r[0] for r in cur.fetchall()}
    log.info('complex_parcels PNU: %d개 (이 PNU만 로드)', len(valid_pnus))

    total_inserted = 0
    start = time.time()

    for shp_path in shp_files:
        try:
            n = load_one_shp(shp_path, conn, batch_size=args.batch_size, dry_run=args.dry_run, valid_pnus=valid_pnus)
            total_inserted += n
        except Exception as e:
            log.error('파일 로드 실패 %s: %s', shp_path, e)
            try:
                conn.rollback()
            except Exception:
                pass
            # 재연결
            try:
                conn.close()
            except Exception:
                pass
            conn = get_conn()

    elapsed = time.time() - start
    log.info('전체 완료: %d건 저장 (%.0f초)', total_inserted, elapsed)

    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM building_dong_geometry")
        log.info('[현황] building_dong_geometry: %d건', cur.fetchone()[0])
    except Exception:
        pass

    conn.close()


if __name__ == '__main__':
    main()
