#!/usr/bin/env python3
"""누락 데이터 보강: zone_code, 좌표, geometry"""
import psycopg2
import json
import re
import os
import time
import urllib.request
import urllib.parse

VWORLD = os.environ.get("VWORLD_APIKEY", "")
ARCGIS_BASE = "https://urban.seoul.go.kr/proxy/proxy.jsp?http://98.33.2.225:6080/arcgis/rest/services/UPIS/20200526_WMS/MapServer"

DB_CFG = dict(dbname="goldenrabbit_db", user="goldenrabbit_user",
              password=os.environ.get("DB_PASSWORD", ""), host="127.0.0.1")


def geocode(addr):
    if not VWORLD:
        return None, None
    try:
        p = urllib.parse.urlencode({
            "service": "address", "request": "getcoord", "version": "2.0",
            "crs": "epsg:4326", "address": addr, "refine": "true",
            "simple": "false", "format": "json", "type": "parcel", "key": VWORLD,
        })
        req = urllib.request.Request(f"https://api.vworld.kr/req/address?{p}",
                                     headers={"User-Agent": "PropValue/2.0"})
        d = json.loads(urllib.request.urlopen(req, timeout=10).read())
        if d.get("response", {}).get("status") == "OK":
            pt = d["response"]["result"]["point"]
            return float(pt["y"]), float(pt["x"])
    except Exception:
        pass
    return None, None


def search_arcgis(query):
    """ArcGIS 전 레이어에서 구역명 검색 → geometry 반환"""
    for lid in range(94, 123):
        try:
            encoded = urllib.parse.quote(f"DGM_NM LIKE '%{query}%'")
            url = (f"{ARCGIS_BASE}/{lid}/query?where={encoded}"
                   f"&outFields=DGM_NM,DGM_AR&returnGeometry=true&outSR=4326&f=json")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            for f in data.get("features", []):
                rings = f.get("geometry", {}).get("rings", [])
                if rings:
                    return {
                        "type": "Polygon",
                        "coordinates": rings,
                    }
        except Exception:
            pass
    return None


def main():
    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor()

    # ====== 1. zone_code 없는 건 → 자체 코드 부여 ======
    print("=== 1. zone_code 보강 ===")
    cur.execute("""SELECT id, zone_name, district
                   FROM redevelopment_zones
                   WHERE zone_code IS NULL OR zone_code = ''""")
    no_code = cur.fetchall()
    fixed_code = 0
    for zid, zname, dist in no_code:
        # sinsoktong-{district}-{name} 형태
        code = f"sinsoktong-{dist or 'unknown'}-{zname[:40]}"
        cur.execute("UPDATE redevelopment_zones SET zone_code = %s WHERE id = %s", (code, zid))
        fixed_code += 1
    conn.commit()
    print(f"  zone_code 부여: {fixed_code}건")

    # ====== 2. 좌표 없는 건 → 다양한 geocoding 시도 ======
    print("\n=== 2. 좌표 보강 ===")
    cur.execute("""SELECT id, zone_name, district, dong
                   FROM redevelopment_zones
                   WHERE center_lat IS NULL""")
    no_coord = cur.fetchall()
    fixed_coord = 0
    for zid, zname, dist, dong in no_coord:
        lat, lon = None, None

        # 시도 1: 동 이름으로
        if dong:
            lat, lon = geocode(f"서울특별시 {dist} {dong}")

        # 시도 2: 구역명에서 동 추출
        if not lat:
            m = re.search(r"([가-힣]+동)", zname)
            if m:
                lat, lon = geocode(f"서울특별시 {dist} {m.group(1)}")

        # 시도 3: 아파트명 → 구 이름 + 아파트명
        if not lat:
            lat, lon = geocode(f"서울특별시 {dist} {zname}")

        # 시도 4: 구 중심 좌표라도
        if not lat and dist:
            lat, lon = geocode(f"서울특별시 {dist}")

        if lat:
            cur.execute("UPDATE redevelopment_zones SET center_lat = %s, center_lon = %s WHERE id = %s",
                        (lat, lon, zid))
            fixed_coord += 1
            print(f"  좌표 확보: {zname} ({dist}) → ({lat:.4f}, {lon:.4f})")
        else:
            print(f"  좌표 실패: {zname} ({dist})")
        time.sleep(0.1)

    conn.commit()
    print(f"  좌표 보강: {fixed_coord}/{len(no_coord)}건")

    # ====== 3. geometry 없는 건 → ArcGIS 검색 시도 ======
    print("\n=== 3. geometry 보강 (ArcGIS 검색) ===")
    cur.execute("""SELECT id, zone_name, district, dong
                   FROM redevelopment_zones
                   WHERE geometry IS NULL""")
    no_geo = cur.fetchall()
    fixed_geo = 0

    for zid, zname, dist, dong in no_geo:
        # 검색어 후보 생성
        queries = []

        # 동+번지 추출
        m = re.search(r"([가-힣]+동)\s*(\d+)", zname)
        if m:
            queries.append(f"{m.group(1)} {m.group(2)}")

        # 구역명 그대로
        short = re.sub(r"\(.*\)", "", zname).strip()
        if short:
            queries.append(short)

        # 숫자 포함 이름 (신림5 → 신림5)
        queries.append(zname)

        geom = None
        for q in queries:
            geom = search_arcgis(q)
            if geom:
                break
            time.sleep(0.2)

        if geom:
            geom_json = json.dumps(geom)
            rings = geom["coordinates"]
            r0 = rings[0]
            clat = sum(c[1] for c in r0) / len(r0)
            clon = sum(c[0] for c in r0) / len(r0)
            cur.execute("""UPDATE redevelopment_zones
                          SET geometry = %s, center_lat = %s, center_lon = %s
                          WHERE id = %s""",
                        (geom_json, clat, clon, zid))
            fixed_geo += 1
            print(f"  geometry 확보: {zname}")
        time.sleep(0.1)

    conn.commit()
    print(f"  geometry 보강: {fixed_geo}/{len(no_geo)}건")

    # ====== 최종 현황 ======
    cur.execute("SELECT count(*) FROM redevelopment_zones")
    total = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE geometry IS NOT NULL")
    geo = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE center_lat IS NOT NULL")
    coord = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE zone_code IS NOT NULL AND zone_code != ''")
    code = cur.fetchone()[0]

    print(f"\n=== 최종 ===")
    print(f"총: {total}건")
    print(f"zone_code: {code}건 ({code*100//total}%)")
    print(f"좌표: {coord}건 ({coord*100//total}%)")
    print(f"geometry: {geo}건 ({geo*100//total}%)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
