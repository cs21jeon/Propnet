"""
디자인부 (@design-lead) Collector

Weekly only: UI 관련 커밋, 서비스 현황 요약 (Claude에게 경쟁사 비교 요청)
DB 직접 쿼리 없음 — 가장 가벼운 collector
"""
import subprocess
import logging
from config import Config
from collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class DesignCollector(BaseCollector):
    department = 'design'
    display_name = '디자인부'
    supports_daily = False
    supports_weekly = True

    def collect_weekly(self) -> dict:
        return {
            'ui_commits': self._get_ui_commits(),
            'service_summary': self._get_service_summary(),
        }

    def _get_ui_commits(self) -> list:
        """최근 1주 UI 관련 git 커밋"""
        try:
            cmd = (
                f"cd {Config.GIT_REPO_DIR} && "
                f"git log --since='7 days ago' --oneline --no-merges "
                f"-- '*.html' '*.css' 'templates/' 'static/' 'marketing/' "
                f"2>/dev/null | head -20"
            )
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=15
            )
            commits = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
            return commits
        except Exception as e:
            return [f"error: {e}"]

    def _get_service_summary(self) -> dict:
        """현재 서비스 구성 요약 (Claude 프롬프트용 컨텍스트)"""
        return {
            'services': [
                {
                    'name': 'PropSheet',
                    'type': '매물관리 스프레드시트',
                    'tech': 'HTMX + Alpine.js',
                    'target': '중개사',
                },
                {
                    'name': 'Propedia',
                    'type': '부동산 백과사전',
                    'tech': 'Flutter 앱 + 정적 웹',
                    'target': '일반 사용자 + 중개사',
                },
                {
                    'name': 'PropMap',
                    'type': '매물 지도',
                    'tech': '정적 HTML/JS',
                    'target': '일반 사용자',
                },
                {
                    'name': 'Proptalk',
                    'type': '업무 음성채팅',
                    'tech': 'Flutter 앱 + Flask',
                    'target': '중개사',
                },
            ],
            'competitors': [
                '직방', '다방', '호갱노노', '네이버 부동산',
                '피터팬의 좋은방 구하기', '부동산플래닛',
            ],
        }
