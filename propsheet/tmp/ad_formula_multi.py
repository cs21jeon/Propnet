#!/usr/bin/env python3
"""Create 광고(자동완성) trigger for 집합부동산 (multi-unit)"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2 import sql as psql

TABLE = 'goldenrabbit01_sales_multi_unit'
DB_ID = 38

FUNC_SQL = """
CREATE OR REPLACE FUNCTION format_ad_text_multi()
RETURNS trigger AS $$
DECLARE
    result TEXT := '';
    price_text TEXT;
    deposit_text TEXT;
    rent_text TEXT;
    v_kind TEXT;
    v_price NUMERIC;
    v_deposit NUMERIC;
    v_rent NUMERIC;
    v_housing NUMERIC;
    slash_pos INT;
    household_text TEXT;
BEGIN
    -- 홍보문구 최상단
    IF COALESCE(TRIM(NEW."홍보문구"), '') != '' THEN
        result := NEW."홍보문구" || E'\\n';
    END IF;

    -- 매물 종류
    result := result || '- 매물 종류 : ' || COALESCE(NEW."물건종류", '') || E'\\n';

    -- 거래 유형
    v_kind := COALESCE(TRIM(NEW."종류"), '');
    result := result || '- 거래 유형 : ' || v_kind || E'\\n';

    -- 금액 (매매/전세/월세에 따라 다르게)
    v_price := COALESCE(NEW."매가(만원)", 0);
    v_deposit := COALESCE(NEW."보증금(만원)", 0);
    v_rent := COALESCE(NEW."월세(만원)", 0);

    IF v_kind = '매매' THEN
        -- 매매가
        IF v_price >= 10000 THEN
            price_text := FLOOR(v_price / 10000)::text || '억';
            IF MOD(v_price::bigint, 10000) > 0 THEN
                price_text := price_text || ' ' || MOD(v_price::bigint, 10000)::text || '만원';
            ELSE
                price_text := price_text || '원';
            END IF;
        ELSE
            price_text := v_price::bigint::text || '만원';
        END IF;
        result := result || '- 금액 : ' || price_text || E'\\n';
    ELSIF v_kind = '전세' THEN
        -- 보증금만
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
        result := result || '- 금액 : ' || deposit_text || E'\\n';
    ELSE
        -- 월세: 보증금 + 월세
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
        result := result || '- 금액 : ' || deposit_text || '/월세 ' || rent_text || E'\\n';
    END IF;

    -- 관리비 (매매가 아닌 경우만)
    IF v_kind != '매매' THEN
        result := result || '- 관리비 : ' || COALESCE(NEW."관리비(만원)"::text, '') || '만원' || E'\\n';
    END IF;

    -- 전용면적
    result := result || '- 전용면적 : ' || COALESCE(NEW."전용면적(㎡)"::text, '') || '㎡ (약' ||
        ROUND(COALESCE(NEW."전용면적(㎡)", 0) / 3.3, 1)::text || '평)' || E'\\n';

    -- 공급면적
    result := result || '- 공급면적 : ' || COALESCE(NEW."공급면적(㎡)"::text, '') || '㎡ (약' ||
        ROUND(COALESCE(NEW."공급면적(㎡)", 0) / 3.3, 1)::text || '평)' || E'\\n';

    -- 대지지분
    result := result || '- 대지지분 : ' || COALESCE(NEW."대지지분(㎡)"::text, '') || '㎡ (약' ||
        ROUND(COALESCE(NEW."대지지분(㎡)", 0) / 3.3, 1)::text || '평)' || E'\\n';

    -- 총세대수 (총 세대/가구/호에서 / 앞부분만)
    IF NEW."총 세대/가구/호" IS NOT NULL AND POSITION('/' IN NEW."총 세대/가구/호") > 0 THEN
        household_text := TRIM(SUBSTRING(NEW."총 세대/가구/호" FROM 1 FOR POSITION('/' IN NEW."총 세대/가구/호") - 1)) || '세대';
    ELSE
        household_text := COALESCE(NEW."총 세대/가구/호", '') || '세대';
    END IF;
    result := result || '- 총세대수 : ' || household_text || E'\\n';

    -- 총주차대수
    result := result || '- 총주차대수 : ' || COALESCE(NEW."총주차대수"::int::text, '0') || '대' || E'\\n';

    -- 승강기
    IF COALESCE(NEW."해당동 승강기수", 0) = 0 THEN
        result := result || '- 승강기 : 無' || E'\\n';
    ELSE
        result := result || '- 승강기 : 有' || E'\\n';
    END IF;

    -- 사용승인일
    IF NEW."사용승인일" IS NOT NULL THEN
        BEGIN
            result := result || '- 사용승인일 : ' || TO_CHAR(NEW."사용승인일"::date, 'YYYY-MM-DD') || E'\\n';
        EXCEPTION WHEN OTHERS THEN
            result := result || '- 사용승인일 : ' || NEW."사용승인일"::text || E'\\n';
        END;
    ELSE
        result := result || '- 사용승인일 : 대장상 미표기' || E'\\n';
    END IF;

    -- 용도지역
    result := result || '- 용도지역 : ' || COALESCE(NEW."용도지역", '') || E'\\n';

    -- 공동주택 공시가격
    v_housing := COALESCE(NEW."주택가격(만원)", 0);
    IF v_housing >= 10000 THEN
        result := result || '- 공동주택 공시가격 : ' || FLOOR(v_housing / 10000)::text || '억';
        IF MOD(v_housing::bigint, 10000) > 0 THEN
            result := result || ' ' || MOD(v_housing::bigint, 10000)::text || '만원';
        ELSE
            result := result || '원';
        END IF;
    ELSE
        result := result || '- 공동주택 공시가격 : ' || v_housing::bigint::text || '만원';
    END IF;
    result := result || E'\\n';

    -- 방/화장실
    result := result || '- 방/화장실 개수 : ' || COALESCE(NEW."방"::int::text, '') || '/' || COALESCE(NEW."화"::int::text, '') || E'\\n';

    -- 방향
    result := result || '- 방향 : ' || COALESCE(NEW."방향", '') || E'\\n';

    -- 입주가능일
    result := result || '- 입주가능일 : ' || COALESCE(NEW."입주가능일", '');

    NEW."광고(자동완성)" := result;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

# Formula text for field_definitions (simplified representation)
MULTI_FORMULA = r"""COALESCE("홍보문구", '') || E'\n' ||
'- 매물 종류 : ' || COALESCE("물건종류", '') || E'\n' ||
'- 거래 유형 : ' || COALESCE("종류", '') || E'\n' ||
'- 금액 : ' ||
CASE WHEN COALESCE("종류", '') = '매매' THEN
  CASE WHEN COALESCE("매가(만원)", 0) >= 10000
    THEN FLOOR("매가(만원)" / 10000)::text || '억' ||
      CASE WHEN MOD("매가(만원)"::bigint, 10000) > 0 THEN ' ' || MOD("매가(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
    ELSE COALESCE("매가(만원)"::bigint::text, '0') || '만원' END
WHEN COALESCE("종류", '') = '전세' THEN
  '보증금 ' || CASE WHEN COALESCE("보증금(만원)", 0) >= 10000
    THEN FLOOR("보증금(만원)" / 10000)::text || '억' ||
      CASE WHEN MOD("보증금(만원)"::bigint, 10000) > 0 THEN ' ' || MOD("보증금(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
    ELSE COALESCE("보증금(만원)"::bigint::text, '0') || '만원' END
ELSE
  '보증금 ' || CASE WHEN COALESCE("보증금(만원)", 0) >= 10000
    THEN FLOOR("보증금(만원)" / 10000)::text || '억' ||
      CASE WHEN MOD("보증금(만원)"::bigint, 10000) > 0 THEN ' ' || MOD("보증금(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
    ELSE COALESCE("보증금(만원)"::bigint::text, '0') || '만원' END ||
  '/월세 ' || CASE WHEN COALESCE("월세(만원)", 0) >= 10000
    THEN FLOOR("월세(만원)" / 10000)::text || '억' ||
      CASE WHEN MOD("월세(만원)"::bigint, 10000) > 0 THEN ' ' || MOD("월세(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
    ELSE COALESCE("월세(만원)"::bigint::text, '0') || '만원' END
END || E'\n' ||
CASE WHEN COALESCE("종류", '') != '매매' THEN '- 관리비 : ' || COALESCE("관리비(만원)"::text, '') || '만원' || E'\n' ELSE '' END ||
'- 전용면적 : ' || COALESCE("전용면적(㎡)"::text, '') || '㎡ (약' || ROUND(COALESCE("전용면적(㎡)", 0) / 3.3, 1)::text || '평)' || E'\n' ||
'- 공급면적 : ' || COALESCE("공급면적(㎡)"::text, '') || '㎡ (약' || ROUND(COALESCE("공급면적(㎡)", 0) / 3.3, 1)::text || '평)' || E'\n' ||
'- 대지지분 : ' || COALESCE("대지지분(㎡)"::text, '') || '㎡ (약' || ROUND(COALESCE("대지지분(㎡)", 0) / 3.3, 1)::text || '평)' || E'\n' ||
'- 총주차대수 : ' || COALESCE("총주차대수"::int::text, '0') || '대' || E'\n' ||
'- 승강기 : ' || CASE WHEN COALESCE("해당동 승강기수", 0) = 0 THEN '無' ELSE '有' END || E'\n' ||
'- 사용승인일 : ' || COALESCE("사용승인일"::text, '대장상 미표기') || E'\n' ||
'- 용도지역 : ' || COALESCE("용도지역", '') || E'\n' ||
'- 방/화장실 개수 : ' || COALESCE("방"::int::text, '') || '/' || COALESCE("화"::int::text, '') || E'\n' ||
'- 방향 : ' || COALESCE("방향", '') || E'\n' ||
'- 입주가능일 : ' || COALESCE("입주가능일", '')"""

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # 1. Create function
        cur.execute(FUNC_SQL)
        print('1. Created format_ad_text_multi() function')

        # 2. Apply trigger
        trigger_name = 'trigger_ad_multi'
        # Drop any old triggers
        cur.execute(psql.SQL("DROP TRIGGER IF EXISTS {} ON {}").format(
            psql.Identifier(f'trigger_ad_{TABLE[:40]}'), psql.Identifier(TABLE)))
        cur.execute(psql.SQL("DROP TRIGGER IF EXISTS {} ON {}").format(
            psql.Identifier(trigger_name), psql.Identifier(TABLE)))
        cur.execute(psql.SQL(
            "CREATE TRIGGER {} BEFORE INSERT OR UPDATE ON {} FOR EACH ROW EXECUTE FUNCTION format_ad_text_multi()"
        ).format(psql.Identifier(trigger_name), psql.Identifier(TABLE)))
        print(f'2. Applied trigger to {TABLE}')

        # 3. Update field_definitions
        cur.execute("""
            INSERT INTO field_definitions (database_id, field_name, display_name, field_type, formula, is_editable)
            VALUES (%s, '광고(자동완성)', '광고(자동완성)', 'formula', %s, false)
            ON CONFLICT (database_id, field_name) DO UPDATE
            SET field_type = 'formula', formula = EXCLUDED.formula, is_editable = false
        """, (DB_ID, MULTI_FORMULA))
        print(f'3. Updated field_definitions for DB {DB_ID}')

        # 4. Trigger update on existing records
        cur.execute(psql.SQL(
            'UPDATE {} SET "광고(자동완성)" = "광고(자동완성)"'
        ).format(psql.Identifier(TABLE)))
        print(f'4. Updated {cur.rowcount} existing records')

        conn.commit()

# Verify
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(psql.SQL('SELECT "광고(자동완성)" FROM {} LIMIT 1').format(psql.Identifier(TABLE)))
        r = cur.fetchone()
        if r and r[0]:
            print(f'\n=== Sample output ===\n{r[0]}')
        else:
            print('\n(no data)')

print('\nDone!')
