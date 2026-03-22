#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

TABLE = 'goldenrabbit01_sales_building'

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # 현황 고유값
        cur.execute(f'SELECT DISTINCT "현황" FROM "{TABLE}" WHERE "현황" IS NOT NULL ORDER BY "현황"')
        print('=== 현황 고유값 ===')
        for r in cur.fetchall():
            print(f'  [{r[0]}]')

        # 현황별 건수
        cur.execute(f'SELECT "현황", COUNT(*) FROM "{TABLE}" GROUP BY "현황" ORDER BY COUNT(*) DESC')
        print('\n=== 현황별 건수 ===')
        for r in cur.fetchall():
            print(f'  [{r[0]}] → {r[1]}건')

        # 광고 관련 컬럼 확인
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND column_name IN ('네이버', '문의', '대표', '광고', '광고매체')
        """, (TABLE,))
        print(f'\n광고 관련 컬럼: {[r[0] for r in cur.fetchall()]}')

        # field_definitions에서 현황 필드 타입 확인
        cur.execute("SELECT field_type, select_options FROM field_definitions WHERE database_id = 39 AND field_name = '현황'")
        fd = cur.fetchone()
        if fd:
            print(f'\n현황 field_type: {fd[0]}, select_options: {fd[1]}')
