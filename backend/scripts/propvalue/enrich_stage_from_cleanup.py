#!/usr/bin/env python3
"""
PropValue stage 보강 - 정보몽땅(cleanup.seoul.go.kr) 크롤링으로 stage 업데이트

정보몽땅에서 사업장 목록을 크롤링하여 zone_name 유사 매칭으로 DB stage 보강.
ArcGIS PROPEL_CD로 커버하지 못한 BZ101(재개발) 120건 등을 타겟.

사용:
  python enrich_stage_from_cleanup.py --dry-run
  python enrich_stage_from_cleanup.py
"""
import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('enrich_cleanup')

DB_PARAMS = {
    "dbname": "goldenrabbit_db",
    "user": "goldenrabbit_user",
    "password": os.environ.get("DB_PASSWORD", ""),
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
}

BASE_URL = 'https://cleanup.seoul.go.kr'
LIST_URL = f'{BASE_URL}/cleanup/bsnssttus/lsubBsnsSttus.do'

STAGE_MAP = {
    '추진주체구성전': '구역지정',
    '추진위원회구성': '추진위',
    '추진위원회승인': '추진위',
    '조합설립인가': '조합설립',
    '조합설립': '조합설립',
    '사업시행인가': '사업시행',
    '사업시행자지정': '사업시행',
    '사업계획승인': '사업시행',
    '관리처분인가': '관리처분',
    '관리처분': '관리처분',
    '착공': '착공',
    '철거': '착공',
    '분양': '착공',
    '준공인가': '준공',
    '이전고시': '준공',
    '조합해산': '조합해산',
    '조합청산': '조합해산',
    '정비구역지정': '구역지정',
    '정비계획 수립': '구역지정',
    '안전진단': '구역지정',
    '조합원 모집신고': '조합설립',
    '조합규약작성': '조합설립',
    '조합창립총회': '조합설립',
    '도시계획심의': '구역지정',
    '지구단위계획수립': '사업시행',
}


def normalize_stage(raw):
    """정보몽땅 진행단계 정규화"""
    raw = raw.strip()
    for key, val in STAGE_MAP.items():
        if key in raw:
            return val
    # 그대로 반환 (알 수 없는 값)
    if raw:
        return raw
    return ""


def fetch_page(page_no=1):
    """정보몽땅 사업장 목록 한 페이지(10건) 가져오기"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        log.error("beautifulsoup4 필요: pip install beautifulsoup4")
        sys.exit(1)

    data = urllib.parse.urlencode({
        'cpage': str(page_no),
        'pageSize': '10',
        'bsnsGubun': '',
        'jachiGubun': '',
        'bsnsNm': '',
        'jbeon': '',
    }).encode('utf-8')

    req = urllib.request.Request(LIST_URL, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    req.add_header('User-Agent', 'Mozilla/5.0 (PropValue stage enrichment)')
    req.add_header('Referer', f'{BASE_URL}/cleanup/bsnssttus/lscrMainIndx.do')

    resp = urllib.request.urlopen(req, timeout=30)
    html = resp.read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    rows = []
    table = soup.find('table')
    if not table:
        return rows

    tbody = table.find('tbody')
    if not tbody:
        return rows

    for tr in tbody.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 6:
            continue
        row = {
            'district': tds[1].get_text(strip=True),
            'project_type': tds[2].get_text(strip=True),
            'zone_name': tds[3].get_text(strip=True),
            'address': tds[4].get_text(strip=True),
            'stage': tds[5].get_text(strip=True),
        }
        rows.append(row)

    return rows


def normalize_name(name):
    """이름 정규화 (매칭용): 공백/특수문자 제거, 숫자 유지"""
    name = re.sub(r'[·\s\-\_\(\)（）]', '', name)
    name = re.sub(r'구역$', '', name)
    name = re.sub(r'정비구역$', '', name)
    name = re.sub(r'재건축정비사업.*', '', name)
    name = re.sub(r'재개발정비사업.*', '', name)
    name = re.sub(r'도시환경정비사업.*', '', name)
    name = re.sub(r'가로주택정비사업.*', '', name)
    name = re.sub(r'정비사업.*', '', name)
    name = re.sub(r'조합$', '', name)
    return name.lower()


def match_zones(cleanup_zones, db_zones):
    """정보몽땅 구역을 DB 구역과 매칭"""
    # db_zones: list of (id, zone_name, district, stage)
    db_by_dist = {}
    for zid, zname, zdist, zstage in db_zones:
        if zdist not in db_by_dist:
            db_by_dist[zdist] = []
        db_by_dist[zdist].append((zid, zname, zstage, normalize_name(zname)))

    matches = []
    matched_ids = set()  # 하나의 DB 구역에 여러 정보몽땅 매칭 방지

    for cz in cleanup_zones:
        cdist = cz['district']
        cname = cz['zone_name']
        cstage = normalize_stage(cz['stage'])
        if not cstage:
            continue

        cnorm = normalize_name(cname)
        candidates = db_by_dist.get(cdist, [])

        best_match = None
        # 1) 정확 매칭
        for zid, zname, zstage, znorm in candidates:
            if zid in matched_ids:
                continue
            if cnorm == znorm:
                best_match = (zid, zname, zstage)
                break

        # 2) 포함 매칭 (한쪽이 다른쪽을 포함, 최소 4글자 + 숫자 경계 확인)
        if not best_match:
            for zid, zname, zstage, znorm in candidates:
                if zid in matched_ids:
                    continue
                if len(cnorm) >= 4 and len(znorm) >= 4:
                    if cnorm in znorm:
                        # cnorm 끝이 숫자이고 znorm에서 그 뒤에 숫자가 이어지면 제외
                        idx = znorm.find(cnorm)
                        end_idx = idx + len(cnorm)
                        if cnorm[-1].isdigit() and end_idx < len(znorm) and znorm[end_idx].isdigit():
                            continue
                        best_match = (zid, zname, zstage)
                        break
                    elif znorm in cnorm:
                        idx = cnorm.find(znorm)
                        end_idx = idx + len(znorm)
                        if znorm[-1].isdigit() and end_idx < len(cnorm) and cnorm[end_idx].isdigit():
                            continue
                        best_match = (zid, zname, zstage)
                        break

        # 3) 동+번호 매칭 (정확한 숫자, "신림1" != "신림10")
        if not best_match:
            cm = re.search(r'([가-힣]+?)(\d+)', cnorm)
            if cm:
                cdong, cnum = cm.group(1), cm.group(2)
                for zid, zname, zstage, znorm in candidates:
                    if zid in matched_ids:
                        continue
                    zm = re.search(r'([가-힣]+?)(\d+)', znorm)
                    if zm and zm.group(1) == cdong and zm.group(2) == cnum:
                        # 숫자 뒤에 다른 숫자가 바로 이어지면 불일치
                        c_end = cm.end()
                        z_end = zm.end()
                        if c_end < len(cnorm) and cnorm[c_end].isdigit():
                            continue
                        if z_end < len(znorm) and znorm[z_end].isdigit():
                            continue
                        best_match = (zid, zname, zstage)
                        break

        if best_match:
            zid, zname, existing_stage = best_match
            matched_ids.add(zid)
            matches.append({
                'db_id': zid,
                'db_name': zname,
                'cleanup_name': cname,
                'new_stage': cstage,
                'existing_stage': existing_stage,
                'district': cdist,
            })

    return matches


def main():
    parser = argparse.ArgumentParser(description='정보몽땅 stage 보강')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--page-limit', type=int, default=None,
                        help='최대 페이지 수 (기본: 전체)')
    args = parser.parse_args()

    if not DB_PARAMS['password']:
        log.error("DB_PASSWORD 환경변수가 필요합니다")
        sys.exit(1)

    # 정보몽땅 크롤링
    log.info("정보몽땅 크롤링 시작...")
    all_cleanup = []
    page = 1
    max_pages = args.page_limit or 120
    seen_names = set()
    consecutive_dupes = 0

    while page <= max_pages:
        rows = fetch_page(page_no=page)
        if not rows:
            log.info("페이지 %d: 데이터 없음 -> 종료", page)
            break

        # 중복 감지: 모든 행이 이미 본 이름이면 범위 초과
        new_rows = [r for r in rows if r['zone_name'] not in seen_names]
        if not new_rows:
            consecutive_dupes += 1
            if consecutive_dupes >= 3:
                log.info("페이지 %d: 연속 3페이지 중복 -> 종료", page)
                break
        else:
            consecutive_dupes = 0
            for r in rows:
                seen_names.add(r['zone_name'])
            all_cleanup.extend(new_rows)

        if page % 10 == 0:
            log.info("페이지 %d: 누적 %d건", page, len(all_cleanup))

        page += 1
        time.sleep(0.5)

    log.info("정보몽땅 총 %d건 수집", len(all_cleanup))

    # stage 분포
    stage_counts = {}
    for r in all_cleanup:
        s = normalize_stage(r['stage'])
        stage_counts[s] = stage_counts.get(s, 0) + 1
    log.info("정보몽땅 stage 분포:")
    for s, c in sorted(stage_counts.items(), key=lambda x: -x[1]):
        log.info("  %s: %d건", s or "(빈)", c)

    # DB에서 stage 없는 구역 조회
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, zone_name, district, stage FROM redevelopment_zones
        WHERE source = 'urban.seoul.go.kr'
          AND (stage IS NULL OR stage = '')
    """)
    db_zones_no_stage = cur.fetchall()
    log.info("DB stage 없는 구역: %d건", len(db_zones_no_stage))

    # 매칭
    matches = match_zones(all_cleanup, db_zones_no_stage)
    log.info("매칭 결과: %d건", len(matches))

    if args.dry_run:
        log.info("")
        log.info("[DRY-RUN] 매칭 샘플:")
        for m in matches[:30]:
            log.info("  %s [%s] <- %s -> %s",
                     m['db_name'], m['district'], m['cleanup_name'], m['new_stage'])
        cur.close()
        conn.close()
        return

    # DB 업데이트
    updated = 0
    for m in matches:
        cur.execute("UPDATE redevelopment_zones SET stage = %s WHERE id = %s",
                    (m['new_stage'], m['db_id']))
        if cur.rowcount > 0:
            updated += 1

    conn.commit()
    log.info("DB 업데이트: %d건", updated)

    # 최종 상태
    cur.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN stage IS NOT NULL AND stage != '' THEN 1 ELSE 0 END)
        FROM redevelopment_zones
    """)
    total, with_stage = cur.fetchone()
    log.info("최종: 총 %d건, stage 보유 %d건 (%d%%)",
             total, with_stage, with_stage * 100 // total if total else 0)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
