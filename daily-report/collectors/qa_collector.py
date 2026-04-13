"""
품질관리부 (@qa-lead) Collector

Daily: 결제 실패율, STT 성공률, 서비스 에러 카운트
Weekly: 에러 트렌드, 결제 안정성, 서비스별 에러 추이
"""
import logging
import subprocess
from datetime import date, timedelta
from collectors.base import BaseCollector
from config import Config

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
            'service_errors': self._get_service_error_counts(hours=24),
        }

    def collect_weekly(self) -> dict:
        return {
            'billing_errors_7d': self._get_billing_errors(days=7),
            'payment_stats_7d': self._get_payment_stats(days=7),
            'stt_usage_7d': self._get_stt_usage(days=7),
            'daily_error_trend': self._get_daily_error_trend(),
            'service_error_trend_7d': self._get_service_error_trend(days=7),
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
        """최근 7일 일별 과금 에러 카운트 (weekly)"""
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

    def _get_service_error_counts(self, hours=24) -> dict:
        """journalctl 기반 서비스별 에러 카운트 (daily)"""
        results = {}
        for name, info in Config.SERVICES.items():
            unit = info['systemd']
            try:
                cmd = (
                    f"journalctl -u {unit} --since '{hours} hours ago' --no-pager 2>/dev/null | "
                    f"grep -ciE '(error|exception|traceback|critical)'"
                )
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=15
                )
                count = int(result.stdout.strip()) if result.stdout.strip() else 0
                results[name] = count
            except Exception as e:
                results[name] = f"error: {e}"
        results['total'] = sum(v for v in results.values() if isinstance(v, int))
        return results

    def _get_service_error_trend(self, days=7) -> dict:
        """journalctl 기반 서비스별 일간 에러 추이 (weekly)"""
        trend = {}
        for name, info in Config.SERVICES.items():
            unit = info['systemd']
            daily_counts = []
            for d in range(days, 0, -1):
                try:
                    since_date = (date.today() - timedelta(days=d)).isoformat()
                    until_date = (date.today() - timedelta(days=d-1)).isoformat()
                    cmd = (
                        f"journalctl -u {unit} --since '{since_date}' --until '{until_date}' --no-pager 2>/dev/null | "
                        f"grep -ciE '(error|exception|traceback|critical)'"
                    )
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True, timeout=10
                    )
                    count = int(result.stdout.strip()) if result.stdout.strip() else 0
                    daily_counts.append({
                        'date': since_date,
                        'count': count,
                    })
                except Exception:
                    daily_counts.append({
                        'date': since_date,
                        'count': -1,
                    })
            trend[name] = daily_counts
        return trend
