#!/usr/bin/env python3
"""Fill building info - fixed API parsing"""
import sys, os, requests, re, time
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

API_KEY = os.getenv('PUBLIC_API_KEY')
BASE_URL = 'http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo'
TABLE = 'sales_building_copy'

# 시군구+법정동 매핑
DISTRICT_MAP = {
    ('동작구', '노량진동'): ('11590', '10100'),
    ('동작구', '상도동'): ('11590', '10200'),
    ('동작구', '본동'): ('11590', '10300'),
    ('동작구', '흑석동'): ('11590', '10400'),
    ('동작구', '동작동'): ('11590', '10500'),
    ('동작구', '사당동'): ('11590', '10700'),
    ('동작구', '대방동'): ('11590', '10800'),
    ('동작구', '신대방동'): ('11590', '10900'),
    ('동작구', '남현동'): ('11590', '10600'),
    ('관악구', '봉천동'): ('11620', '10100'),
    ('관악구', '신림동'): ('11620', '10200'),
    ('관악구', '남현동'): ('11620', '10300'),
    ('서초구', '방배동'): ('11650', '10100'),
    ('서초구', '서초동'): ('11650', '10800'),
}

def parse_address(addr):
    if not addr:
        return None
    addr = addr.strip()
    # (구) (동) (번)-(지)
    m = re.match(r'([가-힣]+구)\s+([가-힣]+동)\s+(\d+)(?:-(\d+))?', addr)
    if not m:
        return None
    gu = m.group(1)
    dong = m.group(2)
    bun = m.group(3)
    ji = m.group(4) or '0'
    codes = DISTRICT_MAP.get((gu, dong))
    if not codes:
        return None
    return codes[0], codes[1], bun.zfill(4), ji.zfill(4)

def fetch_title(sigungu, bjdong, bun, ji):
    params = {
        'serviceKey': API_KEY,
        'sigunguCd': sigungu,
        'bjdongCd': bjdong,
        'platGbCd': '0',
        'bun': bun,
        'ji': ji,
        'numOfRows': '50',
        'pageNo': '1',
        '_type': 'json'
    }
    r = requests.get(BASE_URL, params=params, timeout=10)
    body = r.json().get('response', {}).get('body', {})
    total = int(body.get('totalCount', 0) or 0)
    if total == 0:
        return None
    items_wrap = body.get('items', None)
    if not items_wrap or not isinstance(items_wrap, dict):
        return None
    items = items_wrap.get('item', [])
    if not items:
        return None
    if not isinstance(items, list):
        items = [items]
    return items

def extract_data(items):
    main = items[0]
    for item in items:
        purps = str(item.get('mainPurpsCdNm') or '')
        if '주택' in purps or '다가구' in purps:
            main = item
            break

    total_area = sum(float(i.get('totArea', 0) or 0) for i in items)
    parking = (int(main.get('indrAutoUtcnt', 0) or 0) +
               int(main.get('indrMechUtcnt', 0) or 0) +
               int(main.get('oudrAutoUtcnt', 0) or 0) +
               int(main.get('oudrMechUtcnt', 0) or 0))

    use_apr = str(main.get('useAprDay', '') or '').strip()
    if use_apr and len(use_apr) == 8:
        use_apr = f'{use_apr[:4]}-{use_apr[4:6]}-{use_apr[6:8]}'

    grnd = int(main.get('grndFlrCnt', 0) or 0)
    ugrnd = int(main.get('ugrndFlrCnt', 0) or 0)

    data = {}
    def s(k): return str(main.get(k, '') or '').strip()
    def f(k): return float(main.get(k, 0) or 0)

    if s('bldNm'): data['건물명'] = s('bldNm')
    if s('newPlatPlc'): data['도로명주소'] = s('newPlatPlc')
    if s('mainPurpsCdNm'): data['주용도'] = s('mainPurpsCdNm')
    if s('strctCdNm'): data['주구조'] = s('strctCdNm')
    if s('roofCdNm'): data['지붕'] = s('roofCdNm')
    if f('platArea') > 0: data['대지면적(㎡)'] = f('platArea')
    if f('archArea') > 0: data['건축면적(㎡)'] = f('archArea')
    if total_area > 0: data['연면적(㎡)'] = total_area
    if f('bcRat') > 0: data['건폐율(%)'] = f('bcRat')
    if f('vlRat') > 0: data['용적률(%)'] = f('vlRat')
    if f('heit') > 0: data['높이(m)'] = f('heit')
    data['승강기수'] = int(main.get('rideUseElvtCnt', 0) or 0)
    if parking > 0: data['주차대수'] = parking
    hhld = int(main.get('hhldCnt', 0) or 0)
    fmly = int(main.get('fmlyCnt', 0) or 0)
    ho = int(main.get('hoCnt', 0) or 0)
    if hhld or fmly or ho: data['세대/가구/호'] = f"{hhld}/{fmly}/{ho}"
    if use_apr: data['사용승인일'] = use_apr
    if s('jiyukCdNm'): data['용도지역'] = s('jiyukCdNm')
    data['위반건축물'] = '유' if main.get('vltnBldYn') == 'Y' else 'X'
    if grnd > 0 or ugrnd > 0: data['층수'] = f"-{ugrnd}/{grnd}"

    return data

# Main
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(f'SELECT id, "지번 주소" FROM "{TABLE}" ORDER BY id')
        records = cur.fetchall()
        print(f"Total: {len(records)}")

        # Group by address to avoid duplicate API calls
        addr_cache = {}
        updated = 0
        skipped = []
        no_data = []
        errors = []

        for rec_id, addr in records:
            parsed = parse_address(addr)
            if not parsed:
                skipped.append((rec_id, addr))
                continue

            cache_key = parsed
            if cache_key not in addr_cache:
                try:
                    items = fetch_title(*parsed)
                    if items:
                        addr_cache[cache_key] = extract_data(items)
                    else:
                        addr_cache[cache_key] = None
                    time.sleep(0.3)
                except Exception as e:
                    errors.append((rec_id, addr, str(e)))
                    addr_cache[cache_key] = None
                    continue

            bdata = addr_cache[cache_key]
            if not bdata:
                no_data.append((rec_id, addr))
                continue

            from psycopg2 import sql as psql
            set_parts = []
            vals = []
            for field, value in bdata.items():
                set_parts.append(psql.SQL('{} = ').format(psql.Identifier(field)) + psql.SQL('%s'))
                vals.append(value)
            vals.append(rec_id)
            query = psql.SQL('UPDATE {} SET ').format(psql.Identifier(TABLE)) + \
                    psql.SQL(', ').join(set_parts) + \
                    psql.SQL(' WHERE id = %s')
            # Convert to string, escape % in identifier names (not %s placeholders)
            query_str = query.as_string(cur)
            # Replace % in column names with %% but keep %s placeholders
            # Strategy: replace all %) with %%) in quoted identifiers
            import re as _re
            query_str = _re.sub(r'"([^"]*?)%([^s])', r'"\1%%\2', query_str)
            cur.execute(query_str, vals)
            updated += 1

        conn.commit()

        print(f"\n=== Results ===")
        print(f"Updated: {updated}")
        print(f"No API data: {len(no_data)}")
        print(f"Skipped (parse): {len(skipped)}")
        print(f"Errors: {len(errors)}")

        if skipped:
            print(f"\n--- Skipped ---")
            for r in skipped[:10]:
                print(f"  id={r[0]}: [{r[1]}]")

        if no_data:
            print(f"\n--- No data ---")
            for r in no_data:
                print(f"  id={r[0]}: [{r[1]}]")

        if errors:
            print(f"\n--- Errors ---")
            for r in errors:
                print(f"  id={r[0]}: [{r[1]}] → {r[2]}")

print("\nDone!")
