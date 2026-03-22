#!/usr/bin/env python3
"""Create 광고(자동완성) trigger for 부분부동산 (rental-only, different format)"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2 import sql as psql

TABLE = 'sales_building_copy'

FUNC_SQL = """
CREATE OR REPLACE FUNCTION format_ad_text_partial()
RETURNS trigger AS $$
DECLARE
    result TEXT := '';
    deposit_text TEXT;
    rent_text TEXT;
    v_deposit NUMERIC;
    v_rent NUMERIC;
    v_kind TEXT;
BEGIN
    -- 홍보문구 먼저
    IF COALESCE(TRIM(NEW."홍보문구"), '') != '' THEN
        result := NEW."홍보문구" || E'\n';
    END IF;

    -- 물건종류
    result := result || '- 물건종류 : ' || COALESCE(NEW."물건종류", '') || E'\n';

    -- 임대종류
    v_kind := COALESCE(TRIM(NEW."종류"), '');
    result := result || '- 임대종류 : ' || v_kind || E'\n';

    -- 임대내역
    v_deposit := COALESCE(NULLIF(TRIM(COALESCE(NEW."보증금(만원)"::text, '')), '')::numeric, 0);
    v_rent := COALESCE(NULLIF(TRIM(COALESCE(NEW."월세(만원)"::text, '')), '')::numeric, 0);

    -- 보증금 텍스트
    IF v_deposit >= 10000 THEN
        deposit_text := FLOOR(v_deposit / 10000)::text || '억';
        IF MOD(v_deposit::bigint, 10000) > 0 THEN
            deposit_text := deposit_text || ' ' || MOD(v_deposit::bigint, 10000)::text || '만원';
        ELSE
            deposit_text := deposit_text || '원';
        END IF;
    ELSE
        deposit_text := v_deposit::bigint::text || '만원';
    END IF;

    -- 월세 텍스트
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

    -- 전세: 보증금만 / 월세: 보증금+월세
    IF v_kind LIKE '%전세%' THEN
        result := result || '- 임대내역 : 보증금 ' || deposit_text || E'\n';
    ELSE
        result := result || '- 임대내역 : 보증금 ' || deposit_text || '/월세 ' || rent_text || E'\n';
    END IF;

    -- 관리비
    result := result || '- 관리비 : ' || COALESCE(NEW."관리비"::text, '') || '만원' || E'\n';

    -- 전용면적
    result := result || '- 전용면적 : ' || COALESCE(NEW."전용면적"::text, '') || '㎡' || E'\n';

    -- 방/화장실
    result := result || '- 방/화장실 : ' || COALESCE(NEW."방"::text, '') || '/' || COALESCE(NEW."화"::text, '') || E'\n';

    -- 방향
    result := result || '- 방향 : ' || COALESCE(NEW."방향", '') || E'\n';

    -- 위반건축물
    result := result || '- 위반건축물 : ' || COALESCE(NEW."위반건축물", '') || E'\n';

    -- 입주가능일
    result := result || '- 입주가능일 : ' || COALESCE(NEW."입주가능일", '');

    NEW."광고(자동완성)" := result;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # 1. Create the function
        cur.execute(FUNC_SQL)
        print('1. Created format_ad_text_partial() function')

        # 2. Drop old trigger (format_ad_text) and apply new one
        cur.execute(psql.SQL("DROP TRIGGER IF EXISTS {} ON {}").format(
            psql.Identifier('trigger_ad_sales_building_copy'),
            psql.Identifier(TABLE)))
        print('2. Dropped old trigger')

        trigger_name = 'trigger_ad_partial'
        cur.execute(psql.SQL("DROP TRIGGER IF EXISTS {} ON {}").format(
            psql.Identifier(trigger_name), psql.Identifier(TABLE)))
        cur.execute(psql.SQL(
            "CREATE TRIGGER {} BEFORE INSERT OR UPDATE ON {} FOR EACH ROW EXECUTE FUNCTION format_ad_text_partial()"
        ).format(psql.Identifier(trigger_name), psql.Identifier(TABLE)))
        print(f'3. Applied trigger_ad_partial to {TABLE}')

        # 4. Update existing records
        cur.execute(psql.SQL(
            """UPDATE {} SET "광고(자동완성)" = "광고(자동완성)" """
        ).format(psql.Identifier(TABLE)))
        print(f'4. Updated {cur.rowcount} existing records')

        conn.commit()

print('\nDone!')
