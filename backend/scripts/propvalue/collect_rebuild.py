#!/usr/bin/env python3
"""재건축 신속통합기획 수집"""
import urllib.request, json, re, time, psycopg2, urllib.parse
from bs4 import BeautifulSoup
import os

VWORLD = os.environ.get("VWORLD_APIKEY", "")
DB_CFG = dict(dbname="goldenrabbit_db", user="goldenrabbit_user",
              password=os.environ.get("DB_PASSWORD", ""), host="127.0.0.1")

def geocode(addr):
    if not VWORLD: return None, None
    try:
        p = urllib.parse.urlencode({"service":"address","request":"getcoord","version":"2.0",
            "crs":"epsg:4326","address":addr,"refine":"true","simple":"false",
            "format":"json","type":"parcel","key":VWORLD})
        req = urllib.request.Request(f"https://api.vworld.kr/req/address?{p}",
                                     headers={"User-Agent":"PropValue/2.0"})
        d = json.loads(urllib.request.urlopen(req, timeout=10).read())
        if d.get("response",{}).get("status")=="OK":
            pt = d["response"]["result"]["point"]
            return float(pt["y"]), float(pt["x"])
    except: pass
    return None, None

def scrape_8col(url):
    """8컬럼 테이블: 연번, 구분, 자치구, 구역명, 면적, 세대수, 추진단계, 고시일"""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    zones = []
    for t in soup.find_all("table"):
        for tr in t.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 6: continue
            cells = [td.get_text(strip=True) for td in tds]
            try: int(cells[0])
            except: continue
            # cells[2]가 "XX구"인지 확인
            if not re.match(r"^[가-힣]+구$", cells[2]):
                continue
            zones.append({
                "dist": cells[2], "name": cells[3],
                "area": cells[4].replace(",",""),
                "hh": cells[5].replace(",",""),
                "stage": cells[6] if len(cells) > 6 else "",
            })
    return zones

def main():
    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor()

    # 기존 목록
    cur.execute("SELECT zone_name, district FROM redevelopment_zones")
    existing = set()
    for r in cur.fetchall():
        existing.add(r[1] + "_" + r[0])
        core = re.sub(r"[^가-힣0-9]", "", r[0])
        if core: existing.add(r[1] + "_" + core)

    # 재건축 추진현황
    print("=== 재건축 추진현황 ===")
    zones = scrape_8col("https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn2.do")
    print(f"수집: {len(zones)}건")

    inserted = 0
    for z in zones:
        name = z["name"].strip()
        dist = z["dist"].strip()
        if not name or not dist: continue
        key = dist + "_" + name
        if key in existing: continue

        dong_m = re.search(r"([가-힣]+동)", name)
        dong = dong_m.group(1) if dong_m else None
        if not dong:
            nm = re.match(r"([가-힣]+)", name)
            dong = (nm.group(1) + "동") if nm else None

        lat, lon = None, None
        if dong: lat, lon = geocode(f"서울특별시 {dist} {dong}")
        if not lat: lat, lon = geocode(f"서울특별시 {dist} {name}")

        area = None
        try: area = float(z["area"])
        except: pass
        hh = None
        try: hh = int(z["hh"])
        except: pass

        stage = z["stage"] or "신속통합기획"
        zc = f"sinsoktong-rb-{dist}-{name[:30]}"

        try:
            cur.execute(
                """INSERT INTO redevelopment_zones
                   (zone_name, zone_code, city, district, dong, project_type, stage,
                    area_sqm, households, center_lat, center_lon, source)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (zone_code) DO NOTHING""",
                (name[:100], zc[:100], "서울특별시", dist, dong,
                 "재건축", stage, area, hh, lat, lon, "cleanup_sinsoktong"))
            if cur.rowcount > 0:
                inserted += 1
                existing.add(key)
        except:
            conn.rollback()
        time.sleep(0.05)

    conn.commit()
    print(f"재건축 INSERT: {inserted}건")

    # 재개발 추진현황 (재수집 — 8컬럼 정확 파싱)
    print("\n=== 재개발 추진현황 재수집 ===")
    zones2 = scrape_8col("https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn.do")
    print(f"수집: {len(zones2)}건")

    inserted2 = 0
    updated2 = 0
    for z in zones2:
        name = z["name"].strip()
        dist = z["dist"].strip()
        if not name or not dist: continue

        stage = z["stage"] or "신속통합기획"
        hh = None
        try: hh = int(z["hh"])
        except: pass
        area = None
        try: area = float(z["area"])
        except: pass

        # 이미 있으면 stage 업데이트
        key = dist + "_" + name
        if key in existing:
            cur.execute(
                """UPDATE redevelopment_zones SET stage = %s,
                   households = COALESCE(%s, households),
                   area_sqm = COALESCE(%s, area_sqm)
                   WHERE zone_name = %s AND district = %s AND stage = ''""",
                (stage, hh, area, name, dist))
            if cur.rowcount > 0:
                updated2 += 1
            continue

        dong_m = re.search(r"([가-힣]+동)", name)
        dong = dong_m.group(1) if dong_m else None
        if not dong:
            nm = re.match(r"([가-힣]+)", name)
            dong = (nm.group(1) + "동") if nm else None

        lat, lon = None, None
        if dong: lat, lon = geocode(f"서울특별시 {dist} {dong}")
        if not lat: lat, lon = geocode(f"서울특별시 {dist} {name}")

        zc = f"sinsoktong-rd-{dist}-{name[:30]}"
        try:
            cur.execute(
                """INSERT INTO redevelopment_zones
                   (zone_name, zone_code, city, district, dong, project_type, stage,
                    area_sqm, households, center_lat, center_lon, source)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (zone_code) DO NOTHING""",
                (name[:100], zc[:100], "서울특별시", dist, dong,
                 "재개발", stage, area, hh, lat, lon, "cleanup_sinsoktong"))
            if cur.rowcount > 0:
                inserted2 += 1
                existing.add(key)
        except:
            conn.rollback()
        time.sleep(0.05)

    conn.commit()
    print(f"재개발 INSERT: {inserted2}건, stage 업데이트: {updated2}건")

    # 최종
    cur.execute("SELECT count(*) FROM redevelopment_zones")
    total = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE source = 'cleanup_sinsoktong'")
    st = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE stage != '' AND stage IS NOT NULL")
    staged = cur.fetchone()[0]
    print(f"\nDB 총: {total}건, 신속통합기획: {st}건, stage 있음: {staged}건")

    cur.close(); conn.close()

if __name__ == "__main__":
    main()
