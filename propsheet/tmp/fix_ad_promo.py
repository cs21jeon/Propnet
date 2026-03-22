#!/usr/bin/env python3
"""Add 홍보문구 to top of format_ad_text() trigger (단일부동산)"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2 import sql as psql

FUNC_SQL = """
CREATE OR REPLACE FUNCTION format_ad_text()
RETURNS trigger AS $$
DECLARE
    result TEXT := '';
    price_text TEXT;
    deposit_text TEXT;
    rent_text TEXT;
    lease_line TEXT := '';
    floor_text TEXT;
    slash_pos INT;
    underground INT;
    aboveground INT;
    v_price NUMERIC;
    v_deposit NUMERIC;
    v_rent NUMERIC;
BEGIN
    -- 홍보문구 최상단
    IF COALESCE(TRIM(NEW."홍보문구"), '') != '' THEN
        result := NEW."홍보문구" || E'\\n';
    END IF;

    -- 매매금액
    v_price := COALESCE(NEW."매가(만원)"::numeric, 0);
    IF v_price >= 10000 THEN
        price_text := FLOOR(v_price / 10000)::text || '억';
        IF MOD(v_price::bigint, 10000) > 0 THEN
            price_text := price_text || ' ' || MOD(v_price::bigint, 10000)::text || '만원';
        END IF;
    ELSE
        price_text := v_price::bigint::text || '만원';
    END IF;
    result := result || '- 매매금액 : ' || price_text || E'\\n';

    -- 임대내역
    v_deposit := COALESCE(NULLIF(TRIM(COALESCE(NEW."보증금(만원)"::text, '')), '')::numeric, 0);
    v_rent := COALESCE(NULLIF(TRIM(COALESCE(NEW."월세(만원)"::text, '')), '')::numeric, 0);

    IF v_deposit > 0 OR v_rent > 0 THEN
        IF v_deposit > 0 THEN
            IF v_deposit >= 10000 THEN
                deposit_text := '보증금 ' || FLOOR(v_deposit / 10000)::text || '억';
                IF MOD(v_deposit::bigint, 10000) > 0 THEN
                    deposit_text := deposit_text || ' ' || MOD(v_deposit::bigint, 10000)::text || '만원';
                ELSE
                    deposit_text := deposit_text || '원';
                END IF;
            ELSE
                deposit_text := '보증금 ' || v_deposit::bigint::text || '만원';
            END IF;
        END IF;

        IF v_rent > 0 THEN
            IF v_rent >= 10000 THEN
                rent_text := FLOOR(v_rent / 10000)::text || '억';
                IF MOD(v_rent::bigint, 10000) > 0 THEN
                    rent_text := rent_text || ' ' || MOD(v_rent::bigint, 10000)::text || '만원';
                ELSE
                    rent_text := rent_text || '원';
                END IF;
            ELSE
                rent_text := v_rent::bigint::text || '만원';
            END IF;
        END IF;

        IF v_deposit > 0 AND v_rent > 0 THEN
            lease_line := '- 임대내역 : ' || deposit_text || '/월세 ' || rent_text || ' (관리비포함)';
        ELSIF v_deposit > 0 THEN
            lease_line := '- 임대내역 : ' || deposit_text;
        ELSE
            lease_line := '- 임대내역 : 월세 ' || rent_text || ' (관리비포함)';
        END IF;
        result := result || lease_line || E'\\n';
    END IF;

    -- 건물현황
    result := result || '- 건물현황 : ' || COALESCE(NEW."건물구성", '') || E'\\n';

    -- 대지면적 / 연면적
    result := result || '- 대지면적 : ' || COALESCE(NEW."대지면적(㎡)"::text, '') || '㎡(약' ||
        ROUND(COALESCE(NEW."대지면적(㎡)"::numeric, 0) / 3.3, 1)::text || '평) / 연면적 : ' ||
        COALESCE(NEW."연면적(㎡)"::text, '') || '㎡(약' ||
        ROUND(COALESCE(NEW."연면적(㎡)"::numeric, 0) / 3.3, 1)::text || '평)' || E'\\n';

    -- 층수
    IF NEW."층수" IS NOT NULL AND POSITION('/' IN NEW."층수") > 0 THEN
        slash_pos := POSITION('/' IN NEW."층수");
        BEGIN
            underground := ABS(TRIM(SUBSTRING(NEW."층수" FROM 1 FOR slash_pos - 1))::int);
            aboveground := TRIM(SUBSTRING(NEW."층수" FROM slash_pos + 1))::int;
            IF underground = 0 AND aboveground = 0 THEN
                floor_text := '해당없음';
            ELSIF underground = 0 THEN
                floor_text := '지상' || aboveground::text || '층';
            ELSIF aboveground = 0 THEN
                floor_text := '지하' || underground::text || '층';
            ELSE
                floor_text := '지하' || underground::text || '층/지상' || aboveground::text || '층';
            END IF;
        EXCEPTION WHEN OTHERS THEN
            floor_text := COALESCE(NEW."층수", '');
        END;
    ELSE
        floor_text := COALESCE(NEW."층수", '');
    END IF;
    result := result || '- 층수 : ' || floor_text || E'\\n';

    -- 주차
    result := result || '- 주차 : ' || COALESCE(NEW."주차대수"::text, '0') || '대' || E'\\n';

    -- 승강기
    IF COALESCE(NEW."승강기수"::text, '0') = '0' THEN
        result := result || '- 승강기 : 없음' || E'\\n';
    ELSE
        result := result || '- 승강기 : 有' || E'\\n';
    END IF;

    -- 방향
    result := result || '- 방향 : ' || COALESCE(NEW."방향", '') || ' (주출입구 기준, 호실별 상이함)' || E'\\n';

    -- 주용도
    result := result || '- 주용도 : ' || COALESCE(NEW."주용도", '') || E'\\n';

    -- 용도지역
    result := result || '- 용도지역 : ' || COALESCE(NEW."용도지역", '') || E'\\n';

    -- 위반건축물
    result := result || '- 위반건축물 : ' || COALESCE(NEW."위반건축물", '') || E'\\n';

    -- 사용승인일
    IF NEW."사용승인일" IS NOT NULL AND TRIM(NEW."사용승인일"::text) != '' THEN
        BEGIN
            result := result || '- 사용승인일 : ' || TO_CHAR(NEW."사용승인일"::date, 'YYYY-MM-DD');
        EXCEPTION WHEN OTHERS THEN
            result := result || '- 사용승인일 : ' || NEW."사용승인일"::text;
        END;
    ELSE
        result := result || '- 사용승인일 : 대장상 미표기';
    END IF;

    NEW."광고(자동완성)" := result;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # 1. Update function
        cur.execute(FUNC_SQL)
        print('1. Updated format_ad_text() with 홍보문구 at top')

        # 2. Re-trigger existing records on all building tables
        tables = [
            'goldenrabbit01_sales_building',
            'sales_building',
            'sales_building_bkvh',
            'sales_building_copy',
        ]
        for table in tables:
            cur.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = %s AND column_name = '광고(자동완성)'
            """, (table,))
            if not cur.fetchone():
                continue
            # Check which trigger this table uses
            cur.execute("""
                SELECT tgname FROM pg_trigger t
                JOIN pg_class c ON t.tgrelid = c.oid
                WHERE c.relname = %s AND tgname LIKE 'trigger_ad%%'
            """, (table,))
            triggers = [r[0] for r in cur.fetchall()]
            # Only update tables using format_ad_text (not partial)
            if any('partial' in t for t in triggers):
                print(f'   SKIP {table} (uses partial trigger)')
                continue
            cur.execute(psql.SQL(
                'UPDATE {} SET "광고(자동완성)" = "광고(자동완성)" WHERE "매가(만원)" IS NOT NULL'
            ).format(psql.Identifier(table)))
            print(f'2. Updated {cur.rowcount} records in {table}')

        # 3. Also update field_definitions formula to include 홍보문구
        BUILDING_FORMULA = r"""COALESCE("홍보문구", '') || E'\n' ||
'- 매매금액 : ' ||
CASE WHEN COALESCE("매가(만원)", 0) >= 10000
  THEN FLOOR("매가(만원)" / 10000)::text || '억' ||
    CASE WHEN MOD("매가(만원)"::bigint, 10000) > 0
      THEN ' ' || MOD("매가(만원)"::bigint, 10000)::text || '만원' ELSE '' END
  ELSE COALESCE("매가(만원)"::bigint::text, '0') || '만원' END || E'\n' ||
'- 건물현황 : ' || COALESCE("건물구성", '') || E'\n' ||
'- 층수 : ' || COALESCE("층수", '') || E'\n' ||
'- 주차 : ' || COALESCE("주차대수"::text, '0') || '대' || E'\n' ||
'- 승강기 : ' || CASE WHEN COALESCE("승강기수"::text, '0') = '0' THEN '없음' ELSE '有' END || E'\n' ||
'- 방향 : ' || COALESCE("방향", '') || E'\n' ||
'- 위반건축물 : ' || COALESCE("위반건축물", '') || E'\n' ||
'- 사용승인일 : ' || COALESCE("사용승인일"::text, '대장상 미표기')"""

        for db_id in [1, 39]:
            cur.execute("""
                UPDATE field_definitions SET formula = %s
                WHERE database_id = %s AND field_name = '광고(자동완성)'
            """, (BUILDING_FORMULA, db_id))
            print(f'3. Updated formula for DB {db_id}')

        conn.commit()

print('\nDone!')
