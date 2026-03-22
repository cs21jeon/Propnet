#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

TABLE = 'goldenrabbit01_sales_multi_unit'
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name = %s AND column_name IN ('생성일자', '레코드생성일자')
        """, (TABLE,))
        for r in cur.fetchall():
            print(f'{r[0]}: {r[1]}')

        cur.execute(f'SELECT "생성일자", "레코드생성일자" FROM "{TABLE}" WHERE "생성일자" IS NOT NULL LIMIT 5')
        for r in cur.fetchall():
            print(f'  생성일자=[{r[0]}]  레코드생성일자=[{r[1]}]')

        cur.execute(f'SELECT COUNT(*) FROM "{TABLE}" WHERE "생성일자" IS NOT NULL')
        print(f'생성일자 있는 행: {cur.fetchone()[0]}')
