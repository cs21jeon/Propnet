#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 5 — 공동주택 단지 마스터 API (complex_master)

엔드포인트:
  GET  /api/complex/lookup?complex_pk=...
  GET  /api/complex/lookup?pnu=...
  GET  /api/complex/lookup?lat=...&lon=...&radius_m=500
  GET  /api/complex/search?q=파크리&limit=10
  GET  /api/complex/<complex_pk>/properties?agent_slug=goldenrabbit01

의존:
  services.database_service.get_db_connection
"""
import logging
from flask import Blueprint, jsonify, request
from psycopg2.extras import RealDictCursor

from services.database_service import get_db_connection

logger = logging.getLogger(__name__)

bp = Blueprint('complex', __name__, url_prefix='/api/complex')


# ---------------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------------
TYPE_NAME = {1: '아파트', 2: '연립', 3: '다세대'}


def _serialize_master(row):
    """complex_master 행을 API 응답으로 직렬화."""
    if not row:
        return None
    result = dict(row)
    # 날짜/NUMERIC 등 직렬화
    if result.get('completion_date'):
        result['completion_date'] = result['completion_date'].isoformat()
    if result.get('center_lat') is not None:
        result['center_lat'] = float(result['center_lat'])
    if result.get('center_lon') is not None:
        result['center_lon'] = float(result['center_lon'])
    if result.get('confidence') is not None:
        result['confidence'] = float(result['confidence'])
    result['complex_type_name'] = TYPE_NAME.get(result.get('complex_type_code'))
    # updated_at/created_at 는 iso 포맷
    for k in ('created_at', 'updated_at'):
        if result.get(k):
            result[k] = result[k].isoformat()
    # raw_row는 숨김 (감사용)
    result.pop('raw_row', None)
    return result


def _fetch_full_complex(cur, complex_pk):
    """complex_master + aliases + parcels 전체 조회."""
    cur.execute(
        "SELECT * FROM complex_master WHERE complex_pk = %s",
        (complex_pk,),
    )
    master = cur.fetchone()
    if not master:
        return None

    cur.execute(
        """SELECT alias_type, name, year, source
           FROM complex_aliases
           WHERE complex_pk = %s
           ORDER BY alias_type, year NULLS FIRST""",
        (complex_pk,),
    )
    aliases = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """SELECT pnu, is_primary, jibun, source, confidence
           FROM complex_parcels
           WHERE complex_pk = %s
           ORDER BY is_primary DESC, confidence DESC""",
        (complex_pk,),
    )
    parcels = []
    for r in cur.fetchall():
        p = dict(r)
        if p.get('confidence') is not None:
            p['confidence'] = float(p['confidence'])
        parcels.append(p)

    result = _serialize_master(master)
    result['aliases'] = aliases
    result['parcels'] = parcels
    return result


# ---------------------------------------------------------------------------
# GET /api/complex/lookup
# ---------------------------------------------------------------------------
@bp.get('/lookup')
def lookup():
    complex_pk = (request.args.get('complex_pk') or '').strip()
    pnu = (request.args.get('pnu') or '').strip()
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius_m = request.args.get('radius_m', 500, type=int)

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1) complex_pk 직접 조회
                if complex_pk:
                    data = _fetch_full_complex(cur, complex_pk)
                    if not data:
                        return jsonify({'success': False, 'error': 'not found'}), 404
                    return jsonify({'success': True, 'complex': data})

                # 2) pnu → complex_pk
                if pnu:
                    cur.execute(
                        """SELECT complex_pk FROM complex_parcels
                           WHERE pnu = %s
                           ORDER BY is_primary DESC, confidence DESC
                           LIMIT 1""",
                        (pnu,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return jsonify({'success': False, 'error': 'pnu not matched'}), 404
                    data = _fetch_full_complex(cur, row['complex_pk'])
                    return jsonify({'success': True, 'complex': data})

                # 3) 좌표 반경 조회 (center_lat/lon 보강된 단지만)
                if lat is not None and lon is not None:
                    # BBOX 근사
                    dlat = radius_m / 111000.0
                    dlon = radius_m / (111000.0 * 0.79)
                    cur.execute(
                        """SELECT cm.*,
                                  2 * 6371000 * asin(sqrt(
                                    power(sin(radians((cm.center_lat - %s) / 2)), 2) +
                                    cos(radians(%s)) * cos(radians(cm.center_lat)) *
                                    power(sin(radians((cm.center_lon - %s) / 2)), 2)
                                  )) AS distance_m
                           FROM complex_master cm
                           WHERE cm.center_lat IS NOT NULL
                             AND cm.center_lat BETWEEN %s AND %s
                             AND cm.center_lon BETWEEN %s AND %s
                           ORDER BY distance_m ASC
                           LIMIT 20""",
                        (lat, lat, lon,
                         lat - dlat, lat + dlat,
                         lon - dlon, lon + dlon),
                    )
                    rows = cur.fetchall()
                    results = []
                    for r in rows:
                        d = _serialize_master(r)
                        d['distance_m'] = float(r['distance_m']) if r.get('distance_m') is not None else None
                        results.append(d)
                    return jsonify({'success': True, 'results': results})

                return jsonify({
                    'success': False,
                    'error': 'complex_pk, pnu or (lat,lon) required',
                }), 400

    except Exception as e:
        logger.exception('[complex.lookup] error')
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# GET /api/complex/search
# ---------------------------------------------------------------------------
@bp.get('/search')
def search():
    q = (request.args.get('q') or '').strip()
    limit = request.args.get('limit', 10, type=int)
    if len(q) < 2:
        return jsonify({'success': True, 'results': []})

    # 안전 상한
    limit = min(max(limit, 1), 50)

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # trigram similarity 기반. % 연산자는 psycopg2에서 %% 이스케이프
                # alias 검색 결과와 master 검색 결과를 UNION하되,
                # complex_pk 기준 최고 유사도만 남김
                cur.execute(
                    """
                    WITH master_hits AS (
                        SELECT cm.complex_pk, cm.name, cm.address_jibun,
                               cm.household_count, cm.dong_count,
                               cm.complex_type_code,
                               NULL::text AS match_alias_type,
                               NULL::text AS match_alias_name,
                               similarity(cm.name, %s) AS sim
                        FROM complex_master cm
                        WHERE cm.name %% %s
                    ),
                    alias_hits AS (
                        SELECT cm.complex_pk, cm.name, cm.address_jibun,
                               cm.household_count, cm.dong_count,
                               cm.complex_type_code,
                               ca.alias_type AS match_alias_type,
                               ca.name AS match_alias_name,
                               similarity(ca.name, %s) AS sim
                        FROM complex_aliases ca
                        JOIN complex_master cm ON ca.complex_pk = cm.complex_pk
                        WHERE ca.name %% %s
                    ),
                    all_hits AS (
                        SELECT * FROM master_hits
                        UNION ALL
                        SELECT * FROM alias_hits
                    ),
                    ranked AS (
                        SELECT *,
                               row_number() OVER (PARTITION BY complex_pk ORDER BY sim DESC) AS rn
                        FROM all_hits
                    )
                    SELECT complex_pk, name, address_jibun, household_count, dong_count,
                           complex_type_code, match_alias_type, match_alias_name, sim
                    FROM ranked
                    WHERE rn = 1
                    ORDER BY sim DESC
                    LIMIT %s
                    """,
                    (q, q, q, q, limit),
                )
                rows = cur.fetchall()

        results = []
        for r in rows:
            d = dict(r)
            d['similarity'] = float(d.pop('sim'))
            d['complex_type_name'] = TYPE_NAME.get(d.get('complex_type_code'))
            # match_alias 구조화
            if d.get('match_alias_type'):
                d['match_alias'] = {
                    'type': d.pop('match_alias_type'),
                    'name': d.pop('match_alias_name'),
                }
            else:
                d.pop('match_alias_type', None)
                d.pop('match_alias_name', None)
                d['match_alias'] = None
            results.append(d)

        return jsonify({'success': True, 'results': results, 'query': q})

    except Exception as e:
        logger.exception('[complex.search] error')
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# GET /api/complex/<complex_pk>/properties
# ---------------------------------------------------------------------------
@bp.get('/<complex_pk>/properties')
def properties(complex_pk):
    """
    해당 단지에 등록된 매물 조회.
    현 단계: {agent}_sales_* 테이블에 complex_pk 컬럼이 아직 없으므로
    complex_parcels의 pnu로 매칭. 추후 FK 추가되면 쿼리 전환.
    """
    agent_slug = (request.args.get('agent_slug') or 'goldenrabbit01').strip()
    # 간단한 slug validation
    if not agent_slug.replace('_', '').isalnum():
        return jsonify({'success': False, 'error': 'invalid agent_slug'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # PNU 목록
                cur.execute(
                    "SELECT pnu FROM complex_parcels WHERE complex_pk = %s",
                    (complex_pk,),
                )
                pnus = [r['pnu'] for r in cur.fetchall()]
                if not pnus:
                    return jsonify({'success': False, 'error': 'complex not found'}), 404

                building_table = agent_slug + '_sales_building'
                multi_table = agent_slug + '_sales_multi_unit'

                # 테이블 존재 확인
                cur.execute(
                    """SELECT tablename FROM pg_tables
                       WHERE schemaname='public' AND tablename IN (%s, %s)""",
                    (building_table, multi_table),
                )
                existing = {r['tablename'] for r in cur.fetchall()}

                results = {'building': [], 'multi_unit': []}

                for tbl_name, key in ((building_table, 'building'), (multi_table, 'multi_unit')):
                    if tbl_name not in existing:
                        continue
                    try:
                        cur.execute(
                            # pnu 컬럼이 있다고 가정. 없으면 try/except로 skip
                            f"SELECT * FROM {tbl_name} WHERE pnu = ANY(%s) LIMIT 100",
                            (pnus,),
                        )
                        results[key] = [dict(r) for r in cur.fetchall()]
                    except Exception as e:
                        logger.warning(
                            '[complex.properties] %s 조회 실패: %s', tbl_name, e
                        )
                        conn.rollback()

        return jsonify({
            'success': True,
            'complex_pk': complex_pk,
            'agent_slug': agent_slug,
            'pnus': pnus,
            'counts': {k: len(v) for k, v in results.items()},
            'properties': results,
        })

    except Exception as e:
        logger.exception('[complex.properties] error')
        return jsonify({'success': False, 'error': str(e)}), 500
