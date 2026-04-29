#!/usr/bin/env python3
import psycopg2, os

def load_env(p="/home/webapp/goldenrabbit/backend/.env"):
    if os.path.isfile(p):
        for line in open(p):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

load_env()
conn = psycopg2.connect(
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    port=int(os.environ.get("DB_PORT", "5432")),
    dbname=os.environ.get("DB_NAME", "goldenrabbit_db"),
    user=os.environ.get("DB_USER", "goldenrabbit_user"),
    password=os.environ.get("DB_PASSWORD", ""),
)
cur = conn.cursor()

cur.execute("SELECT COUNT(*), COUNT(DISTINCT pnu) FROM building_dong_geometry")
total, pnus = cur.fetchone()
print(f"building_dong_geometry: {total}건, {pnus} PNU")

cur.execute("""
    SELECT COUNT(DISTINCT cp.pnu)
    FROM complex_parcels cp
    JOIN complex_master cm ON cm.complex_pk = cp.complex_pk
    WHERE cm.household_count >= 50
""")
target_pnu = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(DISTINCT cp.pnu)
    FROM complex_parcels cp
    JOIN complex_master cm ON cm.complex_pk = cp.complex_pk
    WHERE cm.household_count >= 50
      AND cp.pnu NOT IN (SELECT DISTINCT pnu FROM building_dong_geometry)
""")
remaining = cur.fetchone()[0]
covered = target_pnu - remaining
print(f"50+ PNU: total {target_pnu}, covered {covered} ({covered/target_pnu*100:.1f}%), remaining {remaining}")

conn.close()
