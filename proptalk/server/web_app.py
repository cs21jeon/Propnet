"""
Proptalk 웹앱 라우트
PC 브라우저에서 앱과 동일한 기능 제공
"""
import os
import logging
from flask import render_template, send_from_directory, make_response
from config import Config

logger = logging.getLogger(__name__)

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'web')


def register_web_app_routes(app):

    @app.route('/proptalk/web/login')
    def web_login():
        """웹앱 Google OAuth 로그인"""
        return render_template(
            'web/login.html',
            google_client_id=Config.GOOGLE_CLIENT_ID,
        )

    @app.route('/proptalk/web/')
    def web_app():
        """웹앱 메인 (Alpine.js SPA)"""
        return render_template(
            'web/app.html',
            google_client_id=Config.GOOGLE_CLIENT_ID,
        )

    @app.route('/proptalk/web/sw.js')
    def web_service_worker():
        """Service Worker - /proptalk/web/ scope에서 서빙"""
        response = make_response(
            send_from_directory(_STATIC_DIR, 'sw.js')
        )
        response.headers['Content-Type'] = 'application/javascript'
        response.headers['Service-Worker-Allowed'] = '/proptalk/web/'
        response.headers['Cache-Control'] = 'no-cache'
        return response

    @app.route('/proptalk/web/manifest.json')
    def web_manifest():
        """PWA manifest - /proptalk/web/ scope에서 서빙"""
        return send_from_directory(_STATIC_DIR, 'manifest.json',
                                   mimetype='application/manifest+json')

    @app.route('/proptalk/web/static/<path:filename>')
    def web_static(filename):
        """웹앱 정적 파일 서빙 (CSS, JS, images)"""
        return send_from_directory(_STATIC_DIR, filename)
