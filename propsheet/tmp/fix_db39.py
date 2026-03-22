#!/usr/bin/env python3
"""Fix DB 39 (goldenrabbit01_sales_building): defaults + map trigger"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # 1. Drop bad trigger
        cur.execute('DROP TRIGGER IF EXISTS trigger_calculate_values_gb01 ON goldenrabbit01_sales_building')

        # 2. Create simple map trigger function
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_map_link()
            RETURNS trigger AS $$
            BEGIN
                IF NEW."지번 주소" IS NOT NULL THEN
                    NEW."지도" := 'https://map.kakao.com/?q=' || REPLACE(NEW."지번 주소", ' ', '');
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        # 3. Apply trigger
        cur.execute('DROP TRIGGER IF EXISTS trigger_map_link ON goldenrabbit01_sales_building')
        cur.execute("""
            CREATE TRIGGER trigger_map_link
            BEFORE INSERT OR UPDATE ON goldenrabbit01_sales_building
            FOR EACH ROW EXECUTE FUNCTION update_map_link()
        """)
        print("1. Created map trigger")

        # 4. Fix existing map URLs
        cur.execute("""
            UPDATE goldenrabbit01_sales_building
            SET "지도" = 'https://map.kakao.com/?q=' || REPLACE("지번 주소", ' ', '')
            WHERE "지번 주소" IS NOT NULL
        """)
        print(f"2. Updated {cur.rowcount} map URLs")

        # 5. Clear new record defaults (371, 372)
        cur.execute("""
            UPDATE goldenrabbit01_sales_building
            SET "위반건축물" = NULL, "주차대수" = NULL, "승강기수" = NULL
            WHERE id IN (371, 372)
        """)
        print(f"3. Cleared {cur.rowcount} new record defaults")

        conn.commit()

        # Verify
        cur.execute('SELECT id, "위반건축물", "주차대수", "승강기수", substring("지도", 1, 50) FROM goldenrabbit01_sales_building ORDER BY id DESC LIMIT 3')
        for r in cur.fetchall():
            print(f"   id={r[0]}: 위반={r[1]}, 주차={r[2]}, 승강기={r[3]}, map={r[4]}")

print("Done!")
