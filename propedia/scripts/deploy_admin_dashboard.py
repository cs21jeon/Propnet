#!/usr/bin/env python3
"""
통합 관리자 대시보드 배포 스크립트
서버에서 실행: python3 deploy_admin_dashboard.py

생성 파일:
- /backend/property-manager/routes/admin_dashboard.py (재작성)
- /backend/property-manager/services/admin_dashboard_service.py (신규)
- /backend/property-manager/templates/admin/base.html
- /backend/property-manager/templates/admin/dashboard.html
- /backend/property-manager/templates/admin/users.html
- /backend/property-manager/templates/admin/agent_requests.html
- /backend/property-manager/templates/admin/consents.html
- /backend/property-manager/templates/admin/billing.html
- /backend/property-manager/templates/admin/ai_usage.html
- /backend/property-manager/templates/admin/login.html
"""
import os

BASE = '/home/webapp/goldenrabbit/backend/property-manager'
TMPL = os.path.join(BASE, 'templates', 'admin')
ROUTES = os.path.join(BASE, 'routes')
SERVICES = os.path.join(BASE, 'services')

os.makedirs(TMPL, exist_ok=True)
os.makedirs(ROUTES, exist_ok=True)
os.makedirs(SERVICES, exist_ok=True)

files = {}

# ============================================================
# routes/admin_dashboard.py
# ============================================================
files[os.path.join(ROUTES, 'admin_dashboard.py')] = r'''"""
PropNet 통합 관리자 대시보드
- /admin/* 라우트
- propnet_users.role == 'admin' 만 접근 가능
- propnet_auth 라이브러리 사용
"""
import json
import logging
import os
import requests as http_requests
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, g, render_template, redirect, session, url_for

logger = logging.getLogger(__name__)

bp = Blueprint('admin_dashboard', __name__, url_prefix='/admin')


# ── 인증 데코레이터 ──────────────────────────────
def admin_required(f):
    """propnet_users.role == 'admin' 전용 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from propnet_auth.jwt_utils import verify_token

        token = None

        # 1. Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        # 2. Session (web)
        if not token:
            token = session.get('admin_token')

        # 3. propnet_token cookie
        if not token:
            token = request.cookies.get('propnet_token')

        if not token:
            return redirect(url_for('admin_dashboard.admin_login_page'))

        payload = verify_token(token, expected_type='access')
        if not payload:
            # 기존 JWT도 시도 (type 없는 하위 호환)
            payload = verify_token(token)

        if not payload:
            session.pop('admin_token', None)
            return redirect(url_for('admin_dashboard.admin_login_page'))

        # propnet_users에서 role 확인
        from propnet_auth.db import query_one
        user = query_one(
            "SELECT * FROM propnet_users WHERE id = %s AND is_active = TRUE",
            (payload['sub'],)
        )
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'Forbidden - admin only'}), 403

        g.admin_user = user
        return f(*args, **kwargs)
    return decorated


# ── 로그인 ──────────────────────────────
@bp.route('/login', methods=['GET'])
def admin_login_page():
    token = request.args.get('token')
    if token:
        from propnet_auth.jwt_utils import verify_token
        payload = verify_token(token)
        if payload:
            from propnet_auth.db import query_one
            user = query_one(
                "SELECT * FROM propnet_users WHERE id = %s AND role = 'admin' AND is_active = TRUE",
                (payload['sub'],)
            )
            if user:
                session['admin_token'] = token
                return redirect(url_for('admin_dashboard.admin_home'))

    google_client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', os.environ.get('GOOGLE_WEB_CLIENT_ID', ''))
    return render_template('admin/login.html', google_client_id=google_client_id)


@bp.route('/login', methods=['POST'])
def admin_login_post():
    data = request.get_json() or request.form
    google_token = data.get('id_token', '').strip()

    if not google_token:
        return jsonify({'error': 'Google sign-in required'}), 400

    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        idinfo = google_id_token.verify_oauth2_token(
            google_token, google_requests.Request()
        )
        email = idinfo.get('email', '')
        google_id = idinfo.get('sub', '')
        name = idinfo.get('name', '')
    except Exception as e:
        logger.error(f"Google token verification failed: {e}")
        return jsonify({'error': 'Invalid Google token'}), 401

    from propnet_auth.db import query_one
    user = query_one(
        "SELECT * FROM propnet_users WHERE email = %s AND role = 'admin' AND is_active = TRUE",
        (email,)
    )
    if not user:
        return jsonify({'error': '관리자 계정이 아닙니다'}), 403

    from propnet_auth.jwt_utils import create_access_token
    token = create_access_token(user['id'], user['email'], user['role'])
    session['admin_token'] = token
    return jsonify({'ok': True, 'redirect': '/admin/'})


@bp.route('/logout')
def admin_logout():
    session.pop('admin_token', None)
    return redirect(url_for('admin_dashboard.admin_login_page'))


# ── 대시보드 홈 ──────────────────────────────
@bp.route('/')
@admin_required
def admin_home():
    from services.admin_dashboard_service import AdminDashboardService as svc
    stats = svc.get_dashboard_stats()
    recent_users = svc.get_recent_users(10)
    return render_template('admin/dashboard.html',
                           stats=stats, recent_users=recent_users,
                           active='dashboard')


# ── 유저 관리 ──────────────────────────────
@bp.route('/users')
@admin_required
def admin_users():
    from services.admin_dashboard_service import AdminDashboardService as svc
    search = request.args.get('q', '').strip()
    role_filter = request.args.get('role', '').strip()
    users = svc.get_all_users(search=search, role_filter=role_filter)
    return render_template('admin/users.html',
                           users=users, search=search, role_filter=role_filter,
                           active='users')


@bp.route('/api/users/<int:user_id>/role', methods=['POST'])
@admin_required
def api_change_role(user_id):
    """유저 역할 변경 API"""
    from services.admin_dashboard_service import AdminDashboardService as svc
    data = request.get_json()
    new_role = data.get('role', '').strip()

    if new_role not in ('user', 'agent', 'subagent', 'admin'):
        return jsonify({'error': 'Invalid role'}), 400

    result = svc.update_user_role(user_id, new_role, g.admin_user['email'])
    if result.get('error'):
        return jsonify(result), 400
    return jsonify({'ok': True})


# ── Agent 승인 ──────────────────────────────
@bp.route('/agent-requests')
@admin_required
def admin_agent_requests():
    from services.admin_dashboard_service import AdminDashboardService as svc
    requests_list = svc.get_agent_requests()
    return render_template('admin/agent_requests.html',
                           requests=requests_list, active='agent_requests')


@bp.route('/api/agent-requests/<int:req_id>/approve', methods=['POST'])
@admin_required
def api_approve_agent(req_id):
    """Agent 가입 신청 승인"""
    from services.admin_dashboard_service import AdminDashboardService as svc
    result = svc.approve_agent_request(req_id, g.admin_user['email'])
    if result.get('error'):
        return jsonify(result), 400
    return jsonify({'ok': True, 'message': result.get('message', 'Approved')})


@bp.route('/api/agent-requests/<int:req_id>/reject', methods=['POST'])
@admin_required
def api_reject_agent(req_id):
    """Agent 가입 신청 거절"""
    from services.admin_dashboard_service import AdminDashboardService as svc
    data = request.get_json()
    reason = data.get('reason', '').strip()
    result = svc.reject_agent_request(req_id, reason, g.admin_user['email'])
    if result.get('error'):
        return jsonify(result), 400
    return jsonify({'ok': True})


# ── 동의 관리 ──────────────────────────────
@bp.route('/consents')
@admin_required
def admin_consents():
    from services.admin_dashboard_service import AdminDashboardService as svc
    consent_stats = svc.get_consent_stats()
    recent_consents = svc.get_recent_consents(20)
    return render_template('admin/consents.html',
                           consent_stats=consent_stats,
                           recent_consents=recent_consents,
                           active='consents')


# ── Proptalk 과금 ──────────────────────────────
@bp.route('/billing')
@admin_required
def admin_billing():
    from services.admin_dashboard_service import AdminDashboardService as svc
    billing_stats = svc.get_billing_stats()
    billing_users = svc.get_billing_users()
    return render_template('admin/billing.html',
                           stats=billing_stats, users=billing_users,
                           active='billing')


@bp.route('/api/billing/users/<int:user_id>/plan', methods=['POST'])
@admin_required
def api_change_billing(user_id):
    """Proptalk 유저 과금 변경"""
    from services.admin_dashboard_service import AdminDashboardService as svc
    data = request.get_json()
    action = data.get('action')

    result = svc.update_billing(user_id, action, data, g.admin_user['email'])
    if result.get('error'):
        return jsonify(result), 400
    return jsonify({'ok': True})


# ── AI 사용량 ──────────────────────────────
@bp.route('/ai-usage')
@admin_required
def admin_ai_usage():
    return render_template('admin/ai_usage.html', active='ai_usage')


@bp.route('/api/openai-costs')
@admin_required
def api_openai_costs():
    """OpenAI Costs API 프록시"""
    admin_key = os.environ.get('OPENAI_ADMIN_KEY')
    if not admin_key:
        return jsonify({'error': 'OPENAI_ADMIN_KEY not configured'}), 500

    days = int(request.args.get('days', 30))
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    start_ts = int(start.timestamp())

    headers = {
        'Authorization': f'Bearer {admin_key}',
        'Content-Type': 'application/json',
    }

    all_data = []
    page_cursor = None
    try:
        while True:
            params = {
                'start_time': start_ts,
                'bucket_width': '1d',
                'limit': 90,
            }
            if page_cursor:
                params['page'] = page_cursor
            resp = http_requests.get(
                'https://api.openai.com/v1/organization/costs',
                headers=headers, params=params, timeout=45
            )
            if resp.status_code != 200:
                logger.error(f"[OpenAI Costs] {resp.status_code}: {resp.text[:300]}")
                return jsonify({'error': 'OpenAI API error', 'detail': resp.text[:300]}), resp.status_code
            body = resp.json()
            all_data.extend(body.get('data', []))
            page_cursor = body.get('next_page')
            if not page_cursor:
                break
    except Exception as e:
        logger.error(f"[OpenAI Costs] request failed: {e}")
        return jsonify({'error': 'OpenAI API connection failed', 'detail': str(e)}), 504

    return jsonify({'data': all_data})


@bp.route('/api/openai-usage-detail')
@admin_required
def api_openai_usage_detail():
    """OpenAI Usage API 프록시"""
    admin_key = os.environ.get('OPENAI_ADMIN_KEY')
    if not admin_key:
        return jsonify({'error': 'OPENAI_ADMIN_KEY not configured'}), 500

    days = int(request.args.get('days', 30))
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    start_ts = int(start.timestamp())

    headers = {
        'Authorization': f'Bearer {admin_key}',
        'Content-Type': 'application/json',
    }

    result = {}
    # Audio transcriptions
    all_data = []
    page_cursor = None
    while True:
        params = {
            'start_time': start_ts,
            'bucket_width': '1d',
            'group_by': ['model'],
            'limit': 90,
        }
        if page_cursor:
            params['page'] = page_cursor
        try:
            resp = http_requests.get(
                'https://api.openai.com/v1/organization/usage/audio_speeches',
                headers=headers, params=params, timeout=15
            )
            if resp.status_code == 200:
                body = resp.json()
                all_data.extend(body.get('data', []))
                page_cursor = body.get('next_page')
                if not page_cursor:
                    break
            else:
                break
        except Exception:
            break

    result['audio_transcriptions'] = all_data
    return jsonify(result)


@bp.route('/api/openai-credit')
@admin_required
def api_openai_credit_get():
    """OpenAI 크레딧 잔액 조회"""
    from propnet_auth.db import query_one
    row = query_one("SELECT * FROM admin_settings WHERE key = 'openai_credit'")
    total_credit = float(row['value']) if row else 0.0

    # 누적 비용 계산 (간소화: 클라이언트에서 계산하도록)
    return jsonify({
        'total_credit': total_credit,
        'total_used': 0,
        'balance': total_credit,
    })


@bp.route('/api/openai-credit', methods=['POST'])
@admin_required
def api_openai_credit_set():
    """OpenAI 크레딧 설정"""
    from propnet_auth.db import execute
    data = request.get_json()
    val = float(data.get('total_credit', 0))
    execute(
        """INSERT INTO admin_settings (key, value) VALUES ('openai_credit', %s)
           ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()""",
        (str(val), str(val))
    )
    return jsonify({'ok': True})
'''

# ============================================================
# services/admin_dashboard_service.py
# ============================================================
files[os.path.join(SERVICES, 'admin_dashboard_service.py')] = r'''"""
통합 관리자 대시보드 서비스 로직
propnet_auth.db 사용
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AdminDashboardService:

    # ── 대시보드 통계 ──────────────────────────────

    @staticmethod
    def get_dashboard_stats():
        """대시보드 홈 통계"""
        from propnet_auth.db import query_one, query_all

        stats = {}

        # 전체 유저 수
        row = query_one("SELECT COUNT(*) as cnt FROM propnet_users WHERE is_active = TRUE")
        stats['total_users'] = row['cnt'] if row else 0

        # 역할별 유저 수
        rows = query_all(
            "SELECT role, COUNT(*) as cnt FROM propnet_users WHERE is_active = TRUE GROUP BY role"
        )
        role_counts = {r['role']: r['cnt'] for r in rows} if rows else {}
        stats['agents'] = role_counts.get('agent', 0)
        stats['subagents'] = role_counts.get('subagent', 0)
        stats['admins'] = role_counts.get('admin', 0)
        stats['users'] = role_counts.get('user', 0)

        # 서비스별 연결 현황
        rows = query_all(
            "SELECT service, COUNT(*) as cnt FROM service_user_links GROUP BY service"
        )
        service_counts = {r['service']: r['cnt'] for r in rows} if rows else {}
        stats['propedia_users'] = service_counts.get('propedia', 0)
        stats['proptalk_users'] = service_counts.get('proptalk', 0)
        stats['propsheet_users'] = service_counts.get('propsheet', 0)

        # Proptalk 매출 (voiceroom DB)
        try:
            from propnet_auth.db import voiceroom_query_one
            rev = voiceroom_query_one(
                "SELECT COALESCE(SUM(amount), 0) as total FROM payment_transactions WHERE status = 'completed'"
            )
            stats['total_revenue'] = int(rev['total']) if rev else 0
        except Exception as e:
            logger.warning(f"voiceroom revenue query failed: {e}")
            stats['total_revenue'] = 0

        # 대기중 Agent 신청
        pending = query_one(
            "SELECT COUNT(*) as cnt FROM agent_requests WHERE status = 'pending'"
        )
        stats['pending_agent_requests'] = pending['cnt'] if pending else 0

        return stats

    @staticmethod
    def get_recent_users(limit=10):
        """최근 가입 유저"""
        from propnet_auth.db import query_all
        return query_all(
            """SELECT u.*,
                      array_agg(DISTINCT sl.service) FILTER (WHERE sl.service IS NOT NULL) as services
               FROM propnet_users u
               LEFT JOIN service_user_links sl ON sl.propnet_user_id = u.id
               WHERE u.is_active = TRUE
               GROUP BY u.id
               ORDER BY u.created_at DESC
               LIMIT %s""",
            (limit,)
        ) or []

    # ── 유저 관리 ──────────────────────────────

    @staticmethod
    def get_all_users(search='', role_filter=''):
        """전체 유저 목록 (검색/필터 지원)"""
        from propnet_auth.db import query_all

        conditions = ["u.is_active = TRUE"]
        params = []

        if search:
            conditions.append("(u.email ILIKE %s OR u.name ILIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])

        if role_filter:
            conditions.append("u.role = %s")
            params.append(role_filter)

        where = ' AND '.join(conditions)
        return query_all(
            f"""SELECT u.*,
                       array_agg(DISTINCT sl.service) FILTER (WHERE sl.service IS NOT NULL) as services
                FROM propnet_users u
                LEFT JOIN service_user_links sl ON sl.propnet_user_id = u.id
                WHERE {where}
                GROUP BY u.id
                ORDER BY u.created_at DESC""",
            tuple(params)
        ) or []

    @staticmethod
    def update_user_role(user_id, new_role, admin_email):
        """유저 역할 변경"""
        from propnet_auth.db import query_one, execute

        user = query_one("SELECT * FROM propnet_users WHERE id = %s", (user_id,))
        if not user:
            return {'error': 'User not found'}

        if new_role == user['role']:
            return {'ok': True, 'message': 'No change'}

        execute(
            "UPDATE propnet_users SET role = %s, updated_at = NOW() WHERE id = %s",
            (new_role, user_id)
        )
        logger.info(f"[Admin] role change: user={user_id} {user['role']}->{new_role} by {admin_email}")

        # agent로 변경 시 agents 테이블 확인/생성
        if new_role == 'agent':
            existing = query_one("SELECT id FROM agents WHERE email = %s", (user['email'],))
            if not existing:
                execute(
                    """INSERT INTO agents (email, google_id, name, status, approved_at)
                       VALUES (%s, %s, %s, 'approved', NOW())""",
                    (user['email'], user.get('google_id'), user['name'])
                )
                logger.info(f"[Admin] agents record created for {user['email']}")

        return {'ok': True}

    # ── Agent 승인 ──────────────────────────────

    @staticmethod
    def get_agent_requests():
        """Agent 가입 신청 목록"""
        from propnet_auth.db import query_all
        return query_all(
            """SELECT ar.*, pu.name as user_name, pu.email as user_email, pu.avatar_url
               FROM agent_requests ar
               LEFT JOIN propnet_users pu ON pu.id = ar.propnet_user_id
               ORDER BY
                   CASE WHEN ar.status = 'pending' THEN 0 ELSE 1 END,
                   ar.created_at DESC"""
        ) or []

    @staticmethod
    def approve_agent_request(req_id, admin_email):
        """Agent 신청 승인"""
        from propnet_auth.db import query_one, execute

        req = query_one("SELECT * FROM agent_requests WHERE id = %s", (req_id,))
        if not req:
            return {'error': 'Request not found'}
        if req['status'] != 'pending':
            return {'error': f'Already {req["status"]}'}

        user_id = req['propnet_user_id']
        user = query_one("SELECT * FROM propnet_users WHERE id = %s", (user_id,))
        if not user:
            return {'error': 'User not found'}

        # 1. role -> agent
        execute(
            "UPDATE propnet_users SET role = 'agent', updated_at = NOW() WHERE id = %s",
            (user_id,)
        )

        # 2. agents 테이블에 레코드 생성
        agent = execute(
            """INSERT INTO agents (email, google_id, name, agency_name, slug, phone, address, license_no, license_file, status, approved_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'approved', NOW())
               ON CONFLICT (email) DO UPDATE SET
                   agency_name = EXCLUDED.agency_name, slug = EXCLUDED.slug,
                   phone = EXCLUDED.phone, address = EXCLUDED.address,
                   license_no = EXCLUDED.license_no, license_file = EXCLUDED.license_file,
                   status = 'approved', approved_at = NOW()
               RETURNING *""",
            (user['email'], user.get('google_id'), req.get('representative_name') or user['name'],
             req.get('agent_name'), req.get('agent_slug'), req.get('phone'),
             req.get('office_address'), None, req.get('license_file_path'))
        )

        # 3. propnet_users.agent_id 연결
        if agent:
            execute(
                "UPDATE propnet_users SET agent_id = %s WHERE id = %s",
                (agent['id'], user_id)
            )

        # 4. agent_requests 상태 업데이트
        execute(
            "UPDATE agent_requests SET status = 'approved', reviewed_at = NOW() WHERE id = %s",
            (req_id,)
        )

        logger.info(f"[Admin] agent approved: request={req_id} user={user_id} by {admin_email}")

        # 5. PropSheet 워크스페이스 자동 생성 시도
        slug = req.get('agent_slug')
        if slug and agent:
            try:
                _create_propsheet_workspace(agent['id'], slug, req.get('agent_name', ''))
                logger.info(f"[Admin] PropSheet workspace created: slug={slug}")
            except Exception as e:
                logger.error(f"[Admin] PropSheet workspace creation failed: {e}")

        return {'ok': True, 'message': f'Agent approved: {user["email"]}'}

    @staticmethod
    def reject_agent_request(req_id, reason, admin_email):
        """Agent 신청 거절"""
        from propnet_auth.db import query_one, execute

        req = query_one("SELECT * FROM agent_requests WHERE id = %s", (req_id,))
        if not req:
            return {'error': 'Request not found'}
        if req['status'] != 'pending':
            return {'error': f'Already {req["status"]}'}

        execute(
            """UPDATE agent_requests SET status = 'rejected', reject_reason = %s,
                      reviewed_at = NOW()
               WHERE id = %s""",
            (reason, req_id)
        )
        logger.info(f"[Admin] agent rejected: request={req_id} reason={reason} by {admin_email}")
        return {'ok': True}

    # ── 동의 관리 ──────────────────────────────

    @staticmethod
    def get_consent_stats():
        """동의 현황 통계"""
        from propnet_auth.db import query_all, query_one

        stats = {}

        # 약관 유형별 동의 현황
        rows = query_all(
            """SELECT consent_type, version, COUNT(*) as cnt,
                      COUNT(*) FILTER (WHERE agreed = TRUE) as agreed_cnt
               FROM propnet_consents
               GROUP BY consent_type, version
               ORDER BY consent_type, version DESC"""
        )
        stats['by_type'] = rows or []

        # 전체 동의 완료 유저 수 (공통 3종 동의)
        total = query_one(
            """SELECT COUNT(DISTINCT propnet_user_id) as cnt
               FROM propnet_consents
               WHERE consent_type IN ('terms', 'privacy', 'overseas_transfer')
                 AND agreed = TRUE"""
        )
        stats['total_consented'] = total['cnt'] if total else 0

        return stats

    @staticmethod
    def get_recent_consents(limit=20):
        """최근 동의 이력"""
        from propnet_auth.db import query_all
        return query_all(
            """SELECT pc.*, pu.email, pu.name
               FROM propnet_consents pc
               JOIN propnet_users pu ON pu.id = pc.propnet_user_id
               ORDER BY pc.agreed_at DESC
               LIMIT %s""",
            (limit,)
        ) or []

    # ── Proptalk 과금 ──────────────────────────────

    @staticmethod
    def get_billing_stats():
        """Proptalk 과금 통계"""
        try:
            from propnet_auth.db import voiceroom_query_one
            stats = {}
            row = voiceroom_query_one(
                "SELECT COUNT(*) as cnt FROM user_billing"
            )
            stats['total_billing_users'] = row['cnt'] if row else 0

            row = voiceroom_query_one(
                "SELECT COALESCE(SUM(amount), 0) as total FROM payment_transactions WHERE status = 'completed'"
            )
            stats['total_revenue'] = int(row['total']) if row else 0

            row = voiceroom_query_one(
                "SELECT COUNT(*) as cnt FROM user_billing WHERE subscription_status = 'active'"
            )
            stats['active_subscriptions'] = row['cnt'] if row else 0

            return stats
        except Exception as e:
            logger.warning(f"billing stats query failed: {e}")
            return {'total_billing_users': 0, 'total_revenue': 0, 'active_subscriptions': 0}

    @staticmethod
    def get_billing_users():
        """Proptalk 과금 유저 목록"""
        try:
            from propnet_auth.db import get_voiceroom_db
            import psycopg2.extras
            with get_voiceroom_db() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT u.id, u.name, u.email,
                                  ub.remaining_seconds, ub.subscription_status,
                                  bp.name as plan_name, bp.code as plan_code,
                                  u.created_at
                           FROM users u
                           LEFT JOIN user_billing ub ON ub.user_id = u.id
                           LEFT JOIN billing_plans bp ON bp.id = ub.current_plan_id
                           ORDER BY u.created_at DESC"""
                    )
                    return cur.fetchall() or []
        except Exception as e:
            logger.warning(f"billing users query failed: {e}")
            return []

    @staticmethod
    def update_billing(user_id, action, data, admin_email):
        """Proptalk 과금 변경"""
        try:
            from propnet_auth.db import get_voiceroom_db
            import psycopg2.extras
            with get_voiceroom_db() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if action == 'add_seconds':
                        seconds = int(data.get('seconds', 0))
                        if seconds > 0:
                            cur.execute(
                                """INSERT INTO user_billing (user_id, remaining_seconds)
                                   VALUES (%s, %s)
                                   ON CONFLICT (user_id) DO UPDATE
                                   SET remaining_seconds = user_billing.remaining_seconds + %s""",
                                (user_id, seconds, seconds)
                            )
                            logger.info(f"[Admin] billing +{seconds}s user={user_id} by {admin_email}")

                    elif action == 'set_seconds':
                        seconds = int(data.get('seconds', 0))
                        cur.execute(
                            """INSERT INTO user_billing (user_id, remaining_seconds)
                               VALUES (%s, %s)
                               ON CONFLICT (user_id) DO UPDATE SET remaining_seconds = %s""",
                            (user_id, seconds, seconds)
                        )
                        logger.info(f"[Admin] billing set_seconds={seconds} user={user_id} by {admin_email}")

                    elif action == 'set_plan':
                        plan_code = data.get('plan_code')
                        cur.execute("SELECT id FROM billing_plans WHERE code = %s AND is_active = TRUE", (plan_code,))
                        plan = cur.fetchone()
                        if plan:
                            cur.execute(
                                """INSERT INTO user_billing (user_id, current_plan_id)
                                   VALUES (%s, %s)
                                   ON CONFLICT (user_id) DO UPDATE SET current_plan_id = %s""",
                                (user_id, plan['id'], plan['id'])
                            )
                            logger.info(f"[Admin] billing plan={plan_code} user={user_id} by {admin_email}")
                        else:
                            return {'error': f'Plan not found: {plan_code}'}
                    else:
                        return {'error': f'Unknown action: {action}'}
            return {'ok': True}
        except Exception as e:
            logger.error(f"billing update failed: {e}")
            return {'error': str(e)}


def _create_propsheet_workspace(agent_id, slug, agency_name):
    """PropSheet 워크스페이스 자동 생성"""
    from propnet_auth.db import query_one, execute

    existing = query_one("SELECT id FROM workspaces WHERE slug = %s", (slug,))
    if existing:
        return existing

    ws = execute(
        """INSERT INTO workspaces (name, slug, owner_email, created_at)
           VALUES (%s, %s, (SELECT email FROM agents WHERE id = %s), NOW())
           RETURNING *""",
        (agency_name or slug, slug, agent_id)
    )
    if ws:
        logger.info(f"PropSheet workspace created: id={ws['id']} slug={slug}")
    return ws
'''

# ============================================================
# templates/admin/base.html
# ============================================================
files[os.path.join(TMPL, 'base.html')] = r'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{% block title %}Admin{% endblock %} - PropNet</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f2f5; color: #333; }

        /* Navbar */
        .navbar { background: #1a1a2e; color: #fff; padding: 0 16px; display: flex; align-items: center; height: 56px; position: sticky; top: 0; z-index: 100; }
        .navbar .brand { font-weight: 700; font-size: 17px; color: #fff; white-space: nowrap; text-decoration: none; }
        .nav-links { display: flex; align-items: center; gap: 2px; margin-left: 16px; overflow-x: auto; }
        .nav-links a { color: rgba(255,255,255,0.65); text-decoration: none; font-size: 13px; padding: 8px 10px; border-radius: 8px; transition: all 0.2s; white-space: nowrap; }
        .nav-links a:hover { color: #fff; background: rgba(255,255,255,0.1); }
        .nav-links a.active { color: #fff; background: rgba(255,255,255,0.15); font-weight: 600; }
        .nav-right { margin-left: auto; flex-shrink: 0; }
        .nav-right a { color: rgba(255,255,255,0.5); text-decoration: none; font-size: 13px; }
        .nav-right a:hover { color: #fff; }
        .badge-nav { display: inline-block; background: #e74c3c; color: #fff; font-size: 10px; padding: 1px 5px; border-radius: 8px; margin-left: 3px; font-weight: 700; vertical-align: top; }

        /* Container */
        .container { max-width: 1200px; margin: 0 auto; padding: 20px 16px; }

        /* Cards */
        .card { background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
        .card h3 { margin-bottom: 16px; font-size: 15px; color: #555; font-weight: 600; }

        /* Stats Grid */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .stat-card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
        .stat-card .value { font-size: 26px; font-weight: 700; color: #1a1a2e; }
        .stat-card .label { font-size: 12px; color: #999; margin-top: 4px; letter-spacing: 0.3px; }

        /* Table */
        .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th { text-align: left; padding: 10px 12px; border-bottom: 2px solid #eee; color: #888; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; }
        td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; white-space: nowrap; }
        tr:hover { background: #fafbfc; }
        .text-right { text-align: right; }

        /* Badges */
        .badge { display: inline-block; padding: 3px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; }
        .badge-admin { background: #fce4ec; color: #c62828; }
        .badge-agent { background: #e3f2fd; color: #1565c0; }
        .badge-subagent { background: #fff3e0; color: #e65100; }
        .badge-user { background: #e8eaed; color: #5f6368; }
        .badge-pending { background: #fff8e1; color: #f57f17; }
        .badge-approved { background: #e8f5e9; color: #2e7d32; }
        .badge-rejected { background: #fce4ec; color: #c62828; }
        .badge-active { background: #d4edda; color: #155724; }
        .badge-free { background: #e8eaed; color: #5f6368; }
        .badge-expired { background: #f8d7da; color: #721c24; }

        /* Buttons & Inputs */
        a.btn { display: inline-block; padding: 8px 16px; background: #1a1a2e; color: #fff; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 500; }
        a.btn:hover { background: #16213e; }
        .btn-sm { padding: 5px 12px; font-size: 12px; border-radius: 6px; }
        .btn-success { background: #2e7d32; color: #fff; border: none; cursor: pointer; padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; }
        .btn-success:hover { background: #1b5e20; }
        .btn-danger { background: #c62828; color: #fff; border: none; cursor: pointer; padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; }
        .btn-danger:hover { background: #b71c1c; }
        input[type=text], input[type=number], input[type=search], select, textarea {
            padding: 8px 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; background: #fff;
        }
        button { padding: 8px 18px; background: #1a1a2e; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; }
        button:hover { background: #16213e; }

        /* Role select */
        .role-select { padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; border: 2px solid #ddd; cursor: pointer; }
        .role-select.role-admin { border-color: #c62828; background: #fff5f5; }
        .role-select.role-agent { border-color: #1565c0; background: #f0f7ff; }
        .role-select.role-subagent { border-color: #e65100; background: #fff8f0; }

        /* Search */
        .search-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
        .search-bar input { flex: 1; min-width: 200px; }
        .search-bar select { min-width: 120px; }

        /* Utilities */
        .mb-8 { margin-bottom: 8px; }
        .mb-16 { margin-bottom: 16px; }
        .text-muted { color: #999; }
        .text-sm { font-size: 13px; }

        /* Mobile */
        @media (max-width: 767px) {
            .navbar { padding: 0 10px; height: 48px; }
            .navbar .brand { font-size: 14px; }
            .nav-links { gap: 0; margin-left: 6px; }
            .nav-links a { font-size: 12px; padding: 6px 7px; }
            .container { padding: 12px; }
            .stats-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
            .stat-card { padding: 14px; }
            .stat-card .value { font-size: 22px; }
            .card { padding: 14px; border-radius: 10px; }
            table { font-size: 13px; }
            th, td { padding: 8px 10px; }
        }

        @media (min-width: 768px) {
            .container { padding: 24px; }
            .stats-grid { gap: 16px; }
            .stat-card { padding: 24px; }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <a href="/admin/" class="brand">PropNet Admin</a>
        <div class="nav-links">
            <a href="/admin/" class="{% if active == 'dashboard' %}active{% endif %}">대시보드</a>
            <a href="/admin/users" class="{% if active == 'users' %}active{% endif %}">유저</a>
            <a href="/admin/agent-requests" class="{% if active == 'agent_requests' %}active{% endif %}">
                Agent 승인
                {% if pending_count is defined and pending_count > 0 %}<span class="badge-nav">{{ pending_count }}</span>{% endif %}
            </a>
            <a href="/admin/consents" class="{% if active == 'consents' %}active{% endif %}">동의</a>
            <a href="/admin/billing" class="{% if active == 'billing' %}active{% endif %}">과금</a>
            <a href="/admin/ai-usage" class="{% if active == 'ai_usage' %}active{% endif %}">AI</a>
        </div>
        <div class="nav-right">
            <a href="/admin/logout">로그아웃</a>
        </div>
    </nav>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
'''

# ============================================================
# templates/admin/login.html
# ============================================================
files[os.path.join(TMPL, 'login.html')] = r'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - PropNet</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .login-card { background: #fff; border-radius: 16px; padding: 40px; max-width: 400px; width: 90%; text-align: center; box-shadow: 0 4px 24px rgba(0,0,0,0.2); }
        .login-card h1 { font-size: 22px; margin-bottom: 8px; color: #1a1a2e; }
        .login-card p { font-size: 14px; color: #888; margin-bottom: 24px; }
        #g_id_onload, .g_id_signin { display: inline-block; }
        .error { color: #c62828; font-size: 13px; margin-top: 12px; display: none; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>PropNet Admin</h1>
        <p>관리자 계정으로 로그인하세요</p>
        <div id="g_id_onload"
             data-client_id="{{ google_client_id }}"
             data-callback="handleCredentialResponse"
             data-auto_prompt="false">
        </div>
        <div class="g_id_signin"
             data-type="standard"
             data-size="large"
             data-theme="outline"
             data-text="sign_in_with"
             data-shape="rectangular"
             data-logo_alignment="left">
        </div>
        <div id="error" class="error"></div>
    </div>

    <script src="https://accounts.google.com/gsi/client" async defer></script>
    <script>
    async function handleCredentialResponse(response) {
        try {
            const res = await fetch('/admin/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id_token: response.credential})
            });
            const data = await res.json();
            if (data.ok) {
                window.location.href = data.redirect || '/admin/';
            } else {
                document.getElementById('error').textContent = data.error || 'Login failed';
                document.getElementById('error').style.display = 'block';
            }
        } catch (e) {
            document.getElementById('error').textContent = 'Network error';
            document.getElementById('error').style.display = 'block';
        }
    }
    </script>
</body>
</html>
'''

# ============================================================
# templates/admin/dashboard.html
# ============================================================
files[os.path.join(TMPL, 'dashboard.html')] = r'''{% extends "admin/base.html" %}
{% block title %}대시보드{% endblock %}
{% block content %}
<h2 style="font-size:20px;font-weight:700;margin-bottom:16px;">대시보드</h2>

<div class="stats-grid">
    <div class="stat-card">
        <div class="value">{{ stats.total_users }}</div>
        <div class="label">전체 유저</div>
    </div>
    <div class="stat-card">
        <div class="value">{{ stats.agents }}</div>
        <div class="label">Agent</div>
    </div>
    <div class="stat-card">
        <div class="value">{{ stats.subagents }}</div>
        <div class="label">Subagent</div>
    </div>
    <div class="stat-card">
        <div class="value">{{ "{:,}".format(stats.total_revenue) }}</div>
        <div class="label">매출 (원)</div>
    </div>
    {% if stats.pending_agent_requests > 0 %}
    <div class="stat-card" style="border-left: 3px solid #f57f17;">
        <div class="value" style="color:#f57f17;">{{ stats.pending_agent_requests }}</div>
        <div class="label">Agent 승인 대기</div>
    </div>
    {% endif %}
</div>

<div class="stats-grid" style="grid-template-columns: repeat(3, 1fr);">
    <div class="stat-card">
        <div class="value" style="font-size:22px;">{{ stats.propedia_users }}</div>
        <div class="label">Propedia 연결</div>
    </div>
    <div class="stat-card">
        <div class="value" style="font-size:22px;">{{ stats.proptalk_users }}</div>
        <div class="label">Proptalk 연결</div>
    </div>
    <div class="stat-card">
        <div class="value" style="font-size:22px;">{{ stats.propsheet_users }}</div>
        <div class="label">PropSheet 연결</div>
    </div>
</div>

<div class="card">
    <h3>최근 가입 유저</h3>
    {% if recent_users %}
    <div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th>이름</th>
                <th>이메일</th>
                <th>역할</th>
                <th>서비스</th>
                <th>가입일</th>
            </tr>
        </thead>
        <tbody>
            {% for u in recent_users %}
            <tr>
                <td>{{ u.name or '-' }}</td>
                <td>{{ u.email }}</td>
                <td><span class="badge badge-{{ u.role }}">{{ u.role }}</span></td>
                <td>
                    {% if u.services %}
                        {% for s in u.services %}
                            <span class="badge badge-free" style="font-size:10px;">{{ s }}</span>
                        {% endfor %}
                    {% else %}
                        <span class="text-muted text-sm">-</span>
                    {% endif %}
                </td>
                <td>{{ u.created_at.strftime('%Y-%m-%d') if u.created_at else '-' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    </div>
    {% else %}
    <p class="text-muted text-sm">유저가 없습니다.</p>
    {% endif %}
</div>
{% endblock %}
'''

# ============================================================
# templates/admin/users.html
# ============================================================
files[os.path.join(TMPL, 'users.html')] = r'''{% extends "admin/base.html" %}
{% block title %}유저 관리{% endblock %}
{% block content %}
<h2 style="font-size:20px;font-weight:700;margin-bottom:16px;">유저 관리 ({{ users|length }}명)</h2>

<form class="search-bar" method="GET" action="/admin/users">
    <input type="search" name="q" value="{{ search }}" placeholder="이름 또는 이메일 검색...">
    <select name="role" onchange="this.form.submit()">
        <option value="">전체 역할</option>
        <option value="user" {% if role_filter == 'user' %}selected{% endif %}>user</option>
        <option value="agent" {% if role_filter == 'agent' %}selected{% endif %}>agent</option>
        <option value="subagent" {% if role_filter == 'subagent' %}selected{% endif %}>subagent</option>
        <option value="admin" {% if role_filter == 'admin' %}selected{% endif %}>admin</option>
    </select>
    <button type="submit">검색</button>
</form>

<div class="card">
    <div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>이름</th>
                <th>이메일</th>
                <th>역할</th>
                <th>서비스</th>
                <th>가입일</th>
            </tr>
        </thead>
        <tbody>
            {% for u in users %}
            <tr>
                <td>{{ u.id }}</td>
                <td>{{ u.name or '-' }}</td>
                <td>{{ u.email }}</td>
                <td>
                    <select class="role-select role-{{ u.role }}"
                            onchange="changeRole({{ u.id }}, this.value, this)"
                            data-original="{{ u.role }}">
                        <option value="user" {% if u.role == 'user' %}selected{% endif %}>user</option>
                        <option value="subagent" {% if u.role == 'subagent' %}selected{% endif %}>subagent</option>
                        <option value="agent" {% if u.role == 'agent' %}selected{% endif %}>agent</option>
                        <option value="admin" {% if u.role == 'admin' %}selected{% endif %}>admin</option>
                    </select>
                </td>
                <td>
                    {% if u.services %}
                        {% for s in u.services %}
                            <span class="badge badge-free" style="font-size:10px;">{{ s }}</span>
                        {% endfor %}
                    {% else %}
                        -
                    {% endif %}
                </td>
                <td>{{ u.created_at.strftime('%Y-%m-%d') if u.created_at else '-' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    </div>
</div>

<script>
async function changeRole(userId, newRole, selectEl) {
    const original = selectEl.dataset.original;
    if (newRole === original) return;

    if (!confirm(`역할을 ${original} -> ${newRole}(으)로 변경하시겠습니까?`)) {
        selectEl.value = original;
        return;
    }

    try {
        const res = await fetch(`/admin/api/users/${userId}/role`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({role: newRole})
        });
        const data = await res.json();
        if (data.ok) {
            selectEl.dataset.original = newRole;
            selectEl.className = 'role-select role-' + newRole;
        } else {
            alert(data.error || 'Failed');
            selectEl.value = original;
        }
    } catch (e) {
        alert('Network error');
        selectEl.value = original;
    }
}
</script>
{% endblock %}
'''

# ============================================================
# templates/admin/agent_requests.html
# ============================================================
files[os.path.join(TMPL, 'agent_requests.html')] = r'''{% extends "admin/base.html" %}
{% block title %}Agent 승인{% endblock %}
{% block content %}
<h2 style="font-size:20px;font-weight:700;margin-bottom:16px;">Agent 가입 신청</h2>

{% if not requests %}
<div class="card">
    <p class="text-muted text-sm">Agent 가입 신청이 없습니다.</p>
</div>
{% else %}
{% for req in requests %}
<div class="card" id="req-{{ req.id }}" style="{% if req.status == 'pending' %}border-left: 3px solid #f57f17;{% endif %}">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:12px;">
        <div>
            <div style="font-size:16px;font-weight:700;">{{ req.agent_name or '(미입력)' }}</div>
            <div class="text-sm text-muted">{{ req.user_email or req.email or '-' }} | {{ req.user_name or req.name or '-' }}</div>
        </div>
        <span class="badge badge-{{ req.status }}">{{ req.status }}</span>
    </div>

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;font-size:13px;margin-bottom:12px;">
        <div><strong>slug:</strong> {{ req.agent_slug or '-' }}</div>
        <div><strong>대표자:</strong> {{ req.representative_name or req.name or '-' }}</div>
        <div><strong>연락처:</strong> {{ req.phone or '-' }}</div>
        <div><strong>주소:</strong> {{ req.office_address or '-' }}</div>
        <div><strong>등록번호:</strong> {{ req.license_no or '-' }}</div>
        <div><strong>신청일:</strong> {{ req.created_at.strftime('%Y-%m-%d %H:%M') if req.created_at else '-' }}</div>
    </div>

    {% if req.license_file_path %}
    <div style="margin-bottom:12px;">
        <a href="{{ req.license_file_path }}" target="_blank" class="btn btn-sm" style="font-size:12px;">등록증 보기</a>
    </div>
    {% endif %}

    {% if req.status == 'pending' %}
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
        <button class="btn-success" onclick="approveAgent({{ req.id }})">승인</button>
        <button class="btn-danger" onclick="rejectAgent({{ req.id }})">거절</button>
    </div>
    {% elif req.status == 'rejected' and req.reject_reason %}
    <div class="text-sm" style="color:#c62828;margin-top:4px;">거절 사유: {{ req.reject_reason }}</div>
    {% endif %}
</div>
{% endfor %}
{% endif %}

<script>
async function approveAgent(reqId) {
    if (!confirm('이 Agent 신청을 승인하시겠습니까?\n\n승인 시:\n- 역할이 agent로 변경됩니다\n- agents 테이블에 등록됩니다\n- PropSheet 워크스페이스가 생성됩니다')) return;

    try {
        const res = await fetch(`/admin/api/agent-requests/${reqId}/approve`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        const data = await res.json();
        if (data.ok) {
            alert(data.message || '승인되었습니다');
            location.reload();
        } else {
            alert(data.error || '실패');
        }
    } catch (e) {
        alert('Network error');
    }
}

async function rejectAgent(reqId) {
    const reason = prompt('거절 사유를 입력하세요:');
    if (reason === null) return;

    try {
        const res = await fetch(`/admin/api/agent-requests/${reqId}/reject`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({reason: reason})
        });
        const data = await res.json();
        if (data.ok) {
            alert('거절되었습니다');
            location.reload();
        } else {
            alert(data.error || '실패');
        }
    } catch (e) {
        alert('Network error');
    }
}
</script>
{% endblock %}
'''

# ============================================================
# templates/admin/consents.html
# ============================================================
files[os.path.join(TMPL, 'consents.html')] = r'''{% extends "admin/base.html" %}
{% block title %}동의 관리{% endblock %}
{% block content %}
<h2 style="font-size:20px;font-weight:700;margin-bottom:16px;">동의 관리</h2>

<div class="stats-grid" style="grid-template-columns: 1fr;">
    <div class="stat-card">
        <div class="value">{{ consent_stats.total_consented }}</div>
        <div class="label">동의 완료 유저 (공통 약관 1종 이상)</div>
    </div>
</div>

<div class="card">
    <h3>약관 유형별 동의 현황</h3>
    {% if consent_stats.by_type %}
    <div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th>약관 유형</th>
                <th>버전</th>
                <th class="text-right">전체</th>
                <th class="text-right">동의</th>
            </tr>
        </thead>
        <tbody>
            {% for row in consent_stats.by_type %}
            <tr>
                <td>{{ row.consent_type }}</td>
                <td>{{ row.version }}</td>
                <td class="text-right">{{ row.cnt }}</td>
                <td class="text-right">{{ row.agreed_cnt }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    </div>
    {% else %}
    <p class="text-muted text-sm">동의 이력이 없습니다.</p>
    {% endif %}
</div>

<div class="card">
    <h3>최근 동의 이력</h3>
    {% if recent_consents %}
    <div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th>이름</th>
                <th>이메일</th>
                <th>약관</th>
                <th>버전</th>
                <th>동의</th>
                <th>일시</th>
            </tr>
        </thead>
        <tbody>
            {% for c in recent_consents %}
            <tr>
                <td>{{ c.name or '-' }}</td>
                <td>{{ c.email }}</td>
                <td>{{ c.consent_type }}</td>
                <td>{{ c.version }}</td>
                <td>
                    {% if c.agreed %}
                        <span class="badge badge-approved">동의</span>
                    {% else %}
                        <span class="badge badge-rejected">거부</span>
                    {% endif %}
                </td>
                <td>{{ c.agreed_at.strftime('%m/%d %H:%M') if c.agreed_at else '-' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    </div>
    {% else %}
    <p class="text-muted text-sm">동의 이력이 없습니다.</p>
    {% endif %}
</div>
{% endblock %}
'''

# ============================================================
# templates/admin/billing.html
# ============================================================
files[os.path.join(TMPL, 'billing.html')] = r'''{% extends "admin/base.html" %}
{% block title %}Proptalk 과금{% endblock %}
{% block content %}
<h2 style="font-size:20px;font-weight:700;margin-bottom:16px;">Proptalk 과금 관리</h2>

<div class="stats-grid">
    <div class="stat-card">
        <div class="value">{{ stats.total_billing_users }}</div>
        <div class="label">과금 유저</div>
    </div>
    <div class="stat-card">
        <div class="value">{{ stats.active_subscriptions }}</div>
        <div class="label">활성 구독</div>
    </div>
    <div class="stat-card">
        <div class="value">{{ "{:,}".format(stats.total_revenue) }}</div>
        <div class="label">총 매출 (원)</div>
    </div>
</div>

<div class="card">
    <h3>유저별 과금 현황</h3>
    {% if users %}
    <div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>이름</th>
                <th>이메일</th>
                <th>요금제</th>
                <th class="text-right">잔여시간</th>
                <th>상태</th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            {% for u in users %}
            <tr>
                <td>{{ u.id }}</td>
                <td>{{ u.name or '-' }}</td>
                <td>{{ u.email }}</td>
                <td>{{ u.plan_name or '무료' }}</td>
                <td class="text-right">
                    {% if u.remaining_seconds is not none %}
                        {{ "%.1f"|format((u.remaining_seconds or 0) / 60) }}분
                    {% else %}
                        -
                    {% endif %}
                </td>
                <td>
                    {% if u.subscription_status == 'active' %}
                        <span class="badge badge-active">활성</span>
                    {% elif u.subscription_status == 'expired' %}
                        <span class="badge badge-expired">만료</span>
                    {% else %}
                        <span class="badge badge-free">{{ u.subscription_status or '무료' }}</span>
                    {% endif %}
                </td>
                <td>
                    <button class="btn-sm" onclick="toggleDetail({{ u.id }})" style="background:#1a1a2e;color:#fff;border:none;cursor:pointer;padding:4px 10px;border-radius:6px;font-size:12px;">관리</button>
                </td>
            </tr>
            <tr id="detail-{{ u.id }}" style="display:none;">
                <td colspan="7" style="background:#fafbfc;padding:16px;">
                    <div style="display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end;">
                        <div>
                            <label style="font-size:12px;color:#888;display:block;margin-bottom:4px;">시간 추가 (분)</label>
                            <div style="display:flex;gap:4px;">
                                <input type="number" id="addMin-{{ u.id }}" placeholder="분" min="1" style="width:80px;">
                                <button onclick="billingAction({{ u.id }}, 'add_seconds', {seconds: parseInt(document.getElementById('addMin-{{ u.id }}').value)*60})" style="font-size:12px;padding:6px 12px;">추가</button>
                            </div>
                        </div>
                        <div>
                            <label style="font-size:12px;color:#888;display:block;margin-bottom:4px;">잔여시간 설정 (초)</label>
                            <div style="display:flex;gap:4px;">
                                <input type="number" id="setSec-{{ u.id }}" value="{{ (u.remaining_seconds or 0)|int }}" min="0" style="width:100px;">
                                <button onclick="billingAction({{ u.id }}, 'set_seconds', {seconds: parseInt(document.getElementById('setSec-{{ u.id }}').value)})" style="font-size:12px;padding:6px 12px;">설정</button>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    </div>
    {% else %}
    <p class="text-muted text-sm">과금 유저가 없습니다.</p>
    {% endif %}
</div>

<script>
function toggleDetail(userId) {
    const el = document.getElementById('detail-' + userId);
    el.style.display = el.style.display === 'none' ? 'table-row' : 'none';
}

async function billingAction(userId, action, params) {
    try {
        const res = await fetch(`/admin/api/billing/users/${userId}/plan`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action, ...params})
        });
        const data = await res.json();
        if (data.ok) {
            alert('변경되었습니다');
            location.reload();
        } else {
            alert(data.error || '실패');
        }
    } catch (e) {
        alert('Network error');
    }
}
</script>
{% endblock %}
'''

# ============================================================
# templates/admin/ai_usage.html
# ============================================================
files[os.path.join(TMPL, 'ai_usage.html')] = r'''{% extends "admin/base.html" %}
{% block title %}AI 사용량{% endblock %}
{% block content %}
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px;">
    <h2 style="font-size:20px;font-weight:700;">OpenAI API 사용량</h2>
    <div style="display:flex;gap:6px;">
        <button class="period-btn" data-days="7" onclick="loadData(7)">7일</button>
        <button class="period-btn active" data-days="30" onclick="loadData(30)">30일</button>
        <button class="period-btn" data-days="90" onclick="loadData(90)">90일</button>
    </div>
</div>

<div class="card" style="margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
        <div>
            <div style="font-size:12px;color:#999;">충전액</div>
            <div style="font-size:22px;font-weight:700;" id="credit-total">-</div>
        </div>
        <div style="font-size:20px;color:#ccc;">-</div>
        <div>
            <div style="font-size:12px;color:#999;">누적 사용</div>
            <div style="font-size:22px;font-weight:700;color:#e74c3c;" id="credit-used">-</div>
        </div>
        <div style="font-size:20px;color:#ccc;">=</div>
        <div>
            <div style="font-size:12px;color:#999;">잔액</div>
            <div style="font-size:22px;font-weight:700;color:#27ae60;" id="credit-balance">-</div>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:6px;">
        <input type="number" id="creditInput" step="0.01" min="0" style="width:90px;" placeholder="충전액">
        <button onclick="setCredit()">설정</button>
    </div>
</div>

<div class="stats-grid">
    <div class="stat-card">
        <div class="value" id="total-cost">-</div>
        <div class="label">기간 비용 (USD)</div>
    </div>
    <div class="stat-card">
        <div class="value" id="whisper-seconds">-</div>
        <div class="label">Whisper 사용량 (초)</div>
    </div>
    <div class="stat-card">
        <div class="value" id="avg-daily">-</div>
        <div class="label">일평균 비용 (USD)</div>
    </div>
</div>

<div class="card">
    <h3>일별 비용 추이</h3>
    <div style="position:relative;height:280px;">
        <canvas id="costChart"></canvas>
    </div>
</div>

<div class="card">
    <h3>Whisper 음성인식 (초/일)</h3>
    <div style="position:relative;height:240px;">
        <canvas id="whisperChart"></canvas>
    </div>
</div>

<div class="card">
    <h3>일별 상세</h3>
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>날짜</th>
                    <th class="text-right">비용 (USD)</th>
                    <th class="text-right">Whisper (초)</th>
                    <th class="text-right">요청 수</th>
                </tr>
            </thead>
            <tbody id="daily-table"></tbody>
        </table>
    </div>
</div>

<style>
.period-btn {
    padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 600;
    background: #e8eaed; color: #555; border: none; cursor: pointer;
}
.period-btn.active { background: #1a1a2e; color: #fff; }
</style>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<script>
let costChart = null, whisperChart = null;

async function loadData(days) {
    document.querySelectorAll('.period-btn').forEach(b => b.classList.toggle('active', +b.dataset.days === days));

    try {
        const [costsRes, usageRes] = await Promise.all([
            fetch(`/admin/api/openai-costs?days=${days}`),
            fetch(`/admin/api/openai-usage-detail?days=${days}`)
        ]);
        const costs = await costsRes.json();
        const usage = await usageRes.json();

        if (costs.error) { alert(costs.error + '\n' + (costs.detail || '')); return; }

        renderCosts(costs.data || []);
        renderWhisper(usage.audio_transcriptions || []);
    } catch (e) {
        alert('데이터 로드 실패: ' + e.message);
    }
}

function renderCosts(data) {
    const daily = {};
    data.forEach(bucket => {
        const d = new Date(bucket.start_time * 1000).toISOString().slice(0, 10);
        const amt = (bucket.results || []).reduce((s, r) => s + parseFloat(r.amount?.value || 0), 0);
        daily[d] = (daily[d] || 0) + amt;
    });

    const labels = Object.keys(daily).sort();
    const values = labels.map(d => daily[d]);
    const total = values.reduce((a, b) => a + b, 0);

    document.getElementById('total-cost').textContent = '$' + total.toFixed(2);
    document.getElementById('avg-daily').textContent = labels.length ? '$' + (total / labels.length).toFixed(2) : '-';

    // 크레딧 사용량 업데이트
    const usedEl = document.getElementById('credit-used');
    usedEl.textContent = '$' + total.toFixed(2);
    window._totalUsed = total;
    updateBalance();

    if (costChart) costChart.destroy();
    costChart = new Chart(document.getElementById('costChart'), {
        type: 'bar',
        data: {
            labels: labels.map(d => d.slice(5)),
            datasets: [{ label: '비용 (USD)', data: values, backgroundColor: 'rgba(26,26,46,0.7)', borderRadius: 4 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + v.toFixed(2) } }, x: { ticks: { maxRotation: 45, font: { size: 11 } } } }
        }
    });

    window._costDaily = daily;
    mergeTable();
}

function renderWhisper(data) {
    const daily = {};
    data.forEach(bucket => {
        const d = new Date(bucket.start_time * 1000).toISOString().slice(0, 10);
        const secs = (bucket.results || []).reduce((s, r) => s + (r.seconds || 0), 0);
        const requests = (bucket.results || []).reduce((s, r) => s + (r.num_model_requests || 0), 0);
        daily[d] = { seconds: (daily[d]?.seconds || 0) + secs, requests: (daily[d]?.requests || 0) + requests };
    });

    const labels = Object.keys(daily).sort();
    const secValues = labels.map(d => daily[d].seconds);
    const totalSec = secValues.reduce((a, b) => a + b, 0);
    const totalReq = labels.reduce((s, d) => s + daily[d].requests, 0);

    document.getElementById('whisper-seconds').textContent = totalSec > 0 ? totalSec.toLocaleString() + '초' : totalReq + '건';

    if (whisperChart) whisperChart.destroy();
    whisperChart = new Chart(document.getElementById('whisperChart'), {
        type: 'bar',
        data: {
            labels: labels.map(d => d.slice(5)),
            datasets: [{ label: 'Whisper (초)', data: secValues.some(v => v > 0) ? secValues : labels.map(d => daily[d].requests), backgroundColor: 'rgba(52,152,219,0.7)', borderRadius: 4 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true }, x: { ticks: { maxRotation: 45, font: { size: 11 } } } }
        }
    });

    window._whisperDaily = daily;
    mergeTable();
}

function mergeTable() {
    const costDaily = window._costDaily || {};
    const whisperDaily = window._whisperDaily || {};
    const allDates = [...new Set([...Object.keys(costDaily), ...Object.keys(whisperDaily)])].sort().reverse();
    const tbody = document.getElementById('daily-table');
    tbody.innerHTML = allDates.map(d => {
        const cost = costDaily[d] || 0;
        const w = whisperDaily[d] || { seconds: 0, requests: 0 };
        return `<tr><td>${d}</td><td class="text-right">$${cost.toFixed(4)}</td><td class="text-right">${w.seconds > 0 ? w.seconds.toLocaleString() : '-'}</td><td class="text-right">${w.requests > 0 ? w.requests + '건' : '-'}</td></tr>`;
    }).join('');
}

function updateBalance() {
    const total = window._totalCredit || 0;
    const used = window._totalUsed || 0;
    const balance = total - used;
    const el = document.getElementById('credit-balance');
    el.textContent = '$' + balance.toFixed(2);
    el.style.color = balance < 2 ? '#e74c3c' : '#27ae60';
}

async function loadCredit() {
    try {
        const res = await fetch('/admin/api/openai-credit');
        const data = await res.json();
        window._totalCredit = data.total_credit;
        document.getElementById('credit-total').textContent = '$' + data.total_credit.toFixed(2);
        document.getElementById('creditInput').value = data.total_credit;
        updateBalance();
    } catch (e) {
        console.error('크레딧 로드 실패:', e);
    }
}

async function setCredit() {
    const val = parseFloat(document.getElementById('creditInput').value);
    if (isNaN(val) || val < 0) return alert('올바른 금액을 입력하세요');
    const res = await fetch('/admin/api/openai-credit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({total_credit: val})
    });
    const data = await res.json();
    if (data.ok) {
        window._totalCredit = val;
        document.getElementById('credit-total').textContent = '$' + val.toFixed(2);
        updateBalance();
    }
}

loadCredit();
loadData(30);
</script>
{% endblock %}
'''

# ============================================================
# Write all files
# ============================================================
for path, content in files.items():
    # Backup existing file
    if os.path.exists(path):
        backup = path + '.bak'
        try:
            with open(backup, 'w', encoding='utf-8') as f:
                with open(path, 'r', encoding='utf-8') as orig:
                    f.write(orig.read())
            print(f'  Backed up: {path} -> {backup}')
        except Exception as e:
            print(f'  Backup failed: {e}')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  Created: {path}')

print(f'\nDone: {len(files)} files created/updated')
print('\nNext steps:')
print('1. Create admin_settings table if not exists:')
print('   CREATE TABLE IF NOT EXISTS admin_settings (key VARCHAR(100) PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT NOW());')
print('2. Update proppedia app.py to register admin_dashboard blueprint')
print('3. Update Nginx to route /admin/* to port 5010')
print('4. Restart: sudo systemctl restart proppedia')
