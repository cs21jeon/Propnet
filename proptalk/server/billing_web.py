"""
웹 결제 페이지 라우트 (HTML 렌더링)
웹 브라우저에서 Google 로그인 후 결제 진행
+ 랜딩페이지 서빙
"""
import os
import logging
from flask import render_template, request, redirect, jsonify, send_from_directory
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config import Config
from auth import create_token
from models import User

logger = logging.getLogger(__name__)

# 프로젝트 루트 (server/ 의 상위)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def register_billing_web_routes(app):

    # ── 랜딩페이지 ──
    @app.route('/proptalk/')
    def proptalk_landing():
        """Proptalk 랜딩페이지 (Coming Soon)"""
        return send_from_directory(
            os.path.join(_PROJECT_ROOT, 'marketing', 'proptalk'),
            'index.html',
        )

    @app.route('/proptalk/images/<path:filename>')
    def proptalk_images(filename):
        """랜딩페이지용 이미지 서빙"""
        return send_from_directory(
            os.path.join(_PROJECT_ROOT, 'images'),
            filename,
        )

    # ── 사용 가이드 ──
    @app.route('/proptalk/guide')
    def proptalk_guide():
        """Proptalk 사용 가이드"""
        return send_from_directory(
            os.path.join(_PROJECT_ROOT, 'marketing', 'proptalk'),
            'guide.html',
        )

    # ── 법적 문서 페이지 ──
    _MARKETING_DIR = os.path.join(_PROJECT_ROOT, 'marketing', 'proptalk')

    @app.route('/proptalk/terms')
    def proptalk_terms():
        """이용약관"""
        return send_from_directory(_MARKETING_DIR, 'terms-of-service.html')

    @app.route('/proptalk/privacy')
    def proptalk_privacy():
        """개인정보 처리방침"""
        return send_from_directory(_MARKETING_DIR, 'privacy-policy.html')

    @app.route('/proptalk/payment-terms')
    def proptalk_payment_terms():
        """결제/환불 약관"""
        return send_from_directory(_MARKETING_DIR, 'billing-terms.html')

    @app.route('/proptalk/delete-account')
    def proptalk_delete_account():
        """계정 삭제 페이지"""
        return send_from_directory(_MARKETING_DIR, 'delete-account.html')

    # ── 빌링 로그인 ──
    @app.route('/proptalk/billing/login', methods=['GET', 'POST'])
    def billing_login():
        if request.method == 'GET':
            return render_template(
                'billing/login.html',
                google_client_id=Config.GOOGLE_CLIENT_ID,
            )

        # POST: Google ID 토큰으로 로그인
        data = request.get_json()
        google_token = data.get('id_token')
        if not google_token:
            return jsonify({'ok': False, 'error': '토큰이 없습니다'}), 400

        try:
            idinfo = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                Config.GOOGLE_CLIENT_ID,
            )
            google_id = idinfo['sub']
            email = idinfo.get('email', '')
            name = idinfo.get('name', '')
            avatar_url = idinfo.get('picture', '')

            user = User.create(google_id, email, name, avatar_url)
            token = create_token(user['id'])

            return jsonify({'ok': True, 'token': token})
        except Exception as e:
            logger.error(f"Billing login failed: {e}")
            return jsonify({'ok': False, 'error': '로그인 실패'}), 401

    # ── 결제 페이지 ──
    @app.route('/proptalk/billing/')
    def billing_page():
        """요금제 선택 페이지"""
        return render_template(
            'billing/plans.html',
            toss_client_key=Config.TOSS_CLIENT_KEY,
        )

    @app.route('/proptalk/billing/checkout')
    def billing_checkout():
        """Toss SDK 결제 페이지"""
        return render_template(
            'billing/checkout.html',
            toss_client_key=Config.TOSS_CLIENT_KEY,
        )

    @app.route('/proptalk/billing/success')
    def billing_success():
        """결제 성공 페이지"""
        return render_template('billing/success.html')

    @app.route('/proptalk/billing/fail')
    def billing_fail():
        """결제 실패 페이지"""
        return render_template('billing/fail.html')

    @app.route('/proptalk/billing/manage')
    def billing_manage():
        """구독 관리 페이지"""
        return render_template('billing/manage.html')
