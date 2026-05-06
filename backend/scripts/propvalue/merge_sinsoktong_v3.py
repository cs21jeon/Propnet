#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""신속통합기획 데이터 병합 및 보강 v3

현황:
  - 정보몽땅 기준 245건 (재개발 150 + 재건축 95)
  - DB에 이미 전부 존재: ArcGIS 2,904건(geometry 있음) + sinsoktong 115건(geometry 없음)
  - sinsoktong 115건 중 73건은 ArcGIS에 대응 있음 (중복)
  - sinsoktong 115건 중 42건은 진짜 고유 (ArcGIS에 없음)

작업:
  1. sinsoktong <-> ArcGIS 중복 73건: ArcGIS 쪽에 stage/households 병합, sinsoktong 삭제
  2. 고유 42건: ArcGIS에서 geometry 검색 시도, geocoding 보강
  3. 정보몽땅에서 크롤링한 245건의 stage를 ArcGIS 대응 레코드에 업데이트
  4. 재건축 76건(자문 구역) 중 DB에서 stage가 비어있는 것 업데이트

실행:
  source /home/webapp/goldenrabbit/backend/venv/bin/activate
  export $(grep -v '^#' /home/webapp/goldenrabbit/backend/.env | xargs)
  cd /home/webapp/goldenrabbit/backend/scripts/propvalue
  python3 merge_sinsoktong_v3.py
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

import psycopg2
from bs4 import BeautifulSoup

VWORLD = os.environ.get("VWORLD_APIKEY", "")
DB_CFG = dict(
    host="127.0.0.1", port=5432, dbname="goldenrabbit_db",
    user="goldenrabbit_user", password=os.environ.get("DB_PASSWORD", ""))

ARCGIS_BASE = (
    "https://urban.seoul.go.kr/proxy/proxy.jsp?"
    "http://98.33.2.225:6080/arcgis/rest/services/UPIS/20200526_WMS/MapServer"
)

SIGNGU = {
    "11110": "종로구", "11140": "중구", "11170": "용산구", "11200": "성동구",
    "11215": "광진구", "11230": "동대문구", "11260": "중랑구", "11290": "성북구",
    "11305": "강북구", "11320": "도봉구", "11350": "노원구", "11380": "은평구",
    "11410": "서대문구", "11440": "마포구", "11470": "양천구", "11500": "강서구",
    "11530": "구로구", "11545": "금천구", "11560": "영등포구", "11590": "동작구",
    "11620": "관악구", "11650": "서초구", "11680": "강남구", "11710": "송파구",
    "11740": "강동구",
}


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
        req.add_header("User-Agent", "PropValue/3.0")
        resp = urllib.request.urlopen(req, timeout=10)
        d = json.loads(resp.read().decode("utf-8"))
        if d.get("response", {}).get("status") == "OK":
            pt = d["response"]["result"]["point"]
            return float(pt["y"]), float(pt["x"])
    except Exception:
        pass
    return None, None


def normalize(name):
    return re.sub(r"[^가-힣0-9]", "", name)


def scrape_page(url):
    """정보몽땅 테이블 파싱 - 자동 컬럼 감지"""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    zones = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 6:
                continue
            cells = [td.get_text(strip=True) for td in tds]
            try:
                int(cells[0].replace(",", ""))
            except ValueError:
                continue

            # 자치구 위치 찾기
            dist_idx = None
            for i in range(1, min(4, len(cells))):
                if re.match(r"^[가-힣]+구$", cells[i]):
                    dist_idx = i
                    break
            if dist_idx is None:
                continue

            name_idx = dist_idx + 1
            area_idx = dist_idx + 2
            hh_idx = dist_idx + 3
            stage_idx = dist_idx + 4

            if name_idx >= len(cells):
                continue

            name = cells[name_idx].strip()
            if not name or name == cells[dist_idx]:
                continue

            zone = {
                "dist": cells[dist_idx],
                "name": name,
                "area": cells[area_idx].replace(",", "").replace("㎡", "").strip() if area_idx < len(cells) else "",
                "hh": cells[hh_idx].replace(",", "").replace("-", "").replace("\u2014", "").strip() if hh_idx < len(cells) else "",
                "stage": cells[stage_idx].strip() if stage_idx < len(cells) else "",
            }
            zones.append(zone)
    return zones


def search_arcgis_by_name(name, district):
    """ArcGIS에서 이름으로 검색하여 geometry 가져오기"""
    # BZ101(재개발:94), BZ102(재건축:95), BZ105(소규모재건축:98)
    layers = [94, 95, 98, 107, 108]

    # 검색어: 동 이름 추출
    search_terms = []
    # 원본
    search_terms.append(name)
    # 괄호 제거
    clean = re.sub(r"\([^)]*\)", "", name).strip()
    if clean != name:
        search_terms.append(clean)
    # 동+번지 패턴
    m = re.search(r"([가-힣]+동)\s*(\d+)", name)
    if m:
        search_terms.append(f"{m.group(1)} {m.group(2)}")
        search_terms.append(m.group(1))
    # 한글 기본
    m = re.match(r"([가-힣]+)", name)
    if m:
        search_terms.append(m.group(1))

    for lid in layers:
        for term in search_terms:
            try:
                encoded = urllib.parse.quote(term)
                url = (f"{ARCGIS_BASE}/{lid}/query?"
                       f"where=DGM_NM+LIKE+%27%25{encoded}%25%27"
                       f"&outFields=OBJECTID,PRESENT_SN,DGM_NM,SIGNGU_SE,DGM_AR"
                       f"&returnGeometry=true&outSR=4326&f=json")
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())

                for f in data.get("features", []):
                    attrs = f.get("attributes", {})
                    rings = f.get("geometry", {}).get("rings", [])
                    fname = (attrs.get("DGM_NM") or "").strip()
                    sig = attrs.get("SIGNGU_SE", "")
                    fdist = SIGNGU.get(sig, "")

                    if fdist == district and rings:
                        geom = json.dumps({"type": "Polygon", "coordinates": rings})
                        r0 = rings[0]
                        clat = sum(c[1] for c in r0) / len(r0)
                        clon = sum(c[0] for c in r0) / len(r0)
                        return {
                            "geometry": geom,
                            "center_lat": clat,
                            "center_lon": clon,
                            "present_sn": attrs.get("PRESENT_SN", ""),
                            "arcgis_name": fname,
                        }
            except Exception:
                pass
            time.sleep(0.2)

    return None


def main():
    print("=" * 60)
    print("신속통합기획 데이터 병합 및 보강 v3")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor()

    # ======================================
    # STEP 1: 정보몽땅 크롤링
    # ======================================
    print("\n=== STEP 1: 정보몽땅 크롤링 ===")
    rd_zones = scrape_page("https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn.do")
    print(f"  재개발: {len(rd_zones)}건")
    for z in rd_zones:
        z["project_type"] = "재개발"

    rb_zones = scrape_page("https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn2.do")
    print(f"  재건축: {len(rb_zones)}건")
    for z in rb_zones:
        z["project_type"] = "재건축"

    all_cleanup = rd_zones + rb_zones
    # 중복 제거
    seen = set()
    cleanup_unique = []
    for z in all_cleanup:
        k = f"{z['dist']}_{z['name']}"
        if k not in seen:
            seen.add(k)
            cleanup_unique.append(z)
    print(f"  합계 (중복 제거): {len(cleanup_unique)}건")

    # ======================================
    # STEP 2: DB 인덱스 구축
    # ======================================
    print("\n=== STEP 2: DB 인덱스 구축 ===")
    cur.execute("""SELECT id, zone_name, zone_code, district, project_type,
                          stage, households, source, geometry IS NOT NULL as has_geo
                   FROM redevelopment_zones""")
    db_rows = cur.fetchall()
    print(f"  DB 총: {len(db_rows)}건")

    # 인덱스: (district, normalized_name) -> list of rows
    db_idx = {}
    db_by_id = {}
    for row in db_rows:
        rid, rname, rcode, rdist, rptype, rstage, rhh, rsrc, has_geo = row
        db_by_id[rid] = row
        norm = normalize(rname)
        key = (rdist, norm)
        if key not in db_idx:
            db_idx[key] = []
        db_idx[key].append(row)
        # 원본도
        key2 = (rdist, rname)
        if key2 not in db_idx:
            db_idx[key2] = []
        db_idx[key2].append(row)

    # sinsoktong 레코드
    sinsoktong_rows = [r for r in db_rows if r[7] == "cleanup_sinsoktong"]
    print(f"  sinsoktong: {len(sinsoktong_rows)}건")

    # ======================================
    # STEP 3: sinsoktong <-> ArcGIS 중복 병합
    # ======================================
    print("\n=== STEP 3: sinsoktong <-> ArcGIS 중복 병합 ===")
    merged = 0
    kept = 0
    merge_details = []

    for srow in sinsoktong_rows:
        sid, sname, scode, sdist, sptype, sstage, shh, ssrc, shas_geo = srow
        snorm = normalize(sname)

        # ArcGIS 대응 찾기
        arcgis_match = None
        candidates = db_idx.get((sdist, snorm), [])
        # 추가 검색: 이름+구역 패턴
        if not any(c[7] == "urban.seoul.go.kr" for c in candidates):
            candidates2 = db_idx.get((sdist, snorm + "구역"), [])
            candidates = candidates + candidates2

        # 부분 매칭
        if not any(c[7] == "urban.seoul.go.kr" for c in candidates):
            m = re.match(r"([가-힣]+?)(\d+)", snorm)
            if m:
                base, num = m.group(1), m.group(2)
                for (d, n), rows in db_idx.items():
                    if d != sdist:
                        continue
                    if base in n and num in n and any(r[7] == "urban.seoul.go.kr" for r in rows):
                        candidates = candidates + rows
                        break

        for c in candidates:
            if c[7] == "urban.seoul.go.kr" and c[8]:  # has geometry
                arcgis_match = c
                break

        if arcgis_match:
            aid = arcgis_match[0]
            astage = arcgis_match[5]
            ahh = arcgis_match[6]

            # ArcGIS 레코드에 stage/households 병합
            updates = []
            vals = []
            if sstage and (not astage or astage == ""):
                updates.append("stage = %s")
                vals.append(sstage)
            if shh and not ahh:
                updates.append("households = %s")
                vals.append(shh)

            if updates:
                vals.append(aid)
                cur.execute(f"UPDATE redevelopment_zones SET {', '.join(updates)}, updated_at = NOW() WHERE id = %s", vals)

            # sinsoktong 삭제
            cur.execute("DELETE FROM redevelopment_zones WHERE id = %s", (sid,))
            merged += 1
            merge_details.append(f"  {sdist} {sname} (stage={sstage}) -> ArcGIS id={aid} {arcgis_match[1]}")
        else:
            kept += 1

    conn.commit()
    print(f"  병합(삭제): {merged}건")
    print(f"  유지(고유): {kept}건")
    if merge_details[:10]:
        for d in merge_details[:10]:
            print(d)
        if len(merge_details) > 10:
            print(f"  ... +{len(merge_details)-10}건")

    # ======================================
    # STEP 4: 고유 sinsoktong에 geometry 보강
    # ======================================
    print(f"\n=== STEP 4: 고유 sinsoktong geometry 보강 ({kept}건) ===")
    cur.execute("""SELECT id, zone_name, district, center_lat
                   FROM redevelopment_zones
                   WHERE source = 'cleanup_sinsoktong' AND geometry IS NULL""")
    remaining = cur.fetchall()
    geo_added = 0
    coord_added = 0

    for rid, rname, rdist, rlat in remaining:
        # ArcGIS 검색
        arc = search_arcgis_by_name(rname, rdist)
        if arc and arc.get("geometry"):
            cur.execute("""UPDATE redevelopment_zones
                          SET geometry = %s, center_lat = %s, center_lon = %s, updated_at = NOW()
                          WHERE id = %s""",
                       (arc["geometry"], arc["center_lat"], arc["center_lon"], rid))
            geo_added += 1
            print(f"  [GEO] {rdist} {rname} -> ArcGIS: {arc.get('arcgis_name')}")
            continue

        # Geocoding (좌표만)
        if not rlat:
            dong_m = re.search(r"([가-힣]+동)", rname)
            lat, lon = None, None
            if dong_m:
                lat, lon = geocode(f"서울특별시 {rdist} {dong_m.group(1)}")
            if not lat:
                nm = re.match(r"([가-힣]+)", rname)
                if nm:
                    lat, lon = geocode(f"서울특별시 {rdist} {nm.group(1)}동")
            if not lat:
                lat, lon = geocode(f"서울특별시 {rdist}")
            if lat:
                cur.execute("UPDATE redevelopment_zones SET center_lat = %s, center_lon = %s WHERE id = %s",
                           (lat, lon, rid))
                coord_added += 1
            time.sleep(0.05)

    conn.commit()
    print(f"  geometry 추가: {geo_added}건")
    print(f"  좌표 추가: {coord_added}건")

    # ======================================
    # STEP 5: 정보몽땅 245건의 stage를 ArcGIS 대응 레코드에 반영
    # ======================================
    print(f"\n=== STEP 5: 정보몽땅 stage 반영 ({len(cleanup_unique)}건) ===")

    # DB 재로드
    cur.execute("""SELECT id, zone_name, district, stage, source
                   FROM redevelopment_zones""")
    db_fresh = cur.fetchall()
    fresh_idx = {}
    for row in db_fresh:
        rid, rname, rdist, rstage, rsrc = row
        norm = normalize(rname)
        key = (rdist, norm)
        if key not in fresh_idx:
            fresh_idx[key] = []
        fresh_idx[key].append(row)

    stage_updated = 0
    for z in cleanup_unique:
        stage = z.get("stage", "").strip()
        if not stage:
            continue

        dist = z["dist"]
        name = z["name"]
        norm = normalize(name)
        ptype = z["project_type"]

        hh = None
        try:
            hh_str = z.get("hh", "").strip()
            if hh_str:
                hh = int(float(hh_str))
        except (ValueError, TypeError):
            pass

        area = None
        try:
            area_str = z.get("area", "").replace(",", "").strip()
            if area_str:
                area = float(area_str)
        except (ValueError, TypeError):
            pass

        # DB에서 대응 찾기
        candidates = fresh_idx.get((dist, norm), [])
        if not candidates:
            candidates = fresh_idx.get((dist, norm + "구역"), [])
        if not candidates:
            # 부분 매칭
            m = re.match(r"([가-힣]+?)(\d+)", norm)
            if m:
                base, num = m.group(1), m.group(2)
                for (d, n), rows in fresh_idx.items():
                    if d == dist and base in n and num in n:
                        candidates = rows
                        break

        for c in candidates:
            cid, cname, cdist, cstage, csrc = c
            # stage가 비어있거나 "신속통합기획"이면 업데이트
            if not cstage or cstage == "" or cstage == "신속통합기획":
                sets = ["stage = %s"]
                vals = [stage]
                if hh:
                    sets.append("households = COALESCE(%s, households)")
                    vals.append(hh)
                if area:
                    sets.append("area_sqm = COALESCE(%s, area_sqm)")
                    vals.append(area)
                sets.append("updated_at = NOW()")
                vals.append(cid)
                cur.execute(f"UPDATE redevelopment_zones SET {', '.join(sets)} WHERE id = %s", vals)
                if cur.rowcount > 0:
                    stage_updated += 1

    conn.commit()
    print(f"  stage 업데이트: {stage_updated}건")

    # ======================================
    # STEP 6: 최종 결과
    # ======================================
    print(f"\n{'=' * 60}")
    print("=== 최종 결과 ===")
    print(f"{'=' * 60}")

    cur.execute("SELECT count(*) FROM redevelopment_zones")
    total = cur.fetchone()[0]
    cur.execute("SELECT source, count(*) FROM redevelopment_zones GROUP BY source ORDER BY count(*) DESC")
    print(f"총 구역: {total}")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")

    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE geometry IS NOT NULL")
    with_geo = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE center_lat IS NOT NULL")
    with_coord = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE stage IS NOT NULL AND stage != ''")
    with_stage = cur.fetchone()[0]

    print(f"\ngeometry: {with_geo} ({with_geo * 100 // total}%)")
    print(f"좌표: {with_coord} ({with_coord * 100 // total}%)")
    print(f"stage: {with_stage} ({with_stage * 100 // total}%)")

    # 남은 sinsoktong
    cur.execute("""SELECT zone_name, district, stage, geometry IS NOT NULL, center_lat IS NOT NULL
                   FROM redevelopment_zones WHERE source = 'cleanup_sinsoktong'
                   ORDER BY district, zone_name""")
    remaining = cur.fetchall()
    print(f"\n남은 sinsoktong: {len(remaining)}건")
    for r in remaining:
        print(f"  {r[1]} | {r[0]} | stage={r[2]} | geo={r[3]} | coord={r[4]}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
