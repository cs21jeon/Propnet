"""
PropNet 보고 시스템 설정
환경변수는 서버의 /home/webapp/goldenrabbit/backend/.env에서 로드
"""
import os
from pathlib import Path

# .env 파일 로드 (dotenv 없이 직접 파싱)
def _load_env(env_path=None):
    """간단한 .env 파일 파서"""
    if env_path is None:
        env_path = os.environ.get('ENV_FILE', '/home/webapp/goldenrabbit/backend/.env')
    path = Path(env_path)
    if not path.exists():
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = value

_load_env()

# Proptalk 전용 .env도 로드 (voiceroom DB 접속 정보)
_load_env(os.environ.get('PROPTALK_ENV_FILE', '/home/webapp/goldenrabbit/chat_stt/server/.env'))


class Config:
    # ============================================================
    # PostgreSQL - goldenrabbit_db (공유 DB)
    # ============================================================
    MAIN_DB_HOST = os.environ.get('DB_HOST', 'localhost')
    MAIN_DB_PORT = os.environ.get('DB_PORT', '5432')
    MAIN_DB_NAME = os.environ.get('DB_NAME', 'goldenrabbit_db')
    MAIN_DB_USER = os.environ.get('DB_USER', 'goldenrabbit')
    MAIN_DB_PASS = os.environ.get('DB_PASS', '')

    # ============================================================
    # PostgreSQL - voiceroom (Proptalk 전용)
    # ============================================================
    VOICE_DB_HOST = os.environ.get('DB_HOST', 'localhost')
    VOICE_DB_PORT = os.environ.get('DB_PORT', '5432')
    VOICE_DB_NAME = 'voiceroom'
    VOICE_DB_USER = os.environ.get('DB_USER', 'goldenrabbit')
    VOICE_DB_PASS = os.environ.get('DB_PASS', '')

    # ============================================================
    # Claude API
    # ============================================================
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')

    # ============================================================
    # Email (Gmail SMTP)
    # ============================================================
    EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS', '')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    REPORT_RECIPIENT = os.environ.get('REPORT_RECIPIENT', 'cs21.jeon@gmail.com')

    # ============================================================
    # 경로
    # ============================================================
    BACKEND_DIR = '/home/webapp/goldenrabbit/backend'
    NGINX_ACCESS_LOG = '/var/log/nginx/access.log'
    REPORT_OUTPUT_DIR = '/home/webapp/goldenrabbit/backend/daily-report/reports'
    GIT_REPO_DIR = '/home/webapp/goldenrabbit'

    # ============================================================
    # 서비스 포트
    # ============================================================
    SERVICES = {
        'property-manager': {'port': 5000, 'systemd': 'property-manager'},
        'proppedia': {'port': 5010, 'systemd': 'proppedia'},
        'propsheet': {'port': 5020, 'systemd': 'propsheet'},
        'proptalk': {'port': 5030, 'systemd': 'proptalk'},
    }
