#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property Manager - 통합 건축물 정보 조회 서비스
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask, jsonify, render_template, session, request, redirect
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# 환경 변수 로드 (통합 환경 변수 파일 사용)
env_path = Path('/home/webapp/goldenrabbit/backend/.env')
load_dotenv(env_path)

# Flask 앱 생성 (static_url_path 명시)
app = Flask(__name__,
            static_url_path='/static',
            static_folder='static')
CORS(app)

# 템플릿 자동 리로드 활성화 (프로덕션에서도 템플릿 변경 즉시 반영)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# 서브패스 설정 (property-manager와 propsheet 모두 지원)
class MultiPrefixMiddleware(object):
    def __init__(self, app, prefixes):
        self.app = app
        self.prefixes = prefixes  # List of prefixes

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        for prefix in self.prefixes:
            if path.startswith(prefix):
                environ['PATH_INFO'] = path[len(prefix):]
                environ['SCRIPT_NAME'] = prefix
                return self.app(environ, start_response)

        # Fallback: serve without prefix stripping (for /api/*, /property/*, /services)
        environ['SCRIPT_NAME'] = ''
        return self.app(environ, start_response)

app.wsgi_app = MultiPrefixMiddleware(app.wsgi_app, prefixes=['/property-manager', '/propsheet'])
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# 세션 설정
from datetime import timedelta

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_NAME'] = 'session_pm'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # 세션 유지 시간 24시간

# 로깅 설정
log_dir = Path('/home/webapp/goldenrabbit/logs/property-manager')
log_dir.mkdir(parents=True, exist_ok=True)

# RotatingFileHandler 설정 (최대 10MB, 5개 백업 파일)
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

file_handler = RotatingFileHandler(
    log_dir / 'app.log',
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

# 루트 로거 설정
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

# Flask/Werkzeug HTTP 요청 로그를 WARNING 레벨로 변경 (헬스체크 로그 차단)
logging.getLogger('werkzeug').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# 라우트 등록
from routes import search_map, address_finder, geocoding, database, workspace, propsheet, workspace_members, oauth, share, propnet_api, propsheet_save, guide, map_dong, complex as complex_routes, search_unified, ai_search, ai_billing

# PropNet API routes (기존 포트 8000 API 서버 흡수 - 우선 등록)
app.register_blueprint(propnet_api.bp)

# API routes (Property Manager UI 제거, API만 유지)
app.register_blueprint(propsheet_save.bp, url_prefix='/api')
app.register_blueprint(search_map.bp, url_prefix='/api')
app.register_blueprint(address_finder.bp, url_prefix='/api')
app.register_blueprint(geocoding.bp, url_prefix='/api')
app.register_blueprint(database.bp, url_prefix='/api')
app.register_blueprint(workspace.bp, url_prefix='/api')

# PropSheet routes (새 데이터베이스 관리 서비스)
app.register_blueprint(propsheet.bp)
app.register_blueprint(guide.bp)

# Dong clustering API (Week 2, flag-gated)
app.register_blueprint(map_dong.bp)
app.register_blueprint(complex_routes.bp)
app.register_blueprint(search_unified.bp)
app.register_blueprint(workspace_members.bp, url_prefix='/propsheet/api')
app.register_blueprint(oauth.bp)
app.register_blueprint(share.bp)
app.register_blueprint(ai_search.bp, url_prefix='/api')
app.register_blueprint(ai_billing.bp, url_prefix='/api')

# Propedia 앱 API (app_api, app_auth, app_user_data, admin_dashboard)는
# proppedia 서비스(포트 5010)에서 전담. Nginx /app/* → 5010.
# property-manager(5000)에서는 제거됨 (2026-03-27).

@app.route('/')
def index():
    prefix = request.environ.get('SCRIPT_NAME', '')
    if prefix == '/propsheet':
        # Propsheet landing page
        if session.get('logged_in'):
            return redirect('/propsheet/workspaces')
        error = request.args.get('error')
        return render_template('propsheet/landing.html', error=error)
    # Property Manager 제거됨 - Proppedia로 통합 (2026-04-16)
    return redirect('/proppedia/')

# /public/ 및 /address-finder 제거됨 (2026-03-16)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

def _check_existing_server(port):
    """Check if a healthy server is already running on the port. If so, exit cleanly."""
    import urllib.request
    try:
        url = f'http://localhost:{port}/property-manager/health'
        req = urllib.request.Request(url, method='GET')
        response = urllib.request.urlopen(req, timeout=3)
        if response.status == 200:
            logger.info(f"Healthy server already running on port {port}, skipping startup")
            sys.exit(0)
    except Exception:
        pass  # No healthy server running, proceed with startup

if __name__ == '__main__':
    port = int(os.getenv('PROPERTY_MANAGER_PORT', 5000))
    _check_existing_server(port)
    logger.info(f"Starting Property Manager on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
