#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase B — complex_master PNU 확장.

전략:
  1순위 (로컬 DB): building_dong_geometry에서 대표 PNU 주변 300m × bld_nm 매칭
     → 쿼터 소비 없음, 빠름. building_dong_geometry 커버리지 내에서 처리
  2순위 (VWorld): building_dong_geometry에 없는 단지만 VWorld LT_C_BLDGINFO
     → BBOX + bld_nm 매칭으로 PNU 수집

사용:
  # 로컬 DB만 사용 (쿼터 없이 빠른 1차 확장)
  python expand_pnu_by_bbox.py --mode local --sigungu 11710

  # 전국 로컬 확장
  python expand_pnu_by_bbox.py --mode local

  # VWorld 보강 (로컬 커버리지 밖)
  python expand_pnu_by_bbox.py --mode vworld --sigungu 11710 --limit 100
"""
import argparse
import json
import logging
import os
import sys
import time

import psycopg2
import psycopg2.extras
import urllib.parse
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('pnu_expander')

# ------------------------------------------------------------------------------
# DB
# ------------------------------------------------------------------------------
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
# Phase B-1: 로컬 DB 기반 확장
# ------------------------------------------------------------------------------
# 대표 PNU → building_dong_geometry 조회 → lat/lon 획득 → 반경 BBOX 내
# 같은 bld_nm (prefix) 건물의 unique PNU 수집 → complex_parcels INSERT

SQL_LOCAL_EXPAND = """
WITH target_master AS (
    -- 이미 parcels가 2개 이상인 단지는 건너뜀 (재실행 안전)
    SELECT cm.complex_pk, cm.name, cm.representative_pnu
    FROM complex_master cm
    WHERE cm.source = 'reb_csv_20250918'
      {sigungu_clause}
      AND (
        SELECT count(*) FROM complex_parcels cp2 WHERE cp2.complex_pk = cm.complex_pk
      ) = 1
    LIMIT %s
),
rep_coord AS (
    -- 대표 PNU의 좌표
    SELECT tm.complex_pk, tm.name,
           avg(bg.lat) AS lat, avg(bg.lon) AS lon
    FROM target_master tm
    JOIN building_dong_geometry bg ON bg.pnu = tm.representative_pnu
    GROUP BY tm.complex_pk, tm.name
),
nearby AS (
    -- 300m BBOX 내에서 name prefix 매칭되는 PNU 수집
    SELECT rc.complex_pk,
           bg.pnu,
           count(*) AS hit_count
    FROM rep_coord rc
    JOIN building_dong_geometry bg
      ON abs(bg.lat - rc.lat) < 0.003   -- 약 333m
     AND abs(bg.lon - rc.lon) < 0.004   -- 약 345m @ lat 37
    WHERE
        -- 단지명 prefix 매칭 (동호수 제거 후 비교)
        regexp_replace(bg.bld_nm, E' ?\\\\d+동\\\\s*$', '') = rc.name
        OR bg.bld_nm = rc.name
        OR bg.bld_nm LIKE rc.name || '%%'
    GROUP BY rc.complex_pk, bg.pnu
)
INSERT INTO complex_parcels (complex_pk, pnu, is_primary, source, confidence)
SELECT
    n.complex_pk,
    n.pnu,
    FALSE,
    'local_bdg_geom',
    0.90
FROM nearby n
ON CONFLICT (complex_pk, pnu) DO NOTHING
RETURNING complex_pk, pnu;
"""


def run_local_expand(sigungu_filter=None, batch_limit=5000, dry_run=False):
    conn = get_conn()

    sigungu_clause = ''
    if sigungu_filter:
        sgg_tuple = tuple(sigungu_filter)
        # representative_pnu 앞 5자리 비교
        sigungu_clause = "AND LEFT(cm.representative_pnu, 5) IN %s"

    total_added = 0
    total_batches = 0
    start = time.time()

    while True:
        with conn.cursor() as cur:
            if sigungu_filter:
                sql = SQL_LOCAL_EXPAND.format(sigungu_clause=sigungu_clause)
                params = [tuple(sigungu_filter), batch_limit]
            else:
                sql = SQL_LOCAL_EXPAND.format(sigungu_clause='')
                params = [batch_limit]

            if dry_run:
                log.info('[DRY-RUN] SQL 실행 예정: 배치크기 %d', batch_limit)
                cur.execute('SELECT 1')
                break

            cur.execute(sql, params)
            rows = cur.fetchall()
            added = len(rows)
            total_added += added
            total_batches += 1

        conn.commit()

        elapsed = time.time() - start
        log.info('배치 %d: +%d 건 추가 (누적 %d, %.1f초)',
                 total_batches, added, total_added, elapsed)

        # 이번 배치에서 추가가 0이면 종료. (target_master가 0 → 확장할 단지 없음)
        if added == 0:
            break

        # 안전장치: 20배치 이상이면 중단
        if total_batches >= 100:
            log.warning('배치 100 초과, 중단')
            break

    # target_master가 비면 종료. 이 경우 추가는 됐지만 loop 종료 로직 재확인
    # (실제로는 target_master filter "parcels count = 1"이 줄어들어 자연 종료됨)

    conn.close()
    log.info('완료: 추가된 PNU %d 건, 배치 %d회, 총 %.1f초',
             total_added, total_batches, time.time() - start)


# ------------------------------------------------------------------------------
# Phase B-2: VWorld 기반 확장 (로컬 커버리지 밖)
# ------------------------------------------------------------------------------
def _vworld_apikey():
    load_env_file()
    return os.environ.get('VWORLD_APIKEY', '')
VWORLD_BLDG_URL = 'https://api.vworld.kr/req/data'
VWORLD_GEOCODE_URL = 'https://api.vworld.kr/req/address'


def vworld_geocode(address, timeout=8):
    """VWorld 주소 → (lat, lon). 실패 시 None."""
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
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        if data.get('response', {}).get('status') != 'OK':
            return None
        pt = data['response']['result']['point']
        return float(pt['y']), float(pt['x'])
    except Exception as e:
        log.debug('vworld_geocode 실패 (%s): %s', address, e)
        return None


def vworld_query_buildings(lat, lon, radius_m=300):
    """VWorld LT_C_BLDGINFO 도면 조회 (BBOX)."""
    apikey = _vworld_apikey()
    # 약 300m BBOX
    dlat = radius_m / 111000.0
    dlon = radius_m / (111000.0 * 0.79)  # lat 37 근처

    params = {
        'service': 'data',
        'version': '2.0',
        'request': 'GetFeature',
        'format': 'json',
        'size': 500,
        'page': 1,
        'data': 'LT_C_BLDGINFO',
        'geometry': 'true',
        'attribute': 'true',
        'crs': 'EPSG:4326',
        'geomfilter': 'BOX({},{},{},{})'.format(
            lon - dlon, lat - dlat, lon + dlon, lat + dlat,
        ),
        'key': apikey,
    }
    url = VWORLD_BLDG_URL + '?' + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PropNet/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        log.warning('VWorld 호출 실패: %s', e)
        return None


def extract_features(payload):
    """VWorld 응답에서 features 추출."""
    if not payload:
        return []
    try:
        return payload['response']['result']['featureCollection']['features']
    except (KeyError, TypeError):
        return []


def run_vworld_expand(sigungu_filter=None, limit=100, rate_limit=0.3):
    if not _vworld_apikey():
        log.error('VWORLD_APIKEY 환경변수 없음')
        return

    conn = get_conn()

    # 로컬 확장 후에도 parcels=1인 단지 (즉 building_dong_geometry에 없는 단지)
    sql = """
    SELECT cm.complex_pk, cm.name, cm.representative_pnu, cm.address_jibun
    FROM complex_master cm
    WHERE cm.source = 'reb_csv_20250918'
      {sigungu_clause}
      AND (
        SELECT count(*) FROM complex_parcels cp WHERE cp.complex_pk = cm.complex_pk
      ) = 1
      -- VWorld 시도 기록이 있으면 재시도 회피 (현재는 단순 확장)
    ORDER BY cm.household_count DESC NULLS LAST
    LIMIT %s
    """

    sigungu_clause = ''
    params = [limit]
    if sigungu_filter:
        sigungu_clause = "AND LEFT(cm.representative_pnu, 5) IN %s"
        params = [tuple(sigungu_filter), limit]

    with conn.cursor() as cur:
        cur.execute(sql.format(sigungu_clause=sigungu_clause), params)
        targets = cur.fetchall()

    log.info('VWorld 확장 대상: %d 단지', len(targets))

    total_added = 0
    total_geocoded = 0
    for i, (complex_pk, name, rep_pnu, addr) in enumerate(targets):
        # 1) 우선 complex_master.center_lat/lon
        with conn.cursor() as cur:
            cur.execute(
                "SELECT center_lat, center_lon FROM complex_master WHERE complex_pk = %s",
                (complex_pk,),
            )
            row = cur.fetchone()
            if row and row[0] is not None and row[1] is not None:
                lat, lon = float(row[0]), float(row[1])
            else:
                # 2) building_dong_geometry
                cur.execute(
                    "SELECT lat, lon FROM building_dong_geometry WHERE pnu = %s LIMIT 1",
                    (rep_pnu,),
                )
                r2 = cur.fetchone()
                if r2:
                    lat, lon = float(r2[0]), float(r2[1])
                else:
                    # 3) VWorld getCoord (주소 기반)
                    coords = vworld_geocode(addr)
                    time.sleep(rate_limit)  # 호출마다 대기
                    if not coords:
                        log.debug('좌표 획득 실패 skip: %s (%s)', name, addr)
                        continue
                    lat, lon = coords
                    # center_lat/lon 동시 채움 (Phase F 병합)
                    cur.execute(
                        "UPDATE complex_master SET center_lat=%s, center_lon=%s WHERE complex_pk=%s AND center_lat IS NULL",
                        (lat, lon, complex_pk),
                    )
                    conn.commit()
                    total_geocoded += 1

        payload = vworld_query_buildings(float(lat), float(lon))
        features = extract_features(payload)

        added_pnus = []
        for feat in features:
            props = feat.get('properties', {})
            bld_nm = (props.get('bld_nm') or '').strip()
            pnu = props.get('pnu') or props.get('PNU') or ''
            if not pnu or not bld_nm:
                continue

            # 단지명 prefix 매칭
            clean = bld_nm.rsplit(' ', 1)[0] if bld_nm.endswith('동') else bld_nm
            if clean != name and not bld_nm.startswith(name):
                continue

            added_pnus.append(pnu)

        if added_pnus:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(
                    cur,
                    """INSERT INTO complex_parcels (complex_pk, pnu, is_primary, source, confidence)
                       VALUES %s
                       ON CONFLICT (complex_pk, pnu) DO NOTHING""",
                    [(complex_pk, p, False, 'vworld_bbox', 0.85) for p in set(added_pnus)],
                )
            conn.commit()
            total_added += len(set(added_pnus))

        if (i + 1) % 20 == 0:
            log.info('진행: %d/%d, geocoded %d, 추가 PNU %d',
                     i + 1, len(targets), total_geocoded, total_added)

        time.sleep(rate_limit)

    conn.close()
    log.info('VWorld 확장 완료: %d 단지 처리, %d geocoded, %d PNU 추가',
             len(targets), total_geocoded, total_added)


# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description='complex_master PNU 확장')
    p.add_argument('--mode', choices=['local', 'vworld'], required=True)
    p.add_argument('--sigungu', default=None, help='시군구 코드 5자리 CSV')
    p.add_argument('--batch-limit', type=int, default=5000,
                   help='로컬 확장 시 배치당 대상 단지 수')
    p.add_argument('--limit', type=int, default=100,
                   help='VWorld 확장 시 최대 처리 단지 수')
    p.add_argument('--rate-limit', type=float, default=0.3,
                   help='VWorld 호출 간격 (초)')
    p.add_argument('--dry-run', action='store_true')
    return p.parse_args()


def main():
    args = parse_args()

    sigungu_filter = None
    if args.sigungu:
        sigungu_filter = [s.strip() for s in args.sigungu.split(',') if s.strip()]

    if args.mode == 'local':
        run_local_expand(
            sigungu_filter=sigungu_filter,
            batch_limit=args.batch_limit,
            dry_run=args.dry_run,
        )
    elif args.mode == 'vworld':
        run_vworld_expand(
            sigungu_filter=sigungu_filter,
            limit=args.limit,
            rate_limit=args.rate_limit,
        )


if __name__ == '__main__':
    main()
