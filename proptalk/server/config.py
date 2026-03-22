"""
VoiceRoom 서버 설정
"""
import os
from datetime import timedelta

class Config:
    # ============================================================
    # 기본 설정
    # ============================================================
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-to-random-secret-key')
    
    # ============================================================
    # PostgreSQL
    # ============================================================
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'voiceroom')
    DB_USER = os.environ.get('DB_USER', 'goldenrabbit')
    DB_PASS = os.environ.get('DB_PASS', 'your-db-password')
    
    DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    
    # ============================================================
    # JWT 인증
    # ============================================================
    JWT_SECRET = os.environ.get('JWT_SECRET', 'change-this-jwt-secret')
    JWT_EXPIRY = timedelta(days=30)
    
    # ============================================================
    # Google OAuth
    # ============================================================
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    # ============================================================
    # Google Drive API
    # ============================================================
    # Service Account JSON 파일 경로
    GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get(
        'GOOGLE_SERVICE_ACCOUNT_FILE', 
        '/home/hosting_users/goldenrabbit/chat_stt/credentials/service-account.json'
    )
    # Drive 저장 폴더 ID
    GOOGLE_DRIVE_FOLDER_ID = os.environ.get('GOOGLE_DRIVE_FOLDER_ID', '')
    
    # ============================================================
    # Claude API (요약 기능)
    # ============================================================
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')

    # ============================================================
    # Whisper STT
    # ============================================================
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_ADMIN_KEY = os.environ.get('OPENAI_ADMIN_KEY', '')
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'small')
    
    # ============================================================
    # 파일 업로드 및 저장
    # ============================================================
    UPLOAD_FOLDER = os.environ.get(
        'UPLOAD_FOLDER',
        '/home/webapp/goldenrabbit/chat_stt/uploads'
    )
    AUDIO_FOLDER = os.environ.get(
        'AUDIO_FOLDER',
        '/home/webapp/goldenrabbit/chat_stt/audio'
    )
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'webm', 'mp4', 'aac'}
    ALLOWED_FILE_EXTENSIONS = {
        'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp',
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'txt', 'csv', 'json', 'zip',
    }
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

    # 파일 보관 시간 (시간 단위) - 이후 자동 삭제
    AUDIO_RETENTION_HOURS = int(os.environ.get('AUDIO_RETENTION_HOURS', '24'))

    # Google Drive 백업 활성화 여부 (선택 사항)
    ENABLE_GOOGLE_DRIVE_BACKUP = os.environ.get('ENABLE_DRIVE_BACKUP', 'false').lower() == 'true'
    
    # ============================================================
    # 토스페이먼츠 결제
    # ============================================================
    TOSS_CLIENT_KEY = os.environ.get('TOSS_CLIENT_KEY', '')
    TOSS_SECRET_KEY = os.environ.get('TOSS_SECRET_KEY', '')
    TOSS_WEBHOOK_SECRET = os.environ.get('TOSS_WEBHOOK_SECRET', '')
    # AES-256 암호화 키 (64자 hex = 32바이트), billingKey 암호화용
    BILLING_ENCRYPTION_KEY = os.environ.get('BILLING_ENCRYPTION_KEY', '')

    # ============================================================
    # 관리자
    # ============================================================
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

    # ============================================================
    # 서버
    # ============================================================
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5060))
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
