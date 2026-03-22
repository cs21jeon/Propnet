"""
VoiceRoom - 음성 채팅방 STT 플랫폼
메인 Flask 앱
"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config

# ============================================================
# 로깅 설정
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('voiceroom.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# Flask 앱 생성
# ============================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# CORS 허용
CORS(app, origins=['*'])

# SocketIO 초기화
socketio = SocketIO(
    app, 
    cors_allowed_origins='*',
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
)

# ============================================================
# 업로드 및 음성 폴더 생성
# ============================================================
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.AUDIO_FOLDER, exist_ok=True)

# ============================================================
# 라우트 등록
# ============================================================
from auth import register_auth_routes
from routes_rooms import register_room_routes
from routes_messages import register_message_routes
from routes_billing import register_billing_routes
from billing_web import register_billing_web_routes
from routes_admin import register_admin_routes
from websocket import register_websocket

register_auth_routes(app)
register_room_routes(app)
register_message_routes(app, socketio)
register_billing_routes(app)
register_billing_web_routes(app)
register_admin_routes(app)
register_websocket(socketio)

# ============================================================
# 헬스체크
# ============================================================
@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok', 'service': 'VoiceRoom STT'}

# ============================================================
# JSON 직렬화 커스텀 (datetime, date 처리)
# ============================================================
import json
from datetime import datetime, date

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

app.json_provider_class = None  # Flask 3.x
app.json = None

# Flask 3.x 호환
from flask.json.provider import DefaultJSONProvider
class CustomProvider(DefaultJSONProvider):
    @staticmethod
    def default(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f'Object of type {type(obj)} is not JSON serializable')

app.json_provider_class = CustomProvider
app.json = CustomProvider(app)

# ============================================================
# 파일 정리 스케줄러 초기화
# ============================================================
from cleanup_service import init_cleanup_scheduler
init_cleanup_scheduler()

# ============================================================
# 메인
# ============================================================
if __name__ == '__main__':
    logger.info(f"VoiceRoom 서버 시작: {Config.HOST}:{Config.PORT}")
    logger.info(f"Whisper 모델: {Config.WHISPER_MODEL}")
    logger.info(f"파일 보관 시간: {Config.AUDIO_RETENTION_HOURS}시간")

    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True
    )
