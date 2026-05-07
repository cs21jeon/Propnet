#!/usr/bin/env python3
"""신속통합기획(sinsoktong) 데이터 정리 스크립트

문제점:
1. geocoding이 동 단위로만 됨 → 같은 동의 모든 구역이 동일 좌표
2. 부정확한 좌표로 SHP 폴리곤 근접매칭 → 엉뚱한 폴리곤 할당
3. urban.seoul.go.kr 데이터와 중복

해결:
1단계: 확실한 중복 → urban에 stage 전달 후 sinsoktong 삭제
2단계: 고유 항목 → VWorld 지번 geocoding으로 좌표 재설정 + 폴리곤 재매칭
"""
import json, os, sys, time, urllib.parse, urllib.request
import psycopg2

VWORLD = os.environ.get("VWORLD_APIKEY", "")
DB_CFG = dict(host="127.0.0.1", port=5432, dbname="goldenrabbit_db",
              user="goldenrabbit_user", password=os.environ.get("DB_PASSWORD", ""))

# ── 1단계: 확실한 중복 매핑 (sinsoktong_id → urban_id) ──
DUPLICATES = {
    11057: 8041,   # 경남,우성,현대 → 개포 경남·우성3·현대1 (동일 좌표+면적)
    11069: 8099,   # 월계시영(미성,미륭,삼호3) → 월계시영(미륭,미성,삼호3) (동일 좌표+면적)
    10950: 8049,   # 신월 5-72 → 신월5동 72 일대 (동일 좌표+면적)
    11014: 8166,   # 서계동 33 → 서계동통합 (동일 좌표+면적)
    11017: 8566,   # 창신동 23-2 → 창신동 23 일대 (근접 좌표+동일 면적)
    11018: 8548,   # 숭인동 56-4 → 숭인동 56 일대 (근접 좌표+동일 면적)
    11061: 8056,   # 올림픽훼밀리타운 → 올림픽훼미리타운 (동일 면적)
    11015: 8491,   # 가리봉동 115 → 가리봉1구역 (동일 면적 83950/83949.57)
    11011: 8438,   # 신월7-1 → 신월7동1구역 (동일 구역)
    10969: 8143,   # 사당동 416-1(사당15) → 사당동 419-1 (사당15구역, 유사 면적)
    10975: 8144,   # 사당동 63-1 → 사당17구역 (오너 확인)
    10987: 8137,   # 독산동 1022 → 독산4동 1022번지 일대 (동일 지번)
    10986: 8046,   # 독산동 979 → 독산3동 979번지 일대 (동일 지번)
}

# stage 우선순위 (높을수록 진행됨)
STAGE_ORDER = [
    "후보지선정", "신통자문", "신통통보", "신통착수", "용역착수",
    "추진위", "주민공람", "구역지정", "조합설립", "시행자지정(신탁)",
    "심의", "사업시행", "관리처분", "착공", "준공", "조합해산", "해제",
]

def stage_rank(s):
    if not s:
        return -1
    for i, st in enumerate(STAGE_ORDER):
        if st in s:
            return i
    return -1


def geocode_jibun(addr):
    """VWorld 지번 geocoding"""
    if not VWORLD or not addr:
        return None, None
    try:
        p = urllib.parse.urlencode({
            "service": "address", "request": "getcoord", "version": "2.0",
            "crs": "epsg:4326", "address": addr, "refine": "true",
            "simple": "false", "format": "json", "type": "parcel",
            "key": VWORLD
        })
        req = urllib.request.Request(f"https://api.vworld.kr/req/address?{p}")
        req.add_header("User-Agent", "PropValue/1.0")
        resp = urllib.request.urlopen(req, timeout=10)
        d = json.loads(resp.read().decode("utf-8"))
        if d.get("response", {}).get("status") == "OK":
            pt = d["response"]["result"]["point"]
            return float(pt["y"]), float(pt["x"])
    except Exception as e:
        print(f"  geocode error: {e}")
    return None, None


def find_nearest_polygon(cur, lat, lon, max_dist=0.003):
    """같은 district 내에서 가장 가까운 폴리곤 찾기 (SHP 기반 urban 데이터에서)"""
    cur.execute("""
        SELECT id, zone_name, geometry,
               ABS(center_lat - %s) + ABS(center_lon - %s) as dist
        FROM redevelopment_zones
        WHERE source != 'cleanup_sinsoktong'
          AND geometry IS NOT NULL
          AND ABS(center_lat - %s) < %s
          AND ABS(center_lon - %s) < %s
        ORDER BY dist
        LIMIT 1
    """, (lat, lon, lat, max_dist, lon, max_dist))
    row = cur.fetchone()
    if row:
        return row[2]  # geometry jsonb
    return None


def main():
    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor()

    # 현재 상태 확인
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE source='cleanup_sinsoktong'")
    total = cur.fetchone()[0]
    print(f"=== sinsoktong 정리 시작 (총 {total}건) ===\n")

    # ── 1단계: 중복 삭제 + stage 전달 ──
    print("── 1단계: 중복 삭제 ──")
    deleted = 0
    stage_updated = 0

    for sin_id, urban_id in DUPLICATES.items():
        cur.execute("SELECT zone_name, stage, area_sqm, households FROM redevelopment_zones WHERE id=%s", (sin_id,))
        sin = cur.fetchone()
        if not sin:
            print(f"  [SKIP] sin #{sin_id} 없음")
            continue

        cur.execute("SELECT zone_name, stage FROM redevelopment_zones WHERE id=%s", (urban_id,))
        urban = cur.fetchone()
        if not urban:
            print(f"  [SKIP] urban #{urban_id} 없음")
            continue

        sin_name, sin_stage, sin_area, sin_hh = sin
        urban_name, urban_stage = urban

        # sinsoktong의 stage가 더 최신이면 urban에 전달
        if stage_rank(sin_stage) > stage_rank(urban_stage):
            cur.execute("UPDATE redevelopment_zones SET stage=%s, updated_at=NOW() WHERE id=%s",
                        (sin_stage, urban_id))
            stage_updated += 1
            print(f"  [STAGE] #{urban_id} {urban_name}: '{urban_stage}' → '{sin_stage}'")

        # sinsoktong에만 households가 있으면 전달
        if sin_hh and sin_hh > 0:
            cur.execute("""UPDATE redevelopment_zones SET households=COALESCE(households, %s), updated_at=NOW()
                          WHERE id=%s AND (households IS NULL OR households = 0)""",
                        (sin_hh, urban_id))

        # sinsoktong 삭제
        cur.execute("DELETE FROM redevelopment_zones WHERE id=%s", (sin_id,))
        deleted += 1
        print(f"  [DEL] #{sin_id} {sin_name} → #{urban_id} {urban_name}")

    print(f"\n  삭제: {deleted}건, stage 갱신: {stage_updated}건\n")

    # ── 2단계: 나머지 sinsoktong 재geocoding + 폴리곤 재매칭 ──
    print("── 2단계: 나머지 항목 재geocoding ──")
    cur.execute("""SELECT id, zone_name, district, center_lat, center_lon
                   FROM redevelopment_zones
                   WHERE source='cleanup_sinsoktong'
                   ORDER BY id""")
    remaining = cur.fetchall()
    print(f"  남은 항목: {len(remaining)}건\n")

    geocoded = 0
    poly_matched = 0

    for rid, rname, rdistrict, old_lat, old_lon in remaining:
        # 지번 주소로 정밀 geocoding
        import re
        # "사당동 416-1(사당15)" → "사당동 416-1"
        addr_clean = re.sub(r"\(.*\)", "", rname).strip()

        # 완전한 주소로 geocoding 시도
        full_addr = f"서울특별시 {rdistrict} {addr_clean}"
        lat, lon = geocode_jibun(full_addr)

        if not lat:
            # 동 이름만으로 재시도 (fallback)
            dong_match = re.match(r"([가-힣]+동?)", addr_clean)
            if dong_match:
                dong = dong_match.group(1)
                if not dong.endswith("동"):
                    dong += "동"
                fallback_addr = f"서울특별시 {rdistrict} {dong}"
                lat, lon = geocode_jibun(fallback_addr)
                if lat:
                    print(f"  [{rid}] {rname}: fallback geocoding ({fallback_addr})")

        if lat and (abs(float(old_lat or 0) - lat) > 0.001 or abs(float(old_lon or 0) - lon) > 0.001):
            # 좌표가 유의미하게 변경됨 → 업데이트
            cur.execute("""UPDATE redevelopment_zones
                          SET center_lat=%s, center_lon=%s, updated_at=NOW()
                          WHERE id=%s""", (lat, lon, rid))
            geocoded += 1
            print(f"  [{rid}] {rname}: 좌표 갱신 ({old_lat},{old_lon}) → ({lat},{lon})")

            # 새 좌표로 폴리곤 재매칭
            new_geom = find_nearest_polygon(cur, lat, lon)
            if new_geom:
                cur.execute("""UPDATE redevelopment_zones
                              SET geometry=%s, updated_at=NOW()
                              WHERE id=%s""", (json.dumps(new_geom) if isinstance(new_geom, dict) else new_geom, rid))
                poly_matched += 1
                print(f"         → 폴리곤 재매칭 완료")
            else:
                # 기존 잘못된 폴리곤 제거
                cur.execute("""UPDATE redevelopment_zones
                              SET geometry=NULL, updated_at=NOW()
                              WHERE id=%s""", (rid,))
                print(f"         → 근접 폴리곤 없음, 기존 폴리곤 제거")
        elif lat:
            print(f"  [{rid}] {rname}: 좌표 동일 (변경 없음)")
        else:
            print(f"  [{rid}] {rname}: geocoding 실패 ({full_addr})")
            # 기존 잘못된 폴리곤이라도 제거
            cur.execute("""UPDATE redevelopment_zones
                          SET geometry=NULL, updated_at=NOW()
                          WHERE id=%s""", (rid,))

        time.sleep(0.1)  # VWorld rate limit

    print(f"\n  재geocoding: {geocoded}건, 폴리곤 재매칭: {poly_matched}건\n")

    # ── 결과 요약 ──
    conn.commit()
    cur.execute("SELECT count(*) FROM redevelopment_zones WHERE source='cleanup_sinsoktong'")
    final = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM redevelopment_zones")
    total_all = cur.fetchone()[0]
    print(f"=== 정리 완료 ===")
    print(f"  sinsoktong: {total}건 → {final}건 (삭제 {deleted}건)")
    print(f"  DB 전체: {total_all}건")

    conn.close()


if __name__ == "__main__":
    main()
