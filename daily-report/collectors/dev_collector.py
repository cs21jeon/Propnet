"""
개발부 (@dev-lead) Collector

Daily: 서비스 헬스체크, 에러 로그, 코드 변경, 보안 위협 분류
Weekly: 주간 커밋 요약, 반복 에러, 기술 부채
"""
import re
import subprocess
import logging
import urllib.request
import urllib.error
from datetime import datetime
from collections import defaultdict
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
            'security_threats': self._analyze_security_threats(hours=24),
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

    # ================================================================
    # 보안 위협 분류
    # ================================================================

    # 실제 악의적 공격 패턴 (Nginx access.log 기준)
    MALICIOUS_PATTERNS = [
        # SQL Injection
        (r"(UNION\s+SELECT|OR\s+1\s*=\s*1|;\s*DROP\s|SLEEP\s*\(|BENCHMARK\s*\(|'--)", 'SQL Injection'),
        # Path Traversal
        (r"(\.\./|\.\.%2[fF]|/etc/passwd|/etc/shadow|/proc/self)", 'Path Traversal'),
        # 환경변수/설정파일 탈취 시도
        (r"(GET|HEAD|POST)\s+/\.env", 'Config File Access (.env)'),
        (r"(GET|HEAD)\s+/\.git", 'Git Repo Access'),
        (r"(GET|HEAD)\s+.*\.(bak|sql|dump|tar\.gz|zip)\s", 'Backup File Access'),
        # 알려진 취약 소프트웨어 탐색
        (r"/(wp-admin|wp-login|wordpress|wp-content|wp-includes)", 'WordPress Probe'),
        (r"/(phpmyadmin|pma|myadmin|dbadmin|adminer)", 'DB Admin Probe'),
        (r"/(cgi-bin|shell|cmd|exec|system)", 'CGI/Shell Probe'),
        (r"/(actuator|jolokia|console|manager/html)", 'Java Admin Probe'),
        # XSS
        (r"(<script|javascript:|onerror\s*=|onload\s*=)", 'XSS Attempt'),
        # Shell Injection
        (r"(;\s*(cat|ls|whoami|id|uname|wget|curl)\s|`[^`]+`|\$\()", 'Shell Injection'),
        # 크리덴셜 스터핑 (로그인 반복은 별도 카운트)
        (r"POST\s+.*(login|auth|signin|token).*\s(401|403)", 'Auth Brute Force'),
    ]

    # 일상적 스캔/노이즈 패턴 (journalctl 에러 기준)
    NOISE_PATTERNS = [
        (r"Bad request version", 'Port Scan (bad version)'),
        (r"Bad HTTP/0\.9 request", 'Port Scan (HTTP/0.9)'),
        (r"code 400, message Bad request syntax", 'Port Scan (bad syntax)'),
        (r"Invalid HTTP request", 'Port Scan (invalid request)'),
        (r"socket shutdown error.*Bad file descriptor", 'Socket Cleanup (normal)'),
    ]

    def _analyze_security_threats(self, hours=24) -> dict:
        """Nginx access.log + journalctl에서 보안 위협을 분류"""
        result = {
            'malicious': [],       # 실제 악의적 공격
            'noise': [],           # 일상적 스캔/노이즈
            'malicious_ips': {},   # 악의적 IP별 카운트
            'noise_ips': {},       # 노이즈 IP별 카운트
            'summary': {},
        }

        # 1) Nginx access.log에서 악의적 패턴 탐지
        try:
            nginx_malicious = self._scan_nginx_malicious(hours)
            result['malicious'] = nginx_malicious['entries']
            result['malicious_ips'] = nginx_malicious['by_ip']
        except Exception as e:
            logger.error(f"Nginx 보안 분석 실패: {e}")
            result['malicious'] = [{'error': str(e)}]

        # 2) journalctl 에러를 노이즈 vs 실제 에러로 분류
        try:
            noise_result = self._classify_service_errors(hours)
            result['noise'] = noise_result['noise']
            result['noise_ips'] = noise_result['noise_ips']
        except Exception as e:
            logger.error(f"에러 분류 실패: {e}")

        # 3) 요약
        result['summary'] = {
            'malicious_total': len(result['malicious']),
            'malicious_unique_ips': len(result['malicious_ips']),
            'noise_total': len(result['noise']),
            'noise_unique_ips': len(result['noise_ips']),
            'verdict': self._get_verdict(result),
        }

        return result

    def _scan_nginx_malicious(self, hours=24) -> dict:
        """Nginx access.log에서 악의적 요청 패턴 탐지"""
        entries = []
        by_ip = defaultdict(lambda: {'count': 0, 'types': set()})
        lines_to_read = hours * 3000  # 시간당 약 3000줄 추정

        cmd = f"tail -n {lines_to_read} {Config.NGINX_ACCESS_LOG} 2>/dev/null"
        raw = self._run_cmd_output(cmd)
        if not raw:
            return {'entries': [], 'by_ip': {}}

        for line in raw.splitlines():
            for pattern, label in self.MALICIOUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # IP 추출 (Nginx combined log format: IP가 첫 필드)
                    ip = line.split()[0] if line.split() else 'unknown'
                    entries.append({
                        'type': label,
                        'ip': ip,
                        'log': line[:200],  # 200자로 자르기
                    })
                    by_ip[ip]['count'] += 1
                    by_ip[ip]['types'].add(label)
                    break  # 한 줄에 한 패턴만 매칭

        # set → list 변환 (JSON 직렬화)
        by_ip_clean = {}
        for ip, info in by_ip.items():
            by_ip_clean[ip] = {
                'count': info['count'],
                'types': list(info['types']),
            }

        return {'entries': entries[-20:], 'by_ip': by_ip_clean}  # 최근 20건만

    def _classify_service_errors(self, hours=24) -> dict:
        """journalctl 에러 로그를 노이즈/실제 에러로 분류"""
        noise_entries = []
        noise_ips = defaultdict(int)

        for name, info in Config.SERVICES.items():
            unit = info['systemd']
            cmd = (
                f"journalctl -u {unit} --since '{hours} hours ago' --no-pager 2>/dev/null | "
                f"grep -iE '(error|exception|critical)'"
            )
            raw = self._run_cmd_output(cmd)
            if not raw:
                continue

            for line in raw.splitlines():
                is_noise = False
                for pattern, label in self.NOISE_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # IP 추출 시도
                        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                        ip = ip_match.group(1) if ip_match else 'unknown'
                        noise_entries.append({
                            'service': name,
                            'type': label,
                            'ip': ip,
                        })
                        if ip != 'unknown':
                            noise_ips[ip] += 1
                        is_noise = True
                        break

        return {
            'noise': noise_entries[-20:],  # 최근 20건
            'noise_ips': dict(noise_ips),
        }

    def _get_verdict(self, result: dict) -> str:
        """종합 판정"""
        mal = len(result['malicious'])
        noise = len(result['noise'])
        mal_ips = len(result['malicious_ips'])

        if mal == 0 and noise == 0:
            return '보안 이상 없음'
        if mal == 0:
            return f'일상적 스캔만 감지 ({noise}건) — 조치 불필요'
        if mal_ips >= 3 or mal >= 10:
            return f'⚠️ 실제 공격 다수 감지 ({mal}건, {mal_ips}개 IP) — 즉시 점검 필요'
        return f'공격 시도 감지 ({mal}건, {mal_ips}개 IP) — 모니터링 권장'

    @staticmethod
    def _run_cmd_output(cmd: str) -> str:
        """shell 명령 실행 후 stdout 반환"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            return result.stdout
        except Exception:
            return ''

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
