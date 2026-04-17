#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 5 Phase G-1 — 통합 검색 API.

GET /api/search/unified?q=...&lat=...&lon=...&limit=10

입력 패턴 자동 감지:
  - 좌표 "37.5, 127.1" → reverse geocoding (미구현, 후순위)
  - 한글 명사만 → 건물명 우선 (complex_master + aliases)
  - "동명 번지" (예: "신천동 17", "신천동 17-4") → 지번 우선
  - 도로명 + 번호 (예: "송파대로 567") → 도로명
  - 애매하면 3종 병렬 점수 기반 순위

응답:
{
  "query": "파크리",
  "detected_type": "complex_name",
  "results": [
    {"type":"complex", "label":"파크리오", "sublabel":"...", "icon":"🏢",
     "complex_pk":"...", "center":[lat,lon], "score":...},
    {"type":"jibun", "label":"...", "icon":"📍", "pnu":"...", "coords":[lat,lon], "score":...},
    {"type":"road",  "label":"...", "icon":"🛣️", "coords":[lat,lon], "score":...}
  ]
}

성능:
  - 우리 DB 3종 먼저 병렬 쿼리 (< 100ms 목표)
  - VWorld/카카오는 옵션 (지번/도로명 입력 시 async fallback)
  - 결과 LRU 캐시 (1000개 키)

의존:
  services.database_service.get_db_connection
  os.environ['VWORLD_APIKEY'] (선택)
"""
import json
import logging
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from collections import OrderedDict
from functools import lru_cache

from flask import Blueprint, jsonify, request
from psycopg2.extras import RealDictCursor

from services.database_service import get_db_connection

logger = logging.getLogger(__name__)

bp = Blueprint('search_unified', __name__, url_prefix='/api/search')


# ---------------------------------------------------------------------------
# 유틸: 입력 패턴 감지
# ---------------------------------------------------------------------------
RE_COORD = re.compile(r'^\s*(\d+\.\d+)\s*[,\s]\s*(\d+\.\d+)\s*$')
RE_DONG_BUN = re.compile(r'(\S+동)\s+(\d+)(?:-(\d+))?')
# 도로명: "...대로 123", "...길 45", "...로 67"
RE_ROAD = re.compile(r'(\S+(?:대로|로|길))\s+(\d+(?:-\d+)?)')
RE_HANGUL = re.compile(r'^[가-힣0-9\s]+$')


def detect_query_type(q):
    """
    입력 q에서 패턴 감지.
    반환: ('complex_name' | 'jibun' | 'road' | 'coord' | 'mixed', meta)
    """
    q_strip = q.strip()
    m = RE_COORD.match(q_strip)
    if m:
        return 'coord', {'lat': float(m.group(1)), 'lon': float(m.group(2))}

    if RE_ROAD.search(q_strip):
        return 'road', {}
    if RE_DONG_BUN.search(q_strip):
        return 'jibun', {}
    # 한글/숫자/공백으로만 구성되고 동+번지 아님 → 건물명 가능성 높음
    if RE_HANGUL.match(q_strip):
        return 'complex_name', {}
    return 'mixed', {}


# ---------------------------------------------------------------------------
# LRU 캐시 (key = q|limit)
# ---------------------------------------------------------------------------
_CACHE_MAX = 1000
_CACHE_TTL_SEC = 300  # 5분
_cache = OrderedDict()
_cache_lock = threading.Lock()


def cache_get(key):
    with _cache_lock:
        entry = _cache.get(key)
        if not entry:
            return None
        ts, val = entry
        if time.time() - ts > _CACHE_TTL_SEC:
            _cache.pop(key, None)
            return None
        _cache.move_to_end(key)
        return val


def cache_set(key, val):
    with _cache_lock:
        _cache[key] = (time.time(), val)
        if len(_cache) > _CACHE_MAX:
            _cache.popitem(last=False)


# ---------------------------------------------------------------------------
# 검색 소스 1: complex_master + aliases (trigram)
# ---------------------------------------------------------------------------
TYPE_NAME = {1: '아파트', 2: '연립', 3: '다세대'}


def _search_complexes(cur, q, limit=10):
    """
    complex_master.name 및 complex_aliases.name에 대해 trigram 유사도 검색.
    psycopg2: SQL 내 % 리터럴은 %%로 이스케이프.
    """
    try:
        cur.execute(
            """
            WITH hits AS (
                SELECT cm.complex_pk,
                       cm.name,
                       cm.address_jibun,
                       cm.household_count,
                       cm.dong_count,
                       cm.complex_type_code,
                       cm.center_lat,
                       cm.center_lon,
                       similarity(cm.name, %s) AS sim,
                       NULL::text AS match_alias
                FROM complex_master cm
                WHERE cm.name %% %s
                UNION ALL
                SELECT cm.complex_pk,
                       cm.name,
                       cm.address_jibun,
                       cm.household_count,
                       cm.dong_count,
                       cm.complex_type_code,
                       cm.center_lat,
                       cm.center_lon,
                       similarity(ca.name, %s) AS sim,
                       ca.name AS match_alias
                FROM complex_aliases ca
                JOIN complex_master cm ON ca.complex_pk = cm.complex_pk
                WHERE ca.name %% %s
            ),
            ranked AS (
                SELECT *,
                       row_number() OVER (
                           PARTITION BY complex_pk ORDER BY sim DESC NULLS LAST
                       ) AS rn
                FROM hits
            )
            SELECT complex_pk, name, address_jibun, household_count, dong_count,
                   complex_type_code, center_lat, center_lon, sim, match_alias
            FROM ranked
            WHERE rn = 1
            ORDER BY sim DESC NULLS LAST, household_count DESC NULLS LAST
            LIMIT %s
            """,
            (q, q, q, q, limit),
        )
        rows = cur.fetchall()
    except Exception as e:
        logger.warning('[search.complex] 실패: %s', e)
        return []

    out = []
    for r in rows:
        d = dict(r)
        type_name = TYPE_NAME.get(d.get('complex_type_code'), '')
        # 서브라벨 조립: "아파트 · 송파구 신천동 17 · 6864세대"
        sub_parts = []
        if type_name:
            sub_parts.append(type_name)
        if d.get('address_jibun'):
            sub_parts.append(d['address_jibun'])
        if d.get('household_count'):
            sub_parts.append(f"{d['household_count']}세대")
        center = None
        if d.get('center_lat') is not None and d.get('center_lon') is not None:
            center = [float(d['center_lat']), float(d['center_lon'])]
        out.append({
            'type': 'complex',
            'icon': '🏢',
            'label': d.get('name'),
            'sublabel': ' · '.join(sub_parts),
            'complex_pk': d.get('complex_pk'),
            'center': center,
            'match_alias': d.get('match_alias'),
            'household_count': d.get('household_count'),
            'score': float(d.get('sim') or 0),
        })
    return out


def _search_by_address_jibun(cur, q, limit=10):
    """
    지번/도로명 입력 시 complex_master.address_jibun/address_road 매칭.
    예: "신천동 17" → "서울특별시 송파구 신천동 17"을 주소로 갖는 단지(파크리오)
    """
    try:
        cur.execute(
            """
            SELECT complex_pk, name, address_jibun, address_road,
                   household_count, dong_count, complex_type_code,
                   center_lat, center_lon,
                   GREATEST(
                     similarity(address_jibun, %s),
                     COALESCE(similarity(address_road, %s), 0)
                   ) AS sim
            FROM complex_master
            WHERE address_jibun ILIKE %s
               OR address_road ILIKE %s
            ORDER BY sim DESC NULLS LAST, household_count DESC NULLS LAST
            LIMIT %s
            """,
            (q, q, f'%{q}%', f'%{q}%', limit),
        )
        rows = cur.fetchall()
    except Exception as e:
        logger.warning('[search.address_jibun] 실패: %s', e)
        return []

    out = []
    for r in rows:
        d = dict(r)
        type_name = TYPE_NAME.get(d.get('complex_type_code'), '')
        sub_parts = []
        if type_name:
            sub_parts.append(type_name)
        if d.get('address_jibun'):
            sub_parts.append(d['address_jibun'])
        if d.get('household_count'):
            sub_parts.append(f"{d['household_count']}세대")
        center = None
        if d.get('center_lat') is not None and d.get('center_lon') is not None:
            center = [float(d['center_lat']), float(d['center_lon'])]
        out.append({
            'type': 'complex',
            'icon': '🏢',
            'label': d.get('name'),
            'sublabel': ' · '.join(sub_parts),
            'complex_pk': d.get('complex_pk'),
            'center': center,
            'match_alias': None,
            'match_address': True,
            'household_count': d.get('household_count'),
            'score': float(d.get('sim') or 0),
        })
    return out


# ---------------------------------------------------------------------------
# 검색 소스 2: VWorld /req/address (지번/도로명)
# ---------------------------------------------------------------------------
VWORLD_APIKEY = os.environ.get('VWORLD_APIKEY', '')
VWORLD_GEOCODE_URL = 'https://api.vworld.kr/req/address'


def _vworld_address(q, addr_type='parcel', timeout=3):
    """VWorld 주소 → 좌표. addr_type: 'parcel'(지번) | 'road'(도로명)."""
    if not VWORLD_APIKEY:
        return None
    params = {
        'service': 'address',
        'request': 'getcoord',
        'version': '2.0',
        'crs': 'epsg:4326',
        'type': addr_type,
        'address': q,
        'format': 'json',
        'key': VWORLD_APIKEY,
    }
    url = VWORLD_GEOCODE_URL + '?' + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PropNet/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.debug('VWorld getCoord 실패 (%s): %s', q, e)
        return None

    if data.get('response', {}).get('status') != 'OK':
        return None
    try:
        pt = data['response']['result']['point']
        refined = data['response'].get('refined', {}).get('text') or q
        return {
            'label': refined,
            'lat': float(pt['y']),
            'lon': float(pt['x']),
            'addr_type': addr_type,
        }
    except (KeyError, TypeError, ValueError):
        return None


def _search_jibun(q):
    r = _vworld_address(q, addr_type='parcel')
    if not r:
        return []
    return [{
        'type': 'jibun',
        'icon': '📍',
        'label': r['label'],
        'sublabel': '지번 주소',
        'coords': [r['lat'], r['lon']],
        'score': 1.0,
    }]


def _search_road(q):
    r = _vworld_address(q, addr_type='road')
    if not r:
        return []
    return [{
        'type': 'road',
        'icon': '🛣️',
        'label': r['label'],
        'sublabel': '도로명 주소',
        'coords': [r['lat'], r['lon']],
        'score': 1.0,
    }]


# ---------------------------------------------------------------------------
# 통합 엔드포인트
# ---------------------------------------------------------------------------
@bp.get('/unified')
def unified():
    q = (request.args.get('q') or '').strip()
    limit = request.args.get('limit', 10, type=int)
    limit = min(max(limit, 1), 20)

    if len(q) < 2:
        return jsonify({
            'success': True,
            'query': q,
            'detected_type': 'too_short',
            'results': [],
        })

    cache_key = f'{q}|{limit}'
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached)

    detected_type, meta = detect_query_type(q)
    started = time.time()

    results = []

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1차: DB 단지 검색은 항상 수행 (가장 빠름)
                # 지번/도로명 입력이라도 complex_master.address_jibun에 매칭될 수 있음
                complex_hits = _search_complexes(cur, q, limit=limit)
                # 지번 패턴이면 complex_master.address_jibun ILIKE 검색도 추가
                if detected_type in ('jibun', 'road', 'mixed'):
                    addr_hits = _search_by_address_jibun(cur, q, limit=limit)
                    # complex_pk 중복 제거
                    existing_pks = {h.get('complex_pk') for h in complex_hits}
                    for h in addr_hits:
                        if h.get('complex_pk') not in existing_pks:
                            complex_hits.append(h)
    except Exception as e:
        logger.exception('[search.unified] DB 오류')
        complex_hits = []

    # 2차: 지번/도로명 (VWorld) — 감지된 타입에 따라
    jibun_hits = []
    road_hits = []
    if detected_type in ('jibun', 'mixed'):
        jibun_hits = _search_jibun(q)
    if detected_type in ('road', 'mixed'):
        road_hits = _search_road(q)

    # 좌표 직접 입력: 역지오코딩은 현 단계에서 skip, 좌표 자체를 결과로
    if detected_type == 'coord':
        results.append({
            'type': 'coord',
            'icon': '🎯',
            'label': f"{meta['lat']}, {meta['lon']}",
            'sublabel': '좌표',
            'coords': [meta['lat'], meta['lon']],
            'score': 1.0,
        })

    # 점수 기반 병합 — 건물명 우선 (detected_type 반영)
    if detected_type == 'complex_name':
        # 한글 명사는 건물명 가중치 1.5
        for h in complex_hits:
            h['score'] = h.get('score', 0) * 1.5
    elif detected_type == 'jibun':
        for h in jibun_hits:
            h['score'] = h.get('score', 0) * 1.5
    elif detected_type == 'road':
        for h in road_hits:
            h['score'] = h.get('score', 0) * 1.5

    results.extend(complex_hits)
    results.extend(jibun_hits)
    results.extend(road_hits)

    # 점수 내림차순 + limit
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    results = results[:limit]

    elapsed_ms = int((time.time() - started) * 1000)

    payload = {
        'success': True,
        'query': q,
        'detected_type': detected_type,
        'results': results,
        'elapsed_ms': elapsed_ms,
    }
    cache_set(cache_key, payload)
    return jsonify(payload)


# ---------------------------------------------------------------------------
# 빠른 자동완성 — 건물명만 (가장 빠른 경로)
# ---------------------------------------------------------------------------
@bp.get('/suggest')
def suggest():
    """경량 자동완성 (건물명만). UI 키 입력 debounce 250ms 용."""
    q = (request.args.get('q') or '').strip()
    limit = request.args.get('limit', 8, type=int)
    limit = min(max(limit, 1), 20)
    if len(q) < 2:
        return jsonify({'success': True, 'results': []})

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                hits = _search_complexes(cur, q, limit=limit)
    except Exception as e:
        logger.exception('[search.suggest] 오류')
        return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': True, 'results': hits})
