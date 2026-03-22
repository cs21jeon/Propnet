#!/usr/bin/env python3
"""Fix trigger v2: remove references to non-existent columns"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # First check which columns actually exist
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'sales_building'
            AND column_name IN ('순매가(만원)', '감정가율(%)', '실투자금', '실투자금(융자포함)',
                '융자제외수익률(%)', '융자포함수익률', '126%', '공시가(만원)', '토지가치(만원)',
                '10년간수익(만원)', '지도', '주구조값', '연식값', '건물가치(만원)',
                '10년후건물가치(만원)', '10년후토지가치(만원)', '현재가치지수(%)', '10년가치지수(%)')
        """)
        existing = {r[0] for r in cur.fetchall()}
        print(f"Existing trigger columns: {sorted(existing)}")
        missing = {'순매가(만원)', '감정가율(%)', '실투자금', '실투자금(융자포함)',
                '융자제외수익률(%)', '융자포함수익률', '126%', '공시가(만원)', '토지가치(만원)',
                '10년간수익(만원)', '지도', '주구조값', '연식값', '건물가치(만원)',
                '10년후건물가치(만원)', '10년후토지가치(만원)', '현재가치지수(%)', '10년가치지수(%)'} - existing
        print(f"Missing columns: {sorted(missing)}")

        # Rebuild trigger without missing columns
        trigger_sql = """
            CREATE OR REPLACE FUNCTION calculate_property_values()
            RETURNS trigger AS $$
            BEGIN
                NEW."실투자금" := COALESCE(NEW."매가(만원)", 0) - COALESCE(NEW."보증금(만원)", 0);
                NEW."실투자금(융자포함)" := COALESCE(NEW."매가(만원)", 0) - COALESCE(NEW."융자(만원)", 0) - COALESCE(NEW."보증금(만원)", 0);

                IF NEW."실투자금" > 0 THEN
                    NEW."융자제외수익률(%)" := ROUND((COALESCE(NEW."월세(만원)", 0) * 12.0 / NEW."실투자금") * 100, 1);
                ELSE
                    NEW."융자제외수익률(%)" := 0;
                END IF;

                IF NEW."실투자금(융자포함)" > 0 THEN
                    NEW."융자포함수익률" := ROUND(((COALESCE(NEW."월세(만원)", 0) * 12.0 - COALESCE(NEW."융자(만원)", 0) * 0.05) / NEW."실투자금(융자포함)") * 100, 1);
                ELSE
                    NEW."융자포함수익률" := 0;
                END IF;

                NEW."126%" := ROUND(COALESCE(NEW."주택공시가(만원)", 0) * 1.26, 0);
                NEW."공시가(만원)" := ROUND(COALESCE(NEW."토지면적(㎡)", 0) * COALESCE(NEW."공시지가(원/㎡)", 0) / 10000, -2);
                NEW."토지가치(만원)" := ROUND(COALESCE(NEW."토지면적(㎡)", 0) * COALESCE(NEW."공시지가(원/㎡)", 0) * 2 / 10000, 0);
                NEW."10년간수익(만원)" := COALESCE(NEW."월세(만원)", 0) * 120;

                -- 지도 링크 (공백 유지)
                IF NEW."지번 주소" IS NOT NULL THEN
                    NEW."지도" := 'https://map.kakao.com/link/search/' || NEW."지번 주소";
                END IF;

                IF NEW."주구조" IS NOT NULL AND POSITION('콘크리트' IN NEW."주구조") > 0 THEN
                    NEW."주구조값" := 50;
                ELSE
                    NEW."주구조값" := 30;
                END IF;

                IF NEW."사용승인일" IS NOT NULL THEN
                    NEW."연식값" := EXTRACT(YEAR FROM AGE(CURRENT_DATE, NEW."사용승인일"))::INTEGER;
                ELSE
                    NEW."연식값" := 100;
                END IF;

                IF NEW."공시가(만원)" IS NOT NULL AND NEW."공시가(만원)" < COALESCE(NEW."주구조값", 30) THEN
                    NEW."건물가치(만원)" := ROUND(COALESCE(NEW."연면적(㎡)", 0) * 1500000 *
                        ((COALESCE(NEW."주구조값", 30) - COALESCE(NEW."연식값", 100)) / COALESCE(NEW."주구조값", 30)::NUMERIC) / 10000, 0);
                ELSE
                    NEW."건물가치(만원)" := 0;
                END IF;

                IF (COALESCE(NEW."연식값", 0) + 10) < COALESCE(NEW."주구조값", 30) THEN
                    NEW."10년후건물가치(만원)" := ROUND(COALESCE(NEW."연면적(㎡)", 0) * 1500000 *
                        ((COALESCE(NEW."주구조값", 30) - (COALESCE(NEW."연식값", 0) + 10)) / COALESCE(NEW."주구조값", 30)::NUMERIC) / 10000, 0);
                ELSE
                    NEW."10년후건물가치(만원)" := 0;
                END IF;

                NEW."10년후토지가치(만원)" := ROUND(COALESCE(NEW."토지면적(㎡)", 0) *
                    COALESCE(NEW."공시지가(원/㎡)", 0) * POWER(1.026, 10) * 2 / 10000, 0);

                IF COALESCE(NEW."매가(만원)", 0) > 0 THEN
                    NEW."현재가치지수(%)" := ROUND(
                        (COALESCE(NEW."토지가치(만원)", 0) + COALESCE(NEW."건물가치(만원)", 0)) /
                        NEW."매가(만원)" * 100, 1);
                    NEW."10년가치지수(%)" := ROUND(
                        (COALESCE(NEW."10년후토지가치(만원)", 0) + COALESCE(NEW."10년후건물가치(만원)", 0) + COALESCE(NEW."10년간수익(만원)", 0)) /
                        NEW."매가(만원)" * 100, 1);
                ELSE
                    NEW."현재가치지수(%)" := 0;
                    NEW."10년가치지수(%)" := 0;
                END IF;
        """

        # Only add 감정가율 if column exists
        if '감정가율(%)' in existing:
            trigger_sql += """
                IF COALESCE(NEW."감정가(만원,랜드북)", 0) > 0 THEN
                    NEW."감정가율(%)" := ROUND(COALESCE(NEW."매가(만원)", 0) / NEW."감정가(만원,랜드북)" * 100, 1);
                ELSE
                    NEW."감정가율(%)" := NULL;
                END IF;
            """

        trigger_sql += """
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """

        cur.execute(trigger_sql)
        print("1. Trigger updated (no missing columns)")

        # Step 2: Fix existing map URLs
        cur.execute("""
            UPDATE sales_building
            SET "지도" = 'https://map.kakao.com/link/search/' || "지번 주소"
            WHERE "지번 주소" IS NOT NULL
        """)
        print(f"2. Updated {cur.rowcount} map URLs")

        # Step 3: Fix formula
        cur.execute(
            "UPDATE field_definitions SET formula = %s WHERE field_name = '지도' AND database_id = 1",
            ("'https://map.kakao.com/link/search/' || \"지번 주소\"",)
        )
        print("3. Updated formula")

        conn.commit()

        # Verify
        cur.execute("""SELECT id, substring("지도", 1, 70) FROM sales_building ORDER BY id DESC LIMIT 2""")
        for r in cur.fetchall():
            print(f"   id={r[0]}: {r[1]}")

print("Done!")
