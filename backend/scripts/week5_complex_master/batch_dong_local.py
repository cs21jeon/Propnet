#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
building_dong_geometry 배치 수집 — 로컬 PC에서 실행, 서버 DB 직접 접속.
서버 RAM 부하 없이 VWorld API 호출 + 원격 DB INSERT.
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
log = logging.getLogger('batch_dong_local')

# 서버 DB 직접 접속
DB_CONFIG = {
    'host': '175.119.224.71',
    'port': 5432,
    'dbname': 'goldenrabbit_db',
    'user': 'goldenrabbit_user',
    'password': os.environ.get('DB_PASSWORD', ''),
}

VWORLD_APIKEY = os.environ.get('VWORLD_APIKEY', '')
WFS_URL = 'https://api.vworld.kr/req/wfs'
TIMEOUT = 15
BBOX_RADIUS_M = 400.0


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def bbox_from_center(lat, lon, radius_m=BBOX_RADIUS_M):
    lat_rad = math.radians(lat)
    d_lat = radius_m / 111320.0
    d_lon = radius_m / (111320.0 * max(math.cos(lat_rad), 0.01))
    return f'{lon - d_lon},{lat - d_lat},{lon + d_lon},{lat + d_lat}'


def polygon_center(geom):
    if not geom:
        return None
    t = geom.get('type')
    c = geom.get('coordinates') or []
    pts = []
    if t == 'Polygon':
        for ring in c:
            pts.extend(ring)
    elif t == 'MultiPolygon':
        for poly in c:
            for ring in poly:
                pts.extend(ring)
    elif t == 'Point':
        pts.append(c)
    if not pts:
        return None
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return ((min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2)


def collect_for_complex(complex_pk, center_lat, center_lon, pnu_list, conn):
    bbox = bbox_from_center(center_lat, center_lon, BBOX_RADIUS_M)

    try:
        resp = requests.get(WFS_URL, params={
            'key': VWORLD_APIKEY,
            'service': 'WFS',
            'version': '2.0.0',
            'request': 'GetFeature',
            'typename': 'lt_c_bldginfo',
            'srsname': 'EPSG:4326',
            'output': 'application/json',
            'bbox': bbox,
            'maxFeatures': 200,
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        features = resp.json().get('features', []) or []
    except Exception as e:
        log.debug('WFS fail complex=%s: %s', complex_pk, e)
        return 0

    if not features:
        return 0

    pnu_prefixes_15 = {p[:15] for p in pnu_list}
    pnu_prefixes_11 = {p[:11] for p in pnu_list}

    dongs = []
    seen = set()
    core_names = set()

    for f in features:
        props = f.get('properties', {}) or {}
        f_pnu = (props.get('pnu') or '').strip()
        if f_pnu and f_pnu[:15] in pnu_prefixes_15:
            ufid = props.get('ufid')
            if ufid and ufid not in seen:
                seen.add(ufid)
                geom = f.get('geometry') or {}
                center = polygon_center(geom)
                if center:
                    dongs.append((ufid, f_pnu, props.get('dong_nm'),
                                  props.get('bld_nm'), center[1], center[0],
                                  geom, props.get('grnd_flr'), props.get('archarea')))
                    if props.get('bld_nm'):
                        core_names.add(props['bld_nm'])

    if core_names:
        for f in features:
            props = f.get('properties', {}) or {}
            f_pnu = (props.get('pnu') or '').strip()
            if f_pnu and f_pnu[:15] in pnu_prefixes_15:
                continue
            if not f_pnu or f_pnu[:11] not in pnu_prefixes_11:
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
                                  geom, props.get('grnd_flr'), props.get('archarea')))

    saved = 0
    cur = conn.cursor()
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
            log.debug('save fail %s: %s', bd_mgt_sn, e)
            conn.rollback()
            continue
    conn.commit()
    return saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-household', type=int, default=50)
    parser.add_argument('--limit', type=int, default=30000)
    parser.add_argument('--rate-limit', type=float, default=0.3)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    conn = get_conn()
    cur = conn.cursor()
    log.info('DB 접속 OK (%s)', DB_CONFIG['host'])

    # 1) 전체 단지
    cur.execute("""
        SELECT complex_pk, center_lat, center_lon
        FROM complex_master
        WHERE household_count >= %s AND center_lat IS NOT NULL
        ORDER BY household_count DESC
        LIMIT %s
    """, (args.min_household, args.limit))
    all_complexes = [(r[0], float(r[1]), float(r[2])) for r in cur.fetchall()]
    log.info('전체 단지: %d개', len(all_complexes))

    # 2) 이미 처리된 단지
    cur.execute("""
        SELECT DISTINCT cp.complex_pk
        FROM complex_parcels cp
        JOIN building_dong_geometry bg ON bg.pnu = cp.pnu
    """)
    already_done = {r[0] for r in cur.fetchall()}
    log.info('이미 처리: %d개', len(already_done))

    # 3) 미처리 필터
    targets_raw = [(cpk, clat, clon) for cpk, clat, clon in all_complexes if cpk not in already_done]
    log.info('미처리 단지: %d개', len(targets_raw))

    # 4) PNU 목록 조회
    target_pks = [t[0] for t in targets_raw]
    pnu_map = {}
    for batch_start in range(0, len(target_pks), 1000):
        batch = target_pks[batch_start:batch_start + 1000]
        cur.execute(
            "SELECT complex_pk, pnu FROM complex_parcels WHERE complex_pk = ANY(%s)",
            (batch,),
        )
        for cpk, pnu in cur.fetchall():
            pnu_map.setdefault(cpk, []).append(pnu)

    targets = [(cpk, clat, clon, pnu_map.get(cpk, [])) for cpk, clat, clon in targets_raw]
    log.info('수집 대상: %d개 단지', len(targets))

    if args.dry_run:
        log.info('[DRY-RUN] 종료')
        conn.close()
        return

    total_saved = 0
    success_count = 0
    fail_streak = 0
    start = time.time()

    for i, (cpk, clat, clon, pnu_list) in enumerate(targets):
        try:
            saved = collect_for_complex(cpk, clat, clon, pnu_list, conn)
            total_saved += saved
            if saved > 0:
                success_count += 1
                fail_streak = 0
            else:
                fail_streak += 1
        except Exception as e:
            log.warning('complex %s error: %s', cpk, e)
            fail_streak += 1
            try:
                conn.close()
            except Exception:
                pass
            try:
                conn = get_conn()
                log.info('DB reconnected')
                fail_streak = 0
            except Exception as re_err:
                log.error('DB reconnect fail: %s', re_err)

        if (i + 1) % 200 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            remaining = (len(targets) - i - 1) / rate / 60
            log.info('진행: %d/%d 단지, 동저장 %d, 성공 %d (%.0f초, 남은시간 %.0f분)',
                     i + 1, len(targets), total_saved, success_count, elapsed, remaining)

        if fail_streak >= 50:
            log.warning('연속 실패 50회, 조기 종료')
            break

        time.sleep(args.rate_limit)

    elapsed = time.time() - start
    log.info('완료: %d단지, 동저장 %d, 성공 %d (%.0f초)',
             len(targets), total_saved, success_count, elapsed)

    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM building_dong_geometry")
        log.info('[현황] building_dong_geometry: %d건', cur.fetchone()[0])
    except Exception:
        pass

    try:
        conn.close()
    except Exception:
        pass


if __name__ == '__main__':
    main()
