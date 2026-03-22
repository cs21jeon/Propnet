#!/usr/bin/env python3
"""Move remaining 현황 values (거래됨, 확인불가, 계약, 보류, 철회, 자리톡) to 광고 field"""
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
        # Get rows where 현황 still has non-등록/등록대기 values
        cur.execute(f"""
            SELECT id, "현황", "광고" FROM "{TABLE}"
            WHERE "현황" IS NOT NULL
            AND "현황" NOT IN ('등록', '등록대기')
        """)
        rows = cur.fetchall()
        print(f"Processing {len(rows)} rows")

        for row_id, status, existing_ad in rows:
            if not status or not status.strip():
                continue
            # Append status to 광고 field
            if existing_ad and existing_ad.strip():
                new_ad = existing_ad + ', ' + status
            else:
                new_ad = status
            # Set 현황 to 등록대기 (since it had no ad platform)
            cur.execute(f'UPDATE "{TABLE}" SET "광고" = %s, "현황" = %s WHERE id = %s',
                        (new_ad, '등록대기', row_id))

        # Also handle NULL 현황 → 등록대기
        cur.execute(f'UPDATE "{TABLE}" SET "현황" = %s WHERE "현황" IS NULL', ('등록대기',))
        print(f"Set {cur.rowcount} NULL rows to 등록대기")

        conn.commit()

        # Update 광고 select options to include new values
        cur.execute("""
            SELECT select_options FROM field_definitions
            WHERE database_id = %s AND field_name = '광고'
        """, (DB_ID,))
        current = cur.fetchone()
        current_opts = current[0] if current else []

        new_opts = set(current_opts or [])
        new_opts.update(['거래됨', '확인불가', '계약', '보류', '철회', '자리톡', '경매진행중', '일시중단 요청', '전속있음'])
        sorted_opts = sorted(new_opts)

        cur.execute("""
            UPDATE field_definitions SET select_options = %s
            WHERE database_id = %s AND field_name = '광고'
        """, (sorted_opts, DB_ID))
        conn.commit()
        print(f"Updated 광고 options: {sorted_opts}")

        # Verify
        cur.execute(f'SELECT "현황", COUNT(*) FROM "{TABLE}" GROUP BY "현황" ORDER BY COUNT(*) DESC')
        print('\n=== 현황 ===')
        for r in cur.fetchall():
            print(f'  {r[0]} → {r[1]}건')

        cur.execute(f'SELECT "광고", COUNT(*) FROM "{TABLE}" WHERE "광고" IS NOT NULL GROUP BY "광고" ORDER BY COUNT(*) DESC')
        print('\n=== 광고 ===')
        for r in cur.fetchall():
            print(f'  {r[0]} → {r[1]}건')

print("Done!")
