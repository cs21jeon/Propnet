#!/usr/bin/env python3
"""Restore 생성일자 from source by matching 지번 주소 + 호수"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

TABLE = 'goldenrabbit01_sales_multi_unit'
SOURCE = 'sales_multi_unit'

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Check if target has airtable_id
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND column_name = 'airtable_id'
        """, (TABLE,))
        has_airtable = cur.fetchone()

        if has_airtable:
            # Match by airtable_id
            cur.execute(f'''
                UPDATE "{TABLE}" t
                SET "생성일자" = s."생성일자"
                FROM "{SOURCE}" s
                WHERE t."airtable_id" = s."airtable_id"
                AND s."생성일자" IS NOT NULL
            ''')
        else:
            # Match by 지번 주소 + 호수 (unique enough)
            cur.execute(f'''
                UPDATE "{TABLE}" t
                SET "생성일자" = s."생성일자"
                FROM "{SOURCE}" s
                WHERE t."지번 주소" = s."지번 주소"
                AND COALESCE(t."호수", '') = COALESCE(s."호수", '')
                AND s."생성일자" IS NOT NULL
            ''')
        print(f'Restored 생성일자 for {cur.rowcount} rows')

        # Also clear 레코드생성일자 text that we incorrectly set
        cur.execute(f'UPDATE "{TABLE}" SET "레코드생성일자" = NULL')
        print(f'Cleared 레코드생성일자 text ({cur.rowcount} rows)')

        conn.commit()

        # Verify
        cur.execute(f'SELECT COUNT(*) FROM "{TABLE}" WHERE "생성일자" IS NOT NULL')
        print(f'생성일자 not null: {cur.fetchone()[0]}')
        cur.execute(f'SELECT "생성일자" FROM "{TABLE}" WHERE "생성일자" IS NOT NULL LIMIT 3')
        for r in cur.fetchall():
            print(f'  {r[0]}')

print("Done!")
