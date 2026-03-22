#!/usr/bin/env python3
"""
Fill building info from 공공데이터 건축물대장 API for all 부분부동산 records.
- Parse 지번 주소 → 시군구코드 + 법정동코드 + 본번 + 부번
- Fetch 표제부 (getBrTitleInfo)
- Update matching fields
- Skip and report errors
"""
import sys, os, requests, re, time
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

API_KEY = os.getenv('PUBLIC_API_KEY')
BASE_URL = 'http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo'
TABLE = 'sales_building_copy'

# 동작구 법정동코드 매핑
BJDONG_MAP = {
    '노량진동': '10100',
    '상도동': '10200',
    '상도1동': '10200',
    '본동': '10300',
    '흑석동': '10400',
    '동작동': '10500',
    '사당동': '10700',
    '대방동': '10800',
    '신대방동': '10900',
}

SIGUNGU = '11590'  # 동작구

def parse_address(addr):
    """Parse '동작구 사당동 252-10' → (bjdong_cd, bun, ji)"""
    if not addr:
        return None
    addr = addr.strip()
    # Pattern: (구) (동) (번-지) or (구) (동) (번)
    m = re.match(r'.*?([가-힣]+동)\s+(\d+)(?:-(\d+))?', addr)
    if not m:
        return None
    dong = m.group(1)
    bun = m.group(2)
    ji = m.group(3) or '0'
    bjdong = BJDONG_MAP.get(dong)
    if not bjdong:
        return None
    return bjdong, bun.zfill(4), ji.zfill(4)

def fetch_title(bjdong, bun, ji):
    """Fetch 표제부"""
    params = {
        'serviceKey': API_KEY,
        'sigunguCd': SIGUNGU,
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
    if int(body.get('totalCount', 0)) == 0:
        return None
    items = body.get('items', {}).get('item', [])
    if not isinstance(items, list):
        items = [items]
    return items

def extract_data(items):
    """Extract building data from 표제부 items"""
    # Find main building (prefer 주택/다가구)
    main = items[0]
    for item in items:
        purps = item.get('mainPurpsCdNm') or ''
        if '주택' in purps or '다가구' in purps:
            main = item
            break

    total_area = sum(float(i.get('totArea', 0) or 0) for i in items)
    parking = (int(main.get('indrAutoUtcnt', 0) or 0) +
               int(main.get('indrMechUtcnt', 0) or 0) +
               int(main.get('oudrAutoUtcnt', 0) or 0) +
               int(main.get('oudrMechUtcnt', 0) or 0))

    use_apr = main.get('useAprDay', '')
    if use_apr and len(use_apr) == 8:
        use_apr = f'{use_apr[:4]}-{use_apr[4:6]}-{use_apr[6:8]}'

    grnd = main.get('grndFlrCnt', 0) or 0
    ugrnd = main.get('ugrndFlrCnt', 0) or 0

    data = {}

    val = main.get('bldNm', '').strip()
    if val: data['건물명'] = val

    val = main.get('newPlatPlc', '').strip()
    if val: data['도로명주소'] = val

    val = main.get('mainPurpsCdNm', '').strip()
    if val: data['주용도'] = val

    val = main.get('strctCdNm', '').strip()
    if val: data['주구조'] = val

    val = main.get('roofCdNm', '').strip()
    if val: data['지붕'] = val

    plat = float(main.get('platArea', 0) or 0)
    if plat > 0: data['대지면적(㎡)'] = plat

    arch = float(main.get('archArea', 0) or 0)
    if arch > 0: data['건축면적(㎡)'] = arch

    if total_area > 0: data['연면적(㎡)'] = total_area

    bc = float(main.get('bcRat', 0) or 0)
    if bc > 0: data['건폐율(%)'] = bc

    vl = float(main.get('vlRat', 0) or 0)
    if vl > 0: data['용적률(%)'] = vl

    ht = float(main.get('heit', 0) or 0)
    if ht > 0: data['높이(m)'] = ht

    elv = int(main.get('rideUseElvtCnt', 0) or 0)
    data['승강기수'] = elv

    if parking > 0: data['주차대수'] = parking

    hhld = main.get('hhldCnt', 0) or 0
    fmly = main.get('fmlyCnt', 0) or 0
    ho = main.get('hoCnt', 0) or 0
    sega = f"{hhld}/{fmly}/{ho}"
    if sega != '0/0/0': data['세대/가구/호'] = sega

    if use_apr: data['사용승인일'] = use_apr

    val = main.get('jiyukCdNm', '').strip()
    if val: data['용도지역'] = val

    data['위반건축물'] = '유' if main.get('vltnBldYn') == 'Y' else 'X'

    if int(grnd) > 0 or int(ugrnd) > 0:
        data['층수'] = f"-{ugrnd}/{grnd}"

    return data

# Main
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(f'SELECT id, "지번 주소" FROM "{TABLE}" ORDER BY id')
        records = cur.fetchall()
        print(f"Total records: {len(records)}")

        updated = 0
        skipped = []
        no_data = []
        errors = []

        for rec_id, addr in records:
            parsed = parse_address(addr)
            if not parsed:
                skipped.append((rec_id, addr, 'parse failed'))
                continue

            bjdong, bun, ji = parsed

            try:
                items = fetch_title(bjdong, bun, ji)
                if not items:
                    no_data.append((rec_id, addr))
                    continue

                bdata = extract_data(items)
                if not bdata:
                    no_data.append((rec_id, addr))
                    continue

                # Only update fields that are currently NULL or empty
                sets = []
                vals = []
                for field, value in bdata.items():
                    sets.append(f'"{field}" = %s')
                    vals.append(value)

                if sets:
                    vals.append(rec_id)
                    cur.execute(f'UPDATE "{TABLE}" SET {", ".join(sets)} WHERE id = %s', vals)
                    updated += 1

                # Rate limit: ~1 req/sec to be safe
                time.sleep(0.3)

            except Exception as e:
                errors.append((rec_id, addr, str(e)))
                continue

        conn.commit()

        print(f"\n=== Results ===")
        print(f"Updated: {updated}")
        print(f"No data from API: {len(no_data)}")
        print(f"Skipped (parse): {len(skipped)}")
        print(f"Errors: {len(errors)}")

        if skipped:
            print(f"\n--- Skipped ---")
            for r in skipped:
                print(f"  id={r[0]}: [{r[1]}] ({r[2]})")

        if no_data:
            print(f"\n--- No API data ---")
            for r in no_data:
                print(f"  id={r[0]}: [{r[1]}]")

        if errors:
            print(f"\n--- Errors ---")
            for r in errors:
                print(f"  id={r[0]}: [{r[1]}] → {r[2]}")

print("\nDone!")
