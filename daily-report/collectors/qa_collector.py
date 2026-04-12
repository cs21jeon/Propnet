"""
품질관리부 (@qa-lead) Collector

Daily: 결제 실패율, STT 성공률, 5xx 에러율
Weekly: 에러 트렌드, 결제 안정성, 보안 점검
"""
import logging
from datetime import date, timedelta
from collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class QACollector(BaseCollector):
    department = 'qa'
    display_name = '품질관리부'
    supports_daily = True
    supports_weekly = True

    def collect_daily(self) -> dict:
        return {
            'billing_errors': self._get_billing_errors(days=1),
            'payment_stats': self._get_payment_stats(days=1),
            'stt_usage': self._get_stt_usage(days=1),
        }

    def collect_weekly(self) -> dict:
        return {
            'billing_errors_7d': self._get_billing_errors(days=7),
            'payment_stats_7d': self._get_payment_stats(days=7),
            'stt_usage_7d': self._get_stt_usage(days=7),
            'daily_error_trend': self._get_daily_error_trend(),
        }

    def _get_billing_errors(self, days=1) -> dict:
        """billing_error_logs 에러 유형별 카운트"""
        try:
            with self.get_voice_db() as conn:
                since = date.today() - timedelta(days=days)
                rows = self.query_all(
                    conn,
                    """SELECT error_type, COUNT(*) as cnt
                       FROM billing_error_logs
                       WHERE created_at >= %s
                       GROUP BY error_type
                       ORDER BY cnt DESC""",
                    (since,)
                )
                total = sum(r['cnt'] for r in rows)
                return {
                    'total': total,
                    'by_type': {r['error_type']: r['cnt'] for r in rows},
                    'period_days': days,
                }
        except Exception as e:
            return {'error': str(e)}

    def _get_payment_stats(self, days=1) -> dict:
        """결제 성공/실패 비율"""
        try:
            with self.get_voice_db() as conn:
                since = date.today() - timedelta(days=days)
                rows = self.query_all(
                    conn,
                    """SELECT status, COUNT(*) as cnt
                       FROM payment_transactions
                       WHERE created_at >= %s
                       GROUP BY status""",
                    (since,)
                )
                stats = {r['status']: r['cnt'] for r in rows}
                total = sum(stats.values())
                approved = stats.get('approved', 0)
                success_rate = round(approved / total * 100, 1) if total > 0 else 0
                return {
                    'total': total,
                    'by_status': stats,
                    'success_rate_pct': success_rate,
                    'period_days': days,
                }
        except Exception as e:
            return {'error': str(e)}

    def _get_stt_usage(self, days=1) -> dict:
        """STT(Whisper) 사용량"""
        try:
            with self.get_voice_db() as conn:
                since = date.today() - timedelta(days=days)
                result = self.query_one(
                    conn,
                    """SELECT COUNT(*) as call_count,
                              COALESCE(SUM(seconds_used), 0) as total_seconds
                       FROM usage_logs
                       WHERE created_at >= %s""",
                    (since,)
                )
                return {
                    'calls': result.get('call_count', 0),
                    'total_minutes': round(result.get('total_seconds', 0) / 60, 1),
                    'period_days': days,
                }
        except Exception as e:
            return {'error': str(e)}

    def _get_daily_error_trend(self) -> list:
        """최근 7일 일별 에러 카운트 (weekly)"""
        try:
            with self.get_voice_db() as conn:
                since = date.today() - timedelta(days=7)
                rows = self.query_all(
                    conn,
                    """SELECT DATE(created_at) as dt, COUNT(*) as cnt
                       FROM billing_error_logs
                       WHERE created_at >= %s
                       GROUP BY DATE(created_at)
                       ORDER BY dt""",
                    (since,)
                )
                return [
                    {'date': r['dt'].isoformat() if hasattr(r['dt'], 'isoformat') else str(r['dt']),
                     'count': r['cnt']}
                    for r in rows
                ]
        except Exception as e:
            return [{'error': str(e)}]
