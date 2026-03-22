"""
Google OAuth 인증 + JWT 토큰 관리
"""
import jwt
import logging
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, g
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config import Config
from models import User

logger = logging.getLogger(__name__)


# ============================================================
# JWT 토큰 생성/검증
# ============================================================
def create_token(user_id):
    """JWT 토큰 생성"""
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + Config.JWT_EXPIRY,
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')


def decode_token(token):
    """JWT 토큰 디코딩"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============================================================
# 인증 데코레이터
# ============================================================
def login_required(f):
    """로그인 필수 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Authorization 헤더에서 토큰 추출
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': '인증 토큰이 필요합니다'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': '토큰이 만료되었거나 유효하지 않습니다'}), 401
        
        user = User.find_by_id(payload['user_id'])
        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다'}), 401
        
        g.user = user
        g.user_id = user['id']
        return f(*args, **kwargs)
    
    return decorated


# ============================================================
# Google OAuth 로그인 API
# ============================================================
def register_auth_routes(app):
    
    @app.route('/api/auth/google', methods=['POST'])
    def google_login():
        """
        Google Sign-In 토큰 검증 후 JWT 발급
        
        Request:
            { "id_token": "구글에서 받은 id_token" }
        
        Response:
            {
                "token": "JWT 토큰",
                "user": { "id": 1, "name": "...", "email": "..." }
            }
        """
        data = request.get_json()
        google_token = data.get('id_token')
        
        if not google_token:
            return jsonify({'error': 'id_token이 필요합니다'}), 400
        
        try:
            # Google id_token 검증
            idinfo = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                Config.GOOGLE_CLIENT_ID
            )
            
            google_id = idinfo['sub']
            email = idinfo.get('email', '')
            name = idinfo.get('name', email.split('@')[0])
            avatar_url = idinfo.get('picture', '')
            
            # 사용자 생성/업데이트
            user = User.create(google_id, email, name, avatar_url)
            
            # JWT 토큰 발급
            token = create_token(user['id'])
            
            logger.info(f"로그인 성공: {email}")
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'avatar_url': user['avatar_url'],
                }
            })
        
        except ValueError as e:
            logger.error(f"Google 토큰 검증 실패: {e}")
            return jsonify({'error': '유효하지 않은 Google 토큰입니다'}), 401
    
    
    @app.route('/api/auth/me', methods=['GET'])
    @login_required
    def get_me():
        """현재 로그인 사용자 정보"""
        user = g.user
        return jsonify({
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'avatar_url': user['avatar_url'],
            }
        })
