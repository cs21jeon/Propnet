#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""신속통합기획 누락 데이터 추가 수집 v3

정보몽땅 기준 245건 (재개발 150 + 재건축 95) 중 DB에 없는 ~130건을 추가 INSERT.

데이터 소스:
  - https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn.do  (재개발 150건)
  - https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn2.do (재건축 95건)

매칭 로직:
  1. zone_name + district 정확 매칭
  2. zone_name 핵심부분 (한글+숫자만) + district 매칭
  3. ArcGIS zone_name에서 구역명 포함 여부 확인

실행:
  source /home/webapp/goldenrabbit/backend/venv/bin/activate
  export $(grep -v '^#' /home/webapp/goldenrabbit/backend/.env | xargs)
  cd /home/webapp/goldenrabbit/backend/scripts/propvalue
  python3 collect_sinsoktong_v3.py
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
    host="127.0.0.1",
    port=5432,
    dbname="goldenrabbit_db",
    user="goldenrabbit_user",
    password=os.environ.get("DB_PASSWORD", ""),
)

ARCGIS_BASE = (
    "https://urban.seoul.go.kr/proxy/proxy.jsp?"
    "http://98.33.2.225:6080/arcgis/rest/services/UPIS/20200526_WMS/MapServer"
)

# ArcGIS 레이어: 재개발(94), 재건축(95), 소규모재건축(98)
ARCGIS_LAYERS = {
    94: "재개발",
    95: "재건축",
    98: "소규모재건축",
    107: "재개발",   # 뉴타운 재개발
    108: "재건축",   # 뉴타운 재건축
}

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
    """VWorld 주소 -> 좌표"""
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


def normalize_name(name):
    """구역명에서 핵심 부분만 추출 (한글 + 숫자 + 하이픈)"""
    return re.sub(r"[^가-힣0-9\-]", "", name).strip()


def scrape_redevelopment():
    """재개발 페이지 (150건): 1차21 + 2차23 + 수시83 + 기존23"""
    url = "https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn.do"
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
            # 첫 셀이 번호인지
            try:
                int(cells[0].replace(",", ""))
            except ValueError:
                continue
            # cells[1]이 "XX구"인지
            if not re.match(r"^[가-힣]+구$", cells[1]):
                continue

            # 7컬럼: 번호, 자치구, 구역명, 면적, 세대수, 추진단계, 고시일
            zone = {
                "dist": cells[1],
                "name": cells[2].strip(),
                "area": cells[3].replace(",", "").replace("㎡", "").strip(),
                "hh": cells[4].replace(",", "").replace("-", "").replace("—", "").strip(),
                "stage": cells[5].strip() if len(cells) > 5 else "",
                "project_type": "재개발",
            }
            if zone["name"] and zone["name"] != zone["dist"]:
                zones.append(zone)

    return zones


def scrape_reconstruction():
    """재건축 페이지 (95건): 기획19 + 자문76"""
    url = "https://cleanup.seoul.go.kr/cleanup/view/publicIntgrPlanSttn2.do"
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

            # 8컬럼: 번호, 구분(기획/자문), 자치구, 구역명, 면적, 세대수, 추진단계, 고시일
            # 또는 7컬럼: 번호, 자치구, 구역명, 면적, 세대수, 추진단계, 고시일
            dist_idx = None
            for i in range(1, min(3, len(cells))):
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

            zone = {
                "dist": cells[dist_idx],
                "name": cells[name_idx].strip(),
                "area": cells[area_idx].replace(",", "").replace("㎡", "").strip() if area_idx < len(cells) else "",
                "hh": cells[hh_idx].replace(",", "").replace("-", "").replace("—", "").strip() if hh_idx < len(cells) else "",
                "stage": cells[stage_idx].strip() if stage_idx < len(cells) else "",
                "project_type": "재건축",
            }
            if zone["name"] and zone["name"] != zone["dist"]:
                zones.append(zone)

    return zones


def fetch_arcgis_index():
    """ArcGIS에서 구역 이름 -> (PRESENT_SN, geometry, center) 인덱스 구축"""
    print("\n=== ArcGIS 인덱스 구축 ===")
    index = {}  # key: (district, normalized_name) -> value dict

    for lid, ptype in ARCGIS_LAYERS.items():
        try:
            url = (f"{ARCGIS_BASE}/{lid}/query?where=1%3D1"
                   f"&outFields=OBJECTID,PRESENT_SN,DGM_NM,SIGNGU_SE,DGM_AR"
                   f"&returnGeometry=true&outSR=4326&f=json")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())

            for f in data.get("features", []):
                attrs = f.get("attributes", {})
                rings = f.get("geometry", {}).get("rings", [])
                fname = (attrs.get("DGM_NM") or "").strip()
                sig = attrs.get("SIGNGU_SE", "")
                district = SIGNGU.get(sig, "")

                if not fname or not district:
                    continue

                geom = None
                clat, clon = None, None
                if rings:
                    geom = json.dumps({"type": "Polygon", "coordinates": rings})
                    r0 = rings[0]
                    clat = sum(c[1] for c in r0) / len(r0)
                    clon = sum(c[0] for c in r0) / len(r0)

                entry = {
                    "present_sn": attrs.get("PRESENT_SN", ""),
                    "arcgis_name": fname,
                    "district": district,
                    "geometry": geom,
                    "center_lat": clat,
                    "center_lon": clon,
                    "area_sqm": attrs.get("DGM_AR"),
                    "project_type": ptype,
                }

                # 여러 키로 인덱싱
                norm = normalize_name(fname)
                index[(district, norm)] = entry
                index[(district, fname)] = entry

            print(f"  레이어 {lid} ({ptype}): {len(data.get('features', []))}건")
        except Exception as e:
            print(f"  레이어 {lid}: error - {str(e)[:80]}")
        time.sleep(0.5)

    print(f"  ArcGIS 인덱스 총: {len(index)}개 키")
    return index


def find_arcgis_match(name, dist, arcgis_idx):
    """신속통합 구역명을 ArcGIS 인덱스에서 검색"""
    # 1. 정확 매칭 (district + normalized name)
    norm = normalize_name(name)
    match = arcgis_idx.get((dist, norm))
    if match:
        return match

    # 2. 원본 이름 매칭
    match = arcgis_idx.get((dist, name))
    if match:
        return match

    # 3. 부분 매칭: ArcGIS 이름에 신속통합 구역명이 포함되는 경우
    #    예: "면목7" -> "면목동 7-2 일대"
    for (d, k), v in arcgis_idx.items():
        if d != dist:
            continue
        arcgis_norm = normalize_name(k)
        # 신속통합 이름의 핵심 부분이 ArcGIS 이름에 포함?
        # 한글+숫자 패턴 추출
        m = re.match(r"([가-힣]+)(\d+)", norm)
        if m:
            base, num = m.group(1), m.group(2)
            # ArcGIS에서 같은 기본 이름 + 번호 찾기
            am = re.search(rf"{re.escape(base)}.*?{num}", arcgis_norm)
            if am:
                return v

    return None


def main():
    print("=" * 60)
    print("신속통합기획 누락 데이터 추가 수집 v3")
    print("=" * 60)

    # 1. 크롤링
    print("\n=== 1. 정보몽땅 크롤링 ===")
    rd_zones = scrape_redevelopment()
    print(f"  재개발: {len(rd_zones)}건")

    rb_zones = scrape_reconstruction()
    print(f"  재건축: {len(rb_zones)}건")

    all_zones = rd_zones + rb_zones
    print(f"  합계: {len(all_zones)}건")

    # 중복 제거 (같은 구 + 같은 이름)
    seen = set()
    unique = []
    for z in all_zones:
        k = f"{z['dist']}_{z['name']}"
        if k not in seen:
            seen.add(k)
            unique.append(z)
    print(f"  중복 제거 후: {len(unique)}건")

    # 2. DB 기존 데이터 조회
    print("\n=== 2. DB 기존 데이터 조회 ===")
    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor()

    cur.execute("SELECT id, zone_name, zone_code, district, project_type, source FROM redevelopment_zones")
    db_rows = cur.fetchall()
    print(f"  DB 총: {len(db_rows)}건")

    # 매칭 인덱스 구축
    existing_exact = {}      # (district, zone_name) -> id
    existing_norm = {}       # (district, normalized_name) -> id
    existing_codes = set()   # zone_code set

    for rid, rname, rcode, rdist, rptype, rsrc in db_rows:
        existing_exact[(rdist, rname)] = rid
        norm = normalize_name(rname)
        if norm:
            existing_norm[(rdist, norm)] = rid
        if rcode:
            existing_codes.add(rcode)

    # 3. 누락 식별
    print("\n=== 3. 누락 식별 ===")
    missing = []
    matched = []

    for z in unique:
        name = z["name"]
        dist = z["dist"]

        # 정확 매칭
        if (dist, name) in existing_exact:
            matched.append(z)
            continue

        # 정규화 매칭
        norm = normalize_name(name)
        if norm and (dist, norm) in existing_norm:
            matched.append(z)
            continue

        # 부분 매칭: DB 이름에 구역명 핵심 포함 여부
        found = False
        m = re.match(r"([가-힣]+?)(\d+)", norm) if norm else None
        if m:
            base, num = m.group(1), m.group(2)
            for (d, n), rid in existing_norm.items():
                if d != dist:
                    continue
                if base in n and num in n:
                    found = True
                    break

        if found:
            matched.append(z)
            continue

        # 특수 케이스: 괄호 안 이름으로 매칭 (예: "미아4-1(단독재건축)")
        paren = re.search(r"\(([^)]+)\)", name)
        if paren:
            clean = re.sub(r"\([^)]*\)", "", name).strip()
            clean_norm = normalize_name(clean)
            if clean_norm and (dist, clean_norm) in existing_norm:
                matched.append(z)
                continue

        missing.append(z)

    print(f"  이미 존재: {len(matched)}건")
    print(f"  누락: {len(missing)}건")

    if not missing:
        print("\n누락 데이터 없음. 종료.")
        conn.close()
        return

    # 4. ArcGIS 매칭 시도
    arcgis_idx = fetch_arcgis_index()

    # 5. INSERT
    print(f"\n=== 5. INSERT ({len(missing)}건) ===")
    inserted = 0
    geocoded = 0
    arcgis_matched = 0
    errors = []

    for z in missing:
        name = z["name"]
        dist = z["dist"]
        ptype = z["project_type"]

        # ArcGIS 매칭
        arc = find_arcgis_match(name, dist, arcgis_idx)
        geometry = None
        center_lat, center_lon = None, None
        zone_code = None
        area_sqm = None

        if arc:
            arcgis_matched += 1
            geometry = arc.get("geometry")
            center_lat = arc.get("center_lat")
            center_lon = arc.get("center_lon")
            zone_code = arc.get("present_sn")
            area_sqm = arc.get("area_sqm")
            print(f"  [ArcGIS] {dist} {name} -> {arc.get('arcgis_name')}")

        # zone_code 중복 체크
        if zone_code and zone_code in existing_codes:
            # ArcGIS 코드가 이미 DB에 있으면 sinsoktong 코드 사용
            zone_code = None

        if not zone_code:
            prefix = "rd" if ptype == "재개발" else "rb"
            zone_code = f"sinsoktong-{prefix}-{dist}-{name[:30]}"

        # zone_code 중복 최종 체크
        if zone_code in existing_codes:
            zone_code = f"sinsoktong-{ptype[:2]}-{dist}-{name[:25]}-v3"

        # Geocoding (ArcGIS 좌표 없을 때)
        if not center_lat:
            dong_match = re.search(r"([가-힣]+동)", name)
            if dong_match:
                dong = dong_match.group(1)
                center_lat, center_lon = geocode(f"서울특별시 {dist} {dong}")

            if not center_lat:
                # 구역명에서 동 추출 시도
                nm = re.match(r"([가-힣]+)", name)
                if nm:
                    center_lat, center_lon = geocode(f"서울특별시 {dist} {nm.group(1)}동")

            if not center_lat:
                # 구 중심 좌표로 fallback
                center_lat, center_lon = geocode(f"서울특별시 {dist}")

            if center_lat:
                geocoded += 1

        # dong 추출
        dong_match = re.search(r"([가-힣]+동)", name)
        if dong_match:
            dong = dong_match.group(1)
        else:
            nm = re.match(r"([가-힣]+)", name)
            dong = nm.group(1) + "동" if nm else None

        # 면적 / 세대수
        if not area_sqm:
            try:
                area_sqm = float(z.get("area", "").replace(",", ""))
            except (ValueError, TypeError):
                area_sqm = None

        hh = None
        try:
            hh_str = z.get("hh", "").strip()
            if hh_str:
                hh = int(float(hh_str))
        except (ValueError, TypeError):
            pass

        # stage 매핑
        stage = z.get("stage", "").strip()
        if not stage:
            stage = "신속통합기획"

        try:
            cur.execute(
                """INSERT INTO redevelopment_zones
                   (zone_name, zone_code, city, district, dong, project_type, stage,
                    area_sqm, households, geometry, center_lat, center_lon, source, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                   ON CONFLICT (zone_code) DO UPDATE SET
                     stage = EXCLUDED.stage,
                     area_sqm = COALESCE(EXCLUDED.area_sqm, redevelopment_zones.area_sqm),
                     households = COALESCE(EXCLUDED.households, redevelopment_zones.households),
                     project_type = EXCLUDED.project_type,
                     updated_at = NOW()""",
                (name[:100], zone_code[:100], "서울특별시", dist, dong,
                 ptype, stage, area_sqm, hh, geometry,
                 center_lat, center_lon, "cleanup_sinsoktong"))
            if cur.rowcount > 0:
                inserted += 1
                existing_codes.add(zone_code)
                print(f"  + {dist} {name} [{ptype}] stage={stage} geo={'Y' if geometry else 'N'} coord={'Y' if center_lat else 'N'}")
        except Exception as e:
            conn.rollback()
            errors.append(f"{name}: {e}")
            print(f"  ! ERROR {dist} {name}: {e}")

        if center_lat and not arc:
            time.sleep(0.05)  # geocoding rate limit

    conn.commit()

    # 6. 기존 신속통합 데이터의 stage 업데이트
    print(f"\n=== 6. 기존 데이터 stage 업데이트 ===")
    stage_updated = 0
    for z in matched:
        name = z["name"]
        dist = z["dist"]
        stage = z.get("stage", "").strip()
        ptype = z["project_type"]

        if not stage:
            continue

        # 기존 DB의 stage가 비어있거나 "신속통합기획"이면 업데이트
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

        try:
            cur.execute(
                """UPDATE redevelopment_zones
                   SET stage = CASE WHEN stage IN ('', '신속통합기획') OR stage IS NULL THEN %s ELSE stage END,
                       households = COALESCE(%s, households),
                       area_sqm = COALESCE(%s, area_sqm),
                       updated_at = NOW()
                   WHERE district = %s
                     AND (zone_name = %s OR zone_name LIKE %s)
                     AND (stage IN ('', '신속통합기획') OR stage IS NULL
                          OR households IS NULL OR area_sqm IS NULL)""",
                (stage, hh, area, dist, name, f"%%{name}%%"))
            if cur.rowcount > 0:
                stage_updated += 1
        except Exception:
            conn.rollback()

    conn.commit()

    # 7. 결과 보고
    print(f"\n{'=' * 60}")
    print(f"=== 결과 ===")
    print(f"{'=' * 60}")
    print(f"크롤링: 재개발 {len(rd_zones)} + 재건축 {len(rb_zones)} = {len(all_zones)}건")
    print(f"중복 제거: {len(unique)}건")
    print(f"이미 존재: {len(matched)}건")
    print(f"누락 → INSERT: {inserted}건")
    print(f"  - ArcGIS 매칭 (geometry 포함): {arcgis_matched}건")
    print(f"  - Geocoding 좌표: {geocoded}건")
    print(f"기존 stage 업데이트: {stage_updated}건")
    if errors:
        print(f"에러: {len(errors)}건")
        for e in errors[:5]:
            print(f"  - {e}")

    # DB 최종 현황
    cur.execute("SELECT count(*) FROM redevelopment_zones")
    total = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE source = 'cleanup_sinsoktong'")
    sinsoktong = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE geometry IS NOT NULL")
    with_geo = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE center_lat IS NOT NULL")
    with_coord = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE stage IS NOT NULL AND stage != ''")
    with_stage = cur.fetchone()[0]

    print(f"\n=== DB 최종 현황 ===")
    print(f"총 구역: {total}")
    print(f"신속통합기획: {sinsoktong}")
    print(f"geometry: {with_geo} ({with_geo * 100 // total}%%)")
    print(f"좌표: {with_coord} ({with_coord * 100 // total}%%)")
    print(f"stage: {with_stage} ({with_stage * 100 // total}%%)")

    # 누락 목록 출력 (디버깅용)
    if missing:
        print(f"\n=== 누락 구역 상세 ({len(missing)}건) ===")
        for z in missing:
            print(f"  {z['dist']} | {z['name']} | {z['project_type']} | {z.get('stage', '')}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
