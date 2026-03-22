#!/usr/bin/env python3
import sys, os, requests, re
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2 import sql as psql

API_KEY = os.getenv('PUBLIC_API_KEY')
TABLE = 'sales_building_copy'

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(f'UPDATE "{TABLE}" SET "지번 주소" = %s WHERE id = %s', ('동작구 사당동 270-6', 98))
        print(f'Fixed address: {cur.rowcount} row')
        conn.commit()

# Fetch
url = 'http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo'
params = {
    'serviceKey': API_KEY, 'sigunguCd': '11590', 'bjdongCd': '10700',
    'platGbCd': '0', 'bun': '0270', 'ji': '0006',
    'numOfRows': '50', 'pageNo': '1', '_type': 'json'
}
r = requests.get(url, params=params, timeout=10)
items = r.json().get('response',{}).get('body',{}).get('items',{}).get('item',[])
if not isinstance(items, list): items = [items]
if not items:
    print('No data'); exit()

main = items[0]
for i in items:
    if '주택' in str(i.get('mainPurpsCdNm','')): main = i; break

total_area = sum(float(i.get('totArea',0) or 0) for i in items)
use_apr = str(main.get('useAprDay','') or '').strip()
if use_apr and len(use_apr)==8: use_apr = f'{use_apr[:4]}-{use_apr[4:6]}-{use_apr[6:8]}'
grnd = int(main.get('grndFlrCnt',0) or 0)
ugrnd = int(main.get('ugrndFlrCnt',0) or 0)
parking = sum(int(main.get(k,0) or 0) for k in ['indrAutoUtcnt','indrMechUtcnt','oudrAutoUtcnt','oudrMechUtcnt'])

data = {}
def s(k): return str(main.get(k,'') or '').strip()
def f(k): return float(main.get(k,0) or 0)
if s('bldNm'): data['건물명'] = s('bldNm')
if s('newPlatPlc'): data['도로명주소'] = s('newPlatPlc')
if s('mainPurpsCdNm'): data['주용도'] = s('mainPurpsCdNm')
if s('strctCdNm'): data['주구조'] = s('strctCdNm')
if s('roofCdNm'): data['지붕'] = s('roofCdNm')
if f('platArea')>0: data['대지면적(㎡)'] = f('platArea')
if f('archArea')>0: data['건축면적(㎡)'] = f('archArea')
if total_area>0: data['연면적(㎡)'] = total_area
if f('bcRat')>0: data['건폐율(%)'] = f('bcRat')
if f('vlRat')>0: data['용적률(%)'] = f('vlRat')
if f('heit')>0: data['높이(m)'] = f('heit')
data['승강기수'] = int(main.get('rideUseElvtCnt',0) or 0)
if parking>0: data['주차대수'] = parking
if use_apr: data['사용승인일'] = use_apr
if s('jiyukCdNm'): data['용도지역'] = s('jiyukCdNm')
data['위반건축물'] = '유' if main.get('vltnBldYn')=='Y' else 'X'
if grnd>0 or ugrnd>0: data['층수'] = f'-{ugrnd}/{grnd}'

with get_db_connection() as conn:
    with conn.cursor() as cur:
        set_parts = []
        vals = []
        for field, value in data.items():
            set_parts.append(psql.SQL('{} = ').format(psql.Identifier(field)) + psql.SQL('%s'))
            vals.append(value)
        vals.append(98)
        query = psql.SQL('UPDATE {} SET ').format(psql.Identifier(TABLE)) + \
                psql.SQL(', ').join(set_parts) + psql.SQL(' WHERE id = %s')
        query_str = query.as_string(cur)
        query_str = re.sub(r'"([^"]*?)%([^s])', r'"\1%%\2', query_str)
        cur.execute(query_str, vals)
        print(f'Updated id=98: {cur.rowcount} row')
        conn.commit()

print('Done!')
