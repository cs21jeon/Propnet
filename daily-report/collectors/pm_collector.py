"""
제품기획부 (@pm-lead) Collector

Weekly only: 유저 현황, workspace 사용률, agent 현황, 기능 우선순위
"""
import logging
from datetime import date, timedelta
from collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class PMCollector(BaseCollector):
    department = 'pm'
    display_name = '제품기획부'
    supports_daily = False
    supports_weekly = True

    def collect_weekly(self) -> dict:
        return {
            'user_stats': self._get_user_stats(),
            'agent_stats': self._get_agent_stats(),
            'workspace_stats': self._get_workspace_stats(),
            'user_growth_7d': self._get_user_growth(days=7),
        }

    def _get_user_stats(self) -> dict:
        """유저 역할별 현황"""
        try:
            with self.get_main_db() as conn:
                rows = self.query_all(
                    conn,
                    """SELECT role, COUNT(*) as cnt
                       FROM propnet_users
                       WHERE is_active = TRUE
                       GROUP BY role"""
                )
                total = sum(r['cnt'] for r in rows)
                return {
                    'total_active': total,
                    'by_role': {r['role']: r['cnt'] for r in rows},
                }
        except Exception as e:
            return {'error': str(e)}

    def _get_agent_stats(self) -> dict:
        """agent 현황"""
        try:
            with self.get_main_db() as conn:
                total = self.query_scalar(
                    conn, "SELECT COUNT(*) FROM agents"
                )
                active = self.query_scalar(
                    conn, "SELECT COUNT(*) FROM agents WHERE is_active = TRUE"
                )
                pending = self.query_scalar(
                    conn, "SELECT COUNT(*) FROM agents WHERE status = 'pending'"
                )
                return {
                    'total': total or 0,
                    'active': active or 0,
                    'pending': pending or 0,
                }
        except Exception as e:
            return {'error': str(e)}

    def _get_workspace_stats(self) -> dict:
        """PropSheet workspace/database 현황"""
        try:
            with self.get_main_db() as conn:
                ws_count = self.query_scalar(
                    conn, "SELECT COUNT(*) FROM workspaces"
                )
                db_count = self.query_scalar(
                    conn, "SELECT COUNT(*) FROM databases"
                )
                member_count = self.query_scalar(
                    conn, "SELECT COUNT(*) FROM workspace_members"
                )
                # 역할별 멤버 분포
                roles = self.query_all(
                    conn,
                    """SELECT role, COUNT(*) as cnt
                       FROM workspace_members
                       GROUP BY role"""
                )
                return {
                    'workspaces': ws_count or 0,
                    'databases': db_count or 0,
                    'total_members': member_count or 0,
                    'member_roles': {r['role']: r['cnt'] for r in roles},
                }
        except Exception as e:
            return {'error': str(e)}

    def _get_user_growth(self, days=7) -> list:
        """최근 N일간 일별 가입 + 역할 분포"""
        try:
            with self.get_main_db() as conn:
                since = date.today() - timedelta(days=days)
                rows = self.query_all(
                    conn,
                    """SELECT DATE(created_at) as dt, role, COUNT(*) as cnt
                       FROM propnet_users
                       WHERE created_at >= %s
                       GROUP BY DATE(created_at), role
                       ORDER BY dt""",
                    (since,)
                )
                return [
                    {'date': r['dt'].isoformat() if hasattr(r['dt'], 'isoformat') else str(r['dt']),
                     'role': r['role'], 'count': r['cnt']}
                    for r in rows
                ]
        except Exception as e:
            return [{'error': str(e)}]
