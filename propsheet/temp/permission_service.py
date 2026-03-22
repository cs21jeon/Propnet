#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Permission Service - Role-based access control for Propsheet"""

import logging
from functools import wraps
from flask import session, jsonify, redirect, request, abort
from services.workspace_member_service import has_permission
from services.database_service import get_db_connection, get_db_cursor
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

ROLE_LEVELS = {'viewer': 1, 'editor': 2, 'owner': 3}


def get_current_user_id():
    return session.get('user_id')


def is_admin():
    return session.get('is_admin', False)


def check_workspace_permission(workspace_id: int, required_role: str) -> bool:
    """Check if current user has permission. Admin always passes."""
    if is_admin():
        return True

    user_id = get_current_user_id()
    if not user_id:
        return False

    return has_permission(workspace_id, user_id, required_role)


def get_member_role_by_slug(workspace_slug: str, user_id: int) -> str:
    """Look up user's role in a workspace by slug. Returns role string or None."""
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute('''
                SELECT wm.role FROM workspace_members wm
                JOIN workspaces w ON w.id = wm.workspace_id
                WHERE w.slug = %s AND wm.user_id = %s
            ''', (workspace_slug, user_id))
            row = cursor.fetchone()
            return row['role'] if row else None


def get_workspace_slug_for_database(database_id: int) -> str:
    """Get workspace slug for a database ID."""
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute('''
                SELECT w.slug FROM databases d
                JOIN workspaces w ON w.id = d.workspace_id
                WHERE d.id = %s
            ''', (database_id,))
            row = cursor.fetchone()
            return row['slug'] if row else None


def _handle_unauthorized():
    """Return appropriate response for unauthorized access."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': False, 'error': '권한이 없습니다'}), 403
    return redirect('/propsheet/?error=login_required')


def _handle_unauthenticated():
    """Return appropriate response for unauthenticated access."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
    return redirect('/propsheet/?error=login_required')


def propsheet_login_required(f):
    """Decorator: require login, redirect to /propsheet/ landing if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return _handle_unauthenticated()
        return f(*args, **kwargs)
    return decorated


def require_workspace_role(minimum_role):
    """Decorator factory: require minimum workspace role.

    Extracts workspace slug from route kwargs: 'slug', 'ws_slug', or 'workspace_slug'.
    Admin bypasses role check.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('logged_in'):
                return _handle_unauthenticated()

            # Admin bypass
            if session.get('is_admin'):
                return f(*args, **kwargs)

            # Get workspace slug from route params
            ws_slug = kwargs.get('ws_slug') or kwargs.get('slug') or kwargs.get('workspace_slug')
            if not ws_slug:
                return jsonify({'success': False, 'error': 'Workspace not specified'}), 400

            user_id = session.get('user_id')
            user_role = get_member_role_by_slug(ws_slug, user_id)

            if not user_role:
                return _handle_unauthorized()

            if ROLE_LEVELS.get(user_role, 0) < ROLE_LEVELS.get(minimum_role, 0):
                return _handle_unauthorized()

            return f(*args, **kwargs)
        return decorated
    return decorator


def require_database_role(minimum_role):
    """Decorator factory: require minimum role via database_id -> workspace lookup.

    Gets database_id from query param 'database_id' or 'db'.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('logged_in'):
                return _handle_unauthenticated()

            # Admin bypass
            if session.get('is_admin'):
                return f(*args, **kwargs)

            # Get database_id from query params
            db_id = request.args.get('database_id') or request.args.get('db')
            if not db_id:
                # Try form/json data
                data = request.get_json(silent=True) or {}
                db_id = data.get('database_id') or data.get('db')

            if not db_id:
                return jsonify({'success': False, 'error': 'Database not specified'}), 400

            try:
                db_id = int(db_id)
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'Invalid database ID'}), 400

            ws_slug = get_workspace_slug_for_database(db_id)
            if not ws_slug:
                return jsonify({'success': False, 'error': '데이터베이스를 찾을 수 없습니다'}), 404

            user_id = session.get('user_id')
            user_role = get_member_role_by_slug(ws_slug, user_id)

            if not user_role:
                return _handle_unauthorized()

            if ROLE_LEVELS.get(user_role, 0) < ROLE_LEVELS.get(minimum_role, 0):
                return _handle_unauthorized()

            return f(*args, **kwargs)
        return decorated
    return decorator
