#!/usr/bin/env python3
"""신속통합기획 구역에 VWorld SHP 폴리곤 매칭"""
import shapefile, psycopg2, json, os
from pyproj import Transformer

tf = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)

conn = psycopg2.connect(host="127.0.0.1", port=5432, dbname="goldenrabbit_db",
    user="goldenrabbit_user", password=os.environ.get("DB_PASSWORD",""))
cur = conn.cursor()

cur.execute("SELECT id, zone_name, center_lat, center_lon FROM redevelopment_zones WHERE source='cleanup_sinsoktong' AND geometry IS NULL AND center_lat IS NOT NULL")
db_no_geo = cur.fetchall()
print(f"신속통합 geometry 없는 구역: {len(db_no_geo)}건")

# 서울 SHP
shp_data = []
base = "/home/webapp/goldenrabbit/data/propvalue_shp"
for shp_path in [f"{base}/seoul/LSMD_CONT_UD602_11_202604",
                 f"{base}/ud603_seoul/LSMD_CONT_UD603_11_202604",
                 f"{base}/ud630_seoul/LSMD_CONT_UD630_11_202604"]:
    sf = shapefile.Reader(shp_path, encoding="euc-kr", encodingErrors="replace")
    for rec in sf.iterShapeRecords():
        pts = rec.shape.points
        if not pts: continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
        clon, clat = tf.transform(cx, cy)
        parts_idx = list(rec.shape.parts) + [len(pts)]
        rings = []
        for i in range(len(parts_idx)-1):
            ring = [[round(tf.transform(p[0],p[1])[0],7), round(tf.transform(p[0],p[1])[1],7)]
                    for p in pts[parts_idx[i]:parts_idx[i+1]]]
            rings.append(ring)
        shp_data.append((clat, clon, json.dumps({"type":"Polygon","coordinates":rings})))

print(f"SHP 폴리곤: {len(shp_data)}건")

matched = 0
for db_id, db_name, db_lat, db_lon in db_no_geo:
    best_dist = 0.01  # ~1km
    best_geo = None
    for slat, slon, geo in shp_data:
        d = abs(float(db_lat) - slat) + abs(float(db_lon) - slon)
        if d < best_dist:
            best_dist = d
            best_geo = geo
    if best_geo:
        cur.execute("UPDATE redevelopment_zones SET geometry=%s, updated_at=NOW() WHERE id=%s AND geometry IS NULL",
                    (best_geo, db_id))
        if cur.rowcount > 0:
            matched += 1

conn.commit()
print(f"SHP 매칭 폴리곤 추가: {matched}건")

cur.execute("SELECT count(*), count(geometry) FROM redevelopment_zones")
t, g = cur.fetchone()
print(f"DB 총: {t}건, geometry: {g}건")
conn.close()
