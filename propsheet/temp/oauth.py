#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OAuth Routes - Google login/logout and Propsheet landing page"""

import logging
from flask import Blueprint, redirect, request, session, render_template

logger = logging.getLogger(__name__)

bp = Blueprint('oauth', __name__)


@bp.route('/')
def propsheet_landing():
    """Landing page: show login button or redirect to workspaces."""
    if session.get('logged_in'):
        return redirect('/propsheet/workspaces')
    error = request.args.get('error')
    return render_template('propsheet/landing.html', error=error)


@bp.route('/auth/google')
def google_login():
    """Redirect to Google OAuth consent screen."""
    try:
        from services.google_auth_service import get_authorization_url
        authorization_url, state = get_authorization_url()
        session['oauth_state'] = state
        session['oauth_next'] = request.args.get('next', '/propsheet/workspaces')
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        return redirect('/propsheet/?error=auth_failed')


@bp.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    try:
        from services.google_auth_service import exchange_code_for_user_info, find_or_create_user

        # Fix HTTPS: Nginx terminates SSL, Flask sees http://
        callback_url = request.url
        if callback_url.startswith('http://'):
            callback_url = 'https://' + callback_url[7:]

        userinfo = exchange_code_for_user_info(
            authorization_response=callback_url,
            state=session.get('oauth_state')
        )
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        return redirect('/propsheet/?error=auth_failed')

    try:
        user, is_new = find_or_create_user(userinfo)
    except Exception as e:
        logger.error(f"User creation error: {e}")
        return redirect('/propsheet/?error=auth_failed')

    if not user.get('is_active', True):
        return redirect('/propsheet/?error=account_disabled')

    # Set session
    session.permanent = True
    session['logged_in'] = True
    session['user_id'] = user['id']
    session['username'] = user.get('name') or user['email']
    session['user_email'] = user['email']
    session['is_admin'] = (user['email'] == 'cs21.jeon@gmail.com')
    session['avatar_url'] = user.get('avatar_url', '')

    # Clean up OAuth state
    session.pop('oauth_state', None)
    next_url = session.pop('oauth_next', '/propsheet/workspaces')

    logger.info(f"Google OAuth login: {user['email']} (id={user['id']}, new={is_new})")
    return redirect(next_url)


@bp.route('/auth/logout')
def logout():
    """Clear session and redirect to landing."""
    from flask import make_response, current_app

    email = session.get('user_email', 'unknown')
    session.clear()
    session.modified = True

    response = make_response(redirect('/propsheet/'))

    # Delete session cookies at all paths
    cookie_name = current_app.config.get('SESSION_COOKIE_NAME', 'session')
    for path in ['/', '/property-manager', '/propsheet']:
        response.set_cookie(cookie_name, value='', max_age=0, expires=0,
                          path=path, httponly=True, secure=True, samesite='Lax')

    logger.info(f"Logout: {email}")
    return response
