#!/usr/bin/env python3
"""Match 임대차매물 종류 → 부분부동산 룸형태 by 지번주소+호수"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

SOURCE = 'lease_properties'
TARGET = 'sales_building_copy'

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Match by 지번(source) = 지번 주소(target) + 호(source) = 호수(target)
        cur.execute(f"""
            UPDATE "{TARGET}" t
            SET "룸형태" = s."종류"
            FROM "{SOURCE}" s
            WHERE TRIM(t."지번 주소") = TRIM(s."지번")
            AND COALESCE(TRIM(t."호수"), '') = COALESCE(TRIM(s."호"), '')
            AND s."종류" IS NOT NULL
        """)
        print(f"Updated {cur.rowcount} rows")
        conn.commit()

        # Verify
        cur.execute(f'SELECT "룸형태", COUNT(*) FROM "{TARGET}" GROUP BY "룸형태" ORDER BY COUNT(*) DESC')
        print("\n=== 룸형태 결과 ===")
        for r in cur.fetchall():
            print(f"  {r[0]} -> {r[1]}건")
