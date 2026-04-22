#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OAuth Routes - Google login/logout, consent management, and Propsheet landing page

Phase 4-3: propnet_auth 통합
- Google OAuth callback에서 propnet_auth로 통합 유저 생성/조회
- JWT 쿠키 (propnet_token) 설정으로 SSO 지원
- Admin 판별: propnet_users.role == 'admin' (하드코딩 제거)
- 동의 미완료 시 동의 페이지로 리다이렉트
- 동의 CRUD 엔드포인트 추가
"""

import sys
import logging
import uuid
from flask import Blueprint, redirect, request, session, render_template, jsonify, make_response

logger = logging.getLogger(__name__)

# propnet_auth 라이브러리 로드
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/shared')
try:
    from propnet_auth import (
        process_userinfo,
        find_or_create_propnet_user,
        ensure_service_account,
        check_and_accept_invitation,
        create_access_token,
        is_consent_complete,
        get_missing_consents,
        record_consent,
        check_consent_status,
        withdraw_consent,
        set_propnet_cookie,
    )
    from propnet_auth.middleware import clear_propnet_cookie
    from propnet_auth.terms import COMMON_CONSENTS, SERVICE_CONSENTS
    PROPNET_AUTH_AVAILABLE = True
    logger.info("propnet_auth loaded successfully")
except ImportError as e:
    PROPNET_AUTH_AVAILABLE = False
    logger.warning(f"propnet_auth not available, falling back to legacy auth: {e}")

bp = Blueprint('oauth', __name__)


def _get_agent_default_url(sess):
    """세션 정보로 agent/subagent의 기본 URL 결정.
    admin → /propsheet/workspaces, agent/subagent → /propsheet/{slug}/
    """
    if sess.get('is_admin'):
        return '/propsheet/workspaces'
    agent_id = sess.get('agent_id')
    if agent_id:
        try:
            from services.database_service import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT slug FROM agents WHERE id = %s AND is_active = true", (agent_id,))
                    row = cur.fetchone()
                    if row:
                        return f'/propsheet/{row[0]}/'
        except Exception:
            pass
    return '/propsheet/workspaces'


@bp.route('/auth/google')
def google_login():
    """Redirect to Google OAuth consent screen."""
    try:
        from services.google_auth_service import get_authorization_url
        login_hint = request.args.get('login_hint', '')
        authorization_url, state = get_authorization_url(host=request.host, login_hint=login_hint or None)
        session['oauth_state'] = state
        session['oauth_next'] = request.args.get('next', '')
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        return redirect('/propsheet/?error=auth_failed')


@bp.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback with propnet_auth integration."""
    # Step 1: Exchange code for userinfo (기존 유지)
    try:
        from services.google_auth_service import exchange_code_for_user_info, find_or_create_user

        callback_url = request.url
        if callback_url.startswith('http://'):
            callback_url = 'https://' + callback_url[7:]

        userinfo = exchange_code_for_user_info(
            authorization_response=callback_url,
            state=session.get('oauth_state'),
            host=request.host
        )
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        return redirect('/propsheet/?error=auth_failed')

    # Step 2: propnet_auth 통합 유저 처리
    propnet_user = None
    propnet_user_id = None
    is_admin = False

    if PROPNET_AUTH_AVAILABLE:
        try:
            # process_userinfo: userinfo dict를 표준 형식으로 변환
            normalized = process_userinfo(userinfo)

            # 통합 유저 생성/조회
            propnet_user = find_or_create_propnet_user(
                google_id=normalized['google_id'],
                email=normalized['email'],
                name=normalized['name'],
                avatar_url=normalized.get('avatar_url', '')
            )
            propnet_user_id = propnet_user['id']

            # web_users 로컬 계정 연결
            ensure_service_account(propnet_user_id, 'propsheet')

            # subagent 초대 확인
            check_and_accept_invitation(normalized['email'])

            # 최신 propnet_user 다시 조회 (role이 변경되었을 수 있음)
            from propnet_auth.user_service import get_propnet_user
            propnet_user = get_propnet_user(propnet_user_id) or propnet_user

            is_admin = (propnet_user.get('role') == 'admin')

            logger.info(f"propnet_auth: user processed - {normalized['email']} "
                        f"(propnet_id={propnet_user_id}, role={propnet_user.get('role', 'user')})")

            # AI 크레딧 가입 보너스 지급 (idempotent — 이미 지급된 유저는 무시)
            try:
                from services.database_service import get_db_connection as _ai_gc
                from services import ai_billing_service as _ai_billing
                with _ai_gc() as _ai_conn:
                    with _ai_conn.cursor() as _ai_cur:
                        _ai_billing.grant_signup_bonus(_ai_cur, propnet_user_id)
                    _ai_conn.commit()
            except Exception as _ai_e:
                logger.warning(f"AI signup bonus grant failed (non-fatal): {_ai_e}")

        except Exception as e:
            logger.error(f"propnet_auth integration error (fallback to legacy): {e}", exc_info=True)
            propnet_user = None

    # Step 3: 기존 web_users 처리 (propnet_auth 성공 여부와 무관하게 유지)
    try:
        user, is_new = find_or_create_user(userinfo)
    except Exception as e:
        logger.error(f"User creation error: {e}")
        return redirect('/propsheet/?error=auth_failed')

    if not user.get('is_active', True):
        return redirect('/propsheet/?error=account_disabled')

    # Step 4: Role 체크 - PropSheet은 agent/subagent/admin만 접근 가능
    # propnet_users.role이 SSoT (CRITICAL 규칙 16)
    if propnet_user is None:
        # propnet_auth 로드 실패 시 role 판별 불가 → 로그인 거부
        logger.error(f"propnet_auth unavailable, cannot determine role for {user['email']}")
        return redirect('/propsheet/?error=auth_unavailable')

    user_role = propnet_user.get('role', 'user')
    allowed_roles = ('admin', 'agent', 'subagent')

    if user_role not in allowed_roles:
        logger.info(f"PropSheet access denied: {user['email']} (role={user_role})")
        return redirect('/propsheet/?error=role_denied')

    # Step 5: Flask 세션 설정 (기존 유지 - HTMX 페이지 호환)
    session.clear()
    session.modified = True

    session.permanent = True
    session['logged_in'] = True
    session['user_id'] = user['id']
    google_name = user.get('name') or ''
    if google_name:
        session['username'] = google_name + '\ub2d8'
    else:
        session['username'] = user['email'].split('@')[0] + '\ub2d8'
    session['user_email'] = user['email']
    session['is_admin'] = is_admin
    session['avatar_url'] = user.get('avatar_url', '')

    # propnet_user_id를 세션에 저장 (동의 등에서 사용)
    if propnet_user_id:
        session['propnet_user_id'] = propnet_user_id
        session['propnet_role'] = propnet_user.get('role', 'user')

    # Single device session
    device_session_id = uuid.uuid4().hex
    session['device_session_id'] = device_session_id
    try:
        from services.database_service import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE web_users SET active_session_id = %s WHERE id = %s",
                            (device_session_id, user['id']))
                conn.commit()
    except Exception as e:
        logger.warning(f"Failed to save device session: {e}")

    # Auto-link subagent (기존 로직 유지)
    try:
        from services.database_service import get_db_connection as _get_conn
        with _get_conn() as _conn:
            with _conn.cursor() as _cur:
                # Gmail 점 정규화 포함 검색
                from utils.email_utils import normalize_email as _norm_email
                _ne = _norm_email(user['email'])
                _cur.execute("""
                    SELECT id, agent_id FROM subagent_requests
                    WHERE status = 'pending'
                      AND (email = %s OR REPLACE(SPLIT_PART(email, '@', 1), '.', '') || '@' || SPLIT_PART(email, '@', 2) = %s)
                """, (user['email'], _ne))
                _invite = _cur.fetchone()
                if _invite:
                    invite_id, agent_id = _invite
                    # propnet_users만 업데이트 (Single Source of Truth)
                    _propnet_uid = session.get('propnet_user_id')
                    if _propnet_uid:
                        _cur.execute(
                            "UPDATE propnet_users SET role = 'subagent', agent_id = %s WHERE id = %s",
                            (agent_id, _propnet_uid))
                    _cur.execute(
                        "UPDATE subagent_requests SET status = 'approved', user_id = %s, responded_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (user['id'], invite_id))
                    _cur.execute("SELECT slug FROM agents WHERE id = %s", (agent_id,))
                    _agent_slug = _cur.fetchone()
                    if _agent_slug:
                        _cur.execute(
                            "SELECT id FROM workspaces WHERE slug LIKE %s",
                            (_agent_slug[0] + '%%',))
                        for _ws in _cur.fetchall():
                            _cur.execute("""
                                INSERT INTO workspace_members (workspace_id, user_id, role, invited_at, accepted_at)
                                VALUES (%s, %s, 'editor', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                                ON CONFLICT (workspace_id, user_id) DO NOTHING
                            """, (_ws[0], user['id']))
                    _conn.commit()
                    logger.info(f"Auto-linked subagent {user['email']} to agent_id={agent_id}")
    except Exception as _e:
        logger.warning(f"Subagent auto-link check failed: {_e}")

    # propnet_users에서 role/agent_id 설정 (SSoT - web_users 대신)
    # subagent auto-link 후 role이 변경되었을 수 있으므로 재조회
    if PROPNET_AUTH_AVAILABLE and propnet_user_id:
        try:
            from propnet_auth.user_service import get_propnet_user as _get_pu
            propnet_user = _get_pu(propnet_user_id) or propnet_user
        except Exception:
            pass
    if propnet_user:
        session['user_role'] = propnet_user.get('role', 'user')
        session['agent_id'] = propnet_user.get('agent_id')

    # Step 6: 동의 확인 및 리다이렉트 결정
    # agent/subagent는 자기 agent_slug로, admin은 /workspaces로
    default_next = '/propsheet/workspaces'
    if not is_admin:
        agent_id = session.get('agent_id')
        if agent_id:
            try:
                from services.database_service import get_db_connection as _gc
                with _gc() as _cn:
                    with _cn.cursor() as _cr:
                        _cr.execute("SELECT slug FROM agents WHERE id = %s AND is_active = true", (agent_id,))
                        _ar = _cr.fetchone()
                        if _ar:
                            default_next = f'/propsheet/{_ar[0]}/'
            except Exception as _e:
                logger.warning(f"Agent slug lookup failed: {_e}")

    next_url = session.pop('oauth_next', '') or default_next
    session.pop('oauth_state', None)

    # JWT 쿠키 설정 + 동의 체크
    if PROPNET_AUTH_AVAILABLE and propnet_user_id:
        try:
            # 동의 완료 여부 확인
            consent_ok = is_consent_complete(
                propnet_user_id,
                services=['propsheet'],
                role=propnet_user.get('role', 'user')
            )

            if not consent_ok:
                # 동의 미완료 시 동의 페이지로 리다이렉트
                session['consent_next'] = next_url
                next_url = '/propsheet/auth/consent'
                logger.info(f"Consent required for {user['email']}, redirecting to consent page")

            # JWT 쿠키 설정 (동의 여부와 무관하게)
            access_token = create_access_token(
                propnet_user_id,
                email=user['email'],
                role=propnet_user.get('role', 'user')
            )
            response = make_response(redirect(next_url))
            set_propnet_cookie(response, access_token)

            logger.info(f"Google OAuth login: {user['email']} (id={user['id']}, propnet_id={propnet_user_id}, "
                        f"new={is_new}, is_admin={is_admin}, consent_ok={consent_ok})")
            return response

        except Exception as e:
            logger.error(f"JWT cookie / consent check error: {e}", exc_info=True)
            # fallback: 쿠키 없이 리다이렉트

    logger.info(f"Google OAuth login: {user['email']} (id={user['id']}, new={is_new}, is_admin={is_admin})")
    return redirect(next_url)


# ============================================================
# 동의 관련 라우트
# ============================================================

@bp.route('/auth/consent')
def consent_page():
    """동의 화면 렌더링 (GET)."""
    if not session.get('logged_in'):
        return redirect('/propsheet/?error=login_required')

    propnet_user_id = session.get('propnet_user_id')
    if not propnet_user_id:
        # propnet_auth 미사용 시 워크스페이스로
        return redirect('/propsheet/workspaces')

    # 미동의 항목 조회
    try:
        role = session.get('propnet_role', 'user')
        missing = get_missing_consents(propnet_user_id, services=['propsheet'], role=role)

        if not missing:
            # 이미 모두 동의 완료
            next_url = session.pop('consent_next', '') or _get_agent_default_url(session)
            return redirect(next_url)

        return render_template('propsheet/consent.html',
                               consents=missing,
                               user_email=session.get('user_email', ''),
                               username=session.get('username', ''))
    except Exception as e:
        logger.error(f"Consent page error: {e}", exc_info=True)
        return redirect('/propsheet/workspaces')


@bp.route('/auth/consent', methods=['POST'])
def consent_submit():
    """동의 기록 (POST) - HTMX/폼 제출."""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401

    propnet_user_id = session.get('propnet_user_id')
    if not propnet_user_id:
        return jsonify({'success': False, 'error': '통합 인증 정보가 없습니다'}), 400

    try:
        # 폼 데이터 또는 JSON에서 동의 항목 파싱
        if request.is_json:
            data = request.get_json()
            consent_types = data.get('consents', [])
        else:
            # 체크박스 폼: consent_terms=on, consent_privacy=on, ...
            consent_types = []
            for key in request.form:
                if key.startswith('consent_') and request.form[key]:
                    consent_type = key[8:]  # remove 'consent_' prefix
                    consent_types.append({'type': consent_type})

        if not consent_types:
            if request.is_json:
                return jsonify({'success': False, 'error': '동의 항목이 없습니다'}), 400
            return redirect('/propsheet/auth/consent?error=no_consent')

        # 동의 기록
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')

        results = record_consent(
            propnet_user_id,
            consent_types,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if request.is_json:
            return jsonify({'success': True, 'recorded': results})

        # 폼 제출: 원래 페이지로 리다이렉트
        next_url = session.pop('consent_next', '') or _get_agent_default_url(session)
        return redirect(next_url)

    except Exception as e:
        logger.error(f"Consent submit error: {e}", exc_info=True)
        if request.is_json:
            return jsonify({'success': False, 'error': '동의 기록 실패'}), 500
        return redirect('/propsheet/auth/consent?error=submit_failed')


@bp.route('/auth/consent/status')
def consent_status():
    """동의 상태 조회 (JSON API)."""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401

    propnet_user_id = session.get('propnet_user_id')
    if not propnet_user_id:
        return jsonify({'success': False, 'error': '통합 인증 정보가 없습니다'}), 400

    try:
        status = check_consent_status(propnet_user_id)
        role = session.get('propnet_role', 'user')
        missing = get_missing_consents(propnet_user_id, services=['propsheet'], role=role)
        complete = len(missing) == 0

        return jsonify({
            'success': True,
            'consent_complete': complete,
            'consents': status,
            'missing': missing,
        })
    except Exception as e:
        logger.error(f"Consent status error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': '상태 조회 실패'}), 500


@bp.route('/auth/consent/withdraw', methods=['POST'])
def consent_withdraw():
    """동의 철회 (JSON API)."""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401

    propnet_user_id = session.get('propnet_user_id')
    if not propnet_user_id:
        return jsonify({'success': False, 'error': '통합 인증 정보가 없습니다'}), 400

    data = request.get_json(silent=True) or {}
    consent_type = data.get('consent_type')
    if not consent_type:
        return jsonify({'success': False, 'error': 'consent_type이 필요합니다'}), 400

    try:
        result = withdraw_consent(propnet_user_id, consent_type)
        if result:
            return jsonify({'success': True, 'withdrawn': consent_type})
        else:
            return jsonify({'success': False, 'error': '철회할 동의를 찾을 수 없습니다'}), 404
    except Exception as e:
        logger.error(f"Consent withdraw error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': '동의 철회 실패'}), 500


# ============================================================
# 기존 라우트
# ============================================================

@bp.route('/auth/debug')
def auth_debug():
    """Debug: show current session state (admin only)."""
    if not session.get('is_admin'):
        return jsonify({'error': 'admin only'}), 403
    return jsonify({
        'logged_in': session.get('logged_in', False),
        'user_id': session.get('user_id'),
        'user_email': session.get('user_email'),
        'username': session.get('username'),
        'is_admin': session.get('is_admin', False),
        'avatar_url': session.get('avatar_url', ''),
        'propnet_user_id': session.get('propnet_user_id'),
        'propnet_role': session.get('propnet_role'),
        'propnet_auth_available': PROPNET_AUTH_AVAILABLE,
        'all_keys': list(session.keys())
    })


# 로그아웃 후 돌아갈 수 있는 안전한 내부 경로 (open-redirect 방지)
_LOGOUT_SAFE_PREFIXES = (
    '/propmap/',
    '/propsheet/',
    '/billing/',
    '/proppedia/',
    '/proptalk/',
    '/app/',
    '/register/',
)


def _safe_logout_next(url):
    if not url or not isinstance(url, str):
        return None
    if url.startswith('//') or '://' in url or url.startswith('\\'):
        return None
    if not url.startswith('/'):
        return None
    path = url.split('?', 1)[0].split('#', 1)[0]
    for p in _LOGOUT_SAFE_PREFIXES:
        if path == p.rstrip('/') or path.startswith(p):
            return url
    return None


@bp.route('/auth/logout')
def logout():
    """Clear session and JWT cookie, redirect to landing (or ?next= 내부 경로)."""
    email = session.get('user_email', 'unknown')

    # 로그아웃 후 머물 곳 결정: ?next= > 기본 /propsheet/
    next_url = _safe_logout_next(request.args.get('next', '')) or '/propsheet/'

    session.clear()
    session.modified = True

    response = make_response(redirect(next_url))

    # Delete session cookies at all paths
    from flask import current_app
    cookie_name = current_app.config.get('SESSION_COOKIE_NAME', 'session')
    for path in ['/', '/property-manager', '/propsheet']:
        response.set_cookie(cookie_name, value='', max_age=0, expires=0,
                          path=path, httponly=True, secure=True, samesite='Lax')

    # Clear propnet_token JWT cookie
    if PROPNET_AUTH_AVAILABLE:
        try:
            clear_propnet_cookie(response)
        except Exception as e:
            logger.warning(f"Failed to clear propnet cookie: {e}")

    logger.info(f"Logout: {email}")
    return response


# ============================================================
# 회원 탈퇴
# ============================================================
@bp.route('/auth/delete-account', methods=['POST'])
def propsheet_delete_account():
    """PropSheet 회원 탈퇴"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '로그인이 필요합니다'}), 401

    try:
        propnet_user_id = session.get('propnet_user_id')

        from services.database_service import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()

        # propnet 데이터 정리
        if propnet_user_id:
            cur.execute('DELETE FROM propnet_consents WHERE propnet_user_id = %s', (propnet_user_id,))
            # PropSheet 서비스 링크만 삭제 (다른 서비스 영향 없음)
            cur.execute("DELETE FROM service_user_links WHERE propnet_user_id = %s AND service = 'propsheet'", (propnet_user_id,))
            # propnet_users 비활성화 (통합 계정 soft delete)
            cur.execute('UPDATE propnet_users SET is_active = FALSE WHERE id = %s', (propnet_user_id,))

        # web_users 비활성화 (데이터 보존, soft delete)
        cur.execute('UPDATE web_users SET is_active = FALSE WHERE id = %s', (user_id,))

        conn.commit()
        cur.close()
        conn.close()

        # 세션 클리어
        session.clear()

        return jsonify({'success': True, 'message': '회원 탈퇴가 완료되었습니다'})
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'PropSheet 회원 탈퇴 에러: {e}')
        return jsonify({'success': False, 'message': '탈퇴 처리 중 오류가 발생했습니다'}), 500
