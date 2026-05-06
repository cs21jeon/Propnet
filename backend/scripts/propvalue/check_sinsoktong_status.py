#!/usr/bin/env python3
"""신속통합기획 현황 점검"""
import psycopg2, os

conn = psycopg2.connect(
    host="127.0.0.1", port=5432, dbname="goldenrabbit_db",
    user="goldenrabbit_user", password=os.environ.get("DB_PASSWORD", ""))
cur = conn.cursor()

# 1. source별 건수
cur.execute("SELECT source, count(*) FROM redevelopment_zones GROUP BY source ORDER BY count(*) DESC")
print("=== source별 건수 ===")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# 2. geometry NULL
cur.execute("SELECT count(*) FROM redevelopment_zones WHERE geometry IS NULL")
print(f"\ngeometry NULL 총: {cur.fetchone()[0]}")
cur.execute("SELECT source, count(*) FROM redevelopment_zones WHERE geometry IS NULL GROUP BY source")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# 3. stage empty
cur.execute("SELECT count(*) FROM redevelopment_zones WHERE stage = '' OR stage IS NULL")
print(f"\nstage 비어있음: {cur.fetchone()[0]}")

# 4. sinsoktong 115건 상세
cur.execute("""SELECT zone_name, district, stage, project_type,
               center_lat IS NOT NULL as has_coord
               FROM redevelopment_zones
               WHERE source = 'cleanup_sinsoktong'
               ORDER BY district, zone_name""")
rows = cur.fetchall()
print(f"\n=== cleanup_sinsoktong {len(rows)}건 ===")
by_type = {}
for r in rows:
    pt = r[3]
    by_type[pt] = by_type.get(pt, 0) + 1
for pt, cnt in sorted(by_type.items()):
    print(f"  {pt}: {cnt}")

# 5. 정보몽땅 245건 vs DB 대응 확인
# ArcGIS에서 재개발(BZ101=94) 몇 건인지
cur.execute("""SELECT project_type, count(*)
               FROM redevelopment_zones
               WHERE source = 'urban.seoul.go.kr' AND project_type IN ('재개발', '재건축')
               GROUP BY project_type""")
print("\n=== ArcGIS 재개발/재건축 ===")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

cur.close()
conn.close()
