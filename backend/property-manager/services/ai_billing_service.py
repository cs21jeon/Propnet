"""
AI 크레딧 과금 서비스.

지갑(wallet) / 원장(ledger) CRUD, 크레딧 체크/차감, 가입 보너스 지급.
goldenrabbit_db의 ai_credit_wallet / ai_credit_ledger 테이블 사용.

차감 우선순위: free → bundle → pack
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ensure_wallet — 지갑 없으면 생성, 있으면 반환
# =============================================================================

def ensure_wallet(cur, propnet_uid: int) -> dict:
    """지갑 행이 없으면 생성. SELECT ... FOR UPDATE로 잠금."""
    cur.execute(
        "SELECT * FROM ai_credit_wallet WHERE propnet_uid = %s FOR UPDATE",
        (propnet_uid,),
    )
    row = cur.fetchone()
    if row:
        return row
    cur.execute(
        """INSERT INTO ai_credit_wallet (propnet_uid, balance_free, balance_bundle, balance_pack)
           VALUES (%s, 0, 0, 0)
           ON CONFLICT (propnet_uid) DO NOTHING
           RETURNING *""",
        (propnet_uid,),
    )
    row = cur.fetchone()
    if row:
        return row
    # race: 다른 트랜잭션이 먼저 생성
    cur.execute(
        "SELECT * FROM ai_credit_wallet WHERE propnet_uid = %s FOR UPDATE",
        (propnet_uid,),
    )
    return cur.fetchone()


# =============================================================================
# grant_signup_bonus — 가입 보너스 1회 (idempotent)
# =============================================================================

def grant_signup_bonus(cur, propnet_uid: int) -> bool:
    """가입 보너스 1회 지급. 이미 지급됐으면 False 반환."""
    wallet = ensure_wallet(cur, propnet_uid)
    if wallet["signup_bonus_given"]:
        return False

    cur.execute(
        """UPDATE ai_credit_wallet
           SET balance_free = balance_free + 1,
               signup_bonus_given = TRUE
           WHERE propnet_uid = %s AND signup_bonus_given = FALSE
           RETURNING *""",
        (propnet_uid,),
    )
    updated = cur.fetchone()
    if not updated:
        return False

    _write_ledger(
        cur, propnet_uid,
        delta=1,
        source_type="signup",
        source_ref=f"signup_{propnet_uid}",
        snapshot=_snapshot(updated),
        note="가입 보너스 1회",
    )
    return True


# =============================================================================
# check_can_search — 검색 가능 여부 사전 체크
# =============================================================================

def check_can_search(cur, propnet_uid: int, role: str | None = None) -> dict:
    """
    검색 가능 여부를 반환.
    Returns: {ok: bool, reason: str, remaining: int}
    """
    # admin은 무제한
    if role == "admin":
        return {"ok": True, "reason": "admin_unlimited", "remaining": -1}

    wallet = ensure_wallet(cur, propnet_uid)
    total = wallet["balance_free"] + wallet["balance_bundle"] + wallet["balance_pack"]

    if total > 0:
        return {"ok": True, "reason": "has_credits", "remaining": total}

    return {
        "ok": False,
        "reason": "no_credits",
        "remaining": 0,
    }


# =============================================================================
# deduct_credit — 성공 추천 후 원자적 차감
# =============================================================================

def deduct_credit(cur, propnet_uid: int, session_id: str, role: str | None = None) -> dict | None:
    """
    크레딧 1회 차감. free → bundle → pack 순서.
    admin이면 차감 없이 None 반환.
    성공 시 차감 후 wallet 스냅샷 반환.
    중복 차감 방지: source_ref=session_id의 UNIQUE 인덱스.
    동일 세션에서 두 번째 추천이 나와도 추가 차감 없음 (1세션 = 최대 1크레딧).
    """
    import psycopg2

    if role == "admin":
        return None

    # 이미 이 세션에서 차감됐는지 확인
    cur.execute(
        "SELECT 1 FROM ai_credit_ledger WHERE source_type = 'search_use' AND source_ref = %s",
        (str(session_id),),
    )
    if cur.fetchone():
        logger.info("deduct_credit: already deducted for session=%s (no additional charge)", session_id)
        wallet = ensure_wallet(cur, propnet_uid)
        return {
            "bucket": "already_charged",
            "remaining": wallet["balance_free"] + wallet["balance_bundle"] + wallet["balance_pack"],
            "was_free": False,
        }

    wallet = ensure_wallet(cur, propnet_uid)
    bucket = None

    if wallet["balance_free"] > 0:
        bucket = "free"
        cur.execute(
            """UPDATE ai_credit_wallet
               SET balance_free = balance_free - 1
               WHERE propnet_uid = %s AND balance_free > 0
               RETURNING *""",
            (propnet_uid,),
        )
    elif wallet["balance_bundle"] > 0:
        bucket = "bundle"
        cur.execute(
            """UPDATE ai_credit_wallet
               SET balance_bundle = balance_bundle - 1
               WHERE propnet_uid = %s AND balance_bundle > 0
               RETURNING *""",
            (propnet_uid,),
        )
    elif wallet["balance_pack"] > 0:
        bucket = "pack"
        cur.execute(
            """UPDATE ai_credit_wallet
               SET balance_pack = balance_pack - 1
               WHERE propnet_uid = %s AND balance_pack > 0
               RETURNING *""",
            (propnet_uid,),
        )
    else:
        logger.warning("deduct_credit: no credits for uid=%s session=%s", propnet_uid, session_id)
        return None

    updated = cur.fetchone()
    if not updated:
        logger.warning("deduct_credit: race condition for uid=%s", propnet_uid)
        return None

    try:
        _write_ledger(
            cur, propnet_uid,
            delta=-1,
            source_type="search_use",
            source_ref=str(session_id),
            snapshot=_snapshot(updated),
            note=f"AI 검색 차감 (bucket={bucket})",
        )
    except psycopg2.IntegrityError:
        # UNIQUE 인덱스 위반 — 동시 요청으로 이미 차감됨. 지갑 복구.
        logger.warning("deduct_credit: IntegrityError (concurrent deduct) for session=%s", session_id)
        raise

    return {
        "bucket": bucket,
        "remaining": updated["balance_free"] + updated["balance_bundle"] + updated["balance_pack"],
        "was_free": bucket == "free",
    }


# =============================================================================
# get_credit_status — 잔여 크레딧 조회 (API 응답용)
# =============================================================================

def get_credit_status(cur, propnet_uid: int, role: str | None = None) -> dict:
    """잔여 크레딧 정보 반환."""
    if role == "admin":
        return {
            "remaining": -1,
            "is_admin": True,
            "balance_free": 0,
            "balance_bundle": 0,
            "balance_pack": 0,
            "signup_bonus_given": True,
        }

    wallet = ensure_wallet(cur, propnet_uid)
    return {
        "remaining": wallet["balance_free"] + wallet["balance_bundle"] + wallet["balance_pack"],
        "is_admin": False,
        "balance_free": wallet["balance_free"],
        "balance_bundle": wallet["balance_bundle"],
        "balance_pack": wallet["balance_pack"],
        "signup_bonus_given": wallet["signup_bonus_given"],
        "bundle_reset_at": str(wallet["bundle_reset_at"]) if wallet["bundle_reset_at"] else None,
    }


# =============================================================================
# grant_monthly_bundle — 월 번들 리필 (cron 또는 결제 콜백에서 호출)
# =============================================================================

def grant_monthly_bundle(cur, propnet_uid: int, credits: int, plan_code: str) -> bool:
    """
    월 번들 리필. 이전 번들은 소멸(덮어쓰기, 이월 없음).
    """
    wallet = ensure_wallet(cur, propnet_uid)
    old_bundle = wallet["balance_bundle"]

    cur.execute(
        """UPDATE ai_credit_wallet
           SET balance_bundle = %s,
               bundle_reset_at = CURRENT_DATE
           WHERE propnet_uid = %s
           RETURNING *""",
        (credits, propnet_uid),
    )
    updated = cur.fetchone()
    if not updated:
        return False

    delta = credits - old_bundle
    _write_ledger(
        cur, propnet_uid,
        delta=delta,
        source_type="bundle",
        source_ref=plan_code,
        snapshot=_snapshot(updated),
        note=f"월 번들 리필 {credits}회 (plan={plan_code})",
    )
    return True


# =============================================================================
# cancel_bundle — 구독 해지 시 번들 즉시 소멸
# =============================================================================

def cancel_bundle(cur, propnet_uid: int) -> bool:
    """구독 해지 시 balance_bundle을 0으로."""
    wallet = ensure_wallet(cur, propnet_uid)
    if wallet["balance_bundle"] == 0:
        return False

    old_bundle = wallet["balance_bundle"]
    cur.execute(
        """UPDATE ai_credit_wallet
           SET balance_bundle = 0
           WHERE propnet_uid = %s
           RETURNING *""",
        (propnet_uid,),
    )
    updated = cur.fetchone()

    _write_ledger(
        cur, propnet_uid,
        delta=-old_bundle,
        source_type="cancel_bundle",
        source_ref=None,
        snapshot=_snapshot(updated),
        note="구독 해지 — 번들 소멸",
    )
    return True


# =============================================================================
# admin_adjust — 관리자 수동 조정
# =============================================================================

def admin_adjust(cur, propnet_uid: int, delta: int, bucket: str, note: str, admin_email: str) -> dict:
    """
    관리자 수동 크레딧 조정.
    bucket: 'free' | 'bundle' | 'pack'
    delta: +는 지급, -는 차감
    """
    wallet = ensure_wallet(cur, propnet_uid)

    col = f"balance_{bucket}"
    if col not in ("balance_free", "balance_bundle", "balance_pack"):
        raise ValueError(f"Invalid bucket: {bucket}")

    cur.execute(
        f"""UPDATE ai_credit_wallet
            SET {col} = GREATEST(0, {col} + %s)
            WHERE propnet_uid = %s
            RETURNING *""",
        (delta, propnet_uid),
    )
    updated = cur.fetchone()

    _write_ledger(
        cur, propnet_uid,
        delta=delta,
        source_type="admin",
        source_ref=admin_email,
        snapshot=_snapshot(updated),
        note=note or f"관리자 수동 조정 ({bucket} {delta:+d})",
    )
    return _snapshot(updated)


# =============================================================================
# Internal helpers
# =============================================================================

def _snapshot(wallet: dict) -> dict:
    return {
        "free": wallet["balance_free"],
        "bundle": wallet["balance_bundle"],
        "pack": wallet["balance_pack"],
    }


def _write_ledger(cur, propnet_uid, delta, source_type, source_ref, snapshot, note):
    cur.execute(
        """INSERT INTO ai_credit_ledger
               (propnet_uid, delta, source_type, source_ref, balance_snapshot, note)
           VALUES (%s, %s, %s, %s, %s::jsonb, %s)""",
        (
            propnet_uid,
            delta,
            source_type,
            source_ref,
            json.dumps(snapshot),
            note,
        ),
    )
