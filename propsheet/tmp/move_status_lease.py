#!/usr/bin/env python3
"""Move 현황 → 광고 for 부분부동산 (DB43)"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

TABLE = 'sales_building_copy'
DB_ID = 43

AD_PLATFORMS = {'네이버', '디스코', '당근', '비공개', '네이버홀수달올리기', '네이버짝수달등록', '네이버1달건너등록'}

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Check if 광고 column exists
        cur.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = %s AND column_name = '광고'
        """, (TABLE,))
        if not cur.fetchone():
            cur.execute(f'ALTER TABLE "{TABLE}" ADD COLUMN "광고" TEXT')
            conn.commit()
            print("Added 광고 column")

        # Check current values
        cur.execute(f'SELECT DISTINCT "현황" FROM "{TABLE}" WHERE "현황" IS NOT NULL ORDER BY "현황"')
        print('=== 현재 현황 값 ===')
        for r in cur.fetchall():
            print(f'  [{r[0]}]')

        # Process all rows
        cur.execute(f'SELECT id, "현황" FROM "{TABLE}" WHERE "현황" IS NOT NULL')
        rows = cur.fetchall()
        updated = 0
        all_ad_values = set()

        for row_id, status in rows:
            if not status or not status.strip():
                continue
            parts = [p.strip() for p in status.split(',') if p.strip()]
            ad_parts = [p for p in parts if p in AD_PLATFORMS]
            status_parts = [p for p in parts if p not in AD_PLATFORMS]

            # All parts go to 광고
            ad_value = ', '.join(parts) if parts else None
            all_ad_values.update(parts)

            # 현황: 등록 if has ad platform, else 등록대기
            if ad_parts:
                new_status = '등록'
            else:
                new_status = '등록대기'

            cur.execute(f'UPDATE "{TABLE}" SET "광고" = %s, "현황" = %s WHERE id = %s',
                        (ad_value, new_status, row_id))
            updated += 1

        # Handle NULL 현황
        cur.execute(f'UPDATE "{TABLE}" SET "현황" = %s WHERE "현황" IS NULL', ('등록대기',))
        print(f"Set {cur.rowcount} NULL rows to 등록대기")

        conn.commit()
        print(f"Updated {updated} rows")

        # Update field_definitions
        sorted_opts = sorted(all_ad_values)
        cur.execute("""
            INSERT INTO field_definitions (database_id, field_name, display_name, field_type, select_options, is_editable)
            VALUES (%s, '광고', '광고', 'multi-select', %s, true)
            ON CONFLICT (database_id, field_name) DO UPDATE
            SET field_type = 'multi-select', select_options = EXCLUDED.select_options
        """, (DB_ID, sorted_opts))
        print(f"광고 options: {sorted_opts}")

        status_options = ['등록', '등록대기', '거래됨', '철회', '보류', '계약', '전속있음', '확인불가', '경매진행중', '일시중단 요청']
        cur.execute("""
            INSERT INTO field_definitions (database_id, field_name, display_name, field_type, select_options, is_editable)
            VALUES (%s, '현황', '현황', 'single-select', %s, true)
            ON CONFLICT (database_id, field_name) DO UPDATE
            SET field_type = 'single-select', select_options = EXCLUDED.select_options
        """, (DB_ID, status_options))
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

print("Done!")
