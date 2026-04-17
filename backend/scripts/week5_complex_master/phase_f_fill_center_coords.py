#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase F — complex_master.center_lat/center_lon 좌표 보강.

우선순위:
  1) 로컬 building_dong_geometry 조인 (각 complex의 모든 PNU 평균 좌표)
     → 가장 빠르고 정확, VWorld 쿼터 소비 없음
  2) VWorld getCoord (주소→좌표) fallback
     → representative_pnu에 building_dong_geometry 레코드가 없는 단지

사용:
  # 로컬 DB 기반 일괄 보강
  python phase_f_fill_center_coords.py --mode local

  # VWorld 보강 (로컬로 못 채운 단지)
  python phase_f_fill_center_coords.py --mode vworld --limit 500 --rate-limit 0.3

  # 특정 시군구만
  python phase_f_fill_center_coords.py --mode local --sigungu 11710

  # dry-run
  python phase_f_fill_center_coords.py --mode local --dry-run
"""
import argparse
import json
import logging
import os
import time
import urllib.parse
import urllib.request

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('phase_f')


def load_env_file(path='/home/webapp/goldenrabbit/backend/.env'):
    if not os.path.isfile(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())


def get_conn():
    load_env_file()
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        port=int(os.environ.get('DB_PORT', '5432')),
        dbname=os.environ.get('DB_NAME', 'goldenrabbit_db'),
        user=os.environ.get('DB_USER', 'goldenrabbit_user'),
        password=os.environ.get('DB_PASSWORD', ''),
    )


# ------------------------------------------------------------------------------
# 1) 로컬 DB 기반 보강
# ------------------------------------------------------------------------------
# 각 complex_pk의 PNU 중 building_dong_geometry에 있는 건물 좌표의 평균
SQL_LOCAL_FILL = '''
WITH coords AS (
    -- center_lat NULL 단지 중 building_dong_geometry로 커버되는 것만
    SELECT cp.complex_pk,
           avg(bg.lat) AS lat,
           avg(bg.lon) AS lon,
           count(*) AS hit_count
    FROM complex_parcels cp
    JOIN building_dong_geometry bg ON bg.pnu = cp.pnu
    JOIN complex_master cm ON cm.complex_pk = cp.complex_pk
    WHERE cm.center_lat IS NULL
      {sigungu_clause}
    GROUP BY cp.complex_pk
    HAVING avg(bg.lat) IS NOT NULL
    LIMIT %s
)
UPDATE complex_master AS cm
SET center_lat = c.lat,
    center_lon = c.lon
FROM coords c
WHERE cm.complex_pk = c.complex_pk
RETURNING cm.complex_pk, cm.center_lat, cm.center_lon;
'''


def run_local_fill(sigungu_filter=None, batch_size=5000, dry_run=False):
    conn = get_conn()
    sigungu_clause = ''
    params_prefix = []
    if sigungu_filter:
        sigungu_clause = 'AND LEFT(cm.representative_pnu, 5) IN %s'
        params_prefix = [tuple(sigungu_filter)]

    total_updated = 0
    total_batches = 0
    start = time.time()

    while True:
        sql = SQL_LOCAL_FILL.format(sigungu_clause=sigungu_clause)
        params = list(params_prefix) + [batch_size]

        if dry_run:
            log.info('[DRY-RUN] SQL 실행 예정: 배치크기 %d', batch_size)
            with conn.cursor() as cur:
                cur.execute(
                    f'''SELECT count(DISTINCT cp.complex_pk)
                        FROM complex_parcels cp
                        JOIN building_dong_geometry bg ON bg.pnu = cp.pnu
                        JOIN complex_master cm ON cm.complex_pk = cp.complex_pk
                        WHERE cm.center_lat IS NULL
                        {sigungu_clause}''',
                    params_prefix,
                )
                cnt = cur.fetchone()[0]
            log.info('[DRY-RUN] 로컬 DB로 채울 수 있는 단지: %d', cnt)
            break

        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        conn.commit()
        n = len(rows)
        total_updated += n
        total_batches += 1
        elapsed = time.time() - start
        log.info('배치 %d: +%d (누적 %d, %.1f초)', total_batches, n, total_updated, elapsed)
        if n == 0:
            break
        if total_batches >= 200:
            log.warning('배치 200 초과, 중단')
            break

    conn.close()
    log.info('로컬 fill 완료: %d 단지 업데이트, %d 배치, %.1f초',
             total_updated, total_batches, time.time() - start)


# ------------------------------------------------------------------------------
# 2) VWorld getCoord 기반 보강
# ------------------------------------------------------------------------------
VWORLD_GEOCODE_URL = 'https://api.vworld.kr/req/address'


def _vworld_apikey():
    load_env_file()
    return os.environ.get('VWORLD_APIKEY', '')


def vworld_geocode(address):
    """VWorld 지번주소 → 좌표 (EPSG:4326)."""
    apikey = _vworld_apikey()
    if not apikey:
        return None
    params = {
        'service': 'address',
        'request': 'getcoord',
        'version': '2.0',
        'crs': 'epsg:4326',
        'type': 'parcel',
        'address': address,
        'format': 'json',
        'key': apikey,
    }
    url = VWORLD_GEOCODE_URL + '?' + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PropNet/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        if data.get('response', {}).get('status') != 'OK':
            return None
        pt = data['response']['result']['point']
        return float(pt['y']), float(pt['x'])  # (lat, lon)
    except Exception as e:
        log.debug('VWorld getCoord 실패 (%s): %s', address, e)
        return None


def run_vworld_fill(limit=500, rate_limit=0.3, dry_run=False):
    if not _vworld_apikey():
        log.error('VWORLD_APIKEY 환경변수 없음')
        return
    conn = get_conn()

    # 로컬로 못 채운 단지
    with conn.cursor() as cur:
        cur.execute(
            '''SELECT complex_pk, address_jibun
               FROM complex_master
               WHERE center_lat IS NULL
               ORDER BY household_count DESC NULLS LAST
               LIMIT %s''',
            (limit,),
        )
        targets = cur.fetchall()

    log.info('VWorld fill 대상: %d 단지', len(targets))

    if dry_run:
        conn.close()
        return

    updated = 0
    for i, (pk, addr) in enumerate(targets):
        coords = vworld_geocode(addr)
        if coords:
            lat, lon = coords
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE complex_master SET center_lat=%s, center_lon=%s WHERE complex_pk=%s',
                    (lat, lon, pk),
                )
            conn.commit()
            updated += 1

        if (i + 1) % 50 == 0:
            log.info('진행: %d/%d, 업데이트 %d', i + 1, len(targets), updated)

        time.sleep(rate_limit)

    conn.close()
    log.info('VWorld fill 완료: %d/%d 업데이트', updated, len(targets))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['local', 'vworld'], required=True)
    p.add_argument('--sigungu', default=None)
    p.add_argument('--batch-size', type=int, default=5000)
    p.add_argument('--limit', type=int, default=500)
    p.add_argument('--rate-limit', type=float, default=0.3)
    p.add_argument('--dry-run', action='store_true')
    return p.parse_args()


def main():
    args = parse_args()
    sigungu_filter = None
    if args.sigungu:
        sigungu_filter = [s.strip() for s in args.sigungu.split(',') if s.strip()]

    if args.mode == 'local':
        run_local_fill(
            sigungu_filter=sigungu_filter,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
    elif args.mode == 'vworld':
        run_vworld_fill(
            limit=args.limit,
            rate_limit=args.rate_limit,
            dry_run=args.dry_run,
        )


if __name__ == '__main__':
    main()
