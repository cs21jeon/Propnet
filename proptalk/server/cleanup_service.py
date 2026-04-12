"""
음성 파일 자동 정리 서비스 + 구독 자동결제/만료 관리
설정된 시간(기본 24시간) 후 파일 자동 삭제
"""
import os
import time
import uuid
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config

logger = logging.getLogger(__name__)


def cleanup_expired_audio_files():
    """
    만료된 음성 파일 삭제
    AUDIO_RETENTION_HOURS 시간이 지난 파일을 삭제
    """
    audio_folder = Config.AUDIO_FOLDER
    retention_hours = Config.AUDIO_RETENTION_HOURS

    if not os.path.exists(audio_folder):
        logger.debug(f"음성 폴더가 존재하지 않음: {audio_folder}")
        return

    now = datetime.now()
    expiry_time = now - timedelta(hours=retention_hours)
    deleted_count = 0
    error_count = 0

    logger.info(f"[Cleanup] 파일 정리 시작 - {retention_hours}시간 이전 파일 삭제")

    for filename in os.listdir(audio_folder):
        filepath = os.path.join(audio_folder, filename)

        # 디렉토리는 스킵
        if os.path.isdir(filepath):
            continue

        try:
            # 파일 수정 시간 확인
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

            if file_mtime < expiry_time:
                os.remove(filepath)
                deleted_count += 1
                logger.info(f"[Cleanup] 파일 삭제: {filename} (생성: {file_mtime})")

        except Exception as e:
            error_count += 1
            logger.error(f"[Cleanup] 파일 삭제 실패: {filename} - {e}")

    if deleted_count > 0 or error_count > 0:
        logger.info(f"[Cleanup] 정리 완료 - 삭제: {deleted_count}개, 오류: {error_count}개")


def cleanup_temp_uploads():
    """
    임시 업로드 폴더 정리
    1시간 이상 된 임시 파일 삭제
    """
    upload_folder = Config.UPLOAD_FOLDER

    if not os.path.exists(upload_folder):
        return

    now = datetime.now()
    expiry_time = now - timedelta(hours=1)

    for filename in os.listdir(upload_folder):
        filepath = os.path.join(upload_folder, filename)

        if os.path.isdir(filepath):
            continue

        try:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

            if file_mtime < expiry_time:
                os.remove(filepath)
                logger.info(f"[Cleanup] 임시 파일 삭제: {filename}")

        except Exception as e:
            logger.error(f"[Cleanup] 임시 파일 삭제 실패: {filename} - {e}")


# ============================================================
# 구독 자동결제 / 만료 관리
# ============================================================

def process_subscription_renewals():
    """
    만료 임박 구독 자동결제 (매일 03:00 실행)
    만료 1일 이내 + auto_renew=true인 구독 갱신
    """
    from models import query_all
    from models_billing import UserBilling, BillingPlan, PaymentTransaction
    from billing_service import decrypt_billing_key
    from toss_service import charge_billing_key

    try:
        # 만료 1일 이내 + 자동갱신 활성 구독 조회
        renewals = query_all(
            """SELECT ub.*, bp.code as plan_code, bp.name as plan_name,
                      bp.price as plan_price, bp.minutes_included
               FROM user_billing ub
               JOIN billing_plans bp ON ub.current_plan_id = bp.id
               WHERE ub.subscription_status = 'active'
                 AND ub.auto_renew = true
                 AND ub.subscription_expires_at <= NOW() + INTERVAL '1 day'
                 AND ub.billing_key_encrypted IS NOT NULL"""
        )

        if not renewals:
            return

        logger.info(f"[Billing Cron] 갱신 대상: {len(renewals)}건")

        for sub in renewals:
            user_id = sub['user_id']
            try:
                # billingKey 복호화
                billing_key = decrypt_billing_key(
                    sub['billing_key_encrypted'], sub['billing_key_iv']
                )

                # 주문 생성
                order_id = f"renew_{user_id}_{uuid.uuid4().hex[:8]}"
                plan_id = sub['current_plan_id']
                amount = sub['plan_price']

                PaymentTransaction.create(
                    user_id=user_id,
                    plan_id=plan_id,
                    order_id=order_id,
                    amount=amount,
                    billing_type='subscription_renewal',
                )

                # 자동결제
                result = charge_billing_key(
                    billing_key=billing_key,
                    customer_key=sub['customer_key'],
                    order_id=order_id,
                    amount=amount,
                    order_name=f"Proptalk {sub['plan_name']} 갱신",
                )

                if result['success']:
                    # 결제 성공 → 구독 갱신
                    toss_data = result['data']
                    PaymentTransaction.approve(
                        order_id=order_id,
                        payment_key=toss_data.get('paymentKey'),
                        method=toss_data.get('method'),
                        minutes_granted=sub['minutes_included'],
                        raw_response=toss_data,
                    )
                    UserBilling.renew_subscription(user_id, plan_id)
                    logger.info(f"[Billing Cron] 갱신 성공: user={user_id}")
                else:
                    # 결제 실패 → past_due
                    PaymentTransaction.fail(
                        order_id=order_id,
                        error_message=result.get('error'),
                        raw_response=result.get('data'),
                    )
                    UserBilling.set_status(user_id, 'past_due')
                    logger.warning(
                        f"[Billing Cron] 갱신 실패: user={user_id}, "
                        f"error={result.get('error')}"
                    )
                    # 에러 로그 + 갱신 실패 알림
                    try:
                        from models_billing import BillingErrorLog
                        BillingErrorLog.create(
                            error_type='renewal_failed', service='toss_payments',
                            user_id=user_id, order_id=order_id,
                            error_message=result.get('error'),
                            details={'plan_code': sub.get('plan_code'), 'amount': amount}
                        )
                    except Exception:
                        pass
                    try:
                        from notification_service import notify_renewal_failed
                        notify_renewal_failed(user_id)
                    except Exception as noti_err:
                        logger.warning(f"[Billing Cron] 갱신실패 알림 전송 오류: {noti_err}")

            except Exception as e:
                logger.error(f"[Billing Cron] 갱신 오류: user={user_id}, error={e}")

    except Exception as e:
        logger.error(f"[Billing Cron] process_subscription_renewals 오류: {e}")


def expire_past_due_subscriptions():
    """
    결제 실패 3일 경과 구독 만료 처리 (매일 04:00 실행)
    """
    from models import query_all
    from models_billing import UserBilling

    try:
        expired = query_all(
            """SELECT user_id FROM user_billing
               WHERE subscription_status = 'past_due'
                 AND subscription_expires_at < NOW() - INTERVAL '3 days'"""
        )

        if not expired:
            return

        logger.info(f"[Billing Cron] 만료 처리 대상: {len(expired)}건")

        for row in expired:
            user_id = row['user_id']
            UserBilling.set_status(user_id, 'expired')
            logger.info(f"[Billing Cron] 구독 만료: user={user_id}")

    except Exception as e:
        logger.error(f"[Billing Cron] expire_past_due 오류: {e}")


def expire_ended_subscriptions():
    """
    만료일 경과 구독 자동 만료 처리 (매일 04:05 실행)
    - active + auto_renew=false + expires_at 경과 (해지 예정)
    - active + billing_key 없음 + expires_at 경과 (admin 강제 설정)
    - cancelled + expires_at 경과
    NOTE: expires_at IS NULL인 레코드는 제외 (admin 수동 설정분 보호)
    """
    from models import query_all
    from models_billing import UserBilling

    try:
        ended = query_all(
            """SELECT user_id FROM user_billing
               WHERE subscription_status IN ('active', 'cancelled')
                 AND subscription_expires_at IS NOT NULL
                 AND subscription_expires_at < NOW()
                 AND (auto_renew = false OR billing_key_encrypted IS NULL)"""
        )

        if not ended:
            return

        logger.info(f"[Billing Cron] 구독 종료 처리 대상: {len(ended)}건")

        for row in ended:
            user_id = row['user_id']
            UserBilling.set_status(user_id, 'expired')
            logger.info(f"[Billing Cron] 구독 종료 → expired: user={user_id}")

    except Exception as e:
        logger.error(f"[Billing Cron] expire_ended_subscriptions 오류: {e}")


def notify_expiring_subscriptions():
    """
    만료 3일 전 구독자에게 알림 (매일 10:00 실행)
    auto_renew=false인 구독자만 대상 (auto_renew=true는 자동결제되므로 불필요)
    """
    from models import query_all

    try:
        expiring = query_all(
            """SELECT user_id FROM user_billing
               WHERE subscription_status = 'active'
                 AND auto_renew = false
                 AND subscription_expires_at BETWEEN NOW() AND NOW() + INTERVAL '3 days'"""
        )

        if not expiring:
            return

        logger.info(f"[Billing Cron] 만료 임박 알림 대상: {len(expiring)}건")

        from notification_service import notify_subscription_expiring
        for row in expiring:
            try:
                notify_subscription_expiring(row['user_id'], 3)
            except Exception as e:
                logger.warning(f"[Billing Cron] 만료 임박 알림 실패: user={row['user_id']}, {e}")

    except Exception as e:
        logger.error(f"[Billing Cron] notify_expiring_subscriptions 오류: {e}")


def generate_billing_daily_summary():
    """
    일간 과금 요약 생성 (매일 23:55 실행)
    billing_daily_summary 테이블에 당일 데이터 집계 저장
    """
    from models import query_one, execute

    try:
        # 결제 통계
        tx = query_one("""
            SELECT COUNT(*) FILTER (WHERE status = 'approved') as successful,
                   COUNT(*) FILTER (WHERE status = 'failed') as failed,
                   COUNT(*) as total,
                   COALESCE(SUM(amount) FILTER (WHERE status = 'approved'), 0) as revenue,
                   COALESCE(SUM(CASE WHEN status IN ('refunded','partial_refund') THEN refund_amount ELSE 0 END), 0) as refunded
            FROM payment_transactions
            WHERE created_at::date = CURRENT_DATE
        """) or {}

        # 구독 상태
        from models import query_all
        subs_rows = query_all("SELECT subscription_status, COUNT(*) as cnt FROM user_billing GROUP BY subscription_status") or []
        subs = {r['subscription_status']: r['cnt'] for r in subs_rows}

        # 사용량
        usage = query_one("""
            SELECT COALESCE(SUM(seconds_used)/60, 0) as total_minutes,
                   COUNT(DISTINCT user_id) as active_users
            FROM usage_logs WHERE created_at::date = CURRENT_DATE
        """) or {}

        # 신규 가입
        new = query_one("SELECT COUNT(*) as cnt FROM users WHERE created_at::date = CURRENT_DATE") or {}

        execute("""
            INSERT INTO billing_daily_summary
                (date, total_transactions, successful_transactions, failed_transactions,
                 total_revenue, refunded_amount, active_subscriptions, cancelled_subscriptions,
                 new_users, active_users, total_usage_minutes)
            VALUES (CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
                total_transactions = EXCLUDED.total_transactions,
                successful_transactions = EXCLUDED.successful_transactions,
                failed_transactions = EXCLUDED.failed_transactions,
                total_revenue = EXCLUDED.total_revenue,
                refunded_amount = EXCLUDED.refunded_amount,
                active_subscriptions = EXCLUDED.active_subscriptions,
                cancelled_subscriptions = EXCLUDED.cancelled_subscriptions,
                new_users = EXCLUDED.new_users,
                active_users = EXCLUDED.active_users,
                total_usage_minutes = EXCLUDED.total_usage_minutes
        """, (tx.get('total', 0), tx.get('successful', 0), tx.get('failed', 0),
              int(tx.get('revenue', 0)), int(tx.get('refunded', 0)),
              subs.get('active', 0), subs.get('cancelled', 0),
              new.get('cnt', 0), usage.get('active_users', 0),
              round(float(usage.get('total_minutes', 0)), 1)))

        logger.info("[Billing Cron] 일간 요약 생성 완료")

    except Exception as e:
        logger.error(f"[Billing Cron] generate_billing_daily_summary 오류: {e}")


def cleanup_stale_orders():
    """24시간 지난 pending 주문 만료 처리 (매시간 실행)"""
    from models_billing import PaymentTransaction

    try:
        PaymentTransaction.expire_stale_orders()
    except Exception as e:
        logger.error(f"[Billing Cron] cleanup_stale_orders 오류: {e}")


# 스케줄러 인스턴스
_scheduler = None


def init_cleanup_scheduler():
    """
    정리 스케줄러 초기화
    매 시간마다 만료된 파일 정리
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("스케줄러가 이미 실행 중입니다")
        return _scheduler

    _scheduler = BackgroundScheduler()

    # 매 시간마다 만료 파일 정리
    _scheduler.add_job(
        cleanup_expired_audio_files,
        'interval',
        hours=1,
        id='cleanup_audio',
        name='음성 파일 정리'
    )

    # 매 30분마다 임시 파일 정리
    _scheduler.add_job(
        cleanup_temp_uploads,
        'interval',
        minutes=30,
        id='cleanup_temp',
        name='임시 파일 정리'
    )

    # 매일 03:00 구독 자동결제
    _scheduler.add_job(
        process_subscription_renewals,
        'cron',
        hour=3, minute=0,
        id='billing_renewals',
        name='구독 자동결제'
    )

    # 매일 04:00 결제 실패 구독 만료
    _scheduler.add_job(
        expire_past_due_subscriptions,
        'cron',
        hour=4, minute=0,
        id='billing_expire',
        name='구독 만료 처리'
    )

    # 매일 04:05 만료일 경과 구독 종료 (non-renewal)
    _scheduler.add_job(
        expire_ended_subscriptions,
        'cron',
        hour=4, minute=5,
        id='billing_expire_ended',
        name='구독 종료 처리 (만료일 경과)'
    )

    # 매일 10:00 만료 임박 알림
    _scheduler.add_job(
        notify_expiring_subscriptions,
        'cron',
        hour=10, minute=0,
        id='billing_expiring_notify',
        name='구독 만료 임박 알림'
    )

    # 매일 23:55 일간 과금 요약 생성
    _scheduler.add_job(
        generate_billing_daily_summary,
        'cron',
        hour=23, minute=55,
        id='billing_daily_summary',
        name='일간 과금 요약'
    )

    # 매시간 stale 주문 정리
    _scheduler.add_job(
        cleanup_stale_orders,
        'interval',
        hours=1,
        id='billing_stale_orders',
        name='만료 주문 정리'
    )

    _scheduler.start()
    logger.info("[Cleanup] 스케줄러 시작됨")

    # 시작 시 즉시 한 번 실행
    cleanup_expired_audio_files()
    cleanup_temp_uploads()

    return _scheduler


def shutdown_cleanup_scheduler():
    """스케줄러 종료"""
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("[Cleanup] 스케줄러 종료됨")


# 테스트용
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print(f"음성 폴더: {Config.AUDIO_FOLDER}")
    print(f"보관 시간: {Config.AUDIO_RETENTION_HOURS}시간")

    cleanup_expired_audio_files()
    cleanup_temp_uploads()
