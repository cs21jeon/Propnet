#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""신속통합기획 구역 수집 → redevelopment_zones"""
import json, os, re, sys, time, urllib.parse, urllib.request
import psycopg2
from bs4 import BeautifulSoup

VWORLD = os.environ.get("VWORLD_APIKEY", "")
DB_CFG = dict(host="127.0.0.1", port=5432, dbname="goldenrabbit_db",
              user="goldenrabbit_user", password=os.environ.get("DB_PASSWORD",""))

def geocode(addr):
    if not VWORLD or not addr: return None, None
    try:
        p = urllib.parse.urlencode({"service":"address","request":"getcoord","version":"2.0",
            "crs":"epsg:4326","address":addr,"refine":"true","simple":"false",
            "format":"json","type":"parcel","key":VWORLD})
        req = urllib.request.Request(f"https://api.vworld.kr/req/address?{p}")
        req.add_header("User-Agent","PropValue/1.0")
        resp = urllib.request.urlopen(req, timeout=10)
        d = json.loads(resp.read().decode("utf-8"))
        if d.get("response",{}).get("status")=="OK":
            pt = d["response"]["result"]["point"]
            return float(pt["y"]), float(pt["x"])
    except: pass
    return None, None

def scrape_table(url):
    """테이블에서 7컬럼 구역 데이터 추출"""
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    zones = []
    for t in soup.find_all("table"):
        for tr in t.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 5:
                tx = [td.get_text(strip=True) for td in tds]
                try: int(tx[0])
                except: continue
                stage = tx[5] if len(tds) >= 6 else ""
                ntfdate = tx[6] if len(tds) >= 7 else ""
                zones.append({
                    "dist": tx[1], "name": tx[2],
                    "area": tx[3].replace(",",""),
                    "hh": tx[4].replace(",",""),
                    "stage": stage, "ntfdate": ntfdate,
                })
    return zones

def main():
    pages = [
        ("1차", "https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn.do"),
        ("2차", "https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn2.do"),
    ]

    all_zones = []
    for bn, url in pages:
        try:
            zones = scrape_table(url)
            for z in zones:
                z["bn"] = bn
            all_zones.extend(zones)
            print(f"{bn}: {len(zones)}건")
        except Exception as e:
            print(f"{bn}: error {e}")
        time.sleep(0.5)

    # 중복 제거
    seen = set()
    unique = []
    for z in all_zones:
        k = z["dist"] + z["name"]
        if k not in seen:
            seen.add(k)
            unique.append(z)
    print(f"총: {len(all_zones)}, 중복제거: {len(unique)}")

    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor()

    ins = 0
    gc = 0
    for z in unique:
        zc = f"sinsoktong-{z['dist']}-{z['name'][:40]}"
        name = z["name"]
        addr_part = re.sub(r"\(.*\)", "", name).strip()

        # geocoding: "면목7" → "면목동", "사당동 416-1" → 그대로
        dong_match = re.match(r"([가-힣]+)", addr_part)
        if dong_match:
            dong = dong_match.group(1)
            if not dong.endswith("동"):
                dong += "동"
        else:
            dong = addr_part

        lat, lon = geocode(f"서울특별시 {z['dist']} {dong}")
        if not lat:
            lat, lon = geocode(f"서울특별시 {z['dist']} {addr_part}")
        if lat:
            gc += 1

        area = None
        try: area = float(z["area"])
        except: pass
        hh = None
        try: hh = int(z["hh"])
        except: pass

        stage = z["stage"] if z["stage"] else f"신속통합기획 {z['bn']}"

        try:
            cur.execute(
                """INSERT INTO redevelopment_zones
                   (zone_name, zone_code, city, district, project_type, stage,
                    area_sqm, households, center_lat, center_lon, source, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                   ON CONFLICT (zone_code) DO NOTHING""",
                (name[:100], zc[:100], "서울특별시", z["dist"],
                 "재개발", stage, area, hh, lat, lon, "cleanup_sinsoktong"))
            if cur.rowcount > 0:
                ins += 1
        except:
            conn.rollback()

        if lat:
            time.sleep(0.05)

    conn.commit()
    print(f"inserted: {ins}, geocoded: {gc}")

    cur.execute("SELECT count(*) FROM redevelopment_zones")
    print(f"DB 총: {cur.fetchone()[0]}건")
    conn.close()

if __name__ == "__main__":
    main()
