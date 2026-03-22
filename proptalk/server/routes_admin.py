"""
관리자 대시보드 라우트
- ADMIN_EMAIL 환경변수와 일치하는 사용자만 접근 가능
"""
import json
import logging
import os
import time
import requests as http_requests
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify, g, render_template, redirect, session
from auth import login_required, decode_token
from config import Config
from models import User, query_one
from models_billing import (
    UserBilling, PaymentTransaction, UsageLog, AdminQueries, BillingPlan
)

logger = logging.getLogger(__name__)


def admin_required(f):
    """관리자 전용 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # JWT from header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        # JWT from session (web pages)
        if not token:
            token = session.get('admin_token')

        if not token:
            return redirect('/proptalk/admin/login')

        payload = decode_token(token)
        if not payload:
            session.pop('admin_token', None)
            return redirect('/proptalk/admin/login')

        user = User.find_by_id(payload['user_id'])
        if not user or user['email'] != Config.ADMIN_EMAIL:
            return jsonify({'error': 'Forbidden'}), 403

        g.user = user
        g.user_id = user['id']
        return f(*args, **kwargs)
    return decorated


def register_admin_routes(app):

    @app.route('/proptalk/admin/login', methods=['GET'])
    def admin_login_page():
        if not Config.ADMIN_EMAIL:
            return 'Admin not configured', 404
        # 토큰이 query param으로 전달되면 자동 로그인
        token = request.args.get('token')
        if token:
            payload = decode_token(token)
            if payload:
                user = User.find_by_id(payload['user_id'])
                if user and user['email'] == Config.ADMIN_EMAIL:
                    session['admin_token'] = token
                    return redirect('/proptalk/admin/')
        return render_template('admin/login.html', google_client_id=Config.GOOGLE_CLIENT_ID)

    @app.route('/proptalk/admin/login', methods=['POST'])
    def admin_login_post():
        if not Config.ADMIN_EMAIL:
            return jsonify({'error': 'Admin not configured'}), 404

        data = request.get_json() or request.form
        google_token = data.get('id_token', '').strip()

        if not google_token:
            return jsonify({'error': 'Google sign-in required'}), 400

        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
            idinfo = google_id_token.verify_oauth2_token(
                google_token, google_requests.Request(), Config.GOOGLE_CLIENT_ID
            )
            email = idinfo.get('email', '')
        except Exception:
            return jsonify({'error': 'Invalid Google token'}), 401

        if email != Config.ADMIN_EMAIL:
            return jsonify({'error': '관리자 계정이 아닙니다'}), 403

        user = query_one("SELECT * FROM users WHERE email = %s", (email,))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        from auth import create_token
        token = create_token(user['id'])
        session['admin_token'] = token
        return jsonify({'ok': True, 'redirect': '/proptalk/admin/'})

    @app.route('/proptalk/admin/logout')
    def admin_logout():
        session.pop('admin_token', None)
        return redirect('/proptalk/admin/login')

    @app.route('/proptalk/admin/')
    @admin_required
    def admin_dashboard():
        stats = AdminQueries.get_stats()
        recent = AdminQueries.recent_transactions(10)

        return render_template('admin/dashboard.html',
                               stats=stats, recent=recent)

    @app.route('/proptalk/admin/users')
    @admin_required
    def admin_users():
        users = AdminQueries.list_users_with_billing()
        return render_template('admin/users.html', users=users)

    @app.route('/proptalk/admin/users/<int:user_id>')
    @admin_required
    def admin_user_detail(user_id):
        user = User.find_by_id(user_id)
        if not user:
            return 'User not found', 404
        billing = UserBilling.find_by_user_id(user_id)
        transactions = PaymentTransaction.list_for_user(user_id)
        usage = UsageLog.list_for_user(user_id)
        plans = BillingPlan.list_active()
        return render_template('admin/user_detail.html',
                               user=user, billing=billing,
                               transactions=transactions, usage=usage,
                               plans=plans)

    @app.route('/proptalk/admin/api/users/<int:user_id>/plan', methods=['POST'])
    @admin_required
    def admin_change_plan(user_id):
        """사용자 요금제/잔여시간 변경"""
        data = request.get_json()
        action = data.get('action')

        if action == 'add_seconds':
            seconds = int(data.get('seconds', 0))
            if seconds > 0:
                UserBilling.ensure(user_id)
                UserBilling.add_seconds(user_id, seconds)
                logger.info(f"[Admin] user={user_id} +{seconds}s by {g.user['email']}")

        elif action == 'set_plan':
            plan_code = data.get('plan_code')
            plan = BillingPlan.find_by_code(plan_code)
            if plan:
                UserBilling.ensure(user_id)
                from models import execute
                execute(
                    "UPDATE user_billing SET current_plan_id = %s WHERE user_id = %s",
                    (plan['id'], user_id)
                )
                logger.info(f"[Admin] user={user_id} plan={plan_code} by {g.user['email']}")

        elif action == 'set_seconds':
            seconds = int(data.get('seconds', 0))
            UserBilling.ensure(user_id)
            from models import execute
            execute(
                "UPDATE user_billing SET remaining_seconds = %s WHERE user_id = %s",
                (seconds, user_id)
            )
            logger.info(f"[Admin] user={user_id} set_seconds={seconds} by {g.user['email']}")

        return jsonify({'ok': True})

    # ── 버전 이력 ──────────────────────────────

    @app.route('/proptalk/admin/versions')
    @admin_required
    def admin_versions():
        return render_template('admin/versions.html', active='versions')

    # ── OpenAI Usage Dashboard ──────────────────────────────

    @app.route('/proptalk/admin/openai-usage')
    @admin_required
    def admin_openai_usage():
        return render_template('admin/openai_usage.html')

    @app.route('/proptalk/admin/api/openai-costs')
    @admin_required
    def admin_openai_costs():
        """OpenAI Costs API 프록시"""
        admin_key = Config.OPENAI_ADMIN_KEY
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

        # Costs API - 일별 비용
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
            logger.error(f"[OpenAI Costs] 요청 실패: {e}")
            return jsonify({'error': 'OpenAI API 연결 실패', 'detail': str(e)}), 504

        return jsonify({'data': all_data})

    @app.route('/proptalk/admin/api/openai-usage-detail')
    @admin_required
    def admin_openai_usage_detail():
        """OpenAI Usage API 프록시 - 모델별 세부 사용량"""
        admin_key = Config.OPENAI_ADMIN_KEY
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

        # Audio(Whisper) 사용량
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
            resp = http_requests.get(
                'https://api.openai.com/v1/organization/usage/audio_speeches',
                headers=headers, params=params, timeout=15
            )
            # audio_speeches가 없으면 빈 배열
            if resp.status_code == 200:
                body = resp.json()
                all_data.extend(body.get('data', []))
                page_cursor = body.get('next_page')
                if not page_cursor:
                    break
            else:
                break

        # Audio transcriptions (Whisper)
        whisper_data = []
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
            resp = http_requests.get(
                'https://api.openai.com/v1/organization/usage/audio_transcriptions',
                headers=headers, params=params, timeout=15
            )
            if resp.status_code == 200:
                body = resp.json()
                whisper_data.extend(body.get('data', []))
                page_cursor = body.get('next_page')
                if not page_cursor:
                    break
            else:
                logger.warning(f"[OpenAI Usage] audio_transcriptions: {resp.status_code}")
                break

        return jsonify({
            'audio_speeches': all_data,
            'audio_transcriptions': whisper_data,
        })

    # ── OpenAI 크레딧 잔액 관리 ──────────────────────────────

    CREDIT_FILE = os.path.join(os.path.dirname(__file__), '.openai_credit.json')

    @app.route('/proptalk/admin/api/openai-credit')
    @admin_required
    def admin_openai_credit():
        """충전액 조회 + 전체 누적 사용량으로 잔액 계산"""
        # 충전액 읽기
        credit_data = {'total_credit': 10.0}
        if os.path.exists(CREDIT_FILE):
            with open(CREDIT_FILE, 'r') as f:
                credit_data = json.load(f)

        # 전체 누적 비용 조회 (계정 생성 시점부터)
        admin_key = Config.OPENAI_ADMIN_KEY
        if not admin_key:
            return jsonify({
                'total_credit': credit_data['total_credit'],
                'total_used': 0,
                'balance': credit_data['total_credit'],
            })

        headers = {
            'Authorization': f'Bearer {admin_key}',
            'Content-Type': 'application/json',
        }

        # 최근 90일 비용 조회 (전체 이력 조회 시 OpenAI API 타임아웃 발생)
        start_ts = int((datetime.now(timezone.utc) - timedelta(days=90)).timestamp())
        total_used = 0.0
        page_cursor = None
        try:
            while True:
                params = {
                    'start_time': start_ts,
                    'bucket_width': '1d',
                    'limit': 180,
                }
                if page_cursor:
                    params['page'] = page_cursor
                resp = http_requests.get(
                    'https://api.openai.com/v1/organization/costs',
                    headers=headers, params=params, timeout=30
                )
                if resp.status_code != 200:
                    break
                body = resp.json()
                for bucket in body.get('data', []):
                    for r in bucket.get('results', []):
                        total_used += float(r.get('amount', {}).get('value', 0))
                page_cursor = body.get('next_page')
                if not page_cursor:
                    break
        except Exception as e:
            logger.error(f"[OpenAI Credit] 비용 조회 실패: {e}")

        total_credit = credit_data['total_credit']
        return jsonify({
            'total_credit': total_credit,
            'total_used': round(total_used, 4),
            'balance': round(total_credit - total_used, 4),
        })

    @app.route('/proptalk/admin/api/openai-credit', methods=['POST'])
    @admin_required
    def admin_set_openai_credit():
        """충전액 설정"""
        data = request.get_json()
        total_credit = float(data.get('total_credit', 0))
        with open(CREDIT_FILE, 'w') as f:
            json.dump({'total_credit': total_credit}, f)
        logger.info(f"[Admin] OpenAI credit set to ${total_credit} by {g.user['email']}")
        return jsonify({'ok': True, 'total_credit': total_credit})
