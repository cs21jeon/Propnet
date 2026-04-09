#!/usr/bin/env python3
"""
propnet_auth 파일 생성 스크립트
서버에서 실행: python3 create_propnet_auth.py
"""
import os

BASE = '/home/webapp/goldenrabbit/backend/shared/propnet_auth'
os.makedirs(BASE, exist_ok=True)

files = {}

# ============================================================
# config.py
# ============================================================
files['config.py'] = '''"""
PropNet Auth 설정
환경변수에서 모든 비밀값을 읽음 (하드코딩 금지)
"""
import os
from datetime import timedelta

# ============================================================
# JWT 설정
# ============================================================
PROPNET_JWT_SECRET = os.environ.get('PROPNET_JWT_SECRET')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')  # Propedia 기존
JWT_SECRET = os.environ.get('JWT_SECRET')  # Proptalk 기존


def get_primary_secret():
    """JWT 서명에 사용할 기본 시크릿 반환"""
    for secret in [PROPNET_JWT_SECRET, JWT_SECRET_KEY, JWT_SECRET]:
        if secret:
            return secret
    raise RuntimeError("JWT 시크릿이 설정되지 않았습니다. "
                       "PROPNET_JWT_SECRET, JWT_SECRET_KEY, JWT_SECRET 중 하나를 .env에 설정하세요.")


def get_all_secrets():
    """검증 시 순서대로 시도할 시크릿 목록 반환"""
    secrets = []
    for secret in [PROPNET_JWT_SECRET, JWT_SECRET_KEY, JWT_SECRET]:
        if secret and secret not in secrets:
            secrets.append(secret)
    return secrets


# 토큰 만료 설정
ACCESS_TOKEN_EXPIRY = timedelta(hours=24)
REFRESH_TOKEN_EXPIRY = timedelta(days=30)

# ============================================================
# DB 설정 (goldenrabbit_db)
# ============================================================
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'goldenrabbit_db')
DB_USER = os.environ.get('DB_USER', 'goldenrabbit_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

PROPNET_DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ============================================================
# Voiceroom DB 설정 (Proptalk 전용)
# ============================================================
VOICEROOM_DB_HOST = os.environ.get('VOICEROOM_DB_HOST', 'localhost')
VOICEROOM_DB_PORT = os.environ.get('VOICEROOM_DB_PORT', '5432')
VOICEROOM_DB_NAME = os.environ.get('VOICEROOM_DB_NAME', 'voiceroom')
VOICEROOM_DB_USER = os.environ.get('VOICEROOM_DB_USER', 'goldenrabbit_user')
VOICEROOM_DB_PASSWORD = os.environ.get('VOICEROOM_DB_PASSWORD', '')

VOICEROOM_DB_URL = f"postgresql://{VOICEROOM_DB_USER}:{VOICEROOM_DB_PASSWORD}@{VOICEROOM_DB_HOST}:{VOICEROOM_DB_PORT}/{VOICEROOM_DB_NAME}"

# ============================================================
# Google OAuth Client IDs (공개값 - 소스 노출 OK)
# ============================================================
GOOGLE_CLIENT_IDS = [
    # Android/모바일 serverClientId (Propedia + Proptalk)
    '846392940969-a7k37gkon1p451mlnhp0oj9qaok1d8o1.apps.googleusercontent.com',
    # Propedia Web
    '846392940969-sv2936v0tm85j8hvdn3srcmtei1kk25e.apps.googleusercontent.com',
]

# 환경변수에 Proptalk 전용 Client ID가 있으면 추가
_proptalk_client_id = os.environ.get('GOOGLE_CLIENT_ID')
if _proptalk_client_id and _proptalk_client_id not in GOOGLE_CLIENT_IDS:
    GOOGLE_CLIENT_IDS.append(_proptalk_client_id)

# ============================================================
# 쿠키 설정
# ============================================================
COOKIE_NAME = 'propnet_token'
COOKIE_DOMAIN = os.environ.get('PROPNET_COOKIE_DOMAIN', 'goldenrabbit.biz')
COOKIE_SECURE = os.environ.get('PROPNET_COOKIE_SECURE', 'true').lower() == 'true'
COOKIE_SAMESITE = 'Lax'
COOKIE_PATH = '/'
'''

# ============================================================
# db.py
# ============================================================
files['db.py'] = '''"""
DB 연결 풀 및 헬퍼 함수 (psycopg2 기반)
Proptalk models.py 패턴 채택: ThreadedConnectionPool
"""
import logging
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from psycopg2 import pool

from propnet_auth.config import PROPNET_DB_URL, VOICEROOM_DB_URL

logger = logging.getLogger(__name__)

# ============================================================
# goldenrabbit_db 연결 풀
# ============================================================
_db_pool = None


def _get_pool():
    """Lazy initialization of connection pool"""
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=5,
                dsn=PROPNET_DB_URL
            )
            logger.info("propnet_auth: DB connection pool initialized")
        except Exception as e:
            logger.error(f"propnet_auth: DB pool init failed: {e}")
            raise
    return _db_pool


@contextmanager
def get_db():
    """DB 커넥션 컨텍스트 매니저 (goldenrabbit_db)"""
    p = _get_pool()
    conn = p.getconn()
    try:
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def query_one(sql, params=None):
    """단일 행 조회"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def query_all(sql, params=None):
    """다중 행 조회"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def execute(sql, params=None):
    """INSERT/UPDATE/DELETE 실행, RETURNING 결과 반환"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            try:
                return cur.fetchone()
            except psycopg2.ProgrammingError:
                return None


# ============================================================
# voiceroom DB 연결 (Proptalk ensure_service_account 전용)
# ============================================================
@contextmanager
def get_voiceroom_db():
    """voiceroom DB 직접 연결 (풀 미사용, 사용빈도 낮음)"""
    conn = None
    try:
        conn = psycopg2.connect(dsn=VOICEROOM_DB_URL)
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def voiceroom_query_one(sql, params=None):
    """voiceroom DB 단일 행 조회"""
    with get_voiceroom_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def voiceroom_execute(sql, params=None):
    """voiceroom DB INSERT/UPDATE/DELETE"""
    with get_voiceroom_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            try:
                return cur.fetchone()
            except psycopg2.ProgrammingError:
                return None
'''

# ============================================================
# jwt_utils.py
# ============================================================
files['jwt_utils.py'] = '''"""
JWT 토큰 생성/검증
통합 payload: { sub: propnet_user_id, email, role, type: "access"|"refresh" }
"""
import jwt
import logging
from datetime import datetime, timezone

from propnet_auth.config import (
    get_primary_secret,
    get_all_secrets,
    ACCESS_TOKEN_EXPIRY,
    REFRESH_TOKEN_EXPIRY,
)

logger = logging.getLogger(__name__)


def create_access_token(propnet_user_id, email=None, role='user'):
    """
    Access Token 생성 (24시간)

    Args:
        propnet_user_id: propnet_users.id
        email: 사용자 이메일
        role: user, agent, subagent, admin

    Returns:
        JWT 문자열
    """
    now = datetime.now(timezone.utc)
    payload = {
        'sub': propnet_user_id,
        'email': email,
        'role': role,
        'type': 'access',
        'exp': now + ACCESS_TOKEN_EXPIRY,
        'iat': now,
    }
    return jwt.encode(payload, get_primary_secret(), algorithm='HS256')


def create_refresh_token(propnet_user_id):
    """
    Refresh Token 생성 (30일)

    Args:
        propnet_user_id: propnet_users.id

    Returns:
        JWT 문자열
    """
    now = datetime.now(timezone.utc)
    payload = {
        'sub': propnet_user_id,
        'type': 'refresh',
        'exp': now + REFRESH_TOKEN_EXPIRY,
        'iat': now,
    }
    return jwt.encode(payload, get_primary_secret(), algorithm='HS256')


def verify_token(token, expected_type=None):
    """
    JWT 토큰 검증 (다중 secret + 하위 호환)

    다중 secret 시도 순서:
    1. PROPNET_JWT_SECRET
    2. JWT_SECRET_KEY (Propedia)
    3. JWT_SECRET (Proptalk)

    하위 호환:
    - 'sub' 키 없으면 'user_id' 키로 fallback (기존 JWT)
    - 기존 JWT는 type 필드 없음 -> access로 간주

    Args:
        token: JWT 문자열
        expected_type: "access" 또는 "refresh" (None이면 타입 체크 안 함)

    Returns:
        dict: {sub, email, role, type, ...} 또는 None (검증 실패)
    """
    if not token:
        return None

    secrets = get_all_secrets()
    if not secrets:
        logger.error("JWT 시크릿이 설정되지 않았습니다")
        return None

    for secret in secrets:
        try:
            payload = jwt.decode(token, secret, algorithms=['HS256'])

            # 하위 호환: sub 없으면 user_id로 fallback
            if 'sub' not in payload and 'user_id' in payload:
                payload['sub'] = payload['user_id']

            # sub가 여전히 없으면 무효
            if 'sub' not in payload:
                continue

            # 기존 JWT는 type 필드 없음 -> access로 간주
            if 'type' not in payload:
                payload['type'] = 'access'

            # role 기본값
            if 'role' not in payload:
                payload['role'] = 'user'

            # 타입 체크
            if expected_type and payload.get('type') != expected_type:
                logger.debug(f"JWT type mismatch: expected={expected_type}, got={payload.get('type')}")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug(f"JWT expired (secret index: {secrets.index(secret)})")
            return None
        except jwt.InvalidTokenError:
            # 다음 secret으로 시도
            continue

    logger.debug("JWT 검증 실패: 모든 시크릿으로 디코딩 실패")
    return None


def refresh_access_token(refresh_token_str):
    """
    Refresh Token으로 새 Access Token 발급

    Args:
        refresh_token_str: refresh JWT 문자열

    Returns:
        dict: {access_token, refresh_token} 또는 None
    """
    payload = verify_token(refresh_token_str, expected_type='refresh')
    if not payload:
        return None

    propnet_user_id = payload['sub']

    # DB에서 최신 유저 정보 조회
    from propnet_auth.db import query_one
    user = query_one(
        "SELECT id, email, role FROM propnet_users WHERE id = %s AND is_active = TRUE",
        (propnet_user_id,)
    )
    if not user:
        return None

    return {
        'access_token': create_access_token(user['id'], user['email'], user['role']),
        'refresh_token': create_refresh_token(user['id']),
    }
'''

# ============================================================
# terms.py
# ============================================================
files['terms.py'] = '''"""
동의 요건 중앙 관리
서비스/역할별 필수 동의 항목 정의
"""

# 현재 동의 버전
CURRENT_CONSENT_VERSION = '2026-04-01'

# ============================================================
# 전체 서비스 공통 필수 동의
# ============================================================
COMMON_CONSENTS = [
    {
        'type': 'terms',
        'version': CURRENT_CONSENT_VERSION,
        'label': '[필수] 서비스 이용약관',
        'url': '/legal/terms-of-service.html',
        'required': True,
    },
    {
        'type': 'privacy',
        'version': CURRENT_CONSENT_VERSION,
        'label': '[필수] 개인정보 수집 및 이용 동의',
        'url': '/legal/privacy-policy.html',
        'required': True,
    },
    {
        'type': 'overseas_transfer',
        'version': CURRENT_CONSENT_VERSION,
        'label': '[필수] 개인정보 국외 이전 동의',
        'url': '/legal/overseas-transfer.html',
        'required': True,
    },
]

# ============================================================
# 서비스별 추가 동의 (해당 서비스 첫 이용 시)
# ============================================================
SERVICE_CONSENTS = {
    'proptalk': [
        {
            'type': 'proptalk_voice_data',
            'version': CURRENT_CONSENT_VERSION,
            'label': '[필수] 음성 데이터 수집/처리 동의',
            'description': '음성 파일을 OpenAI Whisper API로 전송하여 텍스트 변환',
            'url': '/legal/service-specific/proptalk-voice.html',
            'required': True,
        },
    ],
    'propsheet': [
        {
            'type': 'propsheet_property_data',
            'version': CURRENT_CONSENT_VERSION,
            'label': '[필수] 부동산 매물 데이터 처리 동의',
            'description': '매물 정보 저장, 공유, 타 서비스 연동',
            'url': '/legal/service-specific/propsheet-property.html',
            'required': True,
        },
    ],
    'propedia': [],  # 공통 동의로 충분
}

# ============================================================
# 역할별 추가 동의
# ============================================================
ROLE_CONSENTS = {
    'agent': [
        {
            'type': 'agent_data_responsibility',
            'version': CURRENT_CONSENT_VERSION,
            'label': '[필수] 중개업자 데이터 관리 책임 동의',
            'description': '고객 매물 데이터의 정확성 및 관리 책임',
            'required': True,
        },
    ],
    'subagent': [
        {
            'type': 'subagent_data_access',
            'version': CURRENT_CONSENT_VERSION,
            'label': '[필수] 소속 중개사무소 데이터 접근 동의',
            'description': '소속 Agent의 매물/고객 데이터 열람 범위 동의',
            'required': True,
        },
    ],
}


def get_required_consents(services=None, role=None):
    """
    필수 동의 항목 목록 반환

    Args:
        services: ['propedia', 'proptalk'] 등 서비스 목록 (None이면 공통만)
        role: 'agent', 'subagent' 등 역할 (None이면 역할 동의 미포함)

    Returns:
        list[dict]: 필수 동의 항목 목록
    """
    required = list(COMMON_CONSENTS)

    if services:
        for service in services:
            service_consents = SERVICE_CONSENTS.get(service, [])
            required.extend(service_consents)

    if role:
        role_consents = ROLE_CONSENTS.get(role, [])
        required.extend(role_consents)

    return [c for c in required if c.get('required', False)]
'''

# ============================================================
# user_service.py
# ============================================================
files['user_service.py'] = '''"""
통합 유저 관리 서비스
propnet_users 기준으로 유저 생성/조회, 서비스별 로컬 유저 연결
"""
import logging

from propnet_auth.db import query_one, query_all, execute, voiceroom_query_one, voiceroom_execute

logger = logging.getLogger(__name__)


def find_or_create_propnet_user(google_id, email, name, avatar_url=None):
    """
    이메일 기준으로 propnet_users 조회/생성.
    첫 로그인 시 자동 생성. google_id가 다르면 업데이트.

    Args:
        google_id: Google OAuth sub
        email: 이메일
        name: 사용자 이름
        avatar_url: 프로필 사진 URL

    Returns:
        dict: propnet_users 레코드
    """
    # 1. google_id로 조회
    user = query_one(
        "SELECT * FROM propnet_users WHERE google_id = %s",
        (google_id,)
    )
    if user:
        # 이름/아바타 업데이트
        if user['name'] != name or user['avatar_url'] != avatar_url:
            execute(
                """UPDATE propnet_users SET name = %s, avatar_url = %s, updated_at = NOW()
                   WHERE id = %s""",
                (name, avatar_url, user['id'])
            )
        return query_one("SELECT * FROM propnet_users WHERE id = %s", (user['id'],))

    # 2. 이메일로 조회 (google_id가 아직 없는 마이그레이션 유저)
    user = query_one(
        "SELECT * FROM propnet_users WHERE email = %s",
        (email,)
    )
    if user:
        # google_id 설정
        execute(
            """UPDATE propnet_users SET google_id = %s, name = %s, avatar_url = %s, updated_at = NOW()
               WHERE id = %s""",
            (google_id, name, avatar_url, user['id'])
        )
        return query_one("SELECT * FROM propnet_users WHERE id = %s", (user['id'],))

    # 3. 신규 유저 생성
    user = execute(
        """INSERT INTO propnet_users (google_id, email, name, avatar_url, role)
           VALUES (%s, %s, %s, %s, 'user')
           RETURNING *""",
        (google_id, email, name, avatar_url)
    )
    logger.info(f"propnet_auth: 신규 유저 생성 - {email} (id={user['id']})")
    return user


def get_propnet_user(propnet_user_id):
    """propnet_user_id로 유저 조회"""
    return query_one(
        "SELECT * FROM propnet_users WHERE id = %s AND is_active = TRUE",
        (propnet_user_id,)
    )


def get_propnet_user_by_email(email):
    """이메일로 유저 조회"""
    return query_one(
        "SELECT * FROM propnet_users WHERE email = %s AND is_active = TRUE",
        (email,)
    )


def get_service_link(propnet_user_id, service):
    """서비스별 로컬 유저 ID 조회"""
    return query_one(
        "SELECT * FROM service_user_links WHERE propnet_user_id = %s AND service = %s",
        (propnet_user_id, service)
    )


def ensure_service_account(propnet_user_id, service):
    """
    해당 서비스의 로컬 유저가 없으면 생성 후 service_user_links에 기록.

    Args:
        propnet_user_id: propnet_users.id
        service: 'propedia', 'proptalk', 'propsheet'

    Returns:
        dict: service_user_links 레코드 (local_user_id 포함)
    """
    # 기존 링크 확인
    link = get_service_link(propnet_user_id, service)
    if link:
        return link

    # propnet_user 정보 조회
    user = get_propnet_user(propnet_user_id)
    if not user:
        logger.error(f"propnet_auth: 유저 없음 - propnet_user_id={propnet_user_id}")
        return None

    local_user_id = None

    if service == 'propedia':
        local_user_id = _ensure_propedia_account(user)
    elif service == 'proptalk':
        local_user_id = _ensure_proptalk_account(user)
    elif service == 'propsheet':
        local_user_id = _ensure_propsheet_account(user)
    else:
        logger.error(f"propnet_auth: 알 수 없는 서비스 - {service}")
        return None

    if local_user_id is None:
        return None

    # service_user_links 등록
    link = execute(
        """INSERT INTO service_user_links (propnet_user_id, service, local_user_id)
           VALUES (%s, %s, %s)
           ON CONFLICT (propnet_user_id, service) DO UPDATE SET local_user_id = EXCLUDED.local_user_id
           RETURNING *""",
        (propnet_user_id, service, local_user_id)
    )

    logger.info(f"propnet_auth: 서비스 연결 - {service} local_id={local_user_id} propnet_id={propnet_user_id}")
    return link


def _ensure_propedia_account(propnet_user):
    """Propedia (app_users) 로컬 계정 생성/조회 - goldenrabbit_db"""
    email = propnet_user['email']
    google_id = propnet_user['google_id']
    name = propnet_user['name']

    existing = query_one("SELECT id FROM app_users WHERE email = %s", (email,))
    if existing:
        execute(
            "UPDATE app_users SET propnet_user_id = %s WHERE id = %s",
            (propnet_user['id'], existing['id'])
        )
        return existing['id']

    result = execute(
        """INSERT INTO app_users (email, name, provider, provider_id, is_active, is_verified, propnet_user_id)
           VALUES (%s, %s, 'google', %s, TRUE, TRUE, %s)
           RETURNING id""",
        (email, name, google_id, propnet_user['id'])
    )
    return result['id'] if result else None


def _ensure_proptalk_account(propnet_user):
    """Proptalk (voiceroom.users) 로컬 계정 생성/조회 - 별도 DB"""
    email = propnet_user['email']
    google_id = propnet_user['google_id']
    name = propnet_user['name']
    avatar_url = propnet_user.get('avatar_url', '')

    existing = voiceroom_query_one("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        voiceroom_execute(
            "UPDATE users SET propnet_user_id = %s WHERE id = %s",
            (propnet_user['id'], existing['id'])
        )
        return existing['id']

    result = voiceroom_execute(
        """INSERT INTO users (google_id, email, name, avatar_url, propnet_user_id)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (google_id) DO UPDATE SET propnet_user_id = EXCLUDED.propnet_user_id
           RETURNING id""",
        (google_id, email, name, avatar_url, propnet_user['id'])
    )
    return result['id'] if result else None


def _ensure_propsheet_account(propnet_user):
    """PropSheet (web_users) 로컬 계정 생성/조회 - goldenrabbit_db"""
    email = propnet_user['email']
    google_id = propnet_user['google_id']
    name = propnet_user['name']
    avatar_url = propnet_user.get('avatar_url', '')

    existing = query_one("SELECT id FROM web_users WHERE email = %s", (email,))
    if existing:
        execute(
            "UPDATE web_users SET propnet_user_id = %s WHERE id = %s",
            (propnet_user['id'], existing['id'])
        )
        return existing['id']

    result = execute(
        """INSERT INTO web_users (google_id, email, name, avatar_url, propnet_user_id)
           VALUES (%s, %s, %s, %s, %s)
           RETURNING id""",
        (google_id, email, name, avatar_url, propnet_user['id'])
    )
    return result['id'] if result else None


def check_and_accept_invitation(email):
    """
    subagent_invitations에서 pending 초대 확인.
    있으면 propnet_users의 role을 subagent로 설정하고 agent_id를 연결.

    Args:
        email: 사용자 이메일

    Returns:
        dict: 초대 정보 또는 None
    """
    invitation = query_one(
        """SELECT si.*, pu.name as agent_name
           FROM subagent_invitations si
           JOIN propnet_users pu ON si.agent_id = pu.id
           WHERE si.invited_email = %s AND si.status = 'pending'
           ORDER BY si.created_at DESC LIMIT 1""",
        (email,)
    )

    if not invitation:
        return None

    user = query_one("SELECT * FROM propnet_users WHERE email = %s", (email,))
    if not user:
        return None

    # role을 subagent로 설정, agent_id 연결
    execute(
        """UPDATE propnet_users SET role = 'subagent', agent_id = %s, updated_at = NOW()
           WHERE id = %s""",
        (invitation['agent_id'], user['id'])
    )

    # 초대 수락 처리
    execute(
        """UPDATE subagent_invitations SET status = 'accepted', accepted_at = NOW()
           WHERE id = %s""",
        (invitation['id'],)
    )

    logger.info(f"propnet_auth: subagent 초대 수락 - {email} -> agent_id={invitation['agent_id']}")

    return {
        'invitation_id': invitation['id'],
        'agent_id': invitation['agent_id'],
        'agent_name': invitation['agent_name'],
        'role': 'subagent',
    }


def update_user_role(propnet_user_id, role, agent_id=None):
    """유저 역할 변경 (관리자용)"""
    execute(
        """UPDATE propnet_users SET role = %s, agent_id = %s, updated_at = NOW()
           WHERE id = %s""",
        (role, agent_id, propnet_user_id)
    )
    logger.info(f"propnet_auth: 역할 변경 - propnet_user_id={propnet_user_id} role={role}")
'''

# ============================================================
# consent_service.py
# ============================================================
files['consent_service.py'] = '''"""
통합 동의 관리 서비스
Proptalk의 UserConsent 패턴 기반
"""
import logging

from propnet_auth.db import query_one, query_all, execute
from propnet_auth.terms import (
    CURRENT_CONSENT_VERSION,
    get_required_consents,
)

logger = logging.getLogger(__name__)


def get_missing_consents(propnet_user_id, services=None, role=None):
    """
    유저가 아직 동의하지 않은 필수 항목 목록 반환.

    Args:
        propnet_user_id: propnet_users.id
        services: ['propedia', 'proptalk'] 등 서비스 목록
        role: 'agent', 'subagent' 등 역할

    Returns:
        list[dict]: 미동의 항목 목록
    """
    required = get_required_consents(services=services, role=role)
    missing = []

    for consent in required:
        has = _has_valid_consent(
            propnet_user_id,
            consent['type'],
            consent['version']
        )
        if not has:
            missing.append(consent)

    return missing


def record_consent(propnet_user_id, consents, ip_address=None, user_agent=None):
    """
    동의 이력 기록.

    Args:
        propnet_user_id: propnet_users.id
        consents: [{'type': 'terms', 'version': '2026-04-01'}, ...]
        ip_address: 접속 IP
        user_agent: 접속 User-Agent

    Returns:
        list[dict]: 기록된 동의 목록
    """
    results = []

    for item in consents:
        consent_type = item.get('type')
        version = item.get('version', CURRENT_CONSENT_VERSION)
        service = item.get('service')

        if not consent_type:
            continue

        result = execute(
            """INSERT INTO propnet_consents
                   (propnet_user_id, consent_type, version, service, agreed, agreed_at, ip_address, user_agent)
               VALUES (%s, %s, %s, %s, TRUE, NOW(), %s, %s)
               ON CONFLICT (propnet_user_id, consent_type, version)
               DO UPDATE SET agreed = TRUE, agreed_at = NOW(), withdrawn_at = NULL,
                            ip_address = EXCLUDED.ip_address, user_agent = EXCLUDED.user_agent
               RETURNING *""",
            (propnet_user_id, consent_type, version, service, ip_address, user_agent)
        )

        if result:
            results.append({
                'type': result['consent_type'],
                'version': result['version'],
                'agreed_at': result['agreed_at'].isoformat() if hasattr(result['agreed_at'], 'isoformat') else str(result['agreed_at']),
            })

    if results:
        logger.info(f"propnet_auth: 동의 기록 - propnet_user_id={propnet_user_id}, "
                     f"types={[r['type'] for r in results]}")

    return results


def check_consent_status(propnet_user_id):
    """유저의 전체 동의 현황 반환."""
    rows = query_all(
        """SELECT DISTINCT ON (consent_type)
                  consent_type, version, agreed, agreed_at, withdrawn_at, service
           FROM propnet_consents
           WHERE propnet_user_id = %s
           ORDER BY consent_type, agreed_at DESC""",
        (propnet_user_id,)
    )

    return [
        {
            'type': r['consent_type'],
            'version': r['version'],
            'agreed': r['agreed'] and r['withdrawn_at'] is None,
            'agreed_at': r['agreed_at'].isoformat() if r.get('agreed_at') and hasattr(r['agreed_at'], 'isoformat') else None,
            'withdrawn_at': r['withdrawn_at'].isoformat() if r.get('withdrawn_at') and hasattr(r['withdrawn_at'], 'isoformat') else None,
            'service': r.get('service'),
        }
        for r in rows
    ]


def withdraw_consent(propnet_user_id, consent_type):
    """특정 동의 철회."""
    result = execute(
        """UPDATE propnet_consents SET withdrawn_at = NOW(), agreed = FALSE
           WHERE propnet_user_id = %s AND consent_type = %s AND withdrawn_at IS NULL
           RETURNING *""",
        (propnet_user_id, consent_type)
    )

    if result:
        logger.info(f"propnet_auth: 동의 철회 - propnet_user_id={propnet_user_id}, type={consent_type}")

    return result


def is_consent_complete(propnet_user_id, services=None, role=None):
    """모든 필수 동의가 완료되었는지 확인."""
    missing = get_missing_consents(propnet_user_id, services=services, role=role)
    return len(missing) == 0


def _has_valid_consent(propnet_user_id, consent_type, version=None):
    """특정 동의가 유효한지 확인"""
    if version is None:
        version = CURRENT_CONSENT_VERSION

    result = query_one(
        """SELECT 1 FROM propnet_consents
           WHERE propnet_user_id = %s AND consent_type = %s AND version = %s
                 AND agreed = TRUE AND withdrawn_at IS NULL
           LIMIT 1""",
        (propnet_user_id, consent_type, version)
    )
    return result is not None
'''

# ============================================================
# google_verify.py
# ============================================================
files['google_verify.py'] = '''"""
Google OAuth 검증 - 두 가지 플로우 통합

1. verify_id_token() - Propedia/Proptalk 앱용 (id_token 직접 검증)
2. process_userinfo() - PropSheet 웹용 (code flow 결과)
"""
import logging
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from propnet_auth.config import GOOGLE_CLIENT_IDS

logger = logging.getLogger(__name__)


def verify_id_token(token):
    """
    Google id_token 검증 (Propedia/Proptalk 앱용).
    모든 등록된 Client ID를 순회하며 시도.

    Args:
        token: Google에서 받은 id_token 문자열

    Returns:
        dict: {google_id, email, name, avatar_url}

    Raises:
        ValueError: 모든 Client ID로 검증 실패 시
    """
    if not token:
        raise ValueError("id_token이 필요합니다")

    last_error = None

    for client_id in GOOGLE_CLIENT_IDS:
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                client_id
            )

            google_id = idinfo['sub']
            email = idinfo.get('email', '')
            name = idinfo.get('name', email.split('@')[0] if email else '')
            avatar_url = idinfo.get('picture', '')

            logger.debug(f"Google 토큰 검증 성공: {email} (client_id: ...{client_id[-8:]})")

            return {
                'google_id': google_id,
                'email': email,
                'name': name,
                'avatar_url': avatar_url,
            }

        except ValueError as e:
            last_error = e
            continue

    logger.error(f"Google 토큰 검증 실패 (모든 Client ID 시도): {last_error}")
    raise ValueError(f"유효하지 않은 Google 토큰입니다: {last_error}")


def process_userinfo(userinfo_dict):
    """
    PropSheet 웹용: code flow 결과의 userinfo 딕셔너리 처리.

    Args:
        userinfo_dict: Google userinfo 응답 딕셔너리
            {'sub': '...', 'email': '...', 'name': '...', 'picture': '...'}

    Returns:
        dict: {google_id, email, name, avatar_url} (verify_id_token과 동일 형식)

    Raises:
        ValueError: 필수 필드 누락 시
    """
    if not userinfo_dict:
        raise ValueError("userinfo가 필요합니다")

    google_id = userinfo_dict.get('sub')
    email = userinfo_dict.get('email')

    if not google_id or not email:
        raise ValueError("userinfo에 sub 또는 email이 없습니다")

    name = userinfo_dict.get('name', email.split('@')[0])
    avatar_url = userinfo_dict.get('picture', '')

    return {
        'google_id': google_id,
        'email': email,
        'name': name,
        'avatar_url': avatar_url,
    }
'''

# ============================================================
# invitation.py
# ============================================================
files['invitation.py'] = '''"""
Subagent 초대 관리
Agent가 Subagent를 이메일로 초대, 초대받은 사용자가 가입 시 자동 연결
"""
import logging

from propnet_auth.db import query_one, query_all, execute

logger = logging.getLogger(__name__)


def create_invitation(agent_propnet_user_id, invited_email):
    """
    Subagent 초대 생성.

    Args:
        agent_propnet_user_id: 초대하는 Agent의 propnet_user_id
        invited_email: 초대받을 이메일

    Returns:
        dict: 초대 레코드 또는 None
    """
    agent = query_one(
        "SELECT id, role, name FROM propnet_users WHERE id = %s AND is_active = TRUE",
        (agent_propnet_user_id,)
    )
    if not agent or agent['role'] not in ('agent', 'admin'):
        logger.warning(f"propnet_auth: 초대 실패 - 권한 없음 (propnet_user_id={agent_propnet_user_id})")
        return None

    existing = query_one(
        """SELECT * FROM subagent_invitations
           WHERE agent_id = %s AND invited_email = %s AND status = 'pending'""",
        (agent_propnet_user_id, invited_email)
    )
    if existing:
        logger.info(f"propnet_auth: 이미 초대됨 - {invited_email}")
        return existing

    result = execute(
        """INSERT INTO subagent_invitations (agent_id, invited_email, status)
           VALUES (%s, %s, 'pending')
           ON CONFLICT (agent_id, invited_email) DO UPDATE
           SET status = 'pending', created_at = NOW(), accepted_at = NULL
           RETURNING *""",
        (agent_propnet_user_id, invited_email)
    )

    if result:
        logger.info(f"propnet_auth: 초대 생성 - agent_id={agent_propnet_user_id}, email={invited_email}")

    return result


def accept_invitation(invitation_id, propnet_user_id):
    """초대 수락."""
    invitation = query_one(
        "SELECT * FROM subagent_invitations WHERE id = %s AND status = 'pending'",
        (invitation_id,)
    )
    if not invitation:
        return None

    execute(
        """UPDATE subagent_invitations SET status = 'accepted', accepted_at = NOW()
           WHERE id = %s""",
        (invitation_id,)
    )

    execute(
        """UPDATE propnet_users SET role = 'subagent', agent_id = %s, updated_at = NOW()
           WHERE id = %s""",
        (invitation['agent_id'], propnet_user_id)
    )

    logger.info(f"propnet_auth: 초대 수락 - invitation_id={invitation_id}, "
                f"propnet_user_id={propnet_user_id}, agent_id={invitation['agent_id']}")

    return invitation


def reject_invitation(invitation_id):
    """초대 거절"""
    return execute(
        """UPDATE subagent_invitations SET status = 'rejected'
           WHERE id = %s AND status = 'pending'
           RETURNING *""",
        (invitation_id,)
    )


def check_pending_invitation(email):
    """이메일에 대한 대기 중인 초대 확인."""
    return query_one(
        """SELECT si.*, pu.name as agent_name, pu.email as agent_email
           FROM subagent_invitations si
           JOIN propnet_users pu ON si.agent_id = pu.id
           WHERE si.invited_email = %s AND si.status = 'pending'
           ORDER BY si.created_at DESC LIMIT 1""",
        (email,)
    )


def list_invitations_by_agent(agent_propnet_user_id):
    """Agent가 보낸 초대 목록 조회"""
    return query_all(
        """SELECT si.*, pu.name as invited_user_name
           FROM subagent_invitations si
           LEFT JOIN propnet_users pu ON pu.email = si.invited_email
           WHERE si.agent_id = %s
           ORDER BY si.created_at DESC""",
        (agent_propnet_user_id,)
    )


def cancel_invitation(invitation_id, agent_propnet_user_id):
    """Agent가 보낸 초대 취소"""
    return execute(
        """DELETE FROM subagent_invitations
           WHERE id = %s AND agent_id = %s AND status = 'pending'
           RETURNING *""",
        (invitation_id, agent_propnet_user_id)
    )
'''

# ============================================================
# middleware.py
# ============================================================
files['middleware.py'] = '''"""
Flask 미들웨어 - JWT 인증 데코레이터 + 쿠키 헬퍼
"""
import logging
from functools import wraps
from flask import request, jsonify, g

from propnet_auth.jwt_utils import verify_token
from propnet_auth.consent_service import get_missing_consents
from propnet_auth.config import (
    COOKIE_NAME,
    COOKIE_DOMAIN,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
    COOKIE_PATH,
    ACCESS_TOKEN_EXPIRY,
)

logger = logging.getLogger(__name__)


def set_propnet_cookie(response, access_token):
    """
    PropNet JWT httpOnly 쿠키 설정.
    웹 SSO용.

    Args:
        response: Flask Response 객체
        access_token: JWT access token 문자열

    Returns:
        response: 쿠키가 설정된 Response 객체
    """
    response.set_cookie(
        COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        domain=COOKIE_DOMAIN,
        path=COOKIE_PATH,
        max_age=int(ACCESS_TOKEN_EXPIRY.total_seconds()),
    )
    return response


def clear_propnet_cookie(response):
    """PropNet JWT 쿠키 삭제 (로그아웃용)"""
    response.delete_cookie(
        COOKIE_NAME,
        domain=COOKIE_DOMAIN,
        path=COOKIE_PATH,
    )
    return response


def _extract_token():
    """요청에서 JWT 토큰 추출. 우선순위: Authorization header > 쿠키"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ', 1)[1]

    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        return cookie_token

    return None


def propnet_token_required(f):
    """
    PropNet 통합 JWT 인증 데코레이터.
    성공 시 g.propnet_user_id, g.propnet_email, g.propnet_role 설정.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()

        if not token:
            return jsonify({'error': '인증 토큰이 필요합니다', 'code': 'TOKEN_REQUIRED'}), 401

        payload = verify_token(token, expected_type='access')
        if not payload:
            return jsonify({'error': '토큰이 만료되었거나 유효하지 않습니다', 'code': 'TOKEN_INVALID'}), 401

        g.propnet_user_id = payload['sub']
        g.propnet_email = payload.get('email')
        g.propnet_role = payload.get('role', 'user')
        g.token_payload = payload

        return f(*args, **kwargs)

    return decorated


def consent_required(services=None):
    """
    동의 확인 데코레이터. propnet_token_required 이후에 사용.
    미완료 시 API는 JSON 응답, 웹은 리다이렉트.

    Args:
        services: 확인할 서비스 목록 (예: ['proptalk'])
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            propnet_user_id = g.propnet_user_id
            role = g.propnet_role

            missing = get_missing_consents(
                propnet_user_id,
                services=services,
                role=role
            )

            if missing:
                is_api = (
                    request.is_json or
                    request.headers.get('Accept', '').startswith('application/json') or
                    request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                )

                if is_api:
                    return jsonify({
                        'error': '동의가 필요합니다',
                        'code': 'CONSENT_REQUIRED',
                        'consent_required': True,
                        'missing_consents': missing,
                    }), 403
                else:
                    from flask import redirect
                    return redirect('/legal/consent?next=' + request.path)

            return f(*args, **kwargs)

        return decorated
    return decorator


def admin_required(f):
    """관리자 권한 데코레이터. propnet_token_required 이후에 사용."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.propnet_role != 'admin':
            return jsonify({'error': '관리자 권한이 필요합니다', 'code': 'ADMIN_REQUIRED'}), 403
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """특정 역할 요구 데코레이터. propnet_token_required 이후에 사용."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.propnet_role not in roles:
                return jsonify({
                    'error': '접근 권한이 없습니다',
                    'code': 'ROLE_REQUIRED',
                    'required_roles': list(roles),
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
'''

# ============================================================
# Write all files
# ============================================================
for filename, content in files.items():
    filepath = os.path.join(BASE, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filepath}")

print(f"\nTotal files created: {len(files)}")
print("Done!")
