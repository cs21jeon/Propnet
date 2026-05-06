#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
경기/인천 정비사업 데이터 수집 → redevelopment_zones DB

소스:
  1. 인천: renewal.incheon.go.kr 정비사업 검색 크롤링
  2. 경기: 공공데이터포털 CSV 파일 (수동 다운로드 후 로드)

사용:
  python collect_gyeonggi_incheon.py --incheon
  python collect_gyeonggi_incheon.py --gyeonggi --csv-path /path/to/gyeonggi.csv
  python collect_gyeonggi_incheon.py --incheon --dry-run
"""
import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import psycopg2
import psycopg2.extras

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('collect_gi')

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'dbname': os.environ.get('DB_NAME', 'goldenrabbit_db'),
    'user': os.environ.get('DB_USER', 'goldenrabbit_user'),
    'password': os.environ.get('DB_PASSWORD', ''),
}

VWORLD_APIKEY = os.environ.get('VWORLD_APIKEY', '')

# 인천 정비사업 검색 URL
INCHEON_BASE = 'https://renewal.incheon.go.kr'
INCHEON_SEARCH = f'{INCHEON_BASE}/ires/program/0000-0011-0025/program/business/search.do'

# 인천 자치구 코드
INCHEON_DISTRICTS = {
    'CMCD_0000000000152': '중구',
    'CMCD_0000000000153': '동구',
    'CMCD_0000000000154': '미추홀구',
    'CMCD_0000000000155': '연수구',
    'CMCD_0000000000156': '남동구',
    'CMCD_0000000000157': '부평구',
    'CMCD_0000000000158': '계양구',
    'CMCD_0000000000159': '서구',
    'CMCD_0000000000160': '강화군',
    'CMCD_0000000000161': '옹진군',
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def geocode_address(address):
    """VWorld API로 주소 → 좌표 변환"""
    if not VWORLD_APIKEY or not address:
        return None, None
    try:
        params = urllib.parse.urlencode({
            'service': 'address', 'request': 'getcoord', 'version': '2.0',
            'crs': 'epsg:4326', 'address': address, 'refine': 'true',
            'simple': 'false', 'format': 'json', 'type': 'parcel',
            'key': VWORLD_APIKEY,
        })
        url = f'https://api.vworld.kr/req/address?{params}'
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'PropValue/1.0')
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))
        if data.get('response', {}).get('status') == 'OK':
            point = data['response']['result']['point']
            return float(point['y']), float(point['x'])
    except Exception as e:
        log.debug("geocode 실패 (%s): %s", address, e)
    return None, None


def make_zone_code(city, district, zone_name):
    return f"{city}-{district}-{zone_name}"


# ============================================================
# 인천 크롤링
# ============================================================

def fetch_incheon_page(page=1, district_code=''):
    """인천 정비사업 검색 페이지 크롤링"""
    from bs4 import BeautifulSoup

    data = urllib.parse.urlencode({
        'page': str(page),
        'sigun_gbn_id': district_code,
    }).encode('utf-8')

    req = urllib.request.Request(INCHEON_SEARCH, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    req.add_header('User-Agent', 'Mozilla/5.0 (PropValue data collector)')
    req.add_header('Referer', INCHEON_SEARCH)

    resp = urllib.request.urlopen(req, timeout=30)
    html = resp.read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    rows = []
    table = soup.find('table')
    if not table:
        return rows

    tbody = table.find('tbody')
    if not tbody:
        return rows

    for tr in tbody.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 6:
            continue

        row = {
            'district': tds[1].get_text(strip=True),
            'project_type': tds[2].get_text(strip=True),
            'stage': tds[3].get_text(strip=True),
            'zone_name': tds[4].get_text(strip=True),
            'address': tds[5].get_text(strip=True),
        }
        if row['zone_name']:
            rows.append(row)

    return rows


def collect_incheon():
    """인천 전체 정비사업 수집"""
    all_zones = []
    seen = set()
    page = 1

    while True:
        log.info("[인천] 페이지 %d 수집 중...", page)
        try:
            rows = fetch_incheon_page(page=page)
        except Exception as e:
            log.error("[인천] 페이지 %d 실패: %s", page, e)
            break

        if not rows:
            log.info("[인천] 페이지 %d: 데이터 없음, 종료", page)
            break

        new_count = 0
        for r in rows:
            code = make_zone_code('인천', r['district'], r['zone_name'])
            if code not in seen:
                seen.add(code)
                all_zones.append(r)
                new_count += 1

        if new_count == 0:
            log.info("[인천] 페이지 %d: 모두 중복, 종료", page)
            break

        log.info("[인천] 페이지 %d: %d건 (누적 %d건)", page, new_count, len(all_zones))

        if len(rows) < 10:
            break

        page += 1
        time.sleep(0.5)

    return all_zones


# ============================================================
# 경기도 CSV 로드
# ============================================================

def load_gyeonggi_csv(csv_path):
    """경기도 정비사업 CSV 파일 로드"""
    import csv
    zones = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 필드명은 CSV에 따라 조정 필요
            zone = {
                'district': row.get('시군명', row.get('시군', '')).strip(),
                'zone_name': row.get('정비구역명', row.get('구역명', '')).strip(),
                'project_type': row.get('정비유형', row.get('사업유형', '')).strip(),
                'stage': row.get('사업단계', row.get('진행단계', '')).strip(),
                'address': row.get('위치', row.get('소재지', '')).strip(),
                'area_sqm': row.get('구역면적', row.get('면적', '')).strip(),
            }
            if zone['zone_name'] and zone['district']:
                zones.append(zone)
    return zones


# ============================================================
# DB 저장 (공통)
# ============================================================

def save_to_db(zones, city, source, dry_run=False):
    if dry_run:
        log.info("[DRY-RUN] %d건 저장 예정 (%s)", len(zones), city)
        for z in zones[:5]:
            log.info("  %s | %s | %s | %s | %s",
                     z.get('district'), z.get('project_type'), z.get('zone_name'),
                     z.get('address'), z.get('stage'))
        return

    conn = get_conn()
    cur = conn.cursor()

    upsert_sql = """
        INSERT INTO redevelopment_zones
            (zone_name, zone_code, city, district, dong, project_type, stage,
             area_sqm, center_lat, center_lon, source, raw_data, updated_at)
        VALUES
            (%(zone_name)s, %(zone_code)s, %(city)s, %(district)s, %(dong)s,
             %(project_type)s, %(stage)s, %(area_sqm)s,
             %(center_lat)s, %(center_lon)s, %(source)s, %(raw_data)s, NOW())
        ON CONFLICT (zone_code) DO UPDATE SET
            stage = EXCLUDED.stage,
            area_sqm = COALESCE(EXCLUDED.area_sqm, redevelopment_zones.area_sqm),
            center_lat = COALESCE(EXCLUDED.center_lat, redevelopment_zones.center_lat),
            center_lon = COALESCE(EXCLUDED.center_lon, redevelopment_zones.center_lon),
            raw_data = EXCLUDED.raw_data,
            updated_at = NOW()
    """

    inserted = 0
    geocoded = 0
    for z in zones:
        zone_code = make_zone_code(city, z['district'], z['zone_name'])

        # 주소에서 동 추출
        dong = ''
        addr = z.get('address', '')
        parts = addr.split()
        for p in parts:
            if p.endswith('동') and len(p) >= 2:
                dong = p
                break

        # 면적 파싱
        area = None
        area_raw = z.get('area_sqm', '')
        if area_raw:
            try:
                area = float(re.sub(r'[^\d.]', '', str(area_raw)))
            except (ValueError, TypeError):
                pass

        # geocoding
        full_addr = f"{city} {z['district']} {addr}" if addr else ''
        lat, lon = geocode_address(full_addr)
        if lat is not None:
            geocoded += 1

        params = {
            'zone_name': z['zone_name'],
            'zone_code': zone_code,
            'city': city,
            'district': z['district'],
            'dong': dong or None,
            'project_type': z.get('project_type', ''),
            'stage': z.get('stage', ''),
            'area_sqm': area,
            'center_lat': lat,
            'center_lon': lon,
            'source': source,
            'raw_data': json.dumps(z, ensure_ascii=False),
        }

        try:
            cur.execute(upsert_sql, params)
            inserted += 1
        except Exception as e:
            log.error("INSERT 실패 (%s): %s", zone_code, e)
            conn.rollback()
            continue

        if inserted % 50 == 0:
            conn.commit()
            log.info("  %d건 커밋 (geocoded: %d)...", inserted, geocoded)

        if lat is not None:
            time.sleep(0.05)

    conn.commit()
    cur.close()
    conn.close()
    log.info("총 %d건 저장 완료 (geocoded: %d)", inserted, geocoded)


def main():
    parser = argparse.ArgumentParser(description='경기/인천 정비사업 수집')
    parser.add_argument('--incheon', action='store_true', help='인천 정비사업 수집')
    parser.add_argument('--gyeonggi', action='store_true', help='경기도 정비사업 CSV 로드')
    parser.add_argument('--csv-path', type=str, help='경기도 CSV 파일 경로')
    parser.add_argument('--dry-run', action='store_true', help='DB 저장 없이 테스트')
    args = parser.parse_args()

    try:
        from bs4 import BeautifulSoup  # noqa: F401
    except ImportError:
        log.error("beautifulsoup4 필요: pip install beautifulsoup4")
        sys.exit(1)

    if not args.incheon and not args.gyeonggi:
        log.error("--incheon 또는 --gyeonggi 중 하나 이상 지정 필요")
        sys.exit(1)

    if not DB_CONFIG['password'] and not args.dry_run:
        log.error("DB_PASSWORD 환경변수가 필요합니다")
        sys.exit(1)

    if args.incheon:
        log.info("인천 정비사업 수집 시작")
        zones = collect_incheon()
        log.info("인천 %d건 수집 완료", len(zones))
        if zones:
            save_to_db(zones, '인천광역시', 'incheon_renewal', dry_run=args.dry_run)

    if args.gyeonggi:
        if not args.csv_path:
            log.error("경기도 CSV 파일 경로를 --csv-path로 지정해주세요")
            sys.exit(1)
        log.info("경기도 CSV 로드: %s", args.csv_path)
        zones = load_gyeonggi_csv(args.csv_path)
        log.info("경기도 %d건 로드 완료", len(zones))
        if zones:
            save_to_db(zones, '경기도', 'gyeonggi_csv', dry_run=args.dry_run)

    log.info("완료!")


if __name__ == '__main__':
    main()
