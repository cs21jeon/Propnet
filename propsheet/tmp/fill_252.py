#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

TABLE = 'sales_building_copy'
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(f"""UPDATE "{TABLE}" SET
            "도로명주소" = '서울특별시 동작구 사당로13길 8 (사당동)',
            "주용도" = '제1종근린생활시설',
            "주구조" = '철근콘크리트구조',
            "지붕" = '(철근)콘크리트',
            "건축면적(㎡)" = 80.63,
            "연면적(㎡)" = 411.63,
            "건폐율(%)" = 48.87,
            "용적률(%)" = 182.83,
            "층수" = '-1/4',
            "승강기수" = 0,
            "주차대수" = 0,
            "세대/가구/호" = '0/1/0',
            "사용승인일" = '1990-08-30',
            "위반건축물" = 'X'
        WHERE "지번 주소" LIKE '%252-10%'""")
        print(f'Updated {cur.rowcount} rows')
        conn.commit()
