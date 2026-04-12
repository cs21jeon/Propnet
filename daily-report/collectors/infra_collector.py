"""
인프라부 (@infra-lead) Collector

Daily: 서버 상태, 서비스 가동, 5xx 에러, DB 연결
Weekly: DB 크기 추이, 디스크 증가율, 응답시간 추이
"""
import subprocess
import logging
from datetime import datetime, timedelta
from collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class InfraCollector(BaseCollector):
    department = 'infra'
    display_name = '인프라부'
    supports_daily = True
    supports_weekly = True

    def collect_daily(self) -> dict:
        return {
            'server_status': self._get_server_status(),
            'services': self._get_service_status(),
            'nginx_errors': self._get_nginx_5xx_count(),
            'db_connectivity': self._check_db_connectivity(),
        }

    def collect_weekly(self) -> dict:
        return {
            'db_sizes': self._get_db_sizes(),
            'disk_usage': self._get_disk_usage_detail(),
            'services': self._get_service_status(),
            'nginx_errors_7d': self._get_nginx_5xx_count(days=7),
        }

    def _get_server_status(self) -> dict:
        """CPU, RAM, 디스크 사용률"""
        result = {}
        try:
            # CPU 사용률 (1초 평균)
            load = self._read_file('/proc/loadavg')
            if load:
                parts = load.split()
                result['load_1m'] = float(parts[0])
                result['load_5m'] = float(parts[1])
                result['load_15m'] = float(parts[2])

            # 메모리
            meminfo = self._read_file('/proc/meminfo')
            if meminfo:
                mem = {}
                for line in meminfo.splitlines():
                    if ':' in line:
                        key, val = line.split(':', 1)
                        mem[key.strip()] = int(val.strip().split()[0])  # kB
                total = mem.get('MemTotal', 1)
                available = mem.get('MemAvailable', 0)
                used = total - available
                result['ram_total_mb'] = round(total / 1024)
                result['ram_used_mb'] = round(used / 1024)
                result['ram_usage_pct'] = round(used / total * 100, 1)

            # 디스크
            df_output = self._run_cmd('df -h / --output=size,used,avail,pcent')
            if df_output:
                lines = df_output.strip().splitlines()
                if len(lines) >= 2:
                    parts = lines[1].split()
                    result['disk_total'] = parts[0]
                    result['disk_used'] = parts[1]
                    result['disk_avail'] = parts[2]
                    result['disk_usage_pct'] = parts[3]
        except Exception as e:
            logger.error(f"서버 상태 수집 실패: {e}")
            result['error'] = str(e)
        return result

    def _get_service_status(self) -> dict:
        """systemd 서비스 상태 확인"""
        from config import Config
        services = {}
        for name, info in Config.SERVICES.items():
            unit = info['systemd']
            status = self._run_cmd(f'systemctl is-active {unit}')
            services[name] = {
                'status': status.strip() if status else 'unknown',
                'port': info['port'],
            }
        return services

    def _get_nginx_5xx_count(self, days=1) -> dict:
        """Nginx access.log에서 5xx 에러 카운트"""
        from config import Config
        try:
            # tail로 최근 N일분만 읽기 (약 50000줄/일 가정)
            lines_to_read = days * 50000
            cmd = (
                f"tail -n {lines_to_read} {Config.NGINX_ACCESS_LOG} 2>/dev/null | "
                f"awk '{{print $9}}' | grep -c '^5'"
            )
            count_5xx = self._run_cmd(cmd)
            total_cmd = (
                f"tail -n {lines_to_read} {Config.NGINX_ACCESS_LOG} 2>/dev/null | "
                f"wc -l"
            )
            total = self._run_cmd(total_cmd)
            return {
                'count_5xx': int(count_5xx.strip()) if count_5xx else 0,
                'total_requests': int(total.strip()) if total else 0,
                'period_days': days,
            }
        except Exception as e:
            logger.error(f"Nginx 5xx 수집 실패: {e}")
            return {'error': str(e)}

    def _check_db_connectivity(self) -> dict:
        """DB 연결 상태 체크"""
        result = {}
        try:
            with self.get_main_db() as conn:
                result['goldenrabbit_db'] = 'connected'
        except Exception as e:
            result['goldenrabbit_db'] = f'failed: {e}'

        try:
            with self.get_voice_db() as conn:
                result['voiceroom'] = 'connected'
        except Exception as e:
            result['voiceroom'] = f'failed: {e}'
        return result

    def _get_db_sizes(self) -> dict:
        """DB 크기 조회 (weekly)"""
        result = {}
        try:
            with self.get_main_db() as conn:
                size = self.query_scalar(
                    conn, "SELECT pg_database_size('goldenrabbit_db')"
                )
                result['goldenrabbit_db_mb'] = round(size / 1024 / 1024, 1) if size else 0
        except Exception as e:
            result['goldenrabbit_db_error'] = str(e)

        try:
            with self.get_voice_db() as conn:
                size = self.query_scalar(
                    conn, "SELECT pg_database_size('voiceroom')"
                )
                result['voiceroom_mb'] = round(size / 1024 / 1024, 1) if size else 0
        except Exception as e:
            result['voiceroom_error'] = str(e)
        return result

    def _get_disk_usage_detail(self) -> dict:
        """디스크 상세 사용량 (weekly)"""
        result = {}
        try:
            # 주요 디렉토리 크기
            dirs_to_check = [
                ('/home/webapp/goldenrabbit', 'goldenrabbit_total'),
                ('/home/webapp/goldenrabbit/chat_stt/uploads', 'proptalk_uploads'),
                ('/home/webapp/goldenrabbit/uploads', 'propsheet_uploads'),
                ('/var/log/nginx', 'nginx_logs'),
            ]
            for path, label in dirs_to_check:
                size = self._run_cmd(f'du -sh {path} 2>/dev/null')
                if size:
                    result[label] = size.split()[0]
        except Exception as e:
            result['error'] = str(e)
        return result

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception:
            return ''

    @staticmethod
    def _run_cmd(cmd: str) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            return result.stdout
        except Exception:
            return ''
