"""
매물 데이터 Enrichment Service — Phase 1.

매물 좌표(lat/lon) 기반으로 주변 정보를 자동 계산하여 property_enrichment 테이블에 저장.

Phase 1 범위:
  - 최근접 지하철역 3개 + 거리(m) + 도보시간(분)
  - 반경 1km 이내 학교(초/중/고) 목록 + 거리

트리거 시점:
  - 매물 저장/수정 시 (propsheet_save_service.save_property 후 호출)
  - 관리용 일괄 enrichment 스크립트

Haversine 공식으로 직선거리 계산 (외부 API 호출 없음, 서버 부담 최소).
"""

from __future__ import annotations

import json
import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

# 도보 속도 근사: 80m/분
WALK_SPEED_M_PER_MIN = 80.0

# Phase 1 설정
NEAREST_SUBWAY_COUNT = 3
SCHOOL_RADIUS_M = 1000.0

# 인메모리 캐시 (서버 기동 시 1회 로드, ~2MB)
_subway_cache: list[dict] | None = None
_school_cache: list[dict] | None = None


# -----------------------------------------------------------------------------
# Haversine
# -----------------------------------------------------------------------------

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 GPS 좌표 간 직선거리(미터). Haversine 공식."""
    lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    R = 6_371_000  # 지구 반지름 (m)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# -----------------------------------------------------------------------------
# 캐시 로드
# -----------------------------------------------------------------------------

def _load_subway_cache(conn) -> list[dict]:
    """subway_stations 테이블 전체를 인메모리 캐시로 로드."""
    global _subway_cache
    if _subway_cache is not None:
        return _subway_cache
    with conn.cursor() as cur:
        cur.execute("SELECT station_name, line_name, lat, lon FROM subway_stations")
        rows = cur.fetchall()
    _subway_cache = [
        {"name": r[0], "line": r[1], "lat": r[2], "lon": r[3]}
        for r in rows
    ]
    logger.info("subway_cache loaded: %d stations", len(_subway_cache))
    return _subway_cache


def _load_school_cache(conn) -> list[dict]:
    """schools 테이블 전체를 인메모리 캐시로 로드."""
    global _school_cache
    if _school_cache is not None:
        return _school_cache
    with conn.cursor() as cur:
        cur.execute(
            "SELECT school_name, school_type, lat, lon, student_count "
            "FROM schools WHERE lat IS NOT NULL AND lon IS NOT NULL"
        )
        rows = cur.fetchall()
    _school_cache = [
        {"name": r[0], "type": r[1], "lat": r[2], "lon": r[3], "student_count": r[4]}
        for r in rows
    ]
    logger.info("school_cache loaded: %d schools", len(_school_cache))
    return _school_cache


def invalidate_caches():
    """데이터 갱신 후 캐시 무효화 (관리 스크립트용)."""
    global _subway_cache, _school_cache
    _subway_cache = None
    _school_cache = None


# -----------------------------------------------------------------------------
# 계산 로직
# -----------------------------------------------------------------------------

def find_nearest_subways(
    lat: float, lon: float, stations: list[dict], count: int = NEAREST_SUBWAY_COUNT
) -> list[dict]:
    """좌표 기준 가장 가까운 지하철역 N개 반환."""
    dists = []
    for s in stations:
        d = haversine_m(lat, lon, s["lat"], s["lon"])
        dists.append({
            "name": s["name"],
            "line": s["line"],
            "distance_m": round(d),
            "walk_min": round(d / WALK_SPEED_M_PER_MIN, 1),
        })
    dists.sort(key=lambda x: x["distance_m"])
    return dists[:count]


def find_nearby_schools(
    lat: float, lon: float, schools: list[dict], radius_m: float = SCHOOL_RADIUS_M
) -> list[dict]:
    """좌표 기준 반경 내 학교 목록 반환 (거리순 정렬)."""
    results = []
    for s in schools:
        d = haversine_m(lat, lon, s["lat"], s["lon"])
        if d <= radius_m:
            results.append({
                "name": s["name"],
                "type": s["type"],
                "distance_m": round(d),
                "student_count": s.get("student_count"),
            })
    results.sort(key=lambda x: x["distance_m"])
    return results


# -----------------------------------------------------------------------------
# Enrichment 실행
# -----------------------------------------------------------------------------

def enrich_property(conn, record_id: str, db_id: int, lat: float, lon: float) -> dict | None:
    """단일 매물에 대해 enrichment 계산 후 DB 저장.

    Args:
        conn: psycopg2 connection (autocommit이 아닌 경우 caller가 commit)
        record_id: PropSheet record_id (예: 'rec_abc123')
        db_id: database_id (38, 39, 43)
        lat, lon: 매물 좌표

    Returns:
        enrichment dict 또는 None (좌표 없는 경우)
    """
    if lat is None or lon is None:
        return None

    try:
        stations = _load_subway_cache(conn)
        schools = _load_school_cache(conn)
    except Exception as e:
        logger.warning("enrichment cache load failed (tables may not exist yet): %s", e)
        return None

    if not stations and not schools:
        logger.debug("enrichment skipped: no station/school data loaded")
        return None

    nearest_subway = find_nearest_subways(lat, lon, stations) if stations else []
    nearby_schools = find_nearby_schools(lat, lon, schools) if schools else []

    enrichment = {
        "nearest_subway": nearest_subway,
        "nearby_schools": nearby_schools,
    }

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO property_enrichment
                    (record_id, db_id, nearest_subway, nearby_schools, enriched_at)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, NOW())
                ON CONFLICT (record_id, db_id) DO UPDATE SET
                    nearest_subway = EXCLUDED.nearest_subway,
                    nearby_schools = EXCLUDED.nearby_schools,
                    enriched_at = NOW()
                """,
                (
                    record_id,
                    db_id,
                    json.dumps(nearest_subway, ensure_ascii=False),
                    json.dumps(nearby_schools, ensure_ascii=False),
                ),
            )
        logger.info(
            "enrichment saved: %s (db=%d) subway=%d schools=%d",
            record_id, db_id, len(nearest_subway), len(nearby_schools),
        )
    except Exception as e:
        # enrichment 실패가 매물 저장을 막으면 안 됨
        logger.warning("enrichment save failed (non-fatal): %s", e)

    return enrichment


def enrich_all(conn, batch_size: int = 100) -> dict[str, int]:
    """기존 매물 전체에 대해 일괄 enrichment 실행.

    좌표가 있지만 enrichment가 없는(또는 오래된) 매물 대상.
    """
    from .ai_search_service import PROPERTY_TABLES

    total = 0
    enriched = 0
    skipped = 0

    for table, scope, db_id in PROPERTY_TABLES:
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT record_id, coordinates_lat, coordinates_lon
                    FROM "{table}"
                    WHERE coordinates_lat IS NOT NULL
                      AND coordinates_lon IS NOT NULL
                      AND record_id NOT IN (
                          SELECT record_id FROM property_enrichment WHERE db_id = %s
                      )
                    LIMIT %s
                """, (db_id, batch_size))
                rows = cur.fetchall()

            for rid, lat, lon in rows:
                total += 1
                result = enrich_property(conn, rid, db_id, lat, lon)
                if result:
                    enriched += 1
                else:
                    skipped += 1

            conn.commit()
        except Exception as e:
            logger.error("enrich_all failed for table %s: %s", table, e)
            conn.rollback()

    logger.info("enrich_all done: total=%d enriched=%d skipped=%d", total, enriched, skipped)
    return {"total": total, "enriched": enriched, "skipped": skipped}


def get_enrichment(conn, record_id: str, db_id: int) -> dict[str, Any] | None:
    """매물의 enrichment 데이터 조회."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT nearest_subway, nearby_schools, enriched_at
            FROM property_enrichment
            WHERE record_id = %s AND db_id = %s
            """,
            (record_id, db_id),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "nearest_subway": row[0] or [],
        "nearby_schools": row[1] or [],
        "enriched_at": str(row[2]) if row[2] else None,
    }


__all__ = [
    "haversine_m",
    "enrich_property",
    "enrich_all",
    "get_enrichment",
    "invalidate_caches",
    "find_nearest_subways",
    "find_nearby_schools",
]
