#!/usr/bin/env python3
"""누락 데이터 확인"""
import psycopg2

import os
conn = psycopg2.connect(dbname="goldenrabbit_db", user="goldenrabbit_user",
                         password=os.environ.get("DB_PASSWORD", ""), host="127.0.0.1")
cur = conn.cursor()

# 1. zone_code 없는 건
cur.execute("SELECT count(*) FROM redevelopment_zones WHERE zone_code IS NULL OR zone_code = ''")
no_code = cur.fetchone()[0]

# 2. 좌표 없는 건
cur.execute("SELECT count(*) FROM redevelopment_zones WHERE center_lat IS NULL OR center_lon IS NULL")
no_coord = cur.fetchone()[0]

# 3. geometry 없는 건
cur.execute("SELECT count(*) FROM redevelopment_zones WHERE geometry IS NULL")
no_geo = cur.fetchone()[0]

print(f"zone_code 없음: {no_code}건")
print(f"좌표 없음: {no_coord}건")
print(f"geometry 없음: {no_geo}건")

# geometry 없는 구역 목록
print(f"\n=== geometry 없는 구역 ({no_geo}건) ===")
cur.execute("""SELECT id, zone_name, district, dong, stage, source,
               center_lat IS NOT NULL as has_coord
               FROM redevelopment_zones WHERE geometry IS NULL ORDER BY district, zone_name""")
for r in cur.fetchall():
    dong = r[3] or ""
    print(f"  id={r[0]} | {r[1]} | {r[2]} {dong} | stage={r[4]} | src={r[5]} | coord={r[6]}")

# 좌표 없는 구역
print(f"\n=== 좌표 없는 구역 ===")
cur.execute("""SELECT id, zone_name, district, source
               FROM redevelopment_zones WHERE center_lat IS NULL ORDER BY district""")
for r in cur.fetchall():
    print(f"  id={r[0]} | {r[1]} | {r[2]} | {r[3]}")

# zone_code 없는 구역
print(f"\n=== zone_code 없는 구역 (샘플 20건) ===")
cur.execute("""SELECT id, zone_name, district, source
               FROM redevelopment_zones WHERE zone_code IS NULL OR zone_code = ''
               ORDER BY district LIMIT 20""")
for r in cur.fetchall():
    print(f"  id={r[0]} | {r[1]} | {r[2]} | {r[3]}")

cur.close(); conn.close()
