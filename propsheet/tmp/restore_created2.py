#!/usr/bin/env python3
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
        # 1. Add column if not exists
        cur.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = %s AND column_name = '생성일자'
        """, (TABLE,))
        if not cur.fetchone():
            cur.execute(f'ALTER TABLE "{TABLE}" ADD COLUMN "생성일자" TIMESTAMP')
            print('Added 생성일자 column')
        conn.commit()

    with conn.cursor() as cur:
        # 2. Copy from source by 지번 주소 + 호수
        cur.execute(f'''
            UPDATE "{TABLE}" t
            SET "생성일자" = s."생성일자"
            FROM "{SOURCE}" s
            WHERE t."지번 주소" = s."지번 주소"
            AND COALESCE(t."호수", '') = COALESCE(s."호수", '')
            AND s."생성일자" IS NOT NULL
        ''')
        print(f'Restored 생성일자 for {cur.rowcount} rows')

        # 3. Clear incorrectly set 레코드생성일자
        cur.execute(f'UPDATE "{TABLE}" SET "레코드생성일자" = NULL')
        print(f'Cleared 레코드생성일자 ({cur.rowcount} rows)')

        # 4. Re-add field_definition
        cur.execute("""
            INSERT INTO field_definitions (database_id, field_name, display_name, field_type, is_editable)
            VALUES (38, '생성일자', '생성일자', 'date', false)
            ON CONFLICT (database_id, field_name) DO NOTHING
        """)
        conn.commit()

        # Verify
        cur.execute(f'SELECT COUNT(*) FROM "{TABLE}" WHERE "생성일자" IS NOT NULL')
        print(f'생성일자 not null: {cur.fetchone()[0]}')

print("Done!")
