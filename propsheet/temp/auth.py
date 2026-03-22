#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, make_response, current_app
from functools import wraps
import os
import hashlib
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)

# 환경변수에서 관리자 계정 정보 가져오기
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', '')

def hash_password(password):
    """비밀번호 해시 생성"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_prefix():
    """현재 URL prefix 가져오기"""
    return request.environ.get('SCRIPT_NAME', '')

def login_required(f):
    """로그인 필수 데코레이터 (Property Manager용)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            # All login goes through Google OAuth
            return redirect('/propsheet/auth/google')
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 - Google OAuth로 리다이렉트"""
    if session.get('logged_in'):
        prefix = get_prefix()
        return redirect(f'{prefix}/')
    # Redirect to Google OAuth
    next_url = request.args.get('next', '')
    return redirect(f'/propsheet/auth/google?next={next_url}')

@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """로그아웃 - 세션 클리어 후 Propsheet 랜딩으로"""
    email = session.get('user_email', 'unknown')
    session.clear()
    session.modified = True

    # AJAX 요청
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response = make_response(jsonify({'success': True, 'message': '로그아웃 성공'}))
    else:
        response = make_response(redirect('/propsheet/'))

    # Delete session cookies at all paths
    cookie_name = current_app.config.get('SESSION_COOKIE_NAME', 'session')
    for path in ['/', '/property-manager', '/propsheet']:
        response.set_cookie(cookie_name, value='', max_age=0, expires=0,
                          path=path, httponly=True, secure=True, samesite='Lax')

    logger.info(f"Logout: {email}")
    return response

@bp.route('/check-auth')
def check_auth():
    """인증 상태 확인"""
    return jsonify({
        'authenticated': session.get('logged_in', False),
        'username': session.get('username', ''),
        'email': session.get('user_email', ''),
        'is_admin': session.get('is_admin', False)
    })
