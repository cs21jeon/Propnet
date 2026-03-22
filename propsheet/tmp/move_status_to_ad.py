#!/usr/bin/env python3
"""
Move 현황 field data:
- Extract ad platform names → 광고 field (multi-select)
- Set 현황 → '등록' (if has platform) or keep status value
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2.extras import Json

TABLE = 'goldenrabbit01_sales_building'
DB_ID = 39

# Ad platform keywords
AD_PLATFORMS = {'네이버', '디스코', '당근', '비공개', '네이버홀수달올리기', '네이버짝수달등록', '네이버1달건너등록'}

# Status values that are NOT ad platforms (keep as-is or map)
STATUS_VALUES = {'거래됨', '철회', '보류', '등록대기', '계약', '전속있음', '확인불가', '경매진행중', '일시중단 요청'}

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Get all rows with 현황
        cur.execute(f'SELECT id, "현황" FROM "{TABLE}" WHERE "현황" IS NOT NULL')
        rows = cur.fetchall()
        print(f"Processing {len(rows)} rows")

        updated = 0
        for row_id, status in rows:
            if not status or not status.strip():
                continue

            # Parse multi-select value (comma separated)
            parts = [p.strip() for p in status.split(',') if p.strip()]

            # Split into ad platforms and status values
            ad_parts = []
            status_parts = []
            for p in parts:
                if p in AD_PLATFORMS:
                    ad_parts.append(p)
                else:
                    status_parts.append(p)

            # Determine new 광고 value
            ad_value = ', '.join(ad_parts) if ad_parts else None

            # Determine new 현황 value
            if ad_parts:
                # Has ad platform → 등록
                # But check if there's also a non-ad status (like 보류)
                if status_parts:
                    # Keep the non-ad status (e.g., "보류")
                    new_status = status_parts[0]
                else:
                    new_status = '등록'
            else:
                # No ad platform → keep original or map to 등록대기
                if status_parts:
                    new_status = status_parts[0]
                    # Map specific values
                    if new_status == '등록대기':
                        pass  # already correct
                else:
                    new_status = '등록대기'

            # Update
            cur.execute(f'UPDATE "{TABLE}" SET "광고" = %s, "현황" = %s WHERE id = %s',
                        (ad_value, new_status, row_id))
            updated += 1

        conn.commit()
        print(f"Updated {updated} rows")

        # Update field_definitions: 광고 → multi-select
        ad_options = sorted(AD_PLATFORMS)
        cur.execute("""
            INSERT INTO field_definitions (database_id, field_name, display_name, field_type, select_options, is_editable)
            VALUES (%s, '광고', '광고', 'multi-select', %s, true)
            ON CONFLICT (database_id, field_name) DO UPDATE
            SET field_type = 'multi-select', select_options = EXCLUDED.select_options
        """, (DB_ID, ad_options))
        print(f"Set 광고 field as multi-select with options: {ad_options}")

        # Update 현황 field_definitions: single-select with new options
        status_options = ['등록', '등록대기', '거래됨', '철회', '보류', '계약', '전속있음', '확인불가', '경매진행중', '일시중단 요청']
        cur.execute("""
            UPDATE field_definitions SET field_type = 'single-select', select_options = %s
            WHERE database_id = %s AND field_name = '현황'
        """, (status_options, DB_ID))
        print(f"Updated 현황 select options: {status_options}")

        conn.commit()

        # Verify
        cur.execute(f'SELECT "현황", COUNT(*) FROM "{TABLE}" GROUP BY "현황" ORDER BY COUNT(*) DESC')
        print('\n=== 변환 후 현황 ===')
        for r in cur.fetchall():
            print(f'  {r[0]} → {r[1]}건')

        cur.execute(f'SELECT "광고", COUNT(*) FROM "{TABLE}" WHERE "광고" IS NOT NULL GROUP BY "광고" ORDER BY COUNT(*) DESC LIMIT 15')
        print('\n=== 변환 후 광고 ===')
        for r in cur.fetchall():
            print(f'  {r[0]} → {r[1]}건')

print("\nDone!")
