#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB에서 동탄구 관련 데이터 확인
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "goldenrabbit"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD")
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. 동탄구 관련 법정동 확인
print("=" * 60)
print("1. 동탄구 관련 법정동 (41597%)")
print("=" * 60)
cursor.execute("""
    SELECT bjdong_code, sigungu_name, eupmyeondong_name, full_address
    FROM bjdong_codes_active
    WHERE bjdong_code LIKE '41597%'
    ORDER BY bjdong_code
    LIMIT 10
""")

results = cursor.fetchall()
for r in results:
    code = r['bjdong_code']
    sigungu = r['sigungu_name']
    dong = r['eupmyeondong_name']
    full = r['full_address']
    print(f"  {code} - {sigungu} {dong} | {full}")

# 2. 오산동 검색
print()
print("=" * 60)
print("2. 오산동 검색 (full_address ILIKE)")
print("=" * 60)
cursor.execute("""
    SELECT bjdong_code, sigungu_name, eupmyeondong_name, full_address
    FROM bjdong_codes_active
    WHERE full_address ILIKE '%오산동%'
    ORDER BY bjdong_code
""")

results = cursor.fetchall()
for r in results:
    code = r['bjdong_code']
    sigungu = r['sigungu_name']
    dong = r['eupmyeondong_name']
    full = r['full_address']
    print(f"  {code} - {sigungu} {dong} | {full}")

# 3. 정규화된 시군구명 검색 테스트
print()
print("=" * 60)
print("3. 정규화된 시군구명 검색 테스트")
print("=" * 60)
cursor.execute("""
    SELECT bjdong_code, sigungu_name, eupmyeondong_name,
           regexp_replace(sigungu_name, '^(.+시)(.+구)$', E'\\1 \\2') as normalized,
           regexp_replace(sigungu_name, '^(.+시)(.+구)$', E'\\1 \\2') || ' ' || COALESCE(eupmyeondong_name, '') as full_normalized
    FROM bjdong_codes_active
    WHERE sigungu_name ~ '^.+시.+구$'
      AND eupmyeondong_name = '오산동'
""")

results = cursor.fetchall()
for r in results:
    code = r['bjdong_code']
    sigungu = r['sigungu_name']
    normalized = r['normalized']
    full_norm = r['full_normalized']
    print(f"  {code}: {sigungu} -> {normalized} | 전체: {full_norm}")

# 4. 정규화된 검색어로 검색
print()
print("=" * 60)
print("4. '화성시 동탄구 오산동' ILIKE 검색")
print("=" * 60)
cursor.execute("""
    SELECT bjdong_code, sigungu_name, eupmyeondong_name
    FROM bjdong_codes_active
    WHERE sigungu_name ~ '^.+시.+구$'
      AND (
          regexp_replace(sigungu_name, '^(.+시)(.+구)$', E'\\1 \\2')
          || ' ' || COALESCE(eupmyeondong_name, '')
      ) ILIKE '%오산동%'
""")

results = cursor.fetchall()
for r in results:
    code = r['bjdong_code']
    sigungu = r['sigungu_name']
    dong = r['eupmyeondong_name']
    print(f"  {code} - {sigungu} {dong}")

cursor.close()
conn.close()
