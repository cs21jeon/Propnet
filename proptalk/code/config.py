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
    # 서버 사이드 검증에만 사용 (client_id로 id_token 검증)
    
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
    # Whisper STT
    # ============================================================
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'small')
    
    # ============================================================
    # 파일 업로드
    # ============================================================
    UPLOAD_FOLDER = os.environ.get(
        'UPLOAD_FOLDER',
        '/home/hosting_users/goldenrabbit/chat_stt/uploads'
    )
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'webm', 'mp4', 'aac'}
    
    # ============================================================
    # 서버
    # ============================================================
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5060))
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
