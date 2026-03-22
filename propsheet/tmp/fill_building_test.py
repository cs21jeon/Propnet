#!/usr/bin/env python3
"""
Test: Fill building info for 사당동 1131 records from 공공데이터 건축물대장 API
"""
import sys, os, requests
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

API_KEY = os.getenv('PUBLIC_API_KEY')
BASE_URL = 'http://apis.data.go.kr/1613000/BldRgstHubService'
TABLE = 'sales_building_copy'

def fetch_title_info(sigungu, bjdong, bun, ji):
    """Fetch 표제부 (building title info)"""
    params = {
        'serviceKey': API_KEY,
        'sigunguCd': sigungu,
        'bjdongCd': bjdong,
        'platGbCd': '0',
        'bun': str(bun).zfill(4),
        'ji': str(ji).zfill(4),
        'numOfRows': '100',
        'pageNo': '1',
        '_type': 'json'
    }
    r = requests.get(f'{BASE_URL}/getBrTitleInfo', params=params, timeout=10)
    data = r.json()
    body = data.get('response', {}).get('body', {})
    if int(body.get('totalCount', 0)) == 0:
        return None
    items = body.get('items', {}).get('item', [])
    if not isinstance(items, list):
        items = [items]
    return items

def extract_building_data(items):
    """Extract key fields from 표제부 items (take first/primary)"""
    # Find the main building (largest total area or 주용도=다가구주택/공동주택)
    main = items[0]
    for item in items:
        if '주택' in (item.get('mainPurpsCdNm') or ''):
            main = item
            break

    # Sum areas across all items (same building, different 동)
    total_area = sum(float(i.get('totArea', 0) or 0) for i in items)

    return {
        '건물명': main.get('bldNm') or '',
        '주구조': main.get('strctCdNm') or '',
        '지붕': main.get('roofCdNm') or '',
        '주용도': main.get('mainPurpsCdNm') or '',
        '대지면적(㎡)': float(main.get('platArea', 0) or 0),
        '건축면적(㎡)': float(main.get('archArea', 0) or 0),
        '연면적(㎡)': total_area,
        '건폐율(%)': float(main.get('bcRat', 0) or 0),
        '용적률(%)': float(main.get('vlRat', 0) or 0),
        '높이(m)': float(main.get('heit', 0) or 0),
        '승강기수': int(main.get('rideUseElvtCnt', 0) or 0),
        '주차대수': int(main.get('indrMechUtcnt', 0) or 0) + int(main.get('oudrMechUtcnt', 0) or 0) + int(main.get('indrAutoUtcnt', 0) or 0) + int(main.get('oudrAutoUtcnt', 0) or 0),
        '도로명주소': main.get('newPlatPlc') or '',
        '사용승인일': main.get('useAprDay') or '',
        '용도지역': main.get('jiyukCdNm') or '',
        '위반건축물': '유' if main.get('vltnBldYn') == 'Y' else 'X',
        '층수': f"-{main.get('ugrndFlrCnt', 0)}/{main.get('grndFlrCnt', 0)}",
        '세대/가구/호': f"{main.get('hhldCnt', 0)}/{main.get('fmlyCnt', 0)}/{main.get('hoCnt', 0)}",
    }

# Test with 사당동 1131
print("=== 사당동 1131 조회 ===")
items = fetch_title_info('11590', '10700', '1131', '0')
if not items:
    print("데이터 없음")
    sys.exit(1)

print(f"표제부 {len(items)}건")
bdata = extract_building_data(items)
print("\n추출된 데이터:")
for k, v in bdata.items():
    print(f"  {k}: {v}")

# Apply to records
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT id, "지번 주소" FROM "{TABLE}"
            WHERE "지번 주소" LIKE '%사당동 1131' OR "지번 주소" LIKE '%사당동 1131 %'
        """)
        records = cur.fetchall()
        print(f"\n매칭 레코드: {len(records)}건")

        for rec_id, addr in records:
            sets = []
            vals = []
            for field, value in bdata.items():
                if value and value != '' and value != 0 and value != 0.0:
                    sets.append(f'"{field}" = %s')
                    vals.append(value)
            vals.append(rec_id)
            cur.execute(f'UPDATE "{TABLE}" SET {", ".join(sets)} WHERE id = %s', vals)
            print(f"  Updated id={rec_id} ({addr})")

        conn.commit()

print("\nDone!")
