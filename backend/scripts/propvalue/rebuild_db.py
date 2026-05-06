#!/usr/bin/env python3
"""PropValue DB 전면 재구축 — ArcGIS 기준 + 정보몽땅 보강"""
import psycopg2
import json
import urllib.request
import re
import time
import os

DB_PARAMS = {
    "dbname": "goldenrabbit_db",
    "user": "goldenrabbit_user",
    "password": os.environ.get("DB_PASSWORD", ""),
    "host": "127.0.0.1",
}

ARCGIS_BASE = "https://urban.seoul.go.kr/proxy/proxy.jsp?http://98.33.2.225:6080/arcgis/rest/services/UPIS/20200526_WMS/MapServer"

LAYERS = {
    "BZ101": (94, "재개발"), "BZ102": (95, "재건축"), "BZ103": (96, "도시환경"),
    "BZ104": (97, "주거환경개선"), "BZ105": (98, "소규모재건축"),
    "BZ107": (99, "가로주택"), "BZ108": (100, "기타"),
    "BZ201": (101, "택지개발"), "BZ202": (102, "지구단위계획"),
    "BZ203": (103, "도시개발"), "BZ204": (104, "도시계획시설"),
    "BZ205": (105, "시가지조성"),
    "BZ301": (106, "재정비촉진"), "BZ302": (107, "재개발"),
    "BZ303": (108, "재건축"), "BZ304": (109, "도시환경"),
    "BZ305": (110, "주거환경개선"), "BZ306": (111, "가로주택"),
    "BZ401": (112, "도시재생"), "BZ402": (113, "도시재생"),
    "BZ403": (114, "도시재생"), "BZ404": (115, "도시재생"),
    "BZ501": (116, "역세권"), "BZ502": (117, "역세권"),
    "BZ601": (118, "혁신도시"), "BZ602": (119, "기업도시"),
    "BZ603": (120, "경제자유구역"), "BZ604": (121, "국토부"),
    "BZ606": (122, "신도시"),
}

SIGNGU = {
    "11110": "종로구", "11140": "중구", "11170": "용산구", "11200": "성동구",
    "11215": "광진구", "11230": "동대문구", "11260": "중랑구", "11290": "성북구",
    "11305": "강북구", "11320": "도봉구", "11350": "노원구", "11380": "은평구",
    "11410": "서대문구", "11440": "마포구", "11470": "양천구", "11500": "강서구",
    "11530": "구로구", "11545": "금천구", "11560": "영등포구", "11590": "동작구",
    "11620": "관악구", "11650": "서초구", "11680": "강남구", "11710": "송파구",
    "11740": "강동구", "11000": "서울시",
}


def extract_dong_bonbun(name):
    m = re.search(r"([가-힣]+동)\s*(\d+)", name)
    return (m.group(1), m.group(2)) if m else (None, None)


def extract_short(name):
    m = re.search(r"([가-힣]+?)(\d+)", name)
    return f"{m.group(1)}{m.group(2)}" if m else None


def main():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # ====== 1단계: 백업 + 초기화 ======
    print("=== 1단계: 백업 + 초기화 ===")
    cur.execute("DROP TABLE IF EXISTS redevelopment_zones_backup_v2")
    cur.execute("CREATE TABLE redevelopment_zones_backup_v2 AS SELECT * FROM redevelopment_zones")
    cur.execute("SELECT COUNT(*) FROM redevelopment_zones_backup_v2")
    print(f"백업: {cur.fetchone()[0]}건")

    cur.execute("DELETE FROM redevelopment_zones")
    conn.commit()
    print("초기화 완료")

    # ====== 2단계: ArcGIS INSERT ======
    print("\n=== 2단계: ArcGIS 수집 ===")
    total = 0
    seen = set()

    for code, (lid, type_name) in LAYERS.items():
        try:
            url = (f"{ARCGIS_BASE}/{lid}/query?where=1%3D1"
                   f"&outFields=*&returnGeometry=true&outSR=4326&f=json")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())

            cnt = 0
            for f in data.get("features", []):
                attrs = f.get("attributes", {})
                rings = f.get("geometry", {}).get("rings", [])
                fname = (attrs.get("DGM_NM") or "").strip()
                if not fname or not rings:
                    continue

                sig = attrs.get("SIGNGU_SE", "")
                dedup = f"{sig}_{fname}_{code}"
                if dedup in seen:
                    continue
                seen.add(dedup)

                district = SIGNGU.get(sig, "")
                dong_m = re.search(r"([가-힣]+동)", fname)
                dong = dong_m.group(1) if dong_m else None

                geom = json.dumps({"type": "Polygon", "coordinates": rings})
                r0 = rings[0]
                clat = sum(c[1] for c in r0) / len(r0)
                clon = sum(c[0] for c in r0) / len(r0)

                present_sn = attrs.get("PRESENT_SN", "")
                cur.execute(
                    """INSERT INTO redevelopment_zones
                    (zone_name, zone_code, city, district, dong, project_type, stage,
                     area_sqm, geometry, center_lat, center_lon, source)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (fname, present_sn, "서울특별시", district, dong,
                     type_name, "", attrs.get("DGM_AR"),
                     geom, clat, clon, "urban.seoul.go.kr"))
                cnt += 1
                total += 1

            conn.commit()
            print(f"  {code} ({type_name}): {cnt}건")
        except Exception as e:
            conn.rollback()
            print(f"  {code}: error - {str(e)[:80]}")
        time.sleep(0.3)
    print(f"ArcGIS 총: {total}건")

    # ====== 3단계: 정보몽땅 속성 보강 ======
    print("\n=== 3단계: 정보몽땅 보강 ===")

    cur.execute(
        """SELECT zone_name, district, dong, stage, households, developer,
                  union_approved, biz_approved, mgmt_approved,
                  construction_start, completion_date
           FROM redevelopment_zones_backup_v2
           WHERE source IN ('cleanup_seoul','cleanup_sinsoktong')
             AND stage IS NOT NULL AND stage != ''""")
    cleanup = cur.fetchall()
    print(f"정보몽땅 데이터: {len(cleanup)}건")

    # 현재 DB 인덱싱
    cur.execute("SELECT id, zone_name, district, dong FROM redevelopment_zones")
    db_idx_dong = {}
    db_idx_short = {}
    for zid, zname, zdist, zdong in cur.fetchall():
        d, b = extract_dong_bonbun(zname)
        if d and b and zdist:
            db_idx_dong[f"{zdist}_{d}_{b}"] = zid
        s = extract_short(zname)
        if s and zdist:
            db_idx_short[f"{zdist}_{s}"] = zid

    updated = 0
    for cname, cdist, cdong, cstage, chh, cdev, cu, cb, cm, cs, cc in cleanup:
        mid = None

        # 동+번지
        d, b = extract_dong_bonbun(cname)
        if d and b and cdist:
            mid = db_idx_dong.get(f"{cdist}_{d}_{b}")

        # 괄호 안 이름
        if not mid and cdist:
            pm = re.search(r"\(([^)]+)\)", cname)
            paren = pm.group(1) if pm else None
            s = extract_short(paren) if paren else extract_short(cname)
            if s:
                mid = db_idx_short.get(f"{cdist}_{s}")

        if mid and cstage:
            sets = ["stage = %s"]
            vals = [cstage]
            if chh:
                sets.append("households = %s"); vals.append(chh)
            if cdev:
                sets.append("developer = %s"); vals.append(cdev)
            if cu:
                sets.append("union_approved = %s"); vals.append(cu)
            if cb:
                sets.append("biz_approved = %s"); vals.append(cb)
            if cm:
                sets.append("mgmt_approved = %s"); vals.append(cm)
            if cs:
                sets.append("construction_start = %s"); vals.append(cs)
            if cc:
                sets.append("completion_date = %s"); vals.append(cc)
            vals.append(mid)
            cur.execute(
                f"UPDATE redevelopment_zones SET {', '.join(sets)} WHERE id = %s",
                vals)
            if cur.rowcount > 0:
                updated += 1

    conn.commit()
    print(f"속성 보강: {updated}건")

    # ====== 4단계: 신속통합기획 추가 ======
    print("\n=== 4단계: 신속통합기획 추가 ===")

    cur.execute(
        """SELECT zone_name, district, dong, stage, center_lat, center_lon, area_sqm
           FROM redevelopment_zones_backup_v2
           WHERE source = 'cleanup_sinsoktong'""")
    sinsoktong = cur.fetchall()

    cur.execute("SELECT zone_name FROM redevelopment_zones")
    names = set(r[0] for r in cur.fetchall())

    added = 0
    for sn, sd, sdong, ss, slat, slon, sa in sinsoktong:
        d, b = extract_dong_bonbun(sn)
        exists = sn in names
        if not exists and d and b:
            for n in names:
                if d in n and b in n:
                    exists = True
                    break
        if not exists:
            cur.execute(
                """INSERT INTO redevelopment_zones
                (zone_name, city, district, dong, project_type, stage,
                 area_sqm, center_lat, center_lon, source)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (sn, "서울특별시", sd, sdong, "재개발", ss or "",
                 sa, slat, slon, "cleanup_sinsoktong"))
            names.add(sn)
            added += 1

    conn.commit()
    print(f"신속통합 추가: {added}건")

    # ====== 최종 ======
    cur.execute(
        """SELECT COUNT(*),
                  SUM(CASE WHEN geometry IS NOT NULL THEN 1 ELSE 0 END),
                  SUM(CASE WHEN stage != '' AND stage IS NOT NULL THEN 1 ELSE 0 END)
           FROM redevelopment_zones""")
    t, g, s = cur.fetchone()
    print(f"\n=== 최종 결과 ===")
    print(f"총 구역: {t}")
    print(f"geometry: {g} ({g*100//t}%)")
    print(f"stage: {s} ({s*100//t}%)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
