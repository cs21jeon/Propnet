#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
서울시 정비사업 정보몽땅 → redevelopment_zones DB 수집

cleanup.seoul.go.kr의 사업장 목록을 크롤링하여 DB에 저장.
대표지번 → VWorld API로 geocoding하여 중심좌표 보정.

사용:
  python collect_seoul_zones.py
  python collect_seoul_zones.py --dry-run
  python collect_seoul_zones.py --page-limit 3
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
log = logging.getLogger('collect_seoul')

# --- DB ---
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '175.119.224.71'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'dbname': os.environ.get('DB_NAME', 'goldenrabbit_db'),
    'user': os.environ.get('DB_USER', 'goldenrabbit_user'),
    'password': os.environ.get('DB_PASSWORD', ''),
}

VWORLD_APIKEY = os.environ.get('VWORLD_APIKEY', '')

# 정비사업 정보몽땅 URL
BASE_URL = 'https://cleanup.seoul.go.kr'
LIST_URL = f'{BASE_URL}/cleanup/bsnssttus/lsubBsnsSttus.do'

# 사업구분 코드
PROJECT_TYPES = {
    '재개발': '재개발',
    '재건축': '재건축',
    '소규모재건축': '소규모재건축',
    '가로주택': '가로주택',
    '도시환경': '도시환경',
}

# 진행단계 정규화
STAGE_MAP = {
    '추진주체구성전': '추진위전',
    '추진위원회구성': '추진위',
    '조합설립인가': '조합설립',
    '사업시행인가': '사업시행',
    '관리처분인가': '관리처분',
    '착공': '착공',
    '준공인가': '준공',
    '이전고시': '준공',
    '조합해산': '조합해산',
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def fetch_page(page_no=1, bsns_gubun='', jachi_gubun=''):
    """정보몽땅에서 사업장 목록 한 페이지(10건) 가져오기"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        log.error("beautifulsoup4 필요: pip install beautifulsoup4")
        sys.exit(1)

    data = urllib.parse.urlencode({
        'cpage': str(page_no),
        'pageSize': '10',
        'bsnsGubun': bsns_gubun,
        'jachiGubun': jachi_gubun,
        'bsnsNm': '',
        'jbeon': '',
    }).encode('utf-8')

    req = urllib.request.Request(LIST_URL, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    req.add_header('User-Agent', 'Mozilla/5.0 (PropValue data collector)')
    req.add_header('Referer', f'{BASE_URL}/cleanup/bsnssttus/lscrMainIndx.do')

    resp = urllib.request.urlopen(req, timeout=30)
    html = resp.read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    rows = []
    table = soup.find('table')
    if not table:
        return rows, False

    tbody = table.find('tbody')
    if not tbody:
        return rows, False

    for tr in tbody.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 6:
            continue

        # 사업장 링크에서 ID 추출
        link = tr.find('a')
        cafe_url = ''
        if link and link.get('onclick'):
            m = re.search(r"'([^']+)'", link.get('onclick', ''))
            if m:
                cafe_url = m.group(1)

        row = {
            'district': tds[1].get_text(strip=True),
            'project_type': tds[2].get_text(strip=True),
            'zone_name': tds[3].get_text(strip=True),
            'address': tds[4].get_text(strip=True),
            'stage': tds[5].get_text(strip=True),
            'cafe_url': cafe_url,
        }
        rows.append(row)

    # 다음 페이지 존재 여부
    paging = soup.find('div', class_='paging') or soup.find('ul', class_='pagination')
    has_next = False
    if paging:
        # 현재 페이지보다 큰 페이지 링크가 있으면 다음 페이지 존재
        for a in paging.find_all('a'):
            try:
                pg = int(a.get_text(strip=True))
                if pg > page_no:
                    has_next = True
                    break
            except (ValueError, TypeError):
                pass

    return rows, has_next


def geocode_address(address):
    """VWorld API로 주소 → 좌표 변환"""
    if not VWORLD_APIKEY or not address:
        return None, None

    try:
        params = urllib.parse.urlencode({
            'service': 'address',
            'request': 'getcoord',
            'version': '2.0',
            'crs': 'epsg:4326',
            'address': address,
            'refine': 'true',
            'simple': 'false',
            'format': 'json',
            'type': 'parcel',
            'key': VWORLD_APIKEY,
        })
        url = f'https://api.vworld.kr/req/address?{params}'
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'PropValue/1.0')
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))

        if data.get('response', {}).get('status') == 'OK':
            result = data['response']['result']
            point = result['point']
            return float(point['y']), float(point['x'])
    except Exception as e:
        log.debug("geocode 실패 (%s): %s", address, e)

    return None, None


def normalize_stage(raw_stage):
    """진행단계 정규화"""
    for key, val in STAGE_MAP.items():
        if key in raw_stage:
            return val
    return raw_stage


def normalize_project_type(raw_type):
    """사업구분 정규화"""
    for key, val in PROJECT_TYPES.items():
        if key in raw_type:
            return val
    return raw_type


def make_zone_code(district, zone_name):
    """고유 코드 생성 (서울-강남구-한남3구역)"""
    return f"서울-{district}-{zone_name}"


def collect_all_zones(page_limit=None):
    """전체 사업장 목록 수집"""
    all_zones = []
    page = 1

    while True:
        log.info("페이지 %d 수집 중...", page)
        rows, has_next = fetch_page(page_no=page)
        if not rows:
            log.info("페이지 %d: 데이터 없음, 종료", page)
            break

        all_zones.extend(rows)
        log.info("페이지 %d: %d건 수집 (누적 %d건)", page, len(rows), len(all_zones))

        if not has_next:
            break
        if page_limit and page >= page_limit:
            log.info("페이지 제한(%d) 도달, 종료", page_limit)
            break

        page += 1
        time.sleep(0.5)  # 서버 부하 방지

    return all_zones


def save_to_db(zones, dry_run=False):
    """수집 데이터를 DB에 저장"""
    if dry_run:
        log.info("[DRY-RUN] %d건 저장 예정", len(zones))
        for z in zones[:5]:
            log.info("  %s | %s | %s | %s | %s",
                     z['district'], z['project_type'], z['zone_name'],
                     z['address'], z['stage'])
        return

    conn = get_conn()
    cur = conn.cursor()

    upsert_sql = """
        INSERT INTO redevelopment_zones
            (zone_name, zone_code, city, district, dong, project_type, stage,
             center_lat, center_lon, source, raw_data, updated_at)
        VALUES
            (%(zone_name)s, %(zone_code)s, '서울특별시', %(district)s, %(dong)s,
             %(project_type)s, %(stage)s,
             %(center_lat)s, %(center_lon)s, 'cleanup_seoul', %(raw_data)s, NOW())
        ON CONFLICT (zone_code) DO UPDATE SET
            stage = EXCLUDED.stage,
            center_lat = COALESCE(EXCLUDED.center_lat, redevelopment_zones.center_lat),
            center_lon = COALESCE(EXCLUDED.center_lon, redevelopment_zones.center_lon),
            raw_data = EXCLUDED.raw_data,
            updated_at = NOW()
    """

    inserted = 0
    for z in zones:
        zone_code = make_zone_code(z['district'], z['zone_name'])
        stage = normalize_stage(z['stage'])
        project_type = normalize_project_type(z['project_type'])

        # 주소에서 동 추출
        dong = ''
        addr = z.get('address', '')
        # "강남구 개포동 12" → "개포동"
        parts = addr.split()
        for p in parts:
            if p.endswith('동') and len(p) >= 2:
                dong = p
                break

        # geocoding
        full_address = f"서울특별시 {z['district']} {addr}" if addr else ''
        lat, lon = geocode_address(full_address)

        params = {
            'zone_name': z['zone_name'],
            'zone_code': zone_code,
            'district': z['district'],
            'dong': dong or None,
            'project_type': project_type,
            'stage': stage,
            'center_lat': lat,
            'center_lon': lon,
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
            log.info("  %d건 커밋...", inserted)

        # geocoding rate limit
        if lat is not None:
            time.sleep(0.1)

    conn.commit()
    cur.close()
    conn.close()
    log.info("총 %d건 저장 완료", inserted)


def main():
    parser = argparse.ArgumentParser(description='서울시 정비사업 정보몽땅 수집')
    parser.add_argument('--dry-run', action='store_true', help='DB 저장 없이 테스트')
    parser.add_argument('--page-limit', type=int, default=None, help='최대 페이지 수')
    args = parser.parse_args()

    if not DB_CONFIG['password'] and not args.dry_run:
        log.error("DB_PASSWORD 환경변수가 필요합니다")
        sys.exit(1)

    log.info("서울시 정비사업 정보몽땅 수집 시작")
    zones = collect_all_zones(page_limit=args.page_limit)
    log.info("총 %d건 수집 완료", len(zones))

    if zones:
        save_to_db(zones, dry_run=args.dry_run)

    log.info("완료!")


if __name__ == '__main__':
    main()
