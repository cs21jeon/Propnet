#!/usr/bin/env python3
"""조합해산/조합청산 구역 중 실제로는 활성 사업이 진행 중인 오매칭 검출"""
import os
import sys
import psycopg2
import psycopg2.extras

sys.path.insert(0, os.path.dirname(__file__))
from enrich_stage_exact import search_cleanup, extract_search_key, name_matches, normalize_stage

DB_CFG = dict(
    host="127.0.0.1", port=5432, dbname="goldenrabbit_db",
    user="goldenrabbit_user", password=os.environ.get("DB_PASSWORD", "")
)

DEAD_STAGES = {"조합해산", "조합청산"}
# 해산/청산보다 활성인 단계
ACTIVE_STAGES = {
    "정비계획 수립", "안전진단", "추진위", "구역지정", "조합설립",
    "사업시행", "관리처분", "착공", "분양", "철거",
    "추진위원회승인", "조합설립인가", "사업시행인가", "관리처분인가",
}

import time

conn = psycopg2.connect(**DB_CFG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT id, zone_name, district, stage
    FROM redevelopment_zones
    WHERE stage IN ('조합해산', '조합청산')
      AND is_hidden = FALSE
    ORDER BY district, zone_name
""")
targets = cur.fetchall()
print("조합해산/청산 구역: %d건\n" % len(targets))

fixes = []
for t in targets:
    key = extract_search_key(t["zone_name"])
    if not key:
        continue

    results = search_cleanup(key)
    time.sleep(0.3)

    # 같은 구역에서 활성 사업이 있는지 확인
    active = None
    dead = None
    for r in results:
        if r["district"] != t["district"]:
            continue
        if not name_matches(t["zone_name"], r["zone_name"]):
            continue
        stage = normalize_stage(r["stage"])
        if stage in DEAD_STAGES:
            dead = r
        elif stage in ACTIVE_STAGES or (stage and stage not in DEAD_STAGES):
            if not active:
                active = r

    if active:
        new_stage = normalize_stage(active["stage"])
        fixes.append((t["id"], t["zone_name"], t["district"], t["stage"], new_stage, active["zone_name"]))
        print("[FIX] %s (%s): %s -> %s (from: %s)" % (
            t["zone_name"], t["district"], t["stage"], new_stage, active["zone_name"][:50]))
    else:
        print("[OK ] %s (%s): %s 확인됨" % (t["zone_name"], t["district"], t["stage"]))

print("\n=== 수정 필요: %d건 ===" % len(fixes))

if fixes:
    for fid, fname, fdist, old, new, src in fixes:
        cur.execute("UPDATE redevelopment_zones SET stage = %s, updated_at = NOW() WHERE id = %s", (new, fid))
        print("  UPDATE #%d %s: %s -> %s" % (fid, fname, old, new))
    conn.commit()
    print("커밋 완료")

conn.close()
