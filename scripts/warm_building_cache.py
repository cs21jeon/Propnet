#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
warm_building_cache.py — Week 3

모든 agent 매물 테이블에서 지번 유니크 추출 → get_buildings_by_pnu 호출
→ building_dong_geometry 캐시 저장 + 매물 레코드의 bd_mgt_sn / 좌표 업데이트.

Usage:
    # 드라이런 (실제 저장 없이 리포트만)
    python warm_building_cache.py --dry-run

    # 실제 실행
    python warm_building_cache.py

    # 특정 agent만
    python warm_building_cache.py --agent goldenrabbit

    # 동 매칭 실패 시 LdaregService 폴백 사용
    python warm_building_cache.py --fallback-ldareg

Env:
    VWORLD_APIKEY, PUBLIC_API_KEY, DATABASE_URL
    (또는 propsheet DB 접속 정보 — services.database_service 가 사용)

주의:
    - 이 스크립트는 서버 환경(`/home/webapp/goldenrabbit/backend/property-manager/`)
      에서 실행해야 함. 로컬에서는 DB/API 접속 불가.
    - 드라이런 먼저 실행하여 호출 횟수/실패 케이스 확인 후 실제 실행.
    - VWorld API는 일일 호출 제한 있으니 rate-limit 고려 (기본 0.5초 간격).
"""
import argparse
import logging
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

# 서버 실행 전제: /backend/property-manager/ 를 PYTHONPATH에 포함
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(HERE, '..', 'backend', 'property-manager'))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger('warm_building_cache')

try:
    from services.cadastral_service import CadastralService
    from services import cadastral_service_dong_ext  # noqa: F401 side-effect
    from services.database_service import get_db_connection
    try:
        from services.ldareg_service import LdaregService
    except Exception:
        LdaregService = None
except ImportError as e:
    logger.error(f'서버 환경에서 실행해야 합니다 (sys.path 설정 실패): {e}')
    sys.exit(1)


# ------- DB 헬퍼 -------

def list_agent_tables(conn) -> List[Tuple[str, str]]:
    """
    agent별 매물 테이블 목록 조회 (PropSheet 스키마 기준).
    Returns: [(agent_slug, table_name), ...]

    PropSheet 구조:
      - workspaces.slug = agent slug (예: goldenrabbit, silverrabbit, propnet)
      - databases.workspace_id → workspaces.id
      - databases.table_name = 실제 매물/상담 테이블명

    매물 성격의 테이블만 필터 (상담/문의/일정 등 제외):
      - propnet_single, propnet_multi_unit, propnet_part
      - silverrabbit_single, silverrabbit_multi_unit, silverrabbit_part
      - goldenrabbit01_sales_building, goldenrabbit01_sales_multi_unit
      - 패턴: *_single, *_multi_unit, *_part, *_sales_building, *_sales_multi_unit
    """
    PROPERTY_SUFFIXES = (
        '_single', '_multi_unit', '_part',
        '_sales_building', '_sales_multi_unit',
    )

    tables: List[Tuple[str, str]] = []
    seen = set()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT w.slug, d.table_name
              FROM databases d
              JOIN workspaces w ON d.workspace_id = w.id
             WHERE d.table_name IS NOT NULL
               AND w.slug IS NOT NULL
               AND w.slug <> 'template'
             ORDER BY w.slug, d.display_order
        """)
        for slug, table_name in cur.fetchall():
            if not table_name or not slug:
                continue
            # 매물 테이블만 필터
            if not any(table_name.endswith(suf) for suf in PROPERTY_SUFFIXES):
                continue
            # 실제 존재 여부 확인
            key = (slug, table_name)
            if key in seen:
                continue
            seen.add(key)
            # 테이블 존재 확인
            cur.execute("""
                SELECT 1 FROM information_schema.tables
                 WHERE table_schema='public' AND table_name=%s
            """, (table_name,))
            if cur.fetchone():
                tables.append((slug, table_name))

    return tables


def list_jibuns_from_table(conn, table_name: str) -> List[Tuple[str, str]]:
    """
    테이블에서 (지번주소, 동) 유니크 조회.
    - 컬럼명은 agent마다 다를 수 있으니 information_schema로 먼저 감지.
    Returns: [(jibun_addr, dong), ...]
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
             WHERE table_schema='public' AND table_name=%s
        """, (table_name,))
        cols = {r[0] for r in cur.fetchall()}

    jibun_col = None
    for candidate in ('지번 주소', '지번주소', 'jibun_address', 'jibun', '주소_지번', '지번'):
        if candidate in cols:
            jibun_col = candidate
            break
    if not jibun_col:
        return []

    dong_col = None
    for candidate in ('동', 'dong', 'dong_name', '동명', '동/호', '동 번호', '동번호'):
        if candidate in cols:
            dong_col = candidate
            break

    cols_select = f'"{jibun_col}"' + (f', "{dong_col}"' if dong_col else ', NULL')
    sql = f'SELECT DISTINCT {cols_select} FROM "{table_name}" WHERE "{jibun_col}" IS NOT NULL AND "{jibun_col}" <> \'\''
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return [(r[0], r[1] or '') for r in rows]


# ------- PNU 헬퍼 -------

_SEOUL_GUS = {
    '종로구','중구','용산구','성동구','광진구','동대문구','중랑구','성북구','강북구','도봉구',
    '노원구','은평구','서대문구','마포구','양천구','강서구','구로구','금천구','영등포구','동작구',
    '관악구','서초구','강남구','송파구','강동구',
}

def _normalize_address(addr: str) -> str:
    """
    지번주소 정규화: '동작구 상도동 499-19' → '서울특별시 동작구 상도동 499-19'
    - 첫 토큰이 서울 자치구이면 '서울특별시' prefix 추가
    - 이미 '서울특별시', '경기도' 등 광역 prefix가 있으면 그대로 반환
    """
    if not addr:
        return addr
    addr = addr.strip()
    tokens = addr.split()
    if not tokens:
        return addr
    first = tokens[0]
    # 이미 광역 단위 포함
    if first.endswith(('특별시', '광역시', '특별자치시', '특별자치도', '도')):
        return addr
    # 서울 자치구로 시작하면 서울특별시 prefix
    if first in _SEOUL_GUS:
        return '서울특별시 ' + addr
    # 기타(경기도 성남시 등 생략된 경우)는 원본 유지
    return addr


def jibun_to_pnu(cadastral: CadastralService, jibun_addr: str) -> Optional[str]:
    """
    지번주소 → PNU 19자리

    VWorld /addrlink getCoord 응답의 `refined.structure.level4LC` 가 19자리 PNU.
    (level4LC = 법정동코드 10자리 + 산여부 1자리 + 본번 4자리 + 부번 4자리)

    주소 정규화 (광역시 prefix 보강) 후 재시도.
    """
    # 1차: 기존 메서드 (CadastralService에 구현돼 있을 수 있음)
    for method_name in ('get_pnu_by_address', 'pnu_by_address', 'address_to_pnu'):
        m = getattr(cadastral, method_name, None)
        if callable(m):
            try:
                res = m(jibun_addr)
                pnu = res.get('pnu') if isinstance(res, dict) else res
                if pnu and len(pnu) == 19:
                    return pnu
            except Exception as e:
                logger.debug(f'{method_name} 실패: {e}')

    vworld_key = os.getenv('VWORLD_APIKEY')
    if not vworld_key:
        return None
    import requests

    # 2차: 정규화한 주소로 addrlink 호출
    candidates = []
    normalized = _normalize_address(jibun_addr)
    if normalized and normalized != jibun_addr:
        candidates.append(normalized)
    candidates.append(jibun_addr)

    for addr in candidates:
        try:
            resp = requests.get('https://api.vworld.kr/req/address', params={
                'service': 'address',
                'request': 'getCoord',
                'version': '2.0',
                'crs': 'epsg:4326',
                'address': addr,
                'type': 'PARCEL',
                'format': 'json',
                'key': vworld_key,
            }, timeout=15)
            body = resp.json()
            response = body.get('response', {}) or {}
            if (response.get('status') or '').upper() != 'OK':
                continue
            structure = ((response.get('refined') or {}).get('structure') or {})
            pnu = structure.get('level4LC')
            if pnu and len(pnu) == 19:
                return pnu
        except Exception as e:
            logger.debug(f'addrlink 실패 ({addr}): {e}')
    return None


# ------- 메인 로직 -------

def warm_cache(agents_filter: Optional[str] = None,
               dry_run: bool = False,
               rate_limit: float = 0.5,
               fallback_ldareg: bool = False) -> Dict:
    """
    Returns: 리포트 dict
    """
    stats = {
        'tables_total': 0,
        'jibun_total': 0,
        'pnu_resolved': 0,
        'pnu_failed': 0,
        'dongs_cached': 0,
        'records_updated': 0,
        'errors': [],
    }

    cadastral = CadastralService()
    ldareg = LdaregService() if (LdaregService and fallback_ldareg) else None

    with get_db_connection() as conn:
        tables = list_agent_tables(conn)
        if agents_filter:
            tables = [t for t in tables if t[0] == agents_filter]
        stats['tables_total'] = len(tables)
        logger.info(f'대상 테이블 {len(tables)}개')

        for slug, table_name in tables:
            logger.info(f'--- agent={slug} table={table_name} ---')
            jibuns = list_jibuns_from_table(conn, table_name)
            stats['jibun_total'] += len(jibuns)
            logger.info(f'  유니크 지번: {len(jibuns)}건')

            # 지번 유니크 (동 제외)
            unique_jibuns = sorted({j[0] for j in jibuns})
            logger.info(f'  PNU 해석 대상: {len(unique_jibuns)}건')

            pnu_map: Dict[str, str] = {}
            for jibun in unique_jibuns:
                pnu = jibun_to_pnu(cadastral, jibun)
                if pnu:
                    pnu_map[jibun] = pnu
                    stats['pnu_resolved'] += 1
                else:
                    stats['pnu_failed'] += 1
                time.sleep(rate_limit)

            # PNU별로 get_buildings_by_pnu 호출
            for jibun, pnu in pnu_map.items():
                try:
                    res = cadastral.get_buildings_by_pnu(pnu, address=jibun)
                    if not res.get('success'):
                        stats['errors'].append(f'{slug}/{jibun}: {res.get("error")}')
                        # Ldareg 폴백
                        if ldareg:
                            ld = ldareg.get_dong_list(pnu)
                            if ld.get('success') and ld.get('dong_list'):
                                logger.info(f'    Ldareg 폴백 {len(ld["dong_list"])}개 동')
                        continue

                    dongs = res.get('dongs', [])
                    stats['dongs_cached'] += len(dongs)
                    logger.info(f'  pnu={pnu} jibun={jibun} dongs={len(dongs)}')

                    if dry_run:
                        continue

                    # 캐시 저장은 /map/dong-coords 경로에서 이미 하지만, 여기서는 직접 저장
                    for d in dongs:
                        bd_mgt_sn = d.get('bd_mgt_sn')
                        if not bd_mgt_sn:
                            continue
                        cadastral.cache_building_geometry(
                            bd_mgt_sn=bd_mgt_sn,
                            pnu=d.get('pnu') or pnu,
                            dong_nm=d.get('dong_nm'),
                            bld_nm=d.get('bld_nm'),
                            lat=d['lat'],
                            lon=d['lon'],
                            geometry=d.get('geometry'),
                            grnd_flr=d.get('grnd_flr'),
                            archarea=d.get('archarea'),
                            raw_data=None,
                        )

                    # 매물 레코드 동 필드 → bd_mgt_sn 매칭 + 좌표 업데이트
                    updated = update_records_with_dong(
                        conn, table_name, jibun, dongs, dry_run=dry_run, stats=stats
                    )
                    stats['records_updated'] += updated

                except Exception as e:
                    logger.exception(f'    에러 ({slug}/{jibun}): {e}')
                    stats['errors'].append(f'{slug}/{jibun}: {e}')
                time.sleep(rate_limit)

    return stats


# ------- Week 4: 동/건물명 정규화 유틸 -------

_EMPTY_DONG_TOKENS = {
    '', '동 없음', '동없음', '없음', '-', 'n/a', 'N/A', 'na', 'NA', 'none', 'None',
    '.', '_', '0', '없음동',
}


def _normalize_dong(raw) -> Tuple[str, Optional[int]]:
    """
    동 필드 정규화.
    Returns: (canonical_str, digit_int_or_None)
      - canonical_str: 비교용 표준 문자열 ('103동', 'A동', '비동' 등). 빈 문자열이면 '동 정보 없음'.
      - digit_int_or_None: 숫자부만 추출. 없으면 None.
    """
    if raw is None:
        return '', None
    s = str(raw)
    # 반각/전각 통일 (전각 숫자 → 반각)
    s = s.replace('０', '0').replace('１', '1').replace('２', '2').replace('３', '3').replace('４', '4') \
         .replace('５', '5').replace('６', '6').replace('７', '7').replace('８', '8').replace('９', '9')
    # 공백 정리 (모든 공백 trim + 내부 중복 공백 정리)
    s = s.strip()
    # 유의미 empty 판정
    s_lower = s.lower()
    if s_lower in _EMPTY_DONG_TOKENS or s.strip() == '':
        return '', None
    # 숫자부 추출 (예: '103', '103동', 'A103', '103-1동' 등)
    digit_match = re.search(r'\d+', s)
    digit_int: Optional[int] = int(digit_match.group()) if digit_match else None
    # 표준 형태: 이미 '동'으로 끝나면 유지, 숫자만이면 '동' 붙이기
    if s.endswith('동'):
        canon = s
    elif digit_int is not None and re.fullmatch(r'\d+', s):
        canon = f'{digit_int}동'
    else:
        canon = s  # 'A동', '비동' 등 특수형은 유지
    return canon, digit_int


def _normalize_name(raw) -> str:
    """건물명/기타 텍스트 정규화 (trim + 내부 공백 유지)."""
    if raw is None:
        return ''
    s = str(raw).strip()
    # 양쪽 공백 제거 (내부 공백은 유지)
    return s


def _match_dong(rec_dong, dongs: List[dict]) -> Optional[dict]:
    """
    정교화된 동 매칭 로직.
    1단계: 정규화된 동 문자열 완전일치
    2단계: 숫자부만 추출하여 매칭 ('103' ↔ '103동')
    3단계: 단일 동(동이 1개뿐)인 경우 자동 매칭
    Returns: 매칭된 dong dict 또는 None
    """
    rec_canon, rec_digit = _normalize_dong(rec_dong)

    # dongs 전처리: canonical/digit 인덱스 구축
    dong_entries = []
    for d in dongs:
        name = d.get('dong_nm') or d.get('bld_nm') or ''
        canon, digit = _normalize_dong(name)
        dong_entries.append({
            'dong': d,
            'canon': canon,
            'digit': digit,
            'raw': name,
        })

    # 1단계: canonical 완전일치
    if rec_canon:
        for e in dong_entries:
            if e['canon'] and e['canon'] == rec_canon:
                return e['dong']

    # 2단계: 숫자부 일치 (양쪽 다 숫자 있을 때만)
    if rec_digit is not None:
        digit_matches = [e for e in dong_entries if e['digit'] == rec_digit]
        if len(digit_matches) == 1:
            return digit_matches[0]['dong']
        # 숫자 같은 게 여러 개면 모호 → 매칭 실패
        if len(digit_matches) > 1:
            logger.debug(f'    동 숫자매칭 모호: {rec_dong}(digit={rec_digit}) → 후보 {len(digit_matches)}개')

    # 3단계: 동 레코드 필드 비어있거나 매칭 실패 + dongs가 정확히 1개뿐이면 단일 건물로 간주
    if len(dongs) == 1:
        return dongs[0]

    # 4단계(신규): 동 필드가 비어있고 단일동 아님 → 건물명이 유일한 경우 bld_nm으로 매칭 시도
    # (상위 레이어에서 building_name을 넘기는 구조가 아니므로 생략)

    return None


def update_records_with_dong(conn, table_name: str, jibun: str,
                              dongs: List[dict], dry_run: bool = False,
                              stats: Optional[dict] = None) -> int:
    """
    같은 지번의 매물 레코드들에 대해 정교화된 동 매칭 → bd_mgt_sn + lat/lon 덮어쓰기.

    Week 4 변경점 (C안):
      - `bd_mgt_sn IS NULL` 조건 제거 → 이미 매칭된 건도 재매칭 (좌표 덮어쓰기)
      - 동 필드 정규화 (None/'동 없음'/' ' → 빈 문자열, '103' ↔ '103동')
      - 건물명 trim
      - 좌표 변경 전후 거리 로깅 (stats['large_changes'])
    """
    if not dongs:
        return 0

    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
             WHERE table_schema='public' AND table_name=%s
        """, (table_name,))
        cols = {r[0] for r in cur.fetchall()}

    if 'bd_mgt_sn' not in cols:
        logger.warning(f'    {table_name}: bd_mgt_sn 컬럼 없음 — 스킵')
        return 0

    jibun_col = None
    for candidate in ('지번 주소', '지번주소', 'jibun_address', 'jibun', '지번'):
        if candidate in cols:
            jibun_col = candidate
            break
    dong_col = None
    for candidate in ('동', 'dong', 'dong_name', '동명', '동/호'):
        if candidate in cols:
            dong_col = candidate
            break
    if not jibun_col:
        return 0

    # 좌표 컬럼
    lat_col = None
    for candidate in ('coordinates_lat', 'lat', 'latitude'):
        if candidate in cols:
            lat_col = candidate
            break
    lon_col = None
    for candidate in ('coordinates_lon', 'lon', 'lng', 'longitude'):
        if candidate in cols:
            lon_col = candidate
            break

    id_col = 'id' if 'id' in cols else ('record_id' if 'record_id' in cols else None)
    if not id_col:
        return 0

    # C안: bd_mgt_sn IS NULL 조건 제거 → 전체 레코드 재매칭 (좌표 덮어쓰기)
    select_cols = [f'"{id_col}"']
    if dong_col:
        select_cols.append(f'"{dong_col}"')
    else:
        select_cols.append('NULL')
    if lat_col:
        select_cols.append(f'"{lat_col}"')
    else:
        select_cols.append('NULL')
    if lon_col:
        select_cols.append(f'"{lon_col}"')
    else:
        select_cols.append('NULL')

    sql = f'SELECT {", ".join(select_cols)} FROM "{table_name}" WHERE "{jibun_col}" = %s'

    with conn.cursor() as cur:
        cur.execute(sql, (jibun,))
        rows = cur.fetchall()

    updated = 0
    for row in rows:
        rid = row[0]
        rec_dong = row[1]
        old_lat = row[2]
        old_lon = row[3]

        matched = _match_dong(rec_dong, dongs)
        if not matched:
            if stats is not None:
                stats.setdefault('match_fail_samples', []).append(
                    f'{table_name}/{jibun}/dong={rec_dong!r} (dongs={len(dongs)})'
                )
                stats['match_fail'] = stats.get('match_fail', 0) + 1
            continue

        if stats is not None:
            stats['match_ok'] = stats.get('match_ok', 0) + 1

        # 좌표 변경 거리 계산
        new_lat = matched.get('lat')
        new_lon = matched.get('lon')
        if old_lat is not None and old_lon is not None and new_lat is not None and new_lon is not None:
            try:
                dlat = float(new_lat) - float(old_lat)
                dlon = float(new_lon) - float(old_lon)
                # 대략 m 단위 (1도 위도 ~= 111km, 경도는 cos 보정 필요하지만 서울 기준 약 89km)
                approx_m = ((dlat * 111000) ** 2 + (dlon * 89000) ** 2) ** 0.5
                if approx_m > 100 and stats is not None:
                    stats.setdefault('large_changes', []).append(
                        f'{table_name}/id={rid}/jibun={jibun}: {approx_m:.0f}m '
                        f'({old_lat:.6f},{old_lon:.6f} → {new_lat:.6f},{new_lon:.6f})'
                    )
                if stats is not None:
                    stats['total_change_m'] = stats.get('total_change_m', 0) + approx_m
                    stats['change_count'] = stats.get('change_count', 0) + 1
            except Exception:
                pass

        updates = ['"bd_mgt_sn" = %s']
        params = [matched.get('bd_mgt_sn')]
        if lat_col:
            updates.append(f'"{lat_col}" = %s')
            params.append(new_lat)
        if lon_col:
            updates.append(f'"{lon_col}" = %s')
            params.append(new_lon)
        params.append(rid)

        update_sql = f'UPDATE "{table_name}" SET {", ".join(updates)} WHERE "{id_col}" = %s'
        if dry_run:
            logger.info(f'    [DRY] {update_sql} params={params}')
            updated += 1
        else:
            try:
                with conn.cursor() as cur:
                    cur.execute(update_sql, params)
                conn.commit()
                updated += 1
            except Exception as e:
                conn.rollback()
                logger.error(f'    update 실패 (id={rid}): {e}')
    return updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='실제 DB 변경 없이 리포트만')
    parser.add_argument('--agent', default=None, help='특정 agent slug만 처리')
    parser.add_argument('--rate-limit', type=float, default=0.5, help='VWorld API 호출 간격 (초)')
    parser.add_argument('--fallback-ldareg', action='store_true', help='동 매칭 실패 시 NSDI LdaregService 폴백')
    args = parser.parse_args()

    logger.info(f'=== warm_building_cache 시작 (dry_run={args.dry_run}, agent={args.agent}) ===')
    stats = warm_cache(
        agents_filter=args.agent,
        dry_run=args.dry_run,
        rate_limit=args.rate_limit,
        fallback_ldareg=args.fallback_ldareg,
    )
    logger.info('=== 완료 ===')
    logger.info(f'대상 테이블: {stats["tables_total"]}')
    logger.info(f'유니크 지번: {stats["jibun_total"]}')
    logger.info(f'PNU 해석 성공: {stats["pnu_resolved"]}')
    logger.info(f'PNU 해석 실패: {stats["pnu_failed"]}')
    logger.info(f'캐시된 동 수: {stats["dongs_cached"]}')
    logger.info(f'업데이트된 레코드: {stats["records_updated"]}')
    logger.info(f'매칭 성공: {stats.get("match_ok", 0)}')
    logger.info(f'매칭 실패: {stats.get("match_fail", 0)}')
    if stats.get('change_count'):
        avg = stats.get('total_change_m', 0) / stats['change_count']
        logger.info(f'좌표 변경 평균: {avg:.1f}m (총 {stats["change_count"]}건)')
    if stats.get('large_changes'):
        logger.warning(f'큰 좌표 변경 (>100m) {len(stats["large_changes"])}건:')
        for e in stats['large_changes'][:30]:
            logger.warning(f'  {e}')
    if stats.get('match_fail_samples'):
        logger.info(f'매칭 실패 샘플 {min(30, len(stats["match_fail_samples"]))}건:')
        for e in stats['match_fail_samples'][:30]:
            logger.info(f'  {e}')
    if stats['errors']:
        logger.warning(f'에러 {len(stats["errors"])}건:')
        for e in stats['errors'][:20]:
            logger.warning(f'  {e}')
    return 0 if not stats['errors'] else 1


if __name__ == '__main__':
    sys.exit(main())
