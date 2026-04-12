"""
개발부 (@dev-lead) Collector

Daily: 서비스 헬스체크, 에러 로그, 코드 변경
Weekly: 주간 커밋 요약, 반복 에러, 기술 부채
"""
import subprocess
import logging
import urllib.request
import urllib.error
from datetime import datetime
from collectors.base import BaseCollector
from config import Config

logger = logging.getLogger(__name__)


class DevCollector(BaseCollector):
    department = 'dev'
    display_name = '개발부'
    supports_daily = True
    supports_weekly = True

    def collect_daily(self) -> dict:
        return {
            'health_checks': self._check_service_health(),
            'recent_commits': self._get_recent_commits(since='yesterday'),
            'error_logs': self._get_error_logs(hours=24),
            'restart_count': self._get_restart_count(hours=24),
        }

    def collect_weekly(self) -> dict:
        return {
            'weekly_commits': self._get_recent_commits(since='7 days ago'),
            'commit_count': self._get_commit_count(days=7),
            'error_patterns': self._get_error_patterns(days=7),
            'health_checks': self._check_service_health(),
        }

    # 서비스별 실제 헬스체크 경로 (/ 대신 실제 라우트)
    HEALTH_PATHS = {
        'property-manager': '/services',
        'proppedia': '/app/api/health',
        'propsheet': '/propsheet/',
        'proptalk': '/proptalk/',
    }

    def _check_service_health(self) -> dict:
        """서비스별 HTTP 헬스체크"""
        results = {}
        for name, info in Config.SERVICES.items():
            port = info['port']
            path = self.HEALTH_PATHS.get(name, '/')
            try:
                url = f"http://127.0.0.1:{port}{path}"
                req = urllib.request.Request(url, method='GET')
                start = datetime.now()
                with urllib.request.urlopen(req, timeout=5) as resp:
                    elapsed = (datetime.now() - start).total_seconds()
                    results[name] = {
                        'status': resp.status,
                        'response_time_ms': round(elapsed * 1000),
                    }
            except urllib.error.HTTPError as e:
                results[name] = {'status': e.code, 'response_time_ms': None}
            except Exception as e:
                results[name] = {'status': 'unreachable', 'error': str(e)}
        return results

    def _get_recent_commits(self, since='yesterday') -> list:
        """최근 git 커밋"""
        try:
            cmd = (
                f"cd {Config.GIT_REPO_DIR} && "
                f"git log --since='{since}' --oneline --no-merges -20 2>/dev/null"
            )
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=15
            )
            commits = []
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    commits.append(line.strip())
            return commits
        except Exception as e:
            return [f"error: {e}"]

    def _get_commit_count(self, days=7) -> dict:
        """기간별 커밋 수"""
        try:
            cmd = (
                f"cd {Config.GIT_REPO_DIR} && "
                f"git log --since='{days} days ago' --oneline --no-merges 2>/dev/null | wc -l"
            )
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=15
            )
            return {'count': int(result.stdout.strip()) if result.stdout.strip() else 0}
        except Exception as e:
            return {'error': str(e)}

    def _get_error_logs(self, hours=24) -> dict:
        """journalctl에서 에러/traceback 추출"""
        errors = {}
        for name, info in Config.SERVICES.items():
            unit = info['systemd']
            try:
                cmd = (
                    f"journalctl -u {unit} --since '{hours} hours ago' --no-pager 2>/dev/null | "
                    f"grep -iE '(error|traceback|exception|critical)' | tail -5"
                )
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=15
                )
                lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
                errors[name] = {
                    'count': len(lines),
                    'recent': lines[-3:] if lines else [],
                }
            except Exception as e:
                errors[name] = {'error': str(e)}
        return errors

    def _get_restart_count(self, hours=24) -> dict:
        """서비스 재시작 횟수"""
        restarts = {}
        for name, info in Config.SERVICES.items():
            unit = info['systemd']
            try:
                cmd = (
                    f"journalctl -u {unit} --since '{hours} hours ago' --no-pager 2>/dev/null | "
                    f"grep -c 'Started\\|Stopped'"
                )
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=10
                )
                restarts[name] = int(result.stdout.strip()) if result.stdout.strip() else 0
            except Exception:
                restarts[name] = -1
        return restarts

    def _get_error_patterns(self, days=7) -> list:
        """반복 에러 패턴 (weekly)"""
        try:
            patterns = []
            for name, info in Config.SERVICES.items():
                unit = info['systemd']
                cmd = (
                    f"journalctl -u {unit} --since '{days} days ago' --no-pager 2>/dev/null | "
                    f"grep -iE '(error|exception)' | "
                    f"sed 's/[0-9]\\+//g' | sort | uniq -c | sort -rn | head -3"
                )
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=30
                )
                for line in result.stdout.strip().splitlines():
                    if line.strip():
                        patterns.append(f"[{name}] {line.strip()}")
            return patterns[:10]
        except Exception as e:
            return [f"error: {e}"]
