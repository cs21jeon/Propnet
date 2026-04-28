"""
PropMap AI 매물 검색 — 3-stage 파이프라인.

Stage 1: PostgreSQL Hard Filter (3개 매물 테이블 UNION ALL)
Stage 2: Python Soft Scoring + 이상치 penalty
Stage 3: Claude Sonnet Rerank + 이유 생성

환각 방어
- Stage 3가 반환하는 record_id는 반드시 Stage 2 후보 리스트에 존재해야 한다.
- 일치하지 않으면 invalid_record_ids 배열에 모아 caller(route)에서 재시도/거절 결정.

psycopg2 % 이스케이프 규칙 (CLAUDE.md 규칙 6)
- 필드명에 `%` 포함: "건폐율(%)", "용적률(%)", "융자제외수익률(%)"
- SQL 내 리터럴 `%`는 `%%`로 이스케이프 필수.
"""

from __future__ import annotations

import json
import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from . import ai_outlier_detector as outlier

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# 상수
# -----------------------------------------------------------------------------

PROPERTY_TABLES = [
    # (table_name, scope, db_id)
    ("goldenrabbit01_sales_building", "building", 39),
    ("goldenrabbit01_sales_multi_unit", "unit", 38),
    ("sales_building_copy", "building_copy", 43),
]

STAGE1_HARD_CAP = 500  # Stage 1 결과 상한 — 초과 시 clarify 유도
STAGE2_TOPK = 30  # Stage 3에 넘길 후보 수
STAGE3_TOPK_DEFAULT = 5  # 최종 반환 매물 수

DEFAULT_MODEL = "claude-sonnet-4-6"

# AI 검색에서 절대 접근 금지하는 DB 컬럼 (3개 매물 테이블 공통 적용)
# Stage 1 SQL SELECT에 포함 금지 + _sanitize_row()에서 2차 제거
AI_BLOCKED_COLUMNS: frozenset[str] = frozenset({
    # -- 소유자 PII --
    "소유자명",
    "소유주연락처",
    "소유자주소",
    "소유자생년월일",
    # -- 내부 운영 --
    "비공개메모",
    "홍보문구",
    "상단고정 홍보문구",
    "하단고정 홍보문구",
    "사진링크",
    "건축물대장",
    "네이버",
    "문의",
    "대표",
    "주인세대",
    "주인거주",
    "사진필요",
    "SH가능",
    # -- 시스템 --
    "fields_hash",
    "synced_at",
})


def _sanitize_row(row: dict[str, Any]) -> dict[str, Any]:
    """AI 파이프라인 결과에서 차단 컬럼을 제거하는 방어 레이어."""
    return {k: v for k, v in row.items() if k not in AI_BLOCKED_COLUMNS}


# -----------------------------------------------------------------------------
# 데이터클래스
# -----------------------------------------------------------------------------


@dataclass
class SearchSlots:
    """LLM-2에서 추출한 검색 조건 슬롯."""

    transaction_type: str | None = None  # 매매/전세/월세
    property_types: list[str] = field(default_factory=list)
    regions: list[dict[str, Any]] = field(default_factory=list)
    budget_min: int | None = None
    budget_max: int | None = None
    budget_target: int | None = None
    area_min: float | None = None
    area_max: float | None = None
    area_target: float | None = None
    room_count_min: int | None = None
    yield_min_pct: float | None = None
    priority: str | None = None  # price/yield/location/area/freshness
    keywords: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)
    purpose: str | None = None
    confidence: float = 0.0

    @classmethod
    def from_tool_input(cls, data: dict[str, Any]) -> "SearchSlots":
        budget = data.get("budget_manwon") or {}
        area = data.get("area_pyeong") or {}
        return cls(
            transaction_type=data.get("transaction_type"),
            property_types=list(data.get("property_types") or []),
            regions=list(data.get("regions") or []),
            budget_min=budget.get("min"),
            budget_max=budget.get("max"),
            budget_target=budget.get("target"),
            area_min=area.get("min"),
            area_max=area.get("max"),
            area_target=area.get("target"),
            room_count_min=data.get("room_count_min"),
            yield_min_pct=data.get("yield_min_pct"),
            priority=data.get("priority"),
            keywords=list(data.get("keywords") or []),
            exclude_keywords=list(data.get("exclude_keywords") or []),
            purpose=data.get("purpose"),
            confidence=float(data.get("confidence") or 0.0),
        )


# -----------------------------------------------------------------------------
# Stage 1: SQL Hard Filter
# -----------------------------------------------------------------------------


def _build_stage1_sql(slots: SearchSlots) -> tuple[str, list[Any]]:
    """3개 매물 테이블을 UNION ALL로 묶어 hard filter를 적용하는 SQL 생성.

    주의: 아래 SQL의 리터럴 `%`는 모두 `%%`로 이스케이프되어 있다.
    """
    txn = slots.transaction_type
    budget_min = slots.budget_min
    budget_max = slots.budget_max

    region_likes: list[str] = []
    region_params: list[str] = []
    for r in slots.regions:
        raw = (r.get("raw") or "").strip()
        if raw:
            region_likes.append('"지번 주소" ILIKE %s')
            region_params.append(f"%{raw}%")

    region_clause = f"AND ({' OR '.join(region_likes)})" if region_likes else ""

    property_type_clause = ""
    property_type_params: list[str] = []
    if slots.property_types:
        placeholders = ",".join(["%s"] * len(slots.property_types))
        property_type_clause = f'AND "부동산 유형" IN ({placeholders})'
        property_type_params = list(slots.property_types)

    txn_clause = ""
    txn_params: list[str] = []
    if txn:
        txn_clause = 'AND "거래 유형" = %s'
        txn_params = [txn]

    budget_clause = ""
    budget_params: list[int] = []
    if budget_min is not None:
        budget_clause += ' AND "매가(만원)" >= %s'
        budget_params.append(int(budget_min))
    if budget_max is not None:
        budget_clause += ' AND "매가(만원)" <= %s'
        budget_params.append(int(budget_max))

    yield_clause = ""
    yield_params: list[float] = []
    if slots.yield_min_pct is not None:
        # 컬럼명에 % 포함 -> 리터럴 이스케이프.
        yield_clause = 'AND "융자제외수익률(%%)" >= %s'
        yield_params = [float(slots.yield_min_pct)]

    exclude_clause = (
        'AND "건폐율(%%)" IS NULL OR "건폐율(%%)" <= 100 '
        'AND ("용적률(%%)" IS NULL OR "용적률(%%)" <= 2000) '
    )

    sub_queries: list[str] = []
    params_all: list[Any] = []
    for table, scope, db_id in PROPERTY_TABLES:
        sub = f"""
            SELECT
                %s::text                         AS record_id,
                %s::int                          AS db_id,
                %s::text                         AS scope,
                record_id                        AS rid_raw,
                "지번 주소"                      AS addr,
                "부동산 유형"                    AS property_type,
                "거래 유형"                      AS transaction_type,
                "매가(만원)"                     AS price_manwon,
                "융자제외수익률(%%)"             AS yield_pct,
                "건폐율(%%)"                     AS coverage_ratio_pct,
                "용적률(%%)"                     AS floor_area_ratio_pct,
                coordinates_lat                  AS lat,
                coordinates_lon                  AS lon,
                "대표사진"                       AS photo_url,
                "광고"                           AS ad_text,
                created_at                       AS created_at,
                updated_at                       AS updated_at
            FROM {table}
            WHERE status = '등록'
              AND coordinates_lat IS NOT NULL
              AND coordinates_lon IS NOT NULL
              AND "매가(만원)" IS NOT NULL
              AND "매가(만원)" > 0
              AND "대표사진" IS NOT NULL
              AND "광고" IS NOT NULL
              {txn_clause}
              {budget_clause}
              {property_type_clause}
              {region_clause}
              {yield_clause}
        """
        # record_id placeholder는 '<db_id>:<record_id>' 조합 — 아래 SELECT에서 text로 만드는 값
        # 여기서는 단순히 db_id/table/scope만 파라미터로 넣고, rid_raw에서 실제 record_id를 재조립.
        sub_queries.append(sub)
        params_all.extend([
            f"table-{table}",  # record_id placeholder(나중에 rid_raw로 덮어씀)
            db_id,
            scope,
        ])
        params_all.extend(txn_params)
        params_all.extend(budget_params)
        params_all.extend(property_type_params)
        params_all.extend(region_params)
        params_all.extend(yield_params)

    sql = (
        "SELECT * FROM ("
        + " UNION ALL ".join(f"({q})" for q in sub_queries)
        + f") t LIMIT {STAGE1_HARD_CAP + 1}"
    )
    return sql, params_all


def run_stage1(conn, slots: SearchSlots) -> dict[str, Any]:
    """Stage 1: DB hard filter.

    Returns {"rows": [...], "overflow": bool, "count": int}
    overflow=True 이면 조건이 너무 넓어 STAGE1_HARD_CAP 초과. clarify 유도.
    """
    sql, params = _build_stage1_sql(slots)
    t0 = time.time()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        columns = [c.name for c in cur.description]
        raw = cur.fetchall()

    rows: list[dict[str, Any]] = []
    for row in raw:
        d = dict(zip(columns, row))
        # record_id 조합: '<db_id>:<rid_raw>' 형태.
        d["record_id"] = f"{d['db_id']}:{d.get('rid_raw')}"
        rows.append(d)

    overflow = len(rows) > STAGE1_HARD_CAP
    if overflow:
        rows = rows[:STAGE1_HARD_CAP]

    # 차단 컬럼 제거 (SQL SELECT에 없어야 하지만 방어적으로 2차 제거)
    rows = [_sanitize_row(r) for r in rows]

    # Hard exclude (건폐율/용적률 등) — SQL 에서 대부분 거른 상태이지만 2차 방어.
    filtered: list[dict[str, Any]] = []
    for r in rows:
        flags = outlier.hard_exclude(r)
        if flags:
            continue
        filtered.append(r)

    logger.info(
        "stage1 count=%d (overflow=%s) hard_excluded=%d elapsed_ms=%d",
        len(filtered),
        overflow,
        len(rows) - len(filtered),
        int((time.time() - t0) * 1000),
    )
    return {"rows": filtered, "overflow": overflow, "count": len(filtered)}


# -----------------------------------------------------------------------------
# Stage 2: Soft Scoring
# -----------------------------------------------------------------------------


def _gauss_fit(value: float | None, target: float | None, sigma: float) -> float:
    """가우시안 근접도. value/target None 이면 0."""
    if value is None or target is None or sigma <= 0:
        return 0.0
    diff = (float(value) - float(target)) / float(sigma)
    return math.exp(-0.5 * diff * diff)


def _price_fit(price: float | None, slots: SearchSlots) -> float:
    if price is None:
        return 0.0
    target = slots.budget_target
    if target is None and slots.budget_min and slots.budget_max:
        target = (slots.budget_min + slots.budget_max) / 2
    if target is None:
        return 0.5
    sigma = max((slots.budget_max or target) - (slots.budget_min or target), target * 0.2)
    return _gauss_fit(price, target, sigma)


def _area_fit(area: float | None, slots: SearchSlots) -> float:
    if area is None:
        return 0.0
    target = slots.area_target
    if target is None and slots.area_min and slots.area_max:
        target = (slots.area_min + slots.area_max) / 2
    if target is None:
        return 0.5
    sigma = max((slots.area_max or target) - (slots.area_min or target), target * 0.2)
    return _gauss_fit(area, target, sigma)


def _yield_fit(y: float | None, min_pct: float | None) -> float:
    if y is None:
        return 0.0
    if min_pct is None:
        return 0.5
    if y < min_pct:
        return max(0.0, y / min_pct)
    # 초과할수록 서서히 증가, 15%p 초과는 의심(이상치로도 걸림).
    excess = y - min_pct
    return min(1.0, 0.6 + excess / 15.0 * 0.4)


def _location_fit(addr: str | None, slots: SearchSlots) -> float:
    if not addr or not slots.regions:
        return 0.0
    hits = 0
    total = 0
    for r in slots.regions:
        raw = (r.get("raw") or "").strip()
        if not raw:
            continue
        total += 1
        if raw in addr:
            hits += 1
    return hits / total if total else 0.0


def _freshness(updated_at) -> float:
    if not updated_at:
        return 0.0
    try:
        age_days = (time.time() - updated_at.timestamp()) / 86400.0
    except Exception:
        return 0.0
    # 7일 반감기
    return math.exp(-age_days / 7.0)


def _photo_bonus(photo_url: str | None) -> float:
    if not photo_url:
        return 0.0
    # 쉼표/개행 구분 다중 사진이면 더 높게 (엄밀한 카운트는 아님).
    parts = [p for p in (photo_url or "").replace("\n", ",").split(",") if p.strip()]
    return min(1.0, len(parts) / 3.0)


def _weights_for_priority(priority: str | None) -> dict[str, float]:
    base = {
        "price": 0.25,
        "area": 0.15,
        "location": 0.25,
        "yield": 0.15,
        "freshness": 0.10,
        "photo": 0.05,
        "popularity": 0.05,
    }
    if priority == "price":
        base.update({"price": 0.40, "location": 0.20, "area": 0.10})
    elif priority == "yield":
        base.update({"yield": 0.35, "price": 0.20, "location": 0.15})
    elif priority == "location":
        base.update({"location": 0.40, "price": 0.20, "area": 0.10})
    elif priority == "area":
        base.update({"area": 0.30, "price": 0.25, "location": 0.20})
    elif priority == "freshness":
        base.update({"freshness": 0.25, "price": 0.20, "location": 0.20})
    # 합 1.0 정규화
    total = sum(base.values())
    return {k: v / total for k, v in base.items()}


def run_stage2(stage1_rows: list[dict[str, Any]], slots: SearchSlots) -> list[dict[str, Any]]:
    """Stage 2: Python scoring + outlier annotation. 상위 STAGE2_TOPK 반환."""
    w = _weights_for_priority(slots.priority)

    # price_per_pyeong 없으면 근사치 계산 (area_pyeong 있는 경우만).
    for r in stage1_rows:
        price = r.get("price_manwon")
        area = r.get("area_pyeong") or r.get("gross_area_pyeong") or r.get("exclusive_area_pyeong")
        if isinstance(price, (int, float)) and isinstance(area, (int, float)) and area > 0:
            r["price_per_pyeong_manwon"] = price / area

        # sigungu 추출 (주소 첫 2 토큰)
        addr = r.get("addr") or ""
        tokens = addr.split()
        r["sigungu"] = " ".join(tokens[:2]) if len(tokens) >= 2 else (tokens[0] if tokens else None)

    outlier.annotate_outliers(stage1_rows)

    scored: list[dict[str, Any]] = []
    for r in stage1_rows:
        price_fit = _price_fit(r.get("price_manwon"), slots)
        area_fit = _area_fit(
            r.get("area_pyeong") or r.get("gross_area_pyeong") or r.get("exclusive_area_pyeong"),
            slots,
        )
        location_fit = _location_fit(r.get("addr"), slots)
        yield_fit = _yield_fit(r.get("yield_pct"), slots.yield_min_pct)
        fresh = _freshness(r.get("updated_at"))
        photo = _photo_bonus(r.get("photo_url"))
        popularity = 0.0  # Phase 2에서 property_view_events로 채움.

        raw_score = (
            w["price"] * price_fit
            + w["area"] * area_fit
            + w["location"] * location_fit
            + w["yield"] * yield_fit
            + w["freshness"] * fresh
            + w["photo"] * photo
            + w["popularity"] * popularity
        )
        penalty = outlier.outlier_penalty(r.get("outlier_flags") or [])
        score = max(0.0, raw_score - penalty)

        r_out = {
            **r,
            "score": score,
            "score_breakdown": {
                "price_fit": price_fit,
                "area_fit": area_fit,
                "location_fit": location_fit,
                "yield_fit": yield_fit,
                "freshness": fresh,
                "photo": photo,
                "popularity": popularity,
                "penalty": penalty,
            },
        }
        scored.append(r_out)

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:STAGE2_TOPK]
    logger.info("stage2 top=%d (from %d)", len(top), len(scored))
    return top


# -----------------------------------------------------------------------------
# Stage 3: Claude Sonnet Rerank
# -----------------------------------------------------------------------------


def _make_candidate_payload(stage2_top: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from ..prompts.ai_search_prompts import format_candidate_for_rerank
    return [format_candidate_for_rerank(c) for c in stage2_top]


def run_stage3(
    anthropic_client,
    stage2_top: list[dict[str, Any]],
    slots: SearchSlots,
    user_query: str,
    *,
    model: str = DEFAULT_MODEL,
    top_k: int = STAGE3_TOPK_DEFAULT,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Claude Sonnet Tool Use로 재랭킹.

    환각 방어: 반환된 record_id가 stage2_top에 없으면 invalid_record_ids에 모아 caller가 처리.
    """
    from ..prompts.ai_search_prompts import RERANK_SYSTEM_PROMPT, RERANK_TOOL

    valid_ids = {c["record_id"] for c in stage2_top}
    payload = _make_candidate_payload(stage2_top)

    user_message = json.dumps(
        {
            "user_query": user_query[:1000],
            "slots": {
                "transaction_type": slots.transaction_type,
                "property_types": slots.property_types,
                "regions": [r.get("raw") for r in slots.regions],
                "budget_manwon": {
                    "min": slots.budget_min,
                    "max": slots.budget_max,
                    "target": slots.budget_target,
                },
                "priority": slots.priority,
                "purpose": slots.purpose,
            },
            "candidates": payload,
            "instruction": f"상위 {top_k}개까지 선택. 후보가 부족하면 적게 반환.",
        },
        ensure_ascii=False,
    )

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = anthropic_client.messages.create(
                model=model,
                max_tokens=2000,
                system=RERANK_SYSTEM_PROMPT,
                tools=[RERANK_TOOL],
                tool_choice={"type": "tool", "name": RERANK_TOOL["name"]},
                messages=[{"role": "user", "content": user_message}],
            )
        except Exception as e:  # noqa: BLE001
            last_error = e
            wait = 2 ** (attempt + 1)
            logger.warning("stage3 attempt %d failed: %s (retry in %ds)", attempt + 1, e, wait)
            time.sleep(wait)
            continue

        tool_input = None
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                tool_input = block.input
                break
        if not tool_input:
            last_error = RuntimeError("no tool_use block")
            continue

        selections = tool_input.get("selections") or []
        invalid = [s for s in selections if s.get("record_id") not in valid_ids]
        if invalid:
            logger.warning("stage3 returned invalid record_ids: %s", [s.get("record_id") for s in invalid])
            # 즉시 거절 대신 필터만 적용.
            selections = [s for s in selections if s.get("record_id") in valid_ids]

        selections = selections[:top_k]
        return {
            "selections": selections,
            "summary": tool_input.get("summary") or "",
            "missing_info_hint": tool_input.get("missing_info_hint"),
            "model": model,
            "usage": {
                "input_tokens": getattr(resp.usage, "input_tokens", 0) if hasattr(resp, "usage") else 0,
                "output_tokens": getattr(resp.usage, "output_tokens", 0) if hasattr(resp, "usage") else 0,
            },
            "invalid_record_ids": [s.get("record_id") for s in invalid] if invalid else [],
        }

    # fallback: 규칙 기반 (점수 상위 top_k 그대로).
    logger.error("stage3 all retries failed: %s — fallback to stage2 scores", last_error)
    fallback_sel = []
    for idx, c in enumerate(stage2_top[:top_k]):
        fallback_sel.append({
            "record_id": c["record_id"],
            "db_id": c["db_id"],
            "rank": idx + 1,
            "reason": "LLM 응답 실패로 점수 기준 상위 매물을 노출합니다.",
            "warnings": list(c.get("outlier_flags") or []),
        })
    return {
        "selections": fallback_sel,
        "summary": "AI 응답에 일시적 장애가 있어 기본 점수 순으로 보여드립니다.",
        "missing_info_hint": None,
        "model": model,
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "invalid_record_ids": [],
        "fallback": True,
    }


# -----------------------------------------------------------------------------
# 통합 파이프라인
# -----------------------------------------------------------------------------


def run_full_pipeline(
    conn,
    anthropic_client,
    slots: SearchSlots,
    user_query: str,
    *,
    model: str = DEFAULT_MODEL,
    top_k: int = STAGE3_TOPK_DEFAULT,
) -> dict[str, Any]:
    """Stage 1 → 2 → 3 을 순서대로 실행."""
    stage1 = run_stage1(conn, slots)
    if stage1["overflow"]:
        return {
            "status": "too_broad",
            "stage1_count": stage1["count"],
            "message": "검색 조건이 너무 넓습니다. 지역이나 예산을 더 좁혀 주세요.",
        }
    if stage1["count"] == 0:
        return {
            "status": "no_result",
            "stage1_count": 0,
            "message": "조건에 맞는 매물이 없습니다. 조건을 완화해 보세요.",
        }

    stage2_top = run_stage2(stage1["rows"], slots)
    stage3 = run_stage3(
        anthropic_client,
        stage2_top,
        slots,
        user_query,
        model=model,
        top_k=top_k,
    )

    return {
        "status": "ok",
        "stage1_count": stage1["count"],
        "stage2_top": stage2_top,
        "stage3": stage3,
    }


__all__ = [
    "SearchSlots",
    "run_stage1",
    "run_stage2",
    "run_stage3",
    "run_full_pipeline",
    "STAGE1_HARD_CAP",
    "STAGE2_TOPK",
    "STAGE3_TOPK_DEFAULT",
    "DEFAULT_MODEL",
    "AI_BLOCKED_COLUMNS",
]
