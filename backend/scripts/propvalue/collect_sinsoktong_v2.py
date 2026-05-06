#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""신속통합기획 전체 구역 수집 v2
- 1차/2차 공모 선정구역
- 수시 선정구역
- 재건축 포함
- 정보몽땅 + 서울시 도시재생 페이지에서 수집
"""
import json, os, re, time, urllib.parse, urllib.request
import psycopg2
from bs4 import BeautifulSoup

VWORLD = os.environ.get("VWORLD_APIKEY", "")
DB_CFG = dict(host="127.0.0.1", port=5432, dbname="goldenrabbit_db",
              user="goldenrabbit_user", password=os.environ.get("DB_PASSWORD", ""))


def geocode(addr):
    if not VWORLD or not addr:
        return None, None
    try:
        p = urllib.parse.urlencode({
            "service": "address", "request": "getcoord", "version": "2.0",
            "crs": "epsg:4326", "address": addr, "refine": "true",
            "simple": "false", "format": "json", "type": "parcel", "key": VWORLD,
        })
        req = urllib.request.Request(f"https://api.vworld.kr/req/address?{p}")
        req.add_header("User-Agent", "PropValue/2.0")
        resp = urllib.request.urlopen(req, timeout=10)
        d = json.loads(resp.read().decode("utf-8"))
        if d.get("response", {}).get("status") == "OK":
            pt = d["response"]["result"]["point"]
            return float(pt["y"]), float(pt["x"])
    except Exception:
        pass
    return None, None


def scrape_table(url):
    """정보몽땅 테이블 파싱 — 컬럼 구조 자동 감지"""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    zones = []

    for t in soup.find_all("table"):
        # 헤더 확인
        headers = []
        thead = t.find("thead")
        if thead:
            for th in thead.find_all("th"):
                headers.append(th.get_text(strip=True))

        for tr in t.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue

            cells = [td.get_text(strip=True) for td in tds]

            # 첫 번째 셀이 번호인지 확인
            try:
                int(cells[0].replace(",", ""))
            except ValueError:
                continue

            # 컬럼 매핑 (다양한 테이블 구조 대응)
            zone = {}
            if len(cells) >= 7:
                # 번호, 자치구, 구역명, 위치, 면적, 세대수, 단계, ...
                zone = {
                    "dist": cells[1],
                    "name": cells[2],
                    "location": cells[3] if len(cells) > 3 else "",
                    "area": cells[4].replace(",", "") if len(cells) > 4 else "",
                    "hh": cells[5].replace(",", "") if len(cells) > 5 else "",
                    "stage": cells[6] if len(cells) > 6 else "",
                }
            elif len(cells) >= 5:
                # 번호, 자치구, 구역명, 면적, 세대수
                zone = {
                    "dist": cells[1],
                    "name": cells[2],
                    "location": "",
                    "area": cells[3].replace(",", "") if len(cells) > 3 else "",
                    "hh": cells[4].replace(",", "") if len(cells) > 4 else "",
                    "stage": cells[5] if len(cells) > 5 else "",
                }
            elif len(cells) >= 4:
                zone = {
                    "dist": cells[1],
                    "name": cells[2],
                    "location": "",
                    "area": cells[3].replace(",", "") if len(cells) > 3 else "",
                    "hh": "",
                    "stage": "",
                }

            # 유효성 검증: dist가 "XX구" 형태이고, name이 비어있지 않아야
            if zone.get("dist") and zone.get("name"):
                if re.match(r"^[가-힣]+구$", zone["dist"]) and zone["name"] != zone["dist"]:
                    zones.append(zone)

    return zones


def main():
    # 수집 URL 목록
    pages = [
        # 재개발 1차/2차
        ("재개발1차", "https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn.do", "재개발"),
        ("재개발2차", "https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn2.do", "재개발"),
        # 수시 선정 (페이지가 있는 경우)
        ("재개발수시", "https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn3.do", "재개발"),
        # 재건축
        ("재건축1차", "https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn4.do", "재건축"),
        ("재건축2차", "https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn5.do", "재건축"),
        ("재건축수시", "https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn6.do", "재건축"),
    ]

    all_zones = []
    for bn, url, ptype in pages:
        try:
            zones = scrape_table(url)
            for z in zones:
                z["bn"] = bn
                z["project_type"] = ptype
            all_zones.extend(zones)
            print(f"  {bn}: {len(zones)}건")
        except Exception as e:
            print(f"  {bn}: error - {e}")
        time.sleep(0.5)

    # 선정구역 페이지 (overview)
    try:
        zones = scrape_table("https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanArea.do")
        for z in zones:
            z["bn"] = "선정구역"
            z["project_type"] = "재개발"
        all_zones.extend(zones)
        print(f"  선정구역: {len(zones)}건")
    except Exception as e:
        print(f"  선정구역: error - {e}")

    print(f"\n수집 총: {len(all_zones)}건")

    # 중복 제거
    seen = set()
    unique = []
    for z in all_zones:
        k = f"{z['dist']}_{z['name']}"
        if k not in seen:
            seen.add(k)
            unique.append(z)
    print(f"중복제거: {len(unique)}건")

    # DB 연결
    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor()

    # 기존 DB 이름 목록 (중복 INSERT 방지)
    cur.execute("SELECT zone_name, district FROM redevelopment_zones")
    existing = set()
    for r in cur.fetchall():
        existing.add(f"{r[1]}_{r[0]}")
        # 핵심 부분도 추가
        core = re.sub(r"[^가-힣0-9\-]", "", r[0])
        if core:
            existing.add(f"{r[1]}_{core}")

    inserted = 0
    geocoded = 0
    skipped = 0

    for z in unique:
        name = z["name"].strip()
        dist = z["dist"].strip()

        # 이미 DB에 있는지 확인
        key1 = f"{dist}_{name}"
        core = re.sub(r"[^가-힣0-9\-]", "", name)
        key2 = f"{dist}_{core}"
        if key1 in existing or key2 in existing:
            skipped += 1
            continue

        # dong 추출
        dong_match = re.search(r"([가-힣]+동)", name)
        if dong_match:
            dong = dong_match.group(1)
        else:
            nm = re.match(r"([가-힣]+)", name)
            dong = nm.group(1) + "동" if nm else None

        # geocoding
        lat, lon = None, None
        if dong:
            lat, lon = geocode(f"서울특별시 {dist} {dong}")
        if not lat:
            addr_part = re.sub(r"\(.*\)", "", name).strip()
            lat, lon = geocode(f"서울특별시 {dist} {addr_part}")
        if lat:
            geocoded += 1

        area = None
        try:
            area = float(z.get("area", ""))
        except (ValueError, TypeError):
            pass
        hh = None
        try:
            hh = int(z.get("hh", ""))
        except (ValueError, TypeError):
            pass

        stage = z.get("stage", "").strip()
        if not stage:
            stage = f"신속통합기획"

        ptype = z.get("project_type", "재개발")
        zc = f"sinsoktong-{dist}-{name[:40]}"

        try:
            cur.execute(
                """INSERT INTO redevelopment_zones
                   (zone_name, zone_code, city, district, dong, project_type, stage,
                    area_sqm, households, center_lat, center_lon, source, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                   ON CONFLICT (zone_code) DO UPDATE SET
                     stage = EXCLUDED.stage,
                     area_sqm = COALESCE(EXCLUDED.area_sqm, redevelopment_zones.area_sqm),
                     households = COALESCE(EXCLUDED.households, redevelopment_zones.households),
                     updated_at = NOW()""",
                (name[:100], zc[:100], "서울특별시", dist, dong,
                 ptype, stage, area, hh, lat, lon, "cleanup_sinsoktong"))
            if cur.rowcount > 0:
                inserted += 1
            existing.add(key1)
            if core:
                existing.add(key2)
        except Exception as e:
            conn.rollback()
            print(f"  INSERT error: {name} - {e}")

        if lat:
            time.sleep(0.05)

    conn.commit()
    print(f"\ninserted: {inserted}, skipped(already exists): {skipped}, geocoded: {geocoded}")

    cur.execute("SELECT count(*) FROM redevelopment_zones")
    print(f"DB 총: {cur.fetchone()[0]}건")
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE source = 'cleanup_sinsoktong'")
    print(f"신속통합기획: {cur.fetchone()[0]}건")
    conn.close()


if __name__ == "__main__":
    main()
