"""
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
            session.pop('admin_token', None)
            return redirect(url_for('admin_dashboard.admin_login_page'))

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
    plan_filter = request.args.get('plan', '').strip()
    status_filter = request.args.get('status', '').strip()
    agency_search = request.args.get('agency', '').strip()
    users = svc.get_all_users(
        search=search, role_filter=role_filter,
        plan_filter=plan_filter, status_filter=status_filter,
        agency_search=agency_search
    )
    return render_template('admin/users.html',
                           users=users, search=search, role_filter=role_filter,
                           plan_filter=plan_filter, status_filter=status_filter,
                           agency_search=agency_search, active='users')


@bp.route('/api/users/<int:user_id>/role', methods=['POST'])
@admin_required
def api_change_role(user_id):
    """유저 역할 변경 API"""
    from services.admin_dashboard_service import AdminDashboardService as svc
    data = request.get_json()
    new_role = data.get('role', '').strip()

    if new_role not in ('user', 'agent', 'subagent', 'admin'):
        return jsonify({'error': 'Invalid role'}), 400

    force_detach = data.get('force_detach', False)
    result = svc.update_user_role(user_id, new_role, g.admin_user['email'], force_detach=force_detach)
    if result.get('error'):
        status_code = 409 if result.get('confirm_required') else 400
        return jsonify(result), status_code

    # 감사 로그
    try:
        from propnet_auth.db import get_voiceroom_db
        import json as _json
        with get_voiceroom_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO access_logs (action, resource_type, resource_id, ip_address, details)
                       VALUES ('admin_change_role', 'user', %s, %s, %s)""",
                    (user_id, request.remote_addr, _json.dumps({'new_role': new_role, 'admin': g.admin_user['email']}))
                )
    except Exception:
        pass

    return jsonify({'ok': True})


# ── Agent 승인 ──────────────────────────────
@bp.route('/agent-requests')
@admin_required
def admin_agent_requests():
    from services.admin_dashboard_service import AdminDashboardService as svc
    requests_list = svc.get_agent_requests()
    agents_list = svc.get_registered_agents()
    return render_template('admin/agent_requests.html',
                           requests=requests_list, agents=agents_list, active='agent_requests')


@bp.route('/api/agent-requests/<int:req_id>/approve', methods=['POST'])
@admin_required
def api_approve_agent(req_id):
    """Agent 가입 신청 승인"""
    from services.admin_dashboard_service import AdminDashboardService as svc
    result = svc.approve_agent_request(req_id, g.admin_user['email'])
    if result.get('error'):
        return jsonify(result), 400
    return jsonify({'ok': True, 'message': result.get('message', 'Approved')})


@bp.route('/api/agent-requests/<int:req_id>/force-complete', methods=['POST'])
@admin_required
def api_force_complete_agent(req_id):
    """Agent 가입 강제 완료 (오프라인 결제 등)"""
    from services.admin_dashboard_service import AdminDashboardService as svc
    from propnet_auth.db import query_one, execute

    req = query_one("SELECT * FROM agent_requests WHERE id = %s", (req_id,))
    if not req:
        return jsonify({'error': 'Request not found'}), 400

    if req['status'] != 'approved_pending_payment':
        return jsonify({'error': f'Status must be approved_pending_payment, got {req["status"]}'}), 400

    # 결제 상태 강제 완료
    execute("""
        UPDATE agent_requests
        SET payment_status = 'completed', payment_completed_at = NOW(), status = 'approved'
        WHERE id = %s
    """, (req_id,))

    # voiceroom user_billing 생성 (강제 완료 시 과금 레코드 필요)
    try:
        from propnet_auth.db import voiceroom_query_one, voiceroom_execute, get_voiceroom_db
        from propnet_auth.user_service import ensure_service_account
        import psycopg2.extras

        propnet_user_id = req['propnet_user_id']
        plan_code = req.get('selected_plan_code', 'agent_regular')

        # voiceroom에서 플랜 조회
        plan = voiceroom_query_one(
            "SELECT * FROM billing_plans WHERE code = %s", (plan_code,)
        )

        # proptalk 계정 확보
        link = ensure_service_account(propnet_user_id, 'proptalk')
        if link and plan:
            vr_user_id = link['local_user_id']
            voiceroom_execute("""
                INSERT INTO user_billing (user_id, propnet_user_id, current_plan_id,
                    remaining_seconds, subscription_status,
                    subscription_started_at, subscription_expires_at)
                VALUES (%s, %s, %s, %s, 'active', NOW(), NOW() + INTERVAL '30 days')
                ON CONFLICT (user_id) DO UPDATE SET
                    propnet_user_id = %s,
                    current_plan_id = %s,
                    remaining_seconds = %s,
                    subscription_status = 'active',
                    subscription_started_at = NOW(),
                    subscription_expires_at = NOW() + INTERVAL '30 days',
                    updated_at = NOW()
            """, (vr_user_id, propnet_user_id, plan['id'],
                  plan['minutes_included'] * 60,
                  propnet_user_id, plan['id'],
                  plan['minutes_included'] * 60))
            logger.info(f"[ForceComplete] user_billing created: vr_user={vr_user_id} plan={plan_code}")
    except Exception as e:
        logger.error(f"[ForceComplete] user_billing creation failed: {e}")

    # 환경 셋업 실행
    result = svc.approve_agent_request(req_id, g.admin_user['email'])
    if result.get('error'):
        return jsonify(result), 400
    return jsonify({'ok': True, 'message': 'Force completed: ' + result.get('message', '')})


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
    recent_tx = svc.get_recent_transactions(30)
    return render_template('admin/billing.html',
                           stats=billing_stats, transactions=recent_tx,
                           active='billing')


@bp.route('/api/billing/users/<int:user_id>/plan', methods=['POST'])
@admin_required
def api_change_billing(user_id):
    """Proptalk 유저 과금 변경
    user_id는 propnet_user_id로 간주. voiceroom user_id로 변환 후 실행.
    """
    from services.admin_dashboard_service import AdminDashboardService as svc
    from propnet_auth.db import query_one
    data = request.get_json()
    action = data.get('action')

    # propnet_user_id → voiceroom user_id 변환
    link = query_one(
        "SELECT local_user_id FROM service_user_links WHERE propnet_user_id = %s AND service = 'proptalk'",
        (user_id,)
    )
    if not link:
        # proptalk 계정이 없으면 자동 생성
        from propnet_auth.user_service import ensure_service_account
        link = ensure_service_account(user_id, 'proptalk')
        if not link:
            return jsonify({'error': 'Proptalk 계정을 생성할 수 없습니다'}), 400

    vr_user_id = link['local_user_id']
    result = svc.update_billing(vr_user_id, action, data, g.admin_user['email'], propnet_user_id=user_id)
    if result.get('error'):
        return jsonify(result), 400

    # 감사 로그 기록 (voiceroom.access_logs)
    try:
        from propnet_auth.db import get_voiceroom_db
        import psycopg2.extras, json as _json
        with get_voiceroom_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO access_logs (user_id, action, resource_type, resource_id, ip_address, details)
                       VALUES (%s, %s, 'billing', %s, %s, %s)""",
                    (vr_user_id, f'admin_{action}', user_id, request.remote_addr,
                     _json.dumps({k: v for k, v in data.items() if k != 'action'}, default=str))
                )
    except Exception:
        pass

    return jsonify({'ok': True})


# ── Billing 모니터링 ────────────────────────────
@bp.route('/api/billing-health')
@admin_required
def api_billing_health():
    """과금 시스템 건강 상태"""
    from services.admin_dashboard_service import AdminDashboardService as svc
    health = svc.get_billing_health()
    return jsonify(health)


@bp.route('/api/billing-daily-summary', methods=['POST'])
@admin_required
def api_billing_daily_summary():
    """일간 요약 수동 생성 (target_date 지정 가능)"""
    from services.admin_dashboard_service import AdminDashboardService as svc
    data = request.get_json() or {}
    target_date = data.get('date')  # YYYY-MM-DD or None for today
    result = svc.generate_daily_summary(target_date)
    return jsonify(result)


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


# ── 서버 모니터링 ──────────────────────────────
@bp.route('/server')
@admin_required
def admin_server():
    return render_template('admin/server.html', active='server')


@bp.route('/api/server-stats')
@admin_required
def api_server_stats():
    """실시간 서버 상태"""
    from services.server_monitor_service import ServerMonitorService as svc
    stats = svc.get_realtime_stats()
    stats['services'] = svc.get_service_status()
    stats['top_processes'] = svc.get_process_top(8)
    return jsonify(stats)


@bp.route('/api/server-stats/history')
@admin_required
def api_server_history():
    """서버 상태 히스토리"""
    from services.server_monitor_service import ServerMonitorService as svc
    minutes = int(request.args.get('minutes', 60))
    return jsonify({'data': svc.get_history(minutes)})


@bp.route('/api/server-stats/traffic')
@admin_required
def api_server_traffic():
    """오늘 트래픽 요약"""
    from services.server_monitor_service import ServerMonitorService as svc
    return jsonify(svc.get_traffic_summary())


# ── 공지사항 관리 ──────────────────────────────
@bp.route('/notices')
@admin_required
def admin_notices():
    return render_template('admin/notices.html', active='notices')


@bp.route('/api/notices')
@admin_required
def api_notices_list():
    """공지 목록 JSON API (페이징)"""
    from services.app_notice_service import AppNoticeService
    svc = AppNoticeService()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    result = svc.get_all_notices(page=page, per_page=per_page)
    return jsonify(result)


@bp.route('/api/notices', methods=['POST'])
@admin_required
def api_notices_create():
    """공지 생성"""
    from services.app_notice_service import AppNoticeService
    svc = AppNoticeService()
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': '제목과 내용은 필수입니다'}), 400

    result = svc.create_notice(
        title=data['title'].strip(),
        content=data['content'].strip(),
        notice_type=data.get('notice_type', 'info'),
        start_at=data.get('start_at') or None,
        end_at=data.get('end_at') or None,
        is_dismissible=data.get('is_dismissible', True),
        target_app=data.get('target_app', 'all')
    )
    if result.get('success'):
        logger.info(f"[Admin] Notice created id={result['id']} by {g.admin_user['email']}")
        return jsonify({'ok': True, 'id': result['id']})
    return jsonify({'error': result.get('error', 'Failed')}), 500


@bp.route('/api/notices/<int:notice_id>', methods=['PATCH'])
@admin_required
def api_notices_update(notice_id):
    """공지 수정"""
    from services.app_notice_service import AppNoticeService
    svc = AppNoticeService()
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': '제목과 내용은 필수입니다'}), 400

    result = svc.update_notice(
        notice_id=notice_id,
        title=data['title'].strip(),
        content=data['content'].strip(),
        notice_type=data.get('notice_type', 'info'),
        start_at=data.get('start_at') or None,
        end_at=data.get('end_at') or None,
        is_dismissible=data.get('is_dismissible', True),
        target_app=data.get('target_app', 'all')
    )
    if result.get('success'):
        logger.info(f"[Admin] Notice updated id={notice_id} by {g.admin_user['email']}")
        return jsonify({'ok': True})
    return jsonify({'error': result.get('error', 'Failed')}), 500


@bp.route('/api/notices/<int:notice_id>/publish', methods=['POST'])
@admin_required
def api_notices_publish(notice_id):
    """공지 게시 (is_active=TRUE)"""
    from services.app_notice_service import AppNoticeService
    svc = AppNoticeService()
    result = svc.publish_notice(notice_id)
    if result.get('success'):
        logger.info(f"[Admin] Notice published id={notice_id} by {g.admin_user['email']}")
        return jsonify({'ok': True})
    return jsonify({'error': result.get('error', 'Failed')}), 500


@bp.route('/api/notices/<int:notice_id>/stop', methods=['POST'])
@admin_required
def api_notices_stop(notice_id):
    """공지 중지 (is_active=FALSE)"""
    from services.app_notice_service import AppNoticeService
    svc = AppNoticeService()
    result = svc.stop_notice(notice_id)
    if result.get('success'):
        logger.info(f"[Admin] Notice stopped id={notice_id} by {g.admin_user['email']}")
        return jsonify({'ok': True})
    return jsonify({'error': result.get('error', 'Failed')}), 500


@bp.route('/api/notices/<int:notice_id>', methods=['DELETE'])
@admin_required
def api_notices_delete(notice_id):
    """공지 삭제"""
    from services.app_notice_service import AppNoticeService
    svc = AppNoticeService()
    result = svc.delete_notice(notice_id)
    if result.get('success'):
        logger.info(f"[Admin] Notice deleted id={notice_id} by {g.admin_user['email']}")
        return jsonify({'ok': True})
    return jsonify({'error': result.get('error', 'Failed')}), 500


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


# ── 계약 관리 ──────────────────────────────
@bp.route('/contract')
@admin_required
def contract_page():
    """계약 관리 페이지"""
    return render_template('admin/contract.html', active='contract')


@bp.route('/api/contract/access-logs')
@admin_required
def api_contract_access_logs():
    """관리자 접근 로그 조회"""
    from services.admin_access_log_service import get_access_logs
    agent_slug = request.args.get('agent_slug', '').strip() or None
    logs = get_access_logs(agent_slug=agent_slug, limit=200)
    for log in logs:
        if log.get('accessed_at'):
            log['accessed_at'] = log['accessed_at'].isoformat()
    return jsonify(logs)


@bp.route('/api/contract/disposal-logs')
@admin_required
def api_contract_disposal_logs():
    """데이터 폐기 이력 조회"""
    from services.contract_service import get_disposal_log
    logs = get_disposal_log()
    for log in logs:
        if log.get('disposed_at'):
            log['disposed_at'] = log['disposed_at'].isoformat()
    return jsonify(logs)


@bp.route('/api/contract/agreements')
@admin_required
def api_contract_agreements():
    """등록된 약관 목록"""
    from services.database_service import get_db_connection, get_db_cursor
    from psycopg2.extras import RealDictCursor
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute('''
                SELECT id, type, version, title, effective_date, created_at
                FROM agreements ORDER BY effective_date DESC, type
            ''')
            agreements = [dict(row) for row in cursor.fetchall()]
    for a in agreements:
        if a.get('effective_date'):
            a['effective_date'] = str(a['effective_date'])
        if a.get('created_at'):
            a['created_at'] = a['created_at'].isoformat()
    return jsonify(agreements)


@bp.route('/api/contract/dispose-agent', methods=['POST'])
@admin_required
def api_contract_dispose_agent():
    """Agent 데이터 일괄 삭제 (계약 종료)"""
    from services.contract_service import dispose_agent_data
    data = request.get_json()
    agent_slug = data.get('agent_slug', '').strip()
    if not agent_slug:
        return jsonify({'error': 'agent_slug is required'}), 400

    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    admin_email = g.admin_user.get('email', 'admin')

    result = dispose_agent_data(
        agent_slug=agent_slug,
        disposed_by=admin_email,
        ip_address=ip,
    )
    return jsonify(result)


# ── AI 크레딧 관리 ──────────────────────────────

@bp.route('/api/users/<int:propnet_uid>/ai-credit')
@admin_required
def api_ai_credit_get(propnet_uid):
    """유저 AI 크레딧 상태 + 최근 이력 조회"""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor
    import json as _json

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM ai_credit_wallet WHERE propnet_uid = %s", (propnet_uid,))
            wallet = cur.fetchone()

            cur.execute(
                """SELECT id, delta, source_type, source_ref, balance_snapshot, note,
                          created_at AT TIME ZONE 'Asia/Seoul' AS created_at_kst
                   FROM ai_credit_ledger
                   WHERE propnet_uid = %s
                   ORDER BY created_at DESC LIMIT 20""",
                (propnet_uid,),
            )
            ledger = cur.fetchall()

    if not wallet:
        return jsonify({'wallet': None, 'ledger': []})

    for row in ledger:
        row['created_at_kst'] = str(row['created_at_kst']) if row['created_at_kst'] else None

    return jsonify({
        'wallet': {
            'propnet_uid': wallet['propnet_uid'],
            'balance_free': wallet['balance_free'],
            'balance_bundle': wallet['balance_bundle'],
            'balance_pack': wallet['balance_pack'],
            'signup_bonus_given': wallet['signup_bonus_given'],
            'bundle_reset_at': str(wallet['bundle_reset_at']) if wallet['bundle_reset_at'] else None,
            'total': wallet['balance_free'] + wallet['balance_bundle'] + wallet['balance_pack'],
        },
        'ledger': ledger,
    })


@bp.route('/api/users/<int:propnet_uid>/ai-credit', methods=['POST'])
@admin_required
def api_ai_credit_adjust(propnet_uid):
    """관리자 수동 AI 크레딧 조정"""
    from services.database_service import get_db_connection
    from services import ai_billing_service as ai_billing
    from psycopg2.extras import RealDictCursor

    data = request.get_json()
    delta = int(data.get('delta', 0))
    bucket = data.get('bucket', 'free')
    note = data.get('note', '')

    if delta == 0:
        return jsonify({'error': 'delta는 0이 아니어야 합니다'}), 400
    if bucket not in ('free', 'bundle', 'pack'):
        return jsonify({'error': 'bucket은 free/bundle/pack 중 하나'}), 400

    admin_email = g.admin_user.get('email', 'admin')

    with get_db_connection() as conn:
        conn.cursor_factory = RealDictCursor
        with conn.cursor() as cur:
            result = ai_billing.admin_adjust(cur, propnet_uid, delta, bucket, note, admin_email)
        conn.commit()

    try:
        import json as _json
        from propnet_auth.db import get_voiceroom_db
        with get_voiceroom_db() as vconn:
            with vconn.cursor() as vcur:
                vcur.execute(
                    """INSERT INTO access_logs (action, resource_type, resource_id, ip_address, details)
                       VALUES ('admin_ai_credit_adjust', 'user', %s, %s, %s)""",
                    (propnet_uid, request.remote_addr,
                     _json.dumps({'delta': delta, 'bucket': bucket, 'note': note, 'admin': admin_email}))
                )
    except Exception:
        pass

    return jsonify({'ok': True, 'wallet': result})
