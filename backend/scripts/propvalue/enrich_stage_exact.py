#!/usr/bin/env python3
"""정보몽땅 크롤링으로 정확한 stage 재매칭

cleanup.seoul.go.kr의 사업장 검색 API를 사용하여
DB의 zone_name으로 검색 → 정확 매칭되는 구역의 stage를 가져옴.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import psycopg2
import psycopg2.extras

DB_CFG = dict(
    host="127.0.0.1", port=5432, dbname="goldenrabbit_db",
    user="goldenrabbit_user", password=os.environ.get("DB_PASSWORD", "")
)

STAGE_MAP = {
    "추진주체구성전": "추진위전", "추진위원회구성": "추진위",
    "조합설립인가": "조합설립", "사업시행인가": "사업시행",
    "관리처분인가": "관리처분", "착공": "착공",
    "준공인가": "준공", "이전고시": "준공", "조합해산": "조합해산",
}


def normalize_stage(raw):
    if not raw:
        return ""
    raw = raw.strip()
    for k, v in STAGE_MAP.items():
        if k in raw:
            return v
    return raw


def search_cleanup(query):
    """정보몽땅에서 사업장 검색 (POST)"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("pip install beautifulsoup4")
        sys.exit(1)

    base_url = "https://cleanup.seoul.go.kr/cleanup/bsnssttus/lsubBsnsSttus.do"
    params = {
        "scupBsnsSttus.signguCode": "",
        "scupBsnsSttus.legaldongCode": "",
        "scupBsnsSttus.asscNm": query,
        "scupBsnsSttus.bsnsProgrsSttusCode": "",
        "bsnsSeCodeList": "",
        "bsnsEfctMthdList": "",
        "cafeSttusCodeList": "",
        "operSeCodeList": "",
        "orderValue": "",
        "sortColumn": "",
    }
    url = base_url + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", "Mozilla/5.0 (PropValue stage enrichment)")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("Referer", "https://cleanup.seoul.go.kr/cleanup/bsnssttus/lscrMainIndx.do")

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode("utf-8")
    except Exception as e:
        return []

    soup = BeautifulSoup(html, "html.parser")

    results = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 6:
            continue
        results.append({
            "district": tds[1].get_text(strip=True),
            "project_type": tds[2].get_text(strip=True),
            "zone_name": tds[3].get_text(strip=True),
            "address": tds[4].get_text(strip=True),
            "stage": tds[5].get_text(strip=True),
        })
    return results


def extract_search_key(zone_name):
    """검색용 핵심 키워드 추출 (정보몽땅 사업장명 검색용)

    정보몽땅은 사업장명(조합명)으로만 검색 가능.
    지번형(사당동 419-1)은 검색 불가 → None 반환.
    """
    # 괄호 제거
    clean = re.sub(r"\([^)]*\)", "", zone_name).strip()
    # 지번형: "OO동 NNN-N" → 정보몽땅에서 검색 불가, skip
    m = re.match(r"^[가-힣]+\d*동\s+\d+", clean)
    if m:
        return None
    # "OO숫자구역" or "OO숫자" (구역명 패턴: 방배15, 신림8구역 등)
    m = re.match(r"([가-힣]+\d+)", clean)
    if m:
        return m.group(1)
    # 아파트/연립 이름
    m = re.match(r"(.+(?:아파트|연립|맨션|빌라|타운|마을|주공))", clean)
    if m:
        return m.group(1)
    # 그대로
    return clean[:20]


def name_matches(db_name, cleanup_name):
    """DB 이름과 정보몽땅 이름이 같은 구역인지 판단"""
    # 정확 일치
    if db_name == cleanup_name:
        return True
    # 동+번지 패턴 비교
    db_m = re.match(r"([가-힣]+동)\s*(\d+[-\d]*)", db_name)
    cl_m = re.match(r"([가-힣]+동)\s*(\d+[-\d]*)", cleanup_name)
    if db_m and cl_m:
        return db_m.group(1) == cl_m.group(1) and db_m.group(2) == cl_m.group(2)
    # 구역명 패턴 (방배15 == 방배15구역)
    db_s = re.match(r"([가-힣]+\d+)", db_name)
    cl_s = re.match(r"([가-힣]+\d+)", cleanup_name)
    if db_s and cl_s:
        return db_s.group(1) == cl_s.group(1)
    # 포함 관계 (짧은 이름이 긴 이름에 포함)
    shorter = db_name if len(db_name) < len(cleanup_name) else cleanup_name
    longer = cleanup_name if len(db_name) < len(cleanup_name) else db_name
    if len(shorter) >= 4 and shorter in longer:
        return True
    return False


def main():
    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # stage가 비어있는 구역
    cur.execute("""
        SELECT id, zone_name, district
        FROM redevelopment_zones
        WHERE (stage IS NULL OR stage = '')
          AND is_hidden = FALSE
        ORDER BY district, zone_name
    """)
    targets = cur.fetchall()
    print(f"=== stage 비어있는 구역: {len(targets)}건 ===\n")

    matched = 0
    searched = 0
    errors = 0
    # 검색 캐시 (같은 키워드 재검색 방지)
    cache = {}

    for t in targets:
        zid = t["id"]
        zname = t["zone_name"]
        district = t["district"]
        key = extract_search_key(zname)

        if not key or len(key) < 2:
            continue

        cache_key = f"{district}_{key}"
        if cache_key not in cache:
            results = search_cleanup(key)
            cache[cache_key] = results
            searched += 1
            time.sleep(0.3)  # rate limit
        else:
            results = cache[cache_key]

        # 같은 구에서 이름이 매칭되는 결과 찾기
        best = None
        for r in results:
            if r["district"] == district and name_matches(zname, r["zone_name"]):
                best = r
                break

        if best:
            stage = normalize_stage(best["stage"])
            if stage:
                cur.execute(
                    "UPDATE redevelopment_zones SET stage = %s, updated_at = NOW() WHERE id = %s",
                    (stage, zid))
                matched += 1

        if searched % 100 == 0 and searched > 0:
            conn.commit()
            print(f"  진행: {searched}건 검색, {matched}건 매칭...")

    conn.commit()
    print(f"\n=== 완료 ===")
    print(f"  검색: {searched}건")
    print(f"  매칭: {matched}건")

    # 최종 통계
    cur.execute("""
        SELECT count(*) as total,
          count(CASE WHEN stage != '' AND stage IS NOT NULL THEN 1 END) as staged
        FROM redevelopment_zones WHERE is_hidden = FALSE
    """)
    r = cur.fetchone()
    print(f"  visible 총: {r['total']}건, stage 있음: {r['staged']}건 ({r['staged']*100//r['total']}%)")

    conn.close()


if __name__ == "__main__":
    main()
