#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
building_dong_geometry 배치 수집.

complex_master(50세대+) 단지의 PNU를 기반으로
VWorld WFS(lt_c_bldginfo)에서 동별 좌표를 수집하여
building_dong_geometry 테이블에 저장.

사용:
  # dry-run
  python batch_collect_dong_geometry.py --dry-run

  # 실행 (기본 limit=30000, rate=0.3초)
  python batch_collect_dong_geometry.py --limit 30000 --rate-limit 0.3

  # 최소 세대수 지정
  python batch_collect_dong_geometry.py --min-household 100 --limit 20000
"""
import argparse
import json
import logging
import math
import os
import time

import psycopg2
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('batch_dong')

WFS_URL = 'https://api.vworld.kr/req/wfs'
DATA_URL = 'https://api.vworld.kr/req/data'
TIMEOUT = 15
BBOX_RADIUS_M = 400.0


def load_env(path='/home/webapp/goldenrabbit/backend/.env'):
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


def get_conn():
    load_env()
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        port=int(os.environ.get('DB_PORT', '5432')),
        dbname=os.environ.get('DB_NAME', 'goldenrabbit_db'),
        user=os.environ.get('DB_USER', 'goldenrabbit_user'),
        password=os.environ.get('DB_PASSWORD', ''),
    )


def get_apikey():
    load_env()
    return os.environ.get('VWORLD_APIKEY', '')


# ── 좌표 유틸 ──

def bbox_from_center(lat, lon, radius_m=BBOX_RADIUS_M):
    lat_rad = math.radians(lat)
    d_lat = radius_m / 111320.0
    d_lon = radius_m / (111320.0 * max(math.cos(lat_rad), 0.01))
    return f'{lon - d_lon},{lat - d_lat},{lon + d_lon},{lat + d_lat}'


def polygon_center(geom):
    pts = flatten_coords(geom)
    if not pts:
        return None
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return ((min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2)


def flatten_coords(geom):
    if not geom:
        return []
    t = geom.get('type')
    c = geom.get('coordinates') or []
    out = []
    if t == 'Point':
        out.append(c)
    elif t == 'LineString':
        out.extend(c)
    elif t == 'Polygon':
        for ring in c:
            out.extend(ring)
    elif t == 'MultiPolygon':
        for poly in c:
            for ring in poly:
                out.extend(ring)
    return out


# ── VWorld API ──

def get_parcel_center(pnu, apikey):
    """PNU → 필지 중심좌표 (VWorld Data API)"""
    try:
        resp = requests.get(DATA_URL, params={
            'key': apikey,
            'service': 'data',
            'version': '2.0',
            'request': 'GetFeature',
            'data': 'LP_PA_CBND_BUBUN',
            'attrFilter': f'pnu:=:{pnu}',
            'geometry': 'true',
            'size': 1,
            'format': 'json',
            'crs': 'EPSG:4326',
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        features = (body.get('response', {})
                    .get('result', {})
                    .get('featureCollection', {})
                    .get('features', [])) or []
        if features:
            geom = features[0].get('geometry') or {}
            center = polygon_center(geom)
            if center:
                return center  # (lon, lat)
    except Exception as e:
        log.debug('필지 좌표 조회 실패 pnu=%s: %s', pnu, e)
    return None


def get_buildings_in_bbox(bbox, apikey, max_features=200):
    """BBOX 내 건물 조회 (VWorld WFS lt_c_bldginfo)"""
    try:
        resp = requests.get(WFS_URL, params={
            'key': apikey,
            'service': 'WFS',
            'version': '2.0.0',
            'request': 'GetFeature',
            'typename': 'lt_c_bldginfo',
            'srsname': 'EPSG:4326',
            'output': 'application/json',
            'bbox': bbox,
            'maxFeatures': max_features,
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get('features', []) or []
    except Exception as e:
        log.debug('WFS 조회 실패 bbox=%s: %s', bbox, e)
        return []


# ── 메인 로직 ──

def collect_for_pnu(pnu, apikey, conn):
    """
    1 PNU에 대해 동별 좌표 수집 → building_dong_geometry 저장.
    반환: (호출수, 저장수)
    """
    api_calls = 0

    # 1) center_lat이 있으면 complex_master에서 가져오기 (API 호출 절약)
    cur = conn.cursor()
    cur.execute("""
        SELECT cm.center_lat, cm.center_lon
        FROM complex_parcels cp
        JOIN complex_master cm ON cm.complex_pk = cp.complex_pk
        WHERE cp.pnu = %s AND cm.center_lat IS NOT NULL
        LIMIT 1
    """, (pnu,))
    row = cur.fetchone()

    if row and row[0]:
        center_lat, center_lon = float(row[0]), float(row[1])
    else:
        # Data API로 필지 중심 조회
        result = get_parcel_center(pnu, apikey)
        api_calls += 1
        if not result:
            return api_calls, 0
        center_lon, center_lat = result

    # 2) BBOX → WFS 건물 조회
    bbox = bbox_from_center(center_lat, center_lon, BBOX_RADIUS_M)
    features = get_buildings_in_bbox(bbox, apikey)
    api_calls += 1

    if not features:
        return api_calls, 0

    # 3) PNU prefix 필터링 (15자리: 법정동+산+본번)
    pnu_prefix_15 = pnu[:15]
    pnu_prefix_11 = pnu[:11]

    dongs = []
    seen = set()
    core_names = set()

    for f in features:
        props = f.get('properties', {}) or {}
        f_pnu = (props.get('pnu') or '').strip()
        if f_pnu and f_pnu[:15] == pnu_prefix_15:
            ufid = props.get('ufid')
            if ufid and ufid not in seen:
                seen.add(ufid)
                geom = f.get('geometry') or {}
                center = polygon_center(geom)
                if center:
                    dongs.append((ufid, f_pnu, props.get('dong_nm'),
                                  props.get('bld_nm'), center[1], center[0],
                                  geom, props.get('grnd_flr'),
                                  props.get('archarea')))
                    if props.get('bld_nm'):
                        core_names.add(props['bld_nm'])

    # 동일 단지명 인접 지번 편입
    if core_names:
        for f in features:
            props = f.get('properties', {}) or {}
            f_pnu = (props.get('pnu') or '').strip()
            if f_pnu and f_pnu[:15] == pnu_prefix_15:
                continue
            if not f_pnu or f_pnu[:11] != pnu_prefix_11:
                continue
            bld_nm = props.get('bld_nm') or ''
            if not any(core in bld_nm or bld_nm in core for core in core_names if core):
                continue
            ufid = props.get('ufid')
            if ufid and ufid not in seen:
                seen.add(ufid)
                geom = f.get('geometry') or {}
                center = polygon_center(geom)
                if center:
                    dongs.append((ufid, f_pnu, props.get('dong_nm'),
                                  props.get('bld_nm'), center[1], center[0],
                                  geom, props.get('grnd_flr'),
                                  props.get('archarea')))

    # 4) DB 저장 (UPSERT)
    saved = 0
    for (bd_mgt_sn, d_pnu, dong_nm, bld_nm, lat, lon, geom, grnd_flr, archarea) in dongs:
        try:
            cur.execute("""
                INSERT INTO building_dong_geometry
                    (bd_mgt_sn, pnu, dong_nm, bld_nm, lat, lon, geometry, grnd_flr, archarea, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, NOW())
                ON CONFLICT (bd_mgt_sn) DO UPDATE SET
                    pnu = EXCLUDED.pnu, dong_nm = EXCLUDED.dong_nm, bld_nm = EXCLUDED.bld_nm,
                    lat = EXCLUDED.lat, lon = EXCLUDED.lon, geometry = EXCLUDED.geometry,
                    grnd_flr = EXCLUDED.grnd_flr, archarea = EXCLUDED.archarea, updated_at = NOW()
            """, (bd_mgt_sn, d_pnu, dong_nm, bld_nm, lat, lon,
                  json.dumps(geom) if geom else None, grnd_flr, archarea))
            saved += 1
        except Exception as e:
            log.debug('저장 실패 bd_mgt_sn=%s: %s', bd_mgt_sn, e)
            conn.rollback()
            continue

    conn.commit()
    return api_calls, saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-household', type=int, default=50)
    parser.add_argument('--limit', type=int, default=30000)
    parser.add_argument('--rate-limit', type=float, default=0.3)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    apikey = get_apikey()
    if not apikey:
        log.error('VWORLD_APIKEY 환경변수 없음')
        return

    conn = get_conn()
    cur = conn.cursor()

    # 수집 대상: complex_master 연결된 PNU 중 building_dong_geometry에 없는 것
    # LEFT JOIN이 NOT IN보다 빠름
    cur.execute("""
        SELECT DISTINCT cp.pnu
        FROM complex_parcels cp
        JOIN complex_master cm ON cm.complex_pk = cp.complex_pk
        LEFT JOIN building_dong_geometry bg ON bg.pnu = cp.pnu
        WHERE cm.household_count >= %s
          AND bg.pnu IS NULL
        ORDER BY cp.pnu
        LIMIT %s
    """, (args.min_household, args.limit))
    targets = [r[0] for r in cur.fetchall()]

    log.info('수집 대상 PNU: %d개 (min_hh=%d, limit=%d)',
             len(targets), args.min_household, args.limit)

    if args.dry_run:
        log.info('[DRY-RUN] 종료')
        conn.close()
        return

    total_api = 0
    total_saved = 0
    total_pnu_ok = 0
    fail_streak = 0
    start = time.time()

    for i, pnu in enumerate(targets):
        try:
            api_calls, saved = collect_for_pnu(pnu, apikey, conn)
            total_api += api_calls
            total_saved += saved
            if saved > 0:
                total_pnu_ok += 1
                fail_streak = 0
            else:
                fail_streak += 1
        except Exception as e:
            log.warning('PNU %s 처리 에러: %s', pnu, e)
            fail_streak += 1
            # DB 커넥션 끊김 시 재연결
            try:
                conn.close()
            except Exception:
                pass
            try:
                conn = get_conn()
                log.info('DB 재연결 성공')
                fail_streak = 0  # 재연결 성공하면 리셋
            except Exception as re_err:
                log.error('DB 재연결 실패: %s', re_err)

        if (i + 1) % 100 == 0:
            elapsed = time.time() - start
            log.info('진행: %d/%d PNU, API호출 %d, 동저장 %d, PNU성공 %d (%.0f초)',
                     i + 1, len(targets), total_api, total_saved, total_pnu_ok, elapsed)

        # 연속 실패 50회면 API 문제로 판단하고 종료
        if fail_streak >= 50:
            log.warning('연속 실패 50회, 조기 종료')
            break

        time.sleep(args.rate_limit)

    elapsed = time.time() - start
    log.info('완료: %d/%d PNU 처리, API호출 %d, 동저장 %d, PNU성공 %d (%.0f초)',
             len(targets), len(targets), total_api, total_saved, total_pnu_ok, elapsed)

    # 최종 현황
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM building_dong_geometry")
        total_rows = cur.fetchone()[0]
        log.info('[현황] building_dong_geometry: %d건', total_rows)
    except Exception:
        pass

    try:
        conn.close()
    except Exception:
        pass


if __name__ == '__main__':
    main()
