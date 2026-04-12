"""
그로스부 (@growth-lead) Collector

Daily: DAU (unique IP), 신규 가입, 신규 agent
Weekly: WAU 추이, referrer 분석, 7일 가입 추이
"""
import subprocess
import logging
from datetime import datetime, timedelta, date
from collectors.base import BaseCollector
from config import Config

logger = logging.getLogger(__name__)


class GrowthCollector(BaseCollector):
    department = 'growth'
    display_name = '그로스부'
    supports_daily = True
    supports_weekly = True

    def collect_daily(self) -> dict:
        return {
            'dau': self._get_dau(),
            'new_users_today': self._get_new_users(days=1),
            'new_agents_today': self._get_new_agents(days=1),
            'traffic_by_service': self._get_traffic_by_service(days=1),
        }

    def collect_weekly(self) -> dict:
        return {
            'wau': self._get_wau(),
            'daily_signups_7d': self._get_daily_signups(days=7),
            'daily_agents_7d': self._get_daily_agents(days=7),
            'top_referrers': self._get_top_referrers(),
            'traffic_by_service': self._get_traffic_by_service(days=7),
        }

    def _get_dau(self) -> dict:
        """오늘 unique IP 수 (Nginx access.log)"""
        try:
            cmd = (
                f"tail -n 50000 {Config.NGINX_ACCESS_LOG} 2>/dev/null | "
                f"awk '{{print $1}}' | sort -u | wc -l"
            )
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            return {'unique_ips': int(result.stdout.strip()) if result.stdout.strip() else 0}
        except Exception as e:
            return {'error': str(e)}

    def _get_wau(self) -> dict:
        """최근 7일 일별 unique IP"""
        try:
            # 최근 7일치 로그에서 날짜별 unique IP
            cmd = (
                f"tail -n 350000 {Config.NGINX_ACCESS_LOG} 2>/dev/null | "
                f"awk '{{split($4,a,\"[\"); split(a[2],b,\":\"); print b[1], $1}}' | "
                f"sort -u | awk '{{print $1}}' | sort | uniq -c | sort -rn | head -7"
            )
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            days = []
            for line in result.stdout.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    days.append({'count': int(parts[0]), 'date': parts[1]})
            return {'daily_unique_ips': days}
        except Exception as e:
            return {'error': str(e)}

    def _get_new_users(self, days=1) -> dict:
        """신규 가입 유저 수"""
        try:
            with self.get_main_db() as conn:
                since = date.today() - timedelta(days=days)
                count = self.query_scalar(
                    conn,
                    "SELECT COUNT(*) FROM propnet_users WHERE created_at >= %s",
                    (since,)
                )
                total = self.query_scalar(
                    conn,
                    "SELECT COUNT(*) FROM propnet_users WHERE is_active = TRUE"
                )
                return {'new': count or 0, 'total_active': total or 0}
        except Exception as e:
            return {'error': str(e)}

    def _get_new_agents(self, days=1) -> dict:
        """신규 agent 등록"""
        try:
            with self.get_main_db() as conn:
                since = date.today() - timedelta(days=days)
                count = self.query_scalar(
                    conn,
                    "SELECT COUNT(*) FROM agents WHERE created_at >= %s",
                    (since,)
                )
                total = self.query_scalar(
                    conn,
                    "SELECT COUNT(*) FROM agents WHERE is_active = TRUE"
                )
                pending = self.query_scalar(
                    conn,
                    "SELECT COUNT(*) FROM agents WHERE status = 'pending'"
                )
                return {
                    'new': count or 0,
                    'total_active': total or 0,
                    'pending_approval': pending or 0,
                }
        except Exception as e:
            return {'error': str(e)}

    def _get_daily_signups(self, days=7) -> list:
        """최근 N일간 일별 가입 수"""
        try:
            with self.get_main_db() as conn:
                since = date.today() - timedelta(days=days)
                rows = self.query_all(
                    conn,
                    """SELECT DATE(created_at) as dt, COUNT(*) as cnt
                       FROM propnet_users
                       WHERE created_at >= %s
                       GROUP BY DATE(created_at)
                       ORDER BY dt""",
                    (since,)
                )
                return [{'date': r['dt'].isoformat() if hasattr(r['dt'], 'isoformat') else str(r['dt']),
                         'count': r['cnt']} for r in rows]
        except Exception as e:
            return [{'error': str(e)}]

    def _get_daily_agents(self, days=7) -> list:
        """최근 N일간 일별 agent 등록 수"""
        try:
            with self.get_main_db() as conn:
                since = date.today() - timedelta(days=days)
                rows = self.query_all(
                    conn,
                    """SELECT DATE(created_at) as dt, COUNT(*) as cnt
                       FROM agents
                       WHERE created_at >= %s
                       GROUP BY DATE(created_at)
                       ORDER BY dt""",
                    (since,)
                )
                return [{'date': r['dt'].isoformat() if hasattr(r['dt'], 'isoformat') else str(r['dt']),
                         'count': r['cnt']} for r in rows]
        except Exception as e:
            return [{'error': str(e)}]

    def _get_top_referrers(self, limit=10) -> list:
        """Nginx 로그에서 상위 referrer"""
        try:
            cmd = (
                f'tail -n 350000 {Config.NGINX_ACCESS_LOG} 2>/dev/null | '
                f'awk -F\'"\' \'{{print $4}}\' | '
                f'grep -v "^-$" | grep -v "^$" | '
                f'sort | uniq -c | sort -rn | head -{limit}'
            )
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            referrers = []
            for line in result.stdout.strip().splitlines():
                parts = line.strip().split(None, 1)
                if len(parts) >= 2:
                    referrers.append({'count': int(parts[0]), 'referrer': parts[1]})
            return referrers
        except Exception as e:
            return [{'error': str(e)}]

    def _get_traffic_by_service(self, days=1) -> dict:
        """서비스별 트래픽 분류"""
        try:
            lines_to_read = days * 50000
            services = {
                'propsheet': '/propsheet/',
                'proptalk': '/proptalk/',
                'propedia': '/app/',
                'propmap': '/propmap/',
                'homepage': '/ ',
            }
            result = {}
            for name, pattern in services.items():
                cmd = (
                    f"tail -n {lines_to_read} {Config.NGINX_ACCESS_LOG} 2>/dev/null | "
                    f"grep -c '{pattern}'"
                )
                out = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=15
                )
                result[name] = int(out.stdout.strip()) if out.stdout.strip() else 0
            return result
        except Exception as e:
            return {'error': str(e)}
