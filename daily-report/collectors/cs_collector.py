"""
CS/운영부 (@cs-lead) Collector

Daily: 구독 현황, 이탈, 비활성화, billing 요약
Weekly: 구독 변동 추이, 이탈 패턴, FAQ 갭
"""
import logging
from datetime import date, timedelta
from collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class CSCollector(BaseCollector):
    department = 'cs'
    display_name = 'CS/운영부'
    supports_daily = True
    supports_weekly = True

    def collect_daily(self) -> dict:
        return {
            'subscription_status': self._get_subscription_distribution(),
            'churn_yesterday': self._get_churn(days=1),
            'deactivated_users': self._get_deactivated_users(days=1),
            'billing_summary': self._get_billing_daily_summary(),
        }

    def collect_weekly(self) -> dict:
        return {
            'subscription_status': self._get_subscription_distribution(),
            'churn_7d': self._get_churn(days=7),
            'deactivated_users_7d': self._get_deactivated_users(days=7),
            'subscription_trend': self._get_subscription_trend(),
        }

    def _get_subscription_distribution(self) -> dict:
        """구독 상태 분포"""
        try:
            with self.get_voice_db() as conn:
                rows = self.query_all(
                    conn,
                    """SELECT subscription_status, COUNT(*) as cnt
                       FROM user_billing
                       GROUP BY subscription_status"""
                )
                return {r['subscription_status']: r['cnt'] for r in rows}
        except Exception as e:
            return {'error': str(e)}

    def _get_churn(self, days=1) -> dict:
        """이탈 (구독 만료/취소)"""
        try:
            with self.get_voice_db() as conn:
                since = date.today() - timedelta(days=days)
                # expired 전환 건수
                expired = self.query_scalar(
                    conn,
                    """SELECT COUNT(*) FROM user_billing
                       WHERE subscription_status IN ('expired', 'cancelled')
                       AND updated_at >= %s""",
                    (since,)
                )
                return {
                    'churned': expired or 0,
                    'period_days': days,
                }
        except Exception as e:
            return {'error': str(e)}

    def _get_deactivated_users(self, days=1) -> dict:
        """비활성화 유저"""
        try:
            with self.get_main_db() as conn:
                since = date.today() - timedelta(days=days)
                count = self.query_scalar(
                    conn,
                    """SELECT COUNT(*) FROM propnet_users
                       WHERE is_active = FALSE AND updated_at >= %s""",
                    (since,)
                )
                total_inactive = self.query_scalar(
                    conn,
                    "SELECT COUNT(*) FROM propnet_users WHERE is_active = FALSE"
                )
                return {
                    'recent': count or 0,
                    'total_inactive': total_inactive or 0,
                    'period_days': days,
                }
        except Exception as e:
            return {'error': str(e)}

    def _get_billing_daily_summary(self) -> dict:
        """billing_daily_summary (어제 23:55에 생성됨)"""
        try:
            with self.get_voice_db() as conn:
                yesterday = date.today() - timedelta(days=1)
                row = self.query_one(
                    conn,
                    """SELECT date, total_transactions, successful_transactions,
                              failed_transactions, total_revenue, refunded_amount,
                              active_subscriptions, cancelled_subscriptions,
                              new_users, active_users, total_usage_minutes
                       FROM billing_daily_summary
                       WHERE date = %s""",
                    (yesterday,)
                )
                if row:
                    return {k: str(v) if hasattr(v, 'isoformat') else v
                            for k, v in row.items()}
                return {'message': '어제 요약 데이터 없음'}
        except Exception as e:
            return {'error': str(e)}

    def _get_subscription_trend(self) -> list:
        """최근 7일 구독 변동 추이 (weekly)"""
        try:
            with self.get_voice_db() as conn:
                since = date.today() - timedelta(days=7)
                rows = self.query_all(
                    conn,
                    """SELECT date,
                              total_revenue,
                              total_transactions,
                              new_users
                       FROM billing_daily_summary
                       WHERE date >= %s
                       ORDER BY date""",
                    (since,)
                )
                return [
                    {k: str(v) if hasattr(v, 'isoformat') else v for k, v in r.items()}
                    for r in rows
                ]
        except Exception as e:
            return [{'error': str(e)}]
