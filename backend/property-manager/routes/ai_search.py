"""
PropMap AI 매물 검색 Blueprint (Agentic 아키텍처).

경로 (app.py 에서 url_prefix='/api' 로 등록)
  POST /api/ai/session   : 세션 생성
  POST /api/ai/chat      : Agentic 대화 턴 (tool-use 포함)
  POST /api/ai/feedback  : 추천 결과 피드백
  POST /api/ai/view      : 조회 이벤트 기록 (로그인/비로그인 모두)

접근 제어 (Phase 0)
- 사전 토큰(X-AI-Test-Token 헤더 또는 ?k=<token>) 또는 propnet admin 쿠키.
- 비관리자는 403, 토큰 없으면 401.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from functools import wraps

from flask import Blueprint, g, jsonify, request

sys.path.insert(0, '/home/webapp/goldenrabbit/backend/shared')
from propnet_auth.jwt_utils import verify_token  # noqa: E402

from services import ai_agent_service as agent_service  # noqa: E402
from services import ai_billing_service as ai_billing  # noqa: E402
from services.database_service import get_db_connection  # noqa: E402

logger = logging.getLogger(__name__)

bp = Blueprint("ai_search", __name__)

# -----------------------------------------------------------------------------
# 접근 제어
# -----------------------------------------------------------------------------

AI_TEST_TOKEN = os.environ.get('AI_TEST_TOKEN') or '9834e1186f504a19e61d8e93b292148c'
AI_TEST_SENTINEL_UID = 0


def ai_access_required(fn):
    """테스트 토큰 OR propnet 로그인 허용. g.propnet_user_id, g.propnet_role 설정."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        test_token = request.headers.get('X-AI-Test-Token') or request.args.get('k')
        if test_token and test_token == AI_TEST_TOKEN:
            g.propnet_user_id = AI_TEST_SENTINEL_UID
            g.propnet_role = 'admin'
            g.ai_test_mode = True
            return fn(*args, **kwargs)

        token = request.cookies.get('propnet_token')
        if not token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
        if not token:
            return jsonify({'error': 'unauthorized'}), 401
        try:
            payload = verify_token(token, expected_type='access')
        except Exception:
            payload = None
        if not payload:
            return jsonify({'error': 'unauthorized'}), 401
        g.propnet_user_id = payload.get('sub')
        g.propnet_role = payload.get('role', 'user')
        g.ai_test_mode = False
        return fn(*args, **kwargs)
    return wrapper


def _anthropic_client():
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("anthropic SDK not installed") from e
    api_key = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("CLAUDE_API_KEY not configured")
    return anthropic.Anthropic(api_key=api_key)


def _extract_viewer_uid():
    token = request.cookies.get('propnet_token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
    if not token:
        return None
    try:
        payload = verify_token(token, expected_type='access')
        if payload:
            return payload.get('sub')
    except Exception:
        return None
    return None


# -----------------------------------------------------------------------------
# 세션 헬퍼
# -----------------------------------------------------------------------------

def _load_session(cur, session_id, propnet_uid):
    cur.execute(
        """
        SELECT session_id, propnet_uid, state, turn_count, slots_json,
               total_tokens_in, total_tokens_out
        FROM ai_search_sessions
        WHERE session_id = %s AND propnet_uid = %s
        """,
        (session_id, propnet_uid),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "session_id": row[0],
        "propnet_uid": row[1],
        "state": row[2],
        "turn_count": row[3],
        "slots_json": row[4] or {},
        "total_tokens_in": row[5],
        "total_tokens_out": row[6],
    }


def _save_log(cur, session_id, turn_index, role, text, model=None, tin=0, tout=0, latency_ms=None):
    cur.execute(
        """
        INSERT INTO ai_search_logs
            (session_id, turn_index, role, text, model, tokens_in, tokens_out, latency_ms)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (session_id, turn_index, role, text, model, tin, tout, latency_ms),
    )


# -----------------------------------------------------------------------------
# POST /api/ai/session
# -----------------------------------------------------------------------------

@bp.route("/ai/session", methods=["POST"])
@ai_access_required
def create_session():
    body = request.get_json(silent=True) or {}
    source = (body.get("source") or "web").strip()[:16]

    session_id = str(uuid.uuid4())
    uid = g.propnet_user_id
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_search_sessions
                        (session_id, propnet_uid, source, state, slots_json, user_agent_snapshot)
                    VALUES (%s, %s, %s, 'INIT', '{}'::jsonb, %s)
                    """,
                    (
                        session_id,
                        uid,
                        source,
                        (request.headers.get("User-Agent") or "")[:500],
                    ),
                )
            conn.commit()
    except Exception as e:
        logger.exception("create_session failed")
        return jsonify({"error": "db_error", "detail": str(e)}), 500

    return jsonify({"session_id": session_id, "state": "INIT"})


# -----------------------------------------------------------------------------
# POST /api/ai/chat
# -----------------------------------------------------------------------------

# 과거 messages 를 얼마나 보관할지 (토큰 비용 관리)
MAX_HISTORY_MESSAGES = 24
MAX_TURNS_PER_SESSION = 8  # 세션당 최대 턴 수 (API 비용 방지)


@bp.route("/ai/chat", methods=["POST"])
@ai_access_required
def post_chat():
    body = request.get_json(silent=True) or {}
    session_id = (body.get("session_id") or "").strip()
    user_text = (body.get("text") or "").strip()
    if not session_id or not user_text:
        return jsonify({"error": "bad_request", "detail": "session_id/text required"}), 400
    if len(user_text) > 1000:
        return jsonify({"error": "bad_request", "detail": "text too long (max 1000)"}), 400

    uid = g.propnet_user_id
    role = getattr(g, 'propnet_role', None)

    # --- 크레딧 사전 체크 (admin/test_mode는 무제한) ---
    if not getattr(g, 'ai_test_mode', False):
        with get_db_connection() as check_conn:
            with check_conn.cursor() as check_cur:
                credit_check = ai_billing.check_can_search(check_cur, uid, role=role)
        if not credit_check['ok']:
            return jsonify({
                'error': 'no_credits',
                'detail': '크레딧이 부족합니다',
                'remaining': 0,
            }), 402

    try:
        client = _anthropic_client()
    except RuntimeError as e:
        return jsonify({"error": "config_error", "detail": str(e)}), 500

    with get_db_connection() as conn:
        # 1) 세션 로드 + 사용자 메시지 로그
        with conn.cursor() as cur:
            sess = _load_session(cur, session_id, uid)
            if not sess:
                return jsonify({"error": "session_not_found"}), 404
            turn_index = sess["turn_count"] + 1

            # --- 세션 턴 상한 체크 (API 비용 방지) ---
            if turn_index > MAX_TURNS_PER_SESSION and role != "admin" and not getattr(g, "ai_test_mode", False):
                return jsonify({
                    "error": "session_limit",
                    "detail": "이 대화의 최대 질문 횟수에 도달했습니다. 새 검색을 시작해 주세요.",
                    "turn_limit": MAX_TURNS_PER_SESSION,
                }), 429

            _save_log(cur, session_id, turn_index, "user", user_text)
        conn.commit()

        # 2) 이전 messages 복원 (slots_json.messages 에 보관)
        stored = sess["slots_json"] or {}
        prior_messages = stored.get("messages") or []
        if len(prior_messages) > MAX_HISTORY_MESSAGES:
            prior_messages = prior_messages[-MAX_HISTORY_MESSAGES:]
        messages = list(prior_messages)
        messages.append({"role": "user", "content": user_text})

        # 3) Agent loop
        result = agent_service.run_agent_turn(client, conn, messages)

        # 4) 상태 갱신
        updated_slots = dict(stored)
        # messages 는 tool_use/tool_result 블록 포함 — 너무 길어지지 않도록 캡
        msgs_to_store = result["messages"]
        if len(msgs_to_store) > MAX_HISTORY_MESSAGES:
            msgs_to_store = msgs_to_store[-MAX_HISTORY_MESSAGES:]
        updated_slots["messages"] = msgs_to_store

        recs = result.get("recommendations")
        new_state = "RANKED" if recs and recs.get("selections") else "GATHERING"
        if result.get("stopped") == "error":
            new_state = "ERROR"

        with conn.cursor() as cur:
            _save_log(
                cur, session_id, turn_index, "assistant",
                result["assistant_text"],
                model=agent_service.DEFAULT_MODEL,
                tin=result["usage"]["input_tokens"],
                tout=result["usage"]["output_tokens"],
            )
            # tool 로그도 저장 (디버깅용)
            for tl in result.get("tool_log") or []:
                _save_log(
                    cur, session_id, turn_index, "tool",
                    json.dumps({
                        "tool": tl.get("tool"),
                        "input": tl.get("input"),
                        "result_preview": tl.get("result_preview"),
                    }, ensure_ascii=False, default=str),
                    model=agent_service.DEFAULT_MODEL,
                )
            cur.execute(
                """
                UPDATE ai_search_sessions
                SET turn_count = %s,
                    slots_json = %s::jsonb,
                    state = %s,
                    total_tokens_in = total_tokens_in + %s,
                    total_tokens_out = total_tokens_out + %s,
                    updated_at = NOW()
                WHERE session_id = %s
                """,
                (
                    turn_index,
                    json.dumps(updated_slots, ensure_ascii=False, default=str),
                    new_state,
                    result["usage"]["input_tokens"],
                    result["usage"]["output_tokens"],
                    session_id,
                ),
            )
            if recs and recs.get("selections"):
                sels = recs["selections"]
                cur.execute(
                    """
                    INSERT INTO ai_search_results
                        (session_id, stage, record_ids, db_ids, scores, meta_json)
                    VALUES (%s, 'agent', %s, %s, %s, %s::jsonb)
                    """,
                    (
                        session_id,
                        [s["record_id"] for s in sels],
                        [int(s["db_id"]) for s in sels],
                        [float(s.get("rank", 0)) for s in sels],
                        json.dumps({
                            "summary": recs.get("summary", ""),
                            "rejected": recs.get("rejected") or [],
                        }, ensure_ascii=False),
                    ),
                )
        # --- 크레딧 차감: 추천 결과 성공 시 ---
        credit_after = None
        if recs and recs.get("selections") and not getattr(g, 'ai_test_mode', False):
            with conn.cursor() as deduct_cur:
                credit_after = ai_billing.deduct_credit(
                    deduct_cur, uid, session_id, role=role
                )

        conn.commit()

    return jsonify({
        "assistant_text": result["assistant_text"],
        "recommendations": result.get("recommendations"),
        "credit_after": credit_after,
        "tool_log": [
            {"tool": tl.get("tool"), "input": tl.get("input"), "result_preview": tl.get("result_preview")}
            for tl in (result.get("tool_log") or [])
        ],
        "turn_index": turn_index,
        "iterations": result.get("iterations"),
        "stopped": result.get("stopped"),
        "usage": result.get("usage"),
    })


# -----------------------------------------------------------------------------
# POST /api/ai/feedback
# -----------------------------------------------------------------------------

@bp.route("/ai/feedback", methods=["POST"])
@ai_access_required
def post_feedback():
    body = request.get_json(silent=True) or {}
    session_id = (body.get("session_id") or "").strip() or None
    record_id = (body.get("record_id") or "").strip() or None
    db_id = body.get("db_id")
    verdict = (body.get("verdict") or "").strip()
    reason = (body.get("reason") or "").strip()[:500] or None

    allowed = {"good", "bad", "not_relevant", "clicked", "contacted"}
    if verdict not in allowed:
        return jsonify({"error": "bad_request", "detail": "invalid verdict"}), 400

    uid = g.propnet_user_id
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_feedback
                    (session_id, propnet_uid, record_id, db_id, verdict, reason_text)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (session_id, uid, record_id, db_id, verdict, reason),
            )
        conn.commit()
    return jsonify({"ok": True})


# -----------------------------------------------------------------------------
# POST /api/ai/view
# -----------------------------------------------------------------------------

@bp.route("/ai/view", methods=["POST"])
def post_view():
    body = request.get_json(silent=True) or {}
    record_id = (body.get("record_id") or "").strip()
    db_id = body.get("db_id")
    agent_slug = (body.get("agent_slug") or "").strip()[:64] or None
    source = (body.get("source") or "map").strip()[:32]
    action = (body.get("action") or "impression").strip()[:16]
    viewer_session = request.cookies.get("propmap_view_sid") or (body.get("viewer_session") or "")[:64]

    if not record_id or db_id is None:
        return jsonify({"error": "bad_request"}), 400

    viewer_uid = _extract_viewer_uid()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO property_view_events
                    (record_id, db_id, agent_slug, viewer_uid, viewer_session, source, action)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (record_id, int(db_id), agent_slug, viewer_uid, viewer_session or None, source, action),
            )
        conn.commit()
    return jsonify({"ok": True})
