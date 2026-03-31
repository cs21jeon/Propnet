"""
Google OAuth 인증 + JWT 토큰 관리
PropNet 통합 인증 시스템 연동 (Phase 4-2)
"""
import os
import sys
import logging

# ============================================================
# propnet_auth 공유 라이브러리 로드
# Proptalk은 별도 venv + 별도 DB(voiceroom)이므로
# propnet_auth가 goldenrabbit_db에 연결하려면 DB_NAME 오버라이드 필요
# ============================================================
_original_db_name = os.environ.get('DB_NAME')
os.environ['DB_NAME'] = 'goldenrabbit_db'
# DB_PASSWORD를 Proptalk의 DB_PASS에서 가져옴 (propnet_auth.config가 DB_PASSWORD 사용)
if not os.environ.get('DB_PASSWORD') and os.environ.get('DB_PASS'):
    os.environ['DB_PASSWORD'] = os.environ['DB_PASS']
# VOICEROOM 기본값 설정 (Proptalk .env에 없을 경우 대비)
if not os.environ.get('VOICEROOM_DB_NAME'):
    os.environ['VOICEROOM_DB_NAME'] = _original_db_name or 'voiceroom'
if not os.environ.get('VOICEROOM_DB_PASSWORD') and os.environ.get('DB_PASS'):
    os.environ['VOICEROOM_DB_PASSWORD'] = os.environ['DB_PASS']
if not os.environ.get('VOICEROOM_DB_USER') and os.environ.get('DB_USER'):
    os.environ['VOICEROOM_DB_USER'] = os.environ['DB_USER']

sys.path.insert(0, '/home/webapp/goldenrabbit/backend/shared')

import jwt as pyjwt
import requests as http_requests
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, g
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config import Config
from models import User, query_one, query_all, execute

# propnet_auth 임포트
from propnet_auth import (
    create_access_token, create_refresh_token, verify_token,
    find_or_create_propnet_user, ensure_service_account,
    check_and_accept_invitation,
    record_consent as propnet_record_consent,
    get_missing_consents, check_consent_status as propnet_check_consent_status,
    withdraw_consent as propnet_withdraw_consent,
    is_consent_complete,
)

# DB_NAME 원복 (Proptalk 자체 config/models가 voiceroom을 사용하므로)
if _original_db_name:
    os.environ['DB_NAME'] = _original_db_name

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
# JWT 토큰 생성/검증 (기존 호환 유지 + propnet_auth 통합)
# ============================================================
def create_token(user_id):
    """기존 JWT 토큰 생성 (하위 호환용, 내부 사용 시)"""
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + Config.JWT_EXPIRY,
        'iat': datetime.now(timezone.utc),
    }
    return pyjwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')


def decode_token(token):
    """기존 JWT 토큰 디코딩 (하위 호환용)"""
    try:
        payload = pyjwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        return payload
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


# ============================================================
# 인증 데코레이터 (통합 JWT 우선 + 기존 fallback)
# ============================================================
def login_required(f):
    """로그인 필수 데코레이터 - propnet_auth 통합 JWT 검증"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Authorization 헤더에서 토큰 추출
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': '인증 토큰이 필요합니다'}), 401

        # 1차: propnet_auth 통합 JWT 검증 (다중 secret + 하위 호환)
        payload = verify_token(token, expected_type='access')
        if payload:
            propnet_user_id = payload.get('sub')
            # propnet JWT: sub로 service_user_links에서 local user 찾기
            from propnet_auth.user_service import get_service_link
            link = get_service_link(propnet_user_id, 'proptalk')
            if link:
                user = User.find_by_id(link['local_user_id'])
                if user:
                    g.user = user
                    g.user_id = user['id']
                    g.propnet_user_id = propnet_user_id
                    g.propnet_role = payload.get('role', 'user')
                    return f(*args, **kwargs)

        # 2차: propnet_auth verify_token (type 무시 - 기존 JWT fallback)
        payload = verify_token(token)
        if payload:
            user_id = payload.get('sub') or payload.get('user_id')
            if user_id:
                user = User.find_by_id(user_id)
                if user:
                    g.user = user
                    g.user_id = user['id']
                    g.propnet_user_id = user.get('propnet_user_id') if isinstance(user, dict) else None
                    g.propnet_role = payload.get('role', 'user')
                    return f(*args, **kwargs)

        # 3차: 기존 Proptalk JWT (Config.JWT_SECRET만) - 최종 fallback
        legacy_payload = decode_token(token)
        if legacy_payload:
            user = User.find_by_id(legacy_payload['user_id'])
            if user:
                g.user = user
                g.user_id = user['id']
                g.propnet_user_id = user.get('propnet_user_id') if isinstance(user, dict) else None
                g.propnet_role = 'user'
                return f(*args, **kwargs)

        return jsonify({'error': '토큰이 만료되었거나 유효하지 않습니다'}), 401

    return decorated


# ============================================================
# Google OAuth 로그인 API
# ============================================================
def register_auth_routes(app):

    @app.route('/api/auth/google', methods=['POST'])
    def google_login():
        """
        Google Sign-In 토큰 검증 후 JWT 발급
        propnet_auth 통합: propnet_users 생성 + service_user_links 연결

        Request:
            {
                "id_token": "구글에서 받은 id_token",
                "server_auth_code": "(선택) Drive 권한용 auth code"
            }

        Response:
            {
                "token": "JWT access_token (Proptalk 호환)",
                "access_token": "JWT access_token (Propedia 호환)",
                "refresh_token": "JWT refresh_token",
                "user": { ... },
                "consent_required": bool,
                "missing_consents": [...]
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

            # ============================================================
            # PropNet 통합 인증 처리
            # ============================================================

            # 1. propnet_users 생성/조회
            propnet_user = find_or_create_propnet_user(google_id, email, name, avatar_url)
            propnet_user_id = propnet_user['id']
            role = propnet_user.get('role', 'user')

            # 2. Proptalk 서비스 계정 연결 (voiceroom.users)
            service_link = ensure_service_account(propnet_user_id, 'proptalk')

            # 3. subagent 초대 확인
            invitation = check_and_accept_invitation(email)
            if invitation:
                role = invitation['role']  # 'subagent'

            # 4. 기존 voiceroom.users 생성/업데이트 (하위 호환)
            user = User.create(google_id, email, name, avatar_url)

            # propnet_user_id 연결 (아직 안 되어 있으면)
            if user and not user.get('propnet_user_id'):
                try:
                    execute(
                        "UPDATE users SET propnet_user_id = %s WHERE id = %s",
                        (propnet_user_id, user['id'])
                    )
                except Exception as e:
                    logger.warning(f"propnet_user_id update failed: {e}")

            # server_auth_code가 있으면 Drive 토큰 교환
            drive_connected = False
            if server_auth_code and Config.GOOGLE_CLIENT_SECRET:
                try:
                    tokens = exchange_auth_code(server_auth_code)
                    if tokens and tokens.get('refresh_token'):
                        User.update_google_tokens(user['id'], tokens)
                        drive_connected = True
                        logger.info(f"Drive token saved: {email}")
                    else:
                        existing = User.get_google_tokens(user['id'])
                        if existing and existing.get('refresh_token') and tokens:
                            existing['access_token'] = tokens['access_token']
                            existing['expires_at'] = tokens['expires_at']
                            User.update_google_tokens(user['id'], existing)
                            drive_connected = True
                except Exception as e:
                    logger.error(f"Drive token exchange failed: {e}")
            else:
                existing = User.get_google_tokens(user['id'])
                if existing and existing.get('refresh_token'):
                    drive_connected = True

            # ============================================================
            # 통합 JWT 발급 (propnet_auth)
            # ============================================================
            access_token = create_access_token(propnet_user_id, email, role)
            refresh_token = create_refresh_token(propnet_user_id)

            # 필수 동의 항목 확인 (공통 + Proptalk 음성 데이터)
            missing_consents = get_missing_consents(
                propnet_user_id,
                services=['proptalk'],
                role=role if role != 'user' else None
            )
            consent_required = len(missing_consents) > 0

            logger.info(f"Login success: {email} (Drive: {drive_connected}, "
                         f"consent: {consent_required}, role: {role})")

            return jsonify({
                'token': access_token,           # Proptalk 호환 키
                'access_token': access_token,    # Propedia 호환 키
                'refresh_token': refresh_token,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'avatar_url': user['avatar_url'],
                    'drive_connected': drive_connected,
                    'role': role,
                    'propnet_user_id': propnet_user_id,
                },
                'consent_required': consent_required,
                'missing_consents': missing_consents,
            })

        except ValueError as e:
            logger.error(f"Google token verification failed: {e}")
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
                'role': getattr(g, 'propnet_role', 'user'),
                'propnet_user_id': getattr(g, 'propnet_user_id', None),
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
    # 토큰 갱신
    # ============================================================
    @app.route('/api/auth/refresh', methods=['POST'])
    def refresh_token_endpoint():
        """
        Refresh Token으로 새 Access Token 발급

        Request:
            { "refresh_token": "JWT refresh token" }

        Response:
            {
                "access_token": "new JWT",
                "token": "new JWT (Proptalk 호환)",
                "refresh_token": "new refresh JWT"
            }
        """
        data = request.get_json()
        refresh_token_str = data.get('refresh_token') if data else None

        if not refresh_token_str:
            return jsonify({'error': 'refresh_token이 필요합니다'}), 400

        from propnet_auth.jwt_utils import refresh_access_token
        result = refresh_access_token(refresh_token_str)

        if not result:
            return jsonify({'error': 'refresh_token이 만료되었거나 유효하지 않습니다'}), 401

        return jsonify({
            'access_token': result['access_token'],
            'token': result['access_token'],  # Proptalk 호환
            'refresh_token': result['refresh_token'],
        })

    # ============================================================
    # 동의 관리 (propnet_consents + voiceroom.user_consents 병행)
    # ============================================================
    @app.route('/api/auth/consent', methods=['POST'])
    @login_required
    def record_consent():
        """
        동의 기록 저장
        propnet_consents에 기록 + voiceroom.user_consents에도 병행 기록
        """
        data = request.get_json()
        consents = data.get('consents', [])
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        ua = request.headers.get('User-Agent', '')

        propnet_user_id = getattr(g, 'propnet_user_id', None)

        # 1. propnet_consents에 기록 (통합)
        propnet_results = []
        if propnet_user_id:
            propnet_results = propnet_record_consent(
                propnet_user_id, consents, ip_address=ip, user_agent=ua
            )

        # 2. voiceroom.user_consents에도 병행 기록 (전환 기간)
        for c in consents:
            consent_type = c.get('type', '')
            version = c.get('version', '')
            if not consent_type or not version:
                continue
            try:
                execute(
                    """INSERT INTO user_consents (user_id, consent_type, version, agreed, ip_address, user_agent)
                       VALUES (%s, %s, %s, true, %s, %s)""",
                    (g.user_id, consent_type, version, ip, ua)
                )
            except Exception as e:
                logger.warning(f"voiceroom user_consents insert failed: {e}")

        return jsonify({'ok': True, 'consents': propnet_results})

    @app.route('/api/auth/consent/status', methods=['GET'])
    @login_required
    def get_consent_status():
        """동의 상태 조회 - propnet_consents 기준 (fallback: voiceroom)"""
        propnet_user_id = getattr(g, 'propnet_user_id', None)

        if propnet_user_id:
            # 통합 동의 상태 조회
            consents = propnet_check_consent_status(propnet_user_id)
            missing = get_missing_consents(
                propnet_user_id, services=['proptalk'],
                role=getattr(g, 'propnet_role', None)
            )
            return jsonify({
                'consents': consents,
                'missing': missing,
                'consent_required': len(missing) > 0,
            })

        # fallback: 기존 voiceroom.user_consents
        rows = query_all(
            """SELECT consent_type, version, agreed, agreed_at, withdrawn_at
               FROM user_consents
               WHERE user_id = %s
               ORDER BY id DESC""",
            (g.user_id,)
        )
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
        """동의 철회 - propnet_consents + voiceroom.user_consents 병행"""
        data = request.get_json()
        consent_type = data.get('type', '')
        if not consent_type:
            return jsonify({'error': 'type required'}), 400

        propnet_user_id = getattr(g, 'propnet_user_id', None)

        # 1. propnet_consents에서 철회
        if propnet_user_id:
            propnet_withdraw_consent(propnet_user_id, consent_type)

        # 2. voiceroom.user_consents에서도 철회 (병행)
        try:
            execute(
                """UPDATE user_consents
                   SET withdrawn_at = NOW()
                   WHERE user_id = %s AND consent_type = %s AND withdrawn_at IS NULL""",
                (g.user_id, consent_type)
            )
        except Exception as e:
            logger.warning(f"voiceroom user_consents withdraw failed: {e}")

        return jsonify({'ok': True})

    # ============================================================
    # FCM 디바이스 토큰
    # ============================================================
    @app.route('/api/devices/register', methods=['POST'])
    @login_required
    def register_device_token():
        """FCM 토큰 등록"""
        data = request.get_json()
        fcm_token = (data.get('fcm_token') or '').strip()
        platform = data.get('platform', 'android')

        if not fcm_token:
            return jsonify({'error': 'fcm_token 필요'}), 400

        from models import DeviceToken
        DeviceToken.upsert(g.user_id, fcm_token, platform)
        return jsonify({'ok': True})

    @app.route('/api/devices/unregister', methods=['POST'])
    @login_required
    def unregister_device_token():
        """FCM 토큰 해제 (로그아웃 시)"""
        data = request.get_json()
        fcm_token = (data.get('fcm_token') or '').strip()

        if fcm_token:
            from models import DeviceToken
            DeviceToken.delete(g.user_id, fcm_token)
        return jsonify({'ok': True})

    # ============================================================
    # 계정 삭제
    # ============================================================
    @app.route('/api/auth/account', methods=['DELETE'])
    @login_required
    def delete_account():
        """계정 삭제 - 모든 개인정보 즉시 삭제"""
        user_id = g.user_id
        propnet_user_id = getattr(g, 'propnet_user_id', None)

        # propnet_consents + service_user_links 삭제
        if propnet_user_id:
            try:
                from propnet_auth.db import execute as propnet_execute
                propnet_execute(
                    "DELETE FROM propnet_consents WHERE propnet_user_id = %s",
                    (propnet_user_id,)
                )
                propnet_execute(
                    "DELETE FROM service_user_links WHERE propnet_user_id = %s AND service = 'proptalk'",
                    (propnet_user_id,)
                )
            except Exception as e:
                logger.error(f"propnet data deletion failed: {e}")

        # voiceroom 데이터 삭제
        execute("DELETE FROM user_consents WHERE user_id = %s", (user_id,))
        execute("DELETE FROM users WHERE id = %s", (user_id,))
        logger.info(f"Account deleted: user_id={user_id}, propnet_user_id={propnet_user_id}")
        return jsonify({'ok': True})
