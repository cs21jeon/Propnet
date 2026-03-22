#!/usr/bin/env python3
"""Move 특징 content to 비공개메모 front, then drop 특징 column"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

TABLE = 'goldenrabbit01_sales_multi_unit'
DB_ID = 38

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Check how many rows have 특징 data
        cur.execute(f"""SELECT COUNT(*) FROM "{TABLE}" WHERE "특징" IS NOT NULL AND "특징" != ''""")
        count = cur.fetchone()[0]
        print(f"특징 데이터 있는 행: {count}")

        # Merge: prepend 특징 to 비공개메모
        # Case 1: 비공개메모 has content → "[특징] xxx\n기존메모"
        # Case 2: 비공개메모 is empty → "[특징] xxx"
        cur.execute(f"""
            UPDATE "{TABLE}"
            SET "비공개메모" = CASE
                WHEN "비공개메모" IS NOT NULL AND "비공개메모" != ''
                    THEN '[특징] ' || "특징" || E'\\n' || "비공개메모"
                ELSE '[특징] ' || "특징"
            END
            WHERE "특징" IS NOT NULL AND "특징" != ''
        """)
        print(f"Merged {cur.rowcount} rows into 비공개메모")

        # Drop 특징 column
        cur.execute(f'ALTER TABLE "{TABLE}" DROP COLUMN "특징"')
        print("Dropped 특징 column")

        # Remove field_definition
        cur.execute("DELETE FROM field_definitions WHERE database_id = %s AND field_name = '특징'", (DB_ID,))
        print(f"Removed field_definition ({cur.rowcount})")

        conn.commit()

print("Done!")
