#!/usr/bin/env python3
"""Create 광고(자동완성) trigger function and apply to all relevant tables"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

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
    result := '- 매매금액 : ' || price_text || E'\\n';

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

    -- 층수 (지하/지상 파싱)
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
        # 1. Create the function
        cur.execute(FUNC_SQL)
        print('1. Created format_ad_text() function')

        # 2. Apply trigger to all tables with 광고(자동완성) column
        cur.execute("""
            SELECT DISTINCT table_name FROM information_schema.columns
            WHERE column_name = '광고(자동완성)'
            AND table_schema = 'public'
        """)
        tables = [r[0] for r in cur.fetchall()]
        print(f'   Found tables: {tables}')

        for table in tables:
            # Check required columns exist
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND column_name IN (
                    '매가(만원)', '보증금(만원)', '월세(만원)', '건물구성',
                    '대지면적(㎡)', '연면적(㎡)', '층수', '주차대수', '승강기수',
                    '방향', '주용도', '용도지역', '위반건축물', '사용승인일'
                )
            """, (table,))
            found_cols = {r[0] for r in cur.fetchall()}
            required = {'매가(만원)', '건물구성', '대지면적(㎡)', '연면적(㎡)', '층수'}
            missing = required - found_cols
            if missing:
                print(f'   SKIP {table}: missing {missing}')
                continue

            trigger_name = f'trigger_ad_{table[:40]}'
            from psycopg2 import sql as psql
            cur.execute(psql.SQL('DROP TRIGGER IF EXISTS {} ON {}').format(
                psql.Identifier(trigger_name), psql.Identifier(table)))
            cur.execute(psql.SQL(
                'CREATE TRIGGER {} BEFORE INSERT OR UPDATE ON {} FOR EACH ROW EXECUTE FUNCTION format_ad_text()'
            ).format(psql.Identifier(trigger_name), psql.Identifier(table)))
            print(f'2. Applied trigger to {table}')

            # 3. Trigger update on existing records to regenerate ad text
            cur.execute(psql.SQL(
                'UPDATE {} SET "광고(자동완성)" = "광고(자동완성)" WHERE "매가(만원)" IS NOT NULL'
            ).format(psql.Identifier(table)))
            print(f'   Updated {cur.rowcount} existing records')

        conn.commit()

print('\nDone!')
