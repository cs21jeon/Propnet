"""
Google OAuth 인증 + JWT 토큰 관리
"""
import jwt
import logging
import requests as http_requests
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, g
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config import Config
from models import User, query_one, query_all, execute

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'


def exchange_auth_code(server_auth_code):
    """serverAuthCode를 access_token + refresh_token으로 교환"""
    resp = http_requests.post(GOOGLE_TOKEN_URL, data={
        'code': server_auth_code,
        'client_id': Config.GOOGLE_CLIENT_ID,
        'client_secret': Config.GOOGLE_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': '',
    })

    if resp.status_code != 200:
        logger.error(f"Token exchange failed: {resp.status_code} {resp.text}")
        return None

    data = resp.json()
    return {
        'access_token': data['access_token'],
        'refresh_token': data.get('refresh_token'),
        'expires_at': datetime.now(timezone.utc).timestamp() + data.get('expires_in', 3600),
        'token_type': data.get('token_type', 'Bearer'),
    }


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
        server_auth_code = data.get('server_auth_code')

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

            # server_auth_code가 있으면 Drive 토큰 교환
            drive_connected = False
            if server_auth_code and Config.GOOGLE_CLIENT_SECRET:
                try:
                    tokens = exchange_auth_code(server_auth_code)
                    if tokens and tokens.get('refresh_token'):
                        User.update_google_tokens(user['id'], tokens)
                        drive_connected = True
                        logger.info(f"Drive 토큰 저장 완료: {email}")
                    else:
                        existing = User.get_google_tokens(user['id'])
                        if existing and existing.get('refresh_token') and tokens:
                            existing['access_token'] = tokens['access_token']
                            existing['expires_at'] = tokens['expires_at']
                            User.update_google_tokens(user['id'], existing)
                            drive_connected = True
                except Exception as e:
                    logger.error(f"Drive 토큰 교환 실패: {e}")
            else:
                existing = User.get_google_tokens(user['id'])
                if existing and existing.get('refresh_token'):
                    drive_connected = True

            # JWT 토큰 발급
            token = create_token(user['id'])

            logger.info(f"로그인 성공: {email} (Drive: {drive_connected})")

            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'avatar_url': user['avatar_url'],
                    'drive_connected': drive_connected,
                },
                'consent_required': False,
                'missing_consents': [],
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

    @app.route('/api/auth/profile', methods=['PATCH'])
    @login_required
    def update_profile():
        """프로필 이름 변경"""
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name or len(name) > 50:
            return jsonify({'error': '이름은 1~50자로 입력해주세요'}), 400
        user = User.update_name(g.user_id, name)
        return jsonify({
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'avatar_url': user['avatar_url'],
            }
        })

    # ============================================================
    # 동의 관리
    # ============================================================
    @app.route('/api/auth/consent', methods=['POST'])
    @login_required
    def record_consent():
        """동의 기록 저장"""
        data = request.get_json()
        consents = data.get('consents', [])
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        ua = request.headers.get('User-Agent', '')

        for c in consents:
            consent_type = c.get('type', '')
            version = c.get('version', '')
            if not consent_type or not version:
                continue
            execute(
                """INSERT INTO user_consents (user_id, consent_type, version, agreed, ip_address, user_agent)
                   VALUES (%s, %s, %s, true, %s, %s)""",
                (g.user_id, consent_type, version, ip, ua)
            )

        return jsonify({'ok': True})

    @app.route('/api/auth/consent/status', methods=['GET'])
    @login_required
    def get_consent_status():
        """동의 상태 조회"""
        rows = query_all(
            """SELECT consent_type, version, agreed, agreed_at, withdrawn_at
               FROM user_consents
               WHERE user_id = %s
               ORDER BY id DESC""",
            (g.user_id,)
        )
        # 각 타입별 최신 상태만 반환
        seen = {}
        consents = []
        for r in rows:
            ct = r['consent_type']
            if ct not in seen:
                seen[ct] = True
                consents.append({
                    'consent_type': ct,
                    'version': r['version'],
                    'agreed': r['agreed'] and r['withdrawn_at'] is None,
                    'agreed_at': r['agreed_at'].isoformat() if r['agreed_at'] else None,
                    'withdrawn_at': r['withdrawn_at'].isoformat() if r['withdrawn_at'] else None,
                })
        return jsonify({'consents': consents})

    @app.route('/api/auth/consent/withdraw', methods=['POST'])
    @login_required
    def withdraw_consent():
        """동의 철회"""
        data = request.get_json()
        consent_type = data.get('type', '')
        if not consent_type:
            return jsonify({'error': 'type required'}), 400

        execute(
            """UPDATE user_consents
               SET withdrawn_at = NOW()
               WHERE user_id = %s AND consent_type = %s AND withdrawn_at IS NULL""",
            (g.user_id, consent_type)
        )
        return jsonify({'ok': True})

    # ============================================================
    # 계정 삭제
    # ============================================================
    @app.route('/api/auth/account', methods=['DELETE'])
    @login_required
    def delete_account():
        """계정 삭제 - 모든 개인정보 즉시 삭제"""
        user_id = g.user_id
        execute("DELETE FROM user_consents WHERE user_id = %s", (user_id,))
        execute("DELETE FROM users WHERE id = %s", (user_id,))
        logger.info(f"계정 삭제: user_id={user_id}")
        return jsonify({'ok': True})
