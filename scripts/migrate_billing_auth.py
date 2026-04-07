#!/usr/bin/env python3
"""
Agent 과금 + 인증 통합 마이그레이션 스크립트
서버에서 실행: python3 migrate_billing_auth.py

변경사항:
1. goldenrabbit_db.agent_requests — 결제 관련 컬럼 추가
2. voiceroom.billing_plans — user_type, includes_propsheet 컬럼 + agent 플랜 INSERT
3. voiceroom.user_billing — propnet_user_id 컬럼 추가
"""
import os
import sys
import psycopg2
import psycopg2.extras
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# 환경변수에서 DB 접속정보 읽기
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER', 'goldenrabbit_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')


def migrate_goldenrabbit_db():
    """goldenrabbit_db: agent_requests 테이블 확장"""
    dsn = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/goldenrabbit_db"
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # agent_requests에 결제 관련 컬럼 추가
            migrations = [
                ("selected_plan_code", "VARCHAR(50)"),
                ("payment_status", "VARCHAR(20) DEFAULT 'none'"),
                ("payment_order_id", "VARCHAR(100)"),
                ("payment_completed_at", "TIMESTAMP"),
            ]
            for col_name, col_type in migrations:
                cur.execute("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'agent_requests' AND column_name = %s
                """, (col_name,))
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE agent_requests ADD COLUMN {col_name} {col_type}")
                    logger.info(f"[goldenrabbit_db] Added column: agent_requests.{col_name}")
                else:
                    logger.info(f"[goldenrabbit_db] Column already exists: agent_requests.{col_name}")

            # 기존 approved 상태 중 결제 정보 없는 건은 payment_status='none' 유지 (레거시)
            # 새로운 status 값 'approved_pending_payment' 사용 가능하도록 CHECK 제약 없음 확인
            # (VARCHAR이므로 별도 제약 불필요)

        conn.commit()
        logger.info("[goldenrabbit_db] Migration completed successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"[goldenrabbit_db] Migration failed: {e}")
        raise
    finally:
        conn.close()


def migrate_voiceroom_db():
    """voiceroom DB: billing_plans 확장 + agent 플랜 INSERT + user_billing 확장"""
    dsn = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/voiceroom"
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. billing_plans에 user_type, includes_propsheet 컬럼 추가
            bp_migrations = [
                ("user_type", "VARCHAR(20) DEFAULT 'user'"),
                ("includes_propsheet", "BOOLEAN DEFAULT FALSE"),
            ]
            for col_name, col_type in bp_migrations:
                cur.execute("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'billing_plans' AND column_name = %s
                """, (col_name,))
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE billing_plans ADD COLUMN {col_name} {col_type}")
                    logger.info(f"[voiceroom] Added column: billing_plans.{col_name}")
                else:
                    logger.info(f"[voiceroom] Column already exists: billing_plans.{col_name}")

            # 2. 기존 플랜에 user_type='user' 설정
            cur.execute("""
                UPDATE billing_plans SET user_type = 'user'
                WHERE user_type IS NULL OR user_type = ''
            """)
            logger.info("[voiceroom] Updated existing plans: user_type='user'")

            # 3. Agent 플랜 3개 INSERT (중복 방지)
            agent_plans = [
                {
                    'code': 'agent_regular',
                    'name': 'Agent Regular',
                    'plan_type': 'subscription',
                    'minutes_included': 10,
                    'price': 9900,
                    'overage_rate': 0,
                    'billing_cycle': 'monthly',
                    'user_type': 'agent',
                    'includes_propsheet': True,
                    'sort_order': 10,
                    'description': 'PropSheet 포함 + 기본 Proptalk 10분',
                },
                {
                    'code': 'agent_basic',
                    'name': 'Agent Basic',
                    'plan_type': 'subscription',
                    'minutes_included': 1800,
                    'price': 29900,
                    'overage_rate': 12,
                    'billing_cycle': 'monthly',
                    'user_type': 'agent',
                    'includes_propsheet': True,
                    'sort_order': 11,
                    'description': 'PropSheet 포함 + Proptalk 30시간/월',
                },
                {
                    'code': 'agent_pro',
                    'name': 'Agent Pro',
                    'plan_type': 'subscription',
                    'minutes_included': 5400,
                    'price': 79900,
                    'overage_rate': 12,
                    'billing_cycle': 'monthly',
                    'user_type': 'agent',
                    'includes_propsheet': True,
                    'sort_order': 12,
                    'description': 'PropSheet 포함 + Proptalk 90시간/월',
                },
            ]

            for plan in agent_plans:
                cur.execute("SELECT id FROM billing_plans WHERE code = %s", (plan['code'],))
                existing = cur.fetchone()
                if existing:
                    # 기존 플랜 업데이트 (user_type, includes_propsheet만)
                    cur.execute("""
                        UPDATE billing_plans
                        SET user_type = %s, includes_propsheet = %s,
                            description = %s, sort_order = %s
                        WHERE code = %s
                    """, (plan['user_type'], plan['includes_propsheet'],
                          plan['description'], plan['sort_order'], plan['code']))
                    logger.info(f"[voiceroom] Updated agent plan: {plan['code']}")
                else:
                    cur.execute("""
                        INSERT INTO billing_plans
                            (code, name, plan_type, minutes_included, price,
                             overage_rate, billing_cycle, user_type, includes_propsheet,
                             sort_order, description, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                    """, (plan['code'], plan['name'], plan['plan_type'],
                          plan['minutes_included'], plan['price'],
                          plan['overage_rate'], plan['billing_cycle'],
                          plan['user_type'], plan['includes_propsheet'],
                          plan['sort_order'], plan['description']))
                    logger.info(f"[voiceroom] Inserted agent plan: {plan['code']}")

            # 4. user_billing에 propnet_user_id 컬럼 추가
            cur.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_billing' AND column_name = 'propnet_user_id'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE user_billing ADD COLUMN propnet_user_id INTEGER")
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_billing_propnet
                    ON user_billing(propnet_user_id)
                """)
                logger.info("[voiceroom] Added column: user_billing.propnet_user_id + index")
            else:
                logger.info("[voiceroom] Column already exists: user_billing.propnet_user_id")

            # 5. 기존 user_billing의 propnet_user_id 역매핑 (service_user_links 기반)
            # voiceroom DB에서는 goldenrabbit_db를 직접 조회 불가 → 별도 스크립트에서 처리
            # 여기서는 컬럼 추가만 수행

        conn.commit()
        logger.info("[voiceroom] Migration completed successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"[voiceroom] Migration failed: {e}")
        raise
    finally:
        conn.close()


def backfill_propnet_user_ids():
    """user_billing.propnet_user_id 역매핑 (cross-DB)"""
    gr_dsn = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/goldenrabbit_db"
    vr_dsn = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/voiceroom"

    gr_conn = psycopg2.connect(gr_dsn)
    vr_conn = psycopg2.connect(vr_dsn)
    try:
        # goldenrabbit_db에서 proptalk service_user_links 조회
        with gr_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT propnet_user_id, local_user_id
                FROM service_user_links
                WHERE service = 'proptalk'
            """)
            links = cur.fetchall()

        if not links:
            logger.info("[backfill] No proptalk service_user_links found")
            return

        # voiceroom DB에서 user_billing 업데이트
        with vr_conn.cursor() as cur:
            updated = 0
            for link in links:
                cur.execute("""
                    UPDATE user_billing
                    SET propnet_user_id = %s
                    WHERE user_id = %s AND (propnet_user_id IS NULL OR propnet_user_id != %s)
                """, (link['propnet_user_id'], link['local_user_id'], link['propnet_user_id']))
                if cur.rowcount > 0:
                    updated += 1
            vr_conn.commit()
            logger.info(f"[backfill] Updated {updated} user_billing rows with propnet_user_id")

    except Exception as e:
        vr_conn.rollback()
        logger.error(f"[backfill] Failed: {e}")
        raise
    finally:
        gr_conn.close()
        vr_conn.close()


def verify():
    """마이그레이션 검증"""
    gr_dsn = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/goldenrabbit_db"
    vr_dsn = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/voiceroom"

    # goldenrabbit_db 검증
    conn = psycopg2.connect(gr_dsn)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'agent_requests'
            ORDER BY ordinal_position
        """)
        cols = [r['column_name'] for r in cur.fetchall()]
        required = ['selected_plan_code', 'payment_status', 'payment_order_id', 'payment_completed_at']
        for col in required:
            status = 'OK' if col in cols else 'MISSING'
            logger.info(f"[verify] agent_requests.{col}: {status}")
    conn.close()

    # voiceroom 검증
    conn = psycopg2.connect(vr_dsn)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # billing_plans 컬럼 확인
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'billing_plans'
            ORDER BY ordinal_position
        """)
        cols = [r['column_name'] for r in cur.fetchall()]
        for col in ['user_type', 'includes_propsheet']:
            status = 'OK' if col in cols else 'MISSING'
            logger.info(f"[verify] billing_plans.{col}: {status}")

        # agent 플랜 확인
        cur.execute("SELECT code, user_type, includes_propsheet FROM billing_plans WHERE user_type = 'agent'")
        plans = cur.fetchall()
        logger.info(f"[verify] Agent plans count: {len(plans)}")
        for p in plans:
            logger.info(f"  - {p['code']}: user_type={p['user_type']}, includes_propsheet={p['includes_propsheet']}")

        # user_billing.propnet_user_id 확인
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'user_billing' AND column_name = 'propnet_user_id'
        """)
        status = 'OK' if cur.fetchone() else 'MISSING'
        logger.info(f"[verify] user_billing.propnet_user_id: {status}")
    conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Agent 과금 + 인증 통합 마이그레이션")
    print("=" * 60)

    # .env 파일 로드 (서버 환경)
    env_path = '/home/webapp/goldenrabbit/backend/.env'
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, val = line.partition('=')
                    os.environ.setdefault(key.strip(), val.strip())
        # 환경변수 재설정 (이 스크립트에서 읽은 값 반영)
        globals()['DB_HOST'] = os.environ.get('DB_HOST', 'localhost')
        globals()['DB_PORT'] = os.environ.get('DB_PORT', '5432')
        globals()['DB_USER'] = os.environ.get('DB_USER', 'goldenrabbit_user')
        globals()['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', '')

    print("\n[1/4] goldenrabbit_db 마이그레이션...")
    migrate_goldenrabbit_db()

    print("\n[2/4] voiceroom DB 마이그레이션...")
    migrate_voiceroom_db()

    print("\n[3/4] user_billing propnet_user_id 역매핑...")
    backfill_propnet_user_ids()

    print("\n[4/4] 검증...")
    verify()

    print("\n" + "=" * 60)
    print("마이그레이션 완료!")
    print("=" * 60)
