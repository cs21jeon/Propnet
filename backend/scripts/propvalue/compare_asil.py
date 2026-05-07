#!/usr/bin/env python3
"""아실 vs DB 비교 — 구별 교차 검증"""
import json, os, re, sys
import psycopg2, psycopg2.extras

DB_CFG = dict(host="127.0.0.1", port=5432, dbname="goldenrabbit_db",
              user="goldenrabbit_user", password=os.environ.get("DB_PASSWORD", ""))

# 아실 데이터
asil = json.load(open("/tmp/asil_seoul_final.json"))
asil_seoul = [z for z in asil if 37.44 < z["lat"] < 37.69 and 126.76 < z["lng"] < 127.18]
print(f"아실 서울: {len(asil_seoul)}건")

# DB 데이터
conn = psycopg2.connect(**DB_CFG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("SELECT id, zone_name, district, project_type, stage, center_lat, center_lon, is_hidden, is_sinsoktong FROM redevelopment_zones")
db_all = cur.fetchall()
db_visible = [z for z in db_all if not z["is_hidden"]]
print(f"DB visible: {len(db_visible)}건\n")

# 구 경계 (대략적 좌표)
DISTRICT_BOUNDS = {
    "종로구":   (37.567, 126.970, 37.600, 127.020),
    "중구":     (37.555, 126.970, 37.575, 127.010),
    "용산구":   (37.520, 126.955, 37.555, 127.000),
    "성동구":   (37.545, 127.020, 37.570, 127.065),
    "광진구":   (37.535, 127.070, 37.560, 127.110),
    "동대문구": (37.570, 127.020, 37.600, 127.065),
    "중랑구":   (37.580, 127.065, 37.610, 127.110),
    "성북구":   (37.580, 126.995, 37.610, 127.030),
    "강북구":   (37.610, 126.990, 37.640, 127.030),
    "도봉구":   (37.640, 126.990, 37.670, 127.060),
    "노원구":   (37.620, 127.040, 37.660, 127.100),
    "은평구":   (37.590, 126.910, 37.640, 126.960),
    "서대문구": (37.560, 126.920, 37.595, 126.970),
    "마포구":   (37.540, 126.890, 37.570, 126.960),
    "양천구":   (37.510, 126.830, 37.540, 126.890),
    "강서구":   (37.530, 126.810, 37.590, 126.860),
    "구로구":   (37.480, 126.840, 37.510, 126.900),
    "금천구":   (37.445, 126.880, 37.475, 126.920),
    "영등포구": (37.500, 126.890, 37.530, 126.940),
    "동작구":   (37.475, 126.935, 37.510, 126.985),
    "관악구":   (37.455, 126.915, 37.490, 126.960),
    "서초구":   (37.465, 126.980, 37.510, 127.060),
    "강남구":   (37.480, 127.020, 37.530, 127.090),
    "송파구":   (37.490, 127.080, 37.530, 127.140),
    "강동구":   (37.520, 127.110, 37.560, 127.175),
}

def asil_in_district(z, bounds):
    s_lat, s_lng, e_lat, e_lng = bounds
    return s_lat - 0.01 < z["lat"] < e_lat + 0.01 and s_lng - 0.01 < z["lng"] < e_lng + 0.01

def name_similar(a, b):
    """두 이름이 같은 구역인지 판단"""
    a = re.sub(r"<BR>", " ", a).strip()
    if a == b or a in b or b in a:
        return True
    # 숫자 포함 약칭
    am = re.match(r"([가-힣]+\d+)", a)
    bm = re.match(r"([가-힣]+\d+)", b)
    if am and bm and am.group(1) == bm.group(1):
        return True
    # 동+번지
    am = re.match(r"([가-힣]+동)\s*(\d+)", a)
    bm = re.match(r"([가-힣]+동)\s*(\d+)", b)
    if am and bm and am.group(1) == bm.group(1) and am.group(2) == bm.group(2):
        return True
    return False

# 특정 구만 or 전체
target_district = sys.argv[1] if len(sys.argv) > 1 else None

for district in sorted(DISTRICT_BOUNDS.keys()):
    if target_district and district != target_district:
        continue

    bounds = DISTRICT_BOUNDS[district]
    a_zones = [z for z in asil_seoul if asil_in_district(z, bounds)]
    d_zones = [z for z in db_visible if z["district"] == district]

    # 아실에만 있는 것
    asil_only = []
    for az in a_zones:
        matched = False
        for dz in d_zones:
            if name_similar(az["sTitle"], dz["zone_name"]):
                matched = True
                break
        if not matched:
            asil_only.append(az)

    # DB에만 있는 것
    db_only = []
    for dz in d_zones:
        matched = False
        for az in a_zones:
            if name_similar(az["sTitle"], dz["zone_name"]):
                matched = True
                break
        if not matched:
            db_only.append(dz)

    if asil_only or db_only:
        print(f"=== {district} (아실:{len(a_zones)} / DB:{len(d_zones)}) ===")
        for z in sorted(asil_only, key=lambda x: x["sTitle"]):
            print(f"  [아실만] {z['sTitle']} ({z['title'][:35]})")
        for z in sorted(db_only, key=lambda x: x["zone_name"]):
            print(f"  [DB만]  {z['zone_name']} ({z['project_type']}, {z['stage'] or '미확인'})")
        print()

conn.close()
