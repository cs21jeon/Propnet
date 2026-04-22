#!/usr/bin/env python3
"""
AI 크레딧 월 번들 리필 스크립트.
매월 1일 00:10 KST에 systemd timer로 실행.

동작:
1. voiceroom.user_billing에서 활성 구독자 조회
2. 해당 플랜의 ai_credits_bundle 값 확인
3. goldenrabbit_db.ai_credit_wallet.balance_bundle을 리필 (이월 없음, 덮어쓰기)
4. ai_credit_ledger에 기록

의존:
- voiceroom DB: user_billing + billing_plans (구독 상태/플랜)
- goldenrabbit_db: ai_credit_wallet + ai_credit_ledger (크레딧)
- service_user_links: voiceroom user_id → propnet_user_id 변환
"""

import os
import sys
import json
import logging
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv('/home/webapp/goldenrabbit/backend/.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger('ai_bundle_refill')

# DB 설정
MAIN_DB = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'goldenrabbit_db'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
}

# voiceroom DB (Proptalk)
VOICE_DB = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': 'voiceroom',
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
}


def get_active_subscribers(voice_conn):
    """voiceroom에서 활성 구독자 + 플랜 번들 정보 조회."""
    with voice_conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT ub.user_id AS voiceroom_user_id,
                   bp.code AS plan_code,
                   bp.ai_credits_bundle
            FROM user_billing ub
            JOIN billing_plans bp ON ub.current_plan_id = bp.id
            WHERE ub.subscription_status = 'active'
              AND bp.plan_type = 'subscription'
              AND bp.ai_credits_bundle > 0
        """)
        return cur.fetchall()


def voiceroom_to_propnet_uid(main_conn, voiceroom_user_id):
    """service_user_links에서 voiceroom user_id → propnet_user_id 변환."""
    with main_conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT propnet_user_id FROM service_user_links WHERE service = 'proptalk' AND local_user_id = %s",
            (voiceroom_user_id,),
        )
        row = cur.fetchone()
        return row['propnet_user_id'] if row else None


def refill_bundle(main_conn, propnet_uid, credits, plan_code):
    """balance_bundle을 리필 (이월 없음, 덮어쓰기)."""
    with main_conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 지갑 존재 확인
        cur.execute(
            "SELECT * FROM ai_credit_wallet WHERE propnet_uid = %s FOR UPDATE",
            (propnet_uid,),
        )
        wallet = cur.fetchone()
        if not wallet:
            # 지갑 생성
            cur.execute(
                """INSERT INTO ai_credit_wallet (propnet_uid, balance_free, balance_bundle, balance_pack, signup_bonus_given)
                   VALUES (%s, 0, 0, 0, TRUE)
                   ON CONFLICT (propnet_uid) DO NOTHING""",
                (propnet_uid,),
            )
            cur.execute(
                "SELECT * FROM ai_credit_wallet WHERE propnet_uid = %s FOR UPDATE",
                (propnet_uid,),
            )
            wallet = cur.fetchone()

        old_bundle = wallet['balance_bundle']

        # 리필 (덮어쓰기)
        cur.execute(
            """UPDATE ai_credit_wallet
               SET balance_bundle = %s, bundle_reset_at = CURRENT_DATE
               WHERE propnet_uid = %s
               RETURNING *""",
            (credits, propnet_uid),
        )
        updated = cur.fetchone()

        delta = credits - old_bundle
        snapshot = json.dumps({
            'free': updated['balance_free'],
            'bundle': updated['balance_bundle'],
            'pack': updated['balance_pack'],
        })

        cur.execute(
            """INSERT INTO ai_credit_ledger
                   (propnet_uid, delta, source_type, source_ref, balance_snapshot, note)
               VALUES (%s, %s, 'bundle', %s, %s::jsonb, %s)""",
            (
                propnet_uid,
                delta,
                plan_code,
                snapshot,
                f"월 번들 리필 {credits}회 (plan={plan_code}, old={old_bundle})",
            ),
        )
    main_conn.commit()
    return old_bundle, credits


def main():
    logger.info("=== AI 크레딧 번들 리필 시작 ===")

    try:
        voice_conn = psycopg2.connect(**VOICE_DB)
        main_conn = psycopg2.connect(**MAIN_DB)
    except Exception as e:
        logger.error(f"DB 연결 실패: {e}")
        sys.exit(1)

    try:
        subscribers = get_active_subscribers(voice_conn)
        logger.info(f"활성 구독자: {len(subscribers)}명")

        success = 0
        skipped = 0
        failed = 0

        for sub in subscribers:
            voiceroom_uid = sub['voiceroom_user_id']
            plan_code = sub['plan_code']
            credits = sub['ai_credits_bundle']

            propnet_uid = voiceroom_to_propnet_uid(main_conn, voiceroom_uid)
            if not propnet_uid:
                logger.warning(f"propnet_uid 없음: voiceroom_user_id={voiceroom_uid} (plan={plan_code})")
                skipped += 1
                continue

            try:
                old, new = refill_bundle(main_conn, propnet_uid, credits, plan_code)
                logger.info(f"리필 완료: propnet_uid={propnet_uid} plan={plan_code} {old}→{new}")
                success += 1
            except Exception as e:
                logger.error(f"리필 실패: propnet_uid={propnet_uid} plan={plan_code}: {e}")
                main_conn.rollback()
                failed += 1

        logger.info(f"=== 리필 완료: 성공={success}, 스킵={skipped}, 실패={failed} ===")

    finally:
        voice_conn.close()
        main_conn.close()


if __name__ == '__main__':
    main()
