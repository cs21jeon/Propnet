"""
결제/과금 DB 모델 (psycopg2 기반)
기존 models.py의 query_one/query_all/execute 패턴 재사용
"""
from models import query_one, query_all, execute


# ============================================================
# BillingPlan 모델 (요금제)
# ============================================================
class BillingPlan:
    @staticmethod
    def find_by_code(code):
        return query_one("SELECT * FROM billing_plans WHERE code = %s", (code,))

    @staticmethod
    def find_by_id(plan_id):
        return query_one("SELECT * FROM billing_plans WHERE id = %s", (plan_id,))

    @staticmethod
    def list_active():
        return query_all(
            "SELECT * FROM billing_plans WHERE is_active = true ORDER BY sort_order"
        )


# ============================================================
# UserBilling 모델 (사용자 과금 상태)
# ============================================================
class UserBilling:
    @staticmethod
    def find_by_user_id(user_id):
        return query_one("SELECT * FROM user_billing WHERE user_id = %s", (user_id,))

    @staticmethod
    def ensure(user_id):
        """user_billing 행이 없으면 생성 (무료 600초)"""
        existing = query_one("SELECT * FROM user_billing WHERE user_id = %s", (user_id,))
        if existing:
            return existing
        free_plan = query_one("SELECT * FROM billing_plans WHERE code = 'free'")
        plan_id = free_plan['id'] if free_plan else None
        return execute(
            """INSERT INTO user_billing (user_id, current_plan_id, remaining_seconds, subscription_status)
               VALUES (%s, %s, 600, 'free')
               ON CONFLICT (user_id) DO NOTHING
               RETURNING *""",
            (user_id, plan_id)
        ) or query_one("SELECT * FROM user_billing WHERE user_id = %s", (user_id,))

    @staticmethod
    def get_remaining_seconds(user_id):
        row = query_one(
            "SELECT remaining_seconds FROM user_billing WHERE user_id = %s", (user_id,)
        )
        return row['remaining_seconds'] if row else 0

    @staticmethod
    def deduct_seconds(user_id, seconds):
        """원자적 잔여 시간 차감. 차감 후 잔여 시간 반환."""
        return execute(
            """UPDATE user_billing
               SET remaining_seconds = remaining_seconds - %s,
                   updated_at = NOW()
               WHERE user_id = %s
               RETURNING remaining_seconds""",
            (seconds, user_id)
        )

    @staticmethod
    def add_seconds(user_id, seconds):
        """잔여 시간 추가 (시간팩 구매)"""
        return execute(
            """UPDATE user_billing
               SET remaining_seconds = remaining_seconds + %s,
                   updated_at = NOW()
               WHERE user_id = %s
               RETURNING remaining_seconds""",
            (seconds, user_id)
        )

    @staticmethod
    def activate_subscription(user_id, plan_id, customer_key,
                              billing_key_encrypted=None, billing_key_iv=None):
        """구독 활성화"""
        plan = query_one("SELECT * FROM billing_plans WHERE id = %s", (plan_id,))
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        return execute(
            """UPDATE user_billing
               SET current_plan_id = %s,
                   remaining_seconds = %s * 60,
                   subscription_status = 'active',
                   subscription_started_at = NOW(),
                   subscription_expires_at = NOW() + INTERVAL '30 days',
                   billing_key_encrypted = %s,
                   billing_key_iv = %s,
                   customer_key = %s,
                   auto_renew = true,
                   updated_at = NOW()
               WHERE user_id = %s
               RETURNING *""",
            (plan_id, plan['minutes_included'], billing_key_encrypted,
             billing_key_iv, customer_key, user_id)
        )

    @staticmethod
    def cancel_subscription(user_id):
        """구독 해지 (auto_renew만 끔, 만료일까지 사용 가능)"""
        return execute(
            """UPDATE user_billing
               SET auto_renew = false,
                   subscription_status = 'cancelled',
                   updated_at = NOW()
               WHERE user_id = %s
               RETURNING *""",
            (user_id,)
        )

    @staticmethod
    def renew_subscription(user_id, plan_id):
        """구독 갱신 (크론에서 호출)"""
        plan = query_one("SELECT * FROM billing_plans WHERE id = %s", (plan_id,))
        if not plan:
            return None
        return execute(
            """UPDATE user_billing
               SET remaining_seconds = %s * 60,
                   subscription_expires_at = subscription_expires_at + INTERVAL '30 days',
                   subscription_status = 'active',
                   updated_at = NOW()
               WHERE user_id = %s
               RETURNING *""",
            (plan['minutes_included'], user_id)
        )

    @staticmethod
    def set_status(user_id, status):
        """구독 상태 변경"""
        return execute(
            """UPDATE user_billing
               SET subscription_status = %s, updated_at = NOW()
               WHERE user_id = %s
               RETURNING *""",
            (status, user_id)
        )

    @staticmethod
    def update_billing_key(user_id, billing_key_encrypted, billing_key_iv, customer_key):
        """빌링키 업데이트"""
        return execute(
            """UPDATE user_billing
               SET billing_key_encrypted = %s,
                   billing_key_iv = %s,
                   customer_key = %s,
                   updated_at = NOW()
               WHERE user_id = %s
               RETURNING *""",
            (billing_key_encrypted, billing_key_iv, customer_key, user_id)
        )


# ============================================================
# PaymentTransaction 모델 (결제 이력)
# ============================================================
class PaymentTransaction:
    @staticmethod
    def create(user_id, plan_id, order_id, amount, billing_type='one_time'):
        return execute(
            """INSERT INTO payment_transactions
               (user_id, plan_id, order_id, amount, billing_type, status)
               VALUES (%s, %s, %s, %s, %s, 'pending')
               RETURNING *""",
            (user_id, plan_id, order_id, amount, billing_type)
        )

    @staticmethod
    def find_by_order_id(order_id):
        return query_one(
            "SELECT * FROM payment_transactions WHERE order_id = %s", (order_id,)
        )

    @staticmethod
    def approve(order_id, payment_key, method=None, card_company=None,
                card_number_masked=None, receipt_url=None,
                minutes_granted=None, raw_response=None):
        import json
        return execute(
            """UPDATE payment_transactions
               SET status = 'approved',
                   payment_key = %s,
                   method = %s,
                   card_company = %s,
                   card_number_masked = %s,
                   receipt_url = %s,
                   minutes_granted = %s,
                   raw_response = %s,
                   completed_at = NOW()
               WHERE order_id = %s
               RETURNING *""",
            (payment_key, method, card_company, card_number_masked,
             receipt_url, minutes_granted,
             json.dumps(raw_response) if raw_response else None,
             order_id)
        )

    @staticmethod
    def fail(order_id, error_message=None, raw_response=None):
        import json
        return execute(
            """UPDATE payment_transactions
               SET status = 'failed',
                   error_message = %s,
                   raw_response = %s,
                   completed_at = NOW()
               WHERE order_id = %s
               RETURNING *""",
            (error_message,
             json.dumps(raw_response) if raw_response else None,
             order_id)
        )

    @staticmethod
    def refund(order_id, refund_amount, refund_reason=None):
        return execute(
            """UPDATE payment_transactions
               SET status = CASE WHEN %s >= amount THEN 'refunded' ELSE 'partial_refund' END,
                   refund_amount = %s,
                   refund_reason = %s,
                   refunded_at = NOW()
               WHERE order_id = %s
               RETURNING *""",
            (refund_amount, refund_amount, refund_reason, order_id)
        )

    @staticmethod
    def list_for_user(user_id, limit=50):
        return query_all(
            """SELECT pt.*, bp.name as plan_name, bp.code as plan_code
               FROM payment_transactions pt
               LEFT JOIN billing_plans bp ON pt.plan_id = bp.id
               WHERE pt.user_id = %s
               ORDER BY pt.created_at DESC
               LIMIT %s""",
            (user_id, limit)
        )

    @staticmethod
    def expire_stale_orders():
        """24시간 지난 pending 주문 만료 처리"""
        return execute(
            """UPDATE payment_transactions
               SET status = 'failed', error_message = '주문 만료 (24시간 초과)'
               WHERE status = 'pending'
                 AND created_at < NOW() - INTERVAL '24 hours'"""
        )


# ============================================================
# UsageLog 모델 (사용량 기록)
# ============================================================
class UsageLog:
    @staticmethod
    def create(user_id, audio_file_id, seconds_used, seconds_before, seconds_after, plan_code=None):
        return execute(
            """INSERT INTO usage_logs
               (user_id, audio_file_id, seconds_used, seconds_before, seconds_after, plan_code)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING *""",
            (user_id, audio_file_id, seconds_used, seconds_before, seconds_after, plan_code)
        )

    @staticmethod
    def list_for_user(user_id, limit=50):
        return query_all(
            """SELECT ul.*, af.original_filename
               FROM usage_logs ul
               LEFT JOIN audio_files af ON ul.audio_file_id = af.id
               WHERE ul.user_id = %s
               ORDER BY ul.created_at DESC
               LIMIT %s""",
            (user_id, limit)
        )

    @staticmethod
    def total_seconds_for_user(user_id):
        """사용자 전체 사용량 (초)"""
        row = query_one(
            "SELECT COALESCE(SUM(seconds_used), 0) as total FROM usage_logs WHERE user_id = %s",
            (user_id,)
        )
        return float(row['total']) if row else 0


# ============================================================
# 관리자 전용 쿼리
# ============================================================
class AdminQueries:
    @staticmethod
    def get_stats():
        """전체 통계"""
        return {
            'total_users': (query_one("SELECT COUNT(*) as c FROM users") or {}).get('c', 0),
            'total_usage_minutes': float((query_one(
                "SELECT COALESCE(SUM(seconds_used)/60, 0) as m FROM usage_logs"
            ) or {}).get('m', 0)),
            'total_revenue': float((query_one(
                "SELECT COALESCE(SUM(amount), 0) as r FROM payment_transactions WHERE status='approved'"
            ) or {}).get('r', 0)),
        }

    @staticmethod
    def list_users_with_billing():
        """전체 사용자 + 결제 정보"""
        return query_all(
            """SELECT u.id, u.name, u.email, u.avatar_url, u.created_at,
                      ub.remaining_seconds, ub.subscription_status,
                      bp.name as plan_name, bp.code as plan_code
               FROM users u
               LEFT JOIN user_billing ub ON u.id = ub.user_id
               LEFT JOIN billing_plans bp ON ub.current_plan_id = bp.id
               ORDER BY u.created_at DESC"""
        )

    @staticmethod
    def recent_transactions(limit=20):
        """최근 결제 내역"""
        return query_all(
            """SELECT pt.*, u.name as user_name, u.email as user_email,
                      bp.name as plan_name
               FROM payment_transactions pt
               JOIN users u ON pt.user_id = u.id
               LEFT JOIN billing_plans bp ON pt.plan_id = bp.id
               WHERE pt.status = 'approved'
               ORDER BY pt.created_at DESC
               LIMIT %s""",
            (limit,)
        )
