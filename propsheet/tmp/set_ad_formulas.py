#!/usr/bin/env python3
"""Set field_definitions formula for 광고(자동완성) on all relevant databases.
This ensures the formula column is recognized as 'formula' type and
the trigger fires on related field changes.
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

# Formula for 단일부동산 (building - 매매 포함)
BUILDING_FORMULA = r"""
COALESCE("홍보문구", '') || E'\n' ||
'- 매매금액 : ' ||
CASE WHEN COALESCE("매가(만원)", 0) >= 10000
  THEN FLOOR("매가(만원)" / 10000)::text || '억' ||
    CASE WHEN MOD("매가(만원)"::bigint, 10000) > 0
      THEN ' ' || MOD("매가(만원)"::bigint, 10000)::text || '만원' ELSE '' END
  ELSE COALESCE("매가(만원)"::bigint::text, '0') || '만원' END || E'\n' ||
CASE WHEN COALESCE("보증금(만원)", 0) > 0 OR COALESCE("월세(만원)", 0) > 0 THEN
  '- 임대내역 : ' ||
  CASE WHEN COALESCE("보증금(만원)", 0) > 0 AND COALESCE("월세(만원)", 0) > 0 THEN
    '보증금 ' || CASE WHEN "보증금(만원)" >= 10000
      THEN FLOOR("보증금(만원)" / 10000)::text || '억' ||
        CASE WHEN MOD("보증금(만원)"::bigint, 10000) > 0
          THEN ' ' || MOD("보증금(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
      ELSE "보증금(만원)"::bigint::text || '만원' END ||
    '/월세 ' || CASE WHEN "월세(만원)" >= 10000
      THEN FLOOR("월세(만원)" / 10000)::text || '억' ||
        CASE WHEN MOD("월세(만원)"::bigint, 10000) > 0
          THEN ' ' || MOD("월세(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
      ELSE "월세(만원)"::bigint::text || '만원' END || ' (관리비포함)'
  WHEN COALESCE("보증금(만원)", 0) > 0 THEN
    '보증금 ' || CASE WHEN "보증금(만원)" >= 10000
      THEN FLOOR("보증금(만원)" / 10000)::text || '억' ||
        CASE WHEN MOD("보증금(만원)"::bigint, 10000) > 0
          THEN ' ' || MOD("보증금(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
      ELSE "보증금(만원)"::bigint::text || '만원' END
  ELSE
    '월세 ' || CASE WHEN "월세(만원)" >= 10000
      THEN FLOOR("월세(만원)" / 10000)::text || '억' ||
        CASE WHEN MOD("월세(만원)"::bigint, 10000) > 0
          THEN ' ' || MOD("월세(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
      ELSE "월세(만원)"::bigint::text || '만원' END || ' (관리비포함)'
  END || E'\n'
ELSE '' END ||
'- 건물현황 : ' || COALESCE("건물구성", '') || E'\n' ||
'- 대지면적 : ' || COALESCE("대지면적(㎡)"::text, '') || '㎡(약' || ROUND(COALESCE("대지면적(㎡)", 0) / 3.3, 1)::text || '평) / 연면적 : ' || COALESCE("연면적(㎡)"::text, '') || '㎡(약' || ROUND(COALESCE("연면적(㎡)", 0) / 3.3, 1)::text || '평)' || E'\n' ||
'- 층수 : ' || COALESCE("층수", '') || E'\n' ||
'- 주차 : ' || COALESCE("주차대수"::text, '0') || '대' || E'\n' ||
'- 승강기 : ' || CASE WHEN COALESCE("승강기수"::text, '0') = '0' THEN '없음' ELSE '有' END || E'\n' ||
'- 방향 : ' || COALESCE("방향", '') || ' (주출입구 기준, 호실별 상이함)' || E'\n' ||
'- 주용도 : ' || COALESCE("주용도", '') || E'\n' ||
'- 용도지역 : ' || COALESCE("용도지역", '') || E'\n' ||
'- 위반건축물 : ' || COALESCE("위반건축물", '') || E'\n' ||
'- 사용승인일 : ' || COALESCE("사용승인일"::text, '대장상 미표기')
""".strip()

# Formula for 부분부동산 (partial - 임대 전용)
PARTIAL_FORMULA = r"""
COALESCE("홍보문구", '') || E'\n' ||
'- 물건종류 : ' || COALESCE("물건종류", '') || E'\n' ||
'- 임대종류 : ' || COALESCE("종류", '') || E'\n' ||
'- 임대내역 : ' ||
CASE WHEN COALESCE("종류", '') LIKE '%전세%' THEN
  '보증금 ' || CASE WHEN COALESCE("보증금(만원)", 0) >= 10000
    THEN FLOOR("보증금(만원)" / 10000)::text || '억' ||
      CASE WHEN MOD("보증금(만원)"::bigint, 10000) > 0
        THEN ' ' || MOD("보증금(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
    ELSE COALESCE("보증금(만원)"::bigint::text, '0') || '만원' END
ELSE
  '보증금 ' || CASE WHEN COALESCE("보증금(만원)", 0) >= 10000
    THEN FLOOR("보증금(만원)" / 10000)::text || '억' ||
      CASE WHEN MOD("보증금(만원)"::bigint, 10000) > 0
        THEN ' ' || MOD("보증금(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
    ELSE COALESCE("보증금(만원)"::bigint::text, '0') || '만원' END ||
  '/월세 ' || CASE WHEN COALESCE("월세(만원)", 0) >= 10000
    THEN FLOOR("월세(만원)" / 10000)::text || '억' ||
      CASE WHEN MOD("월세(만원)"::bigint, 10000) > 0
        THEN ' ' || MOD("월세(만원)"::bigint, 10000)::text || '만원' ELSE '원' END
    ELSE COALESCE("월세(만원)"::bigint::text, '0') || '만원' END
END || E'\n' ||
'- 관리비 : ' || COALESCE("관리비"::text, '') || '만원' || E'\n' ||
'- 전용면적 : ' || COALESCE("전용면적"::text, '') || '㎡' || E'\n' ||
'- 방/화장실 : ' || COALESCE("방"::text, '') || '/' || COALESCE("화"::text, '') || E'\n' ||
'- 방향 : ' || COALESCE("방향", '') || E'\n' ||
'- 위반건축물 : ' || COALESCE("위반건축물", '') || E'\n' ||
'- 입주가능일 : ' || COALESCE("입주가능일", '')
""".strip()

# DB ID -> formula mapping
DB_FORMULAS = {
    # 단일부동산 (건물 매매)
    1: BUILDING_FORMULA,    # 건물 매물 (sales_building)
    39: BUILDING_FORMULA,   # 단일부동산 (goldenrabbit01_sales_building)
    # 부분부동산 (임대)
    43: PARTIAL_FORMULA,    # 부분부동산 (sales_building_copy)
}

with get_db_connection() as conn:
    with conn.cursor() as cur:
        for db_id, formula in DB_FORMULAS.items():
            cur.execute("""
                INSERT INTO field_definitions (database_id, field_name, display_name, field_type, formula, is_editable)
                VALUES (%s, '광고(자동완성)', '광고(자동완성)', 'formula', %s, false)
                ON CONFLICT (database_id, field_name) DO UPDATE
                SET field_type = 'formula', formula = EXCLUDED.formula, is_editable = false
            """, (db_id, formula))
            print(f'DB {db_id}: formula set ({len(formula)} chars)')

        conn.commit()

print('\nDone!')
