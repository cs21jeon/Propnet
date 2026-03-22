#!/usr/bin/env python3
"""Add device session check to all auth decorators via shared helper"""

PERM_PATH = '/home/webapp/goldenrabbit/backend/property-manager/services/permission_service.py'
with open(PERM_PATH, 'r') as f:
    perm = f.read()

# Add device check helper call to _handle_unauthenticated area
# Create a shared check function that all decorators call

# First, add device check to require_workspace_role
old_ws = """    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('logged_in'):
                return _handle_unauthenticated()

            # Admin bypass
            if session.get('is_admin'):
                return f(*args, **kwargs)"""

new_ws = """    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('logged_in'):
                return _handle_unauthenticated()
            # Single device check
            _kicked = _check_device_kick()
            if _kicked:
                return _kicked

            # Admin bypass
            if session.get('is_admin'):
                return f(*args, **kwargs)"""

if old_ws in perm:
    perm = perm.replace(old_ws, new_ws, 1)
    print("1. Added device check to require_workspace_role")
else:
    print("1. WARN: require_workspace_role pattern not found")

# Add to require_database_role
old_db = """def require_database_role(minimum_role):"""
# Read the function to find the same pattern
import re
db_match = re.search(r'def require_database_role.*?if not session\.get\(.logged_in.\):\s*return _handle_unauthenticated\(\)', perm, re.DOTALL)
if db_match:
    old_db_block = db_match.group(0)
    new_db_block = old_db_block + """
            # Single device check
            _kicked = _check_device_kick()
            if _kicked:
                return _kicked"""
    perm = perm.replace(old_db_block, new_db_block, 1)
    print("2. Added device check to require_database_role")
else:
    print("2. WARN: require_database_role pattern not found")

# Refactor: extract device check into helper so propsheet_login_required uses it too
old_check_inline = """        # Single device check: verify this session is still active
        device_sid = session.get('device_session_id')
        if device_sid:
            user_id = session.get('user_id')
            if user_id and not _check_device_session(user_id, device_sid):
                session.clear()
                from flask import request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json':
                    return jsonify({'success': False, 'error': '다른 기기에서 로그인하여 현재 세션이 종료되었습니다.'}), 401
                return redirect('/propsheet/?error=session_expired_other_device')"""

new_check_inline = """        # Single device check
        _kicked = _check_device_kick()
        if _kicked:
            return _kicked"""

if old_check_inline in perm:
    perm = perm.replace(old_check_inline, new_check_inline, 1)
    print("3. Simplified propsheet_login_required to use _check_device_kick()")

# Add _check_device_kick helper before _check_device_session
old_check_fn = """def _check_device_session(user_id, device_session_id):"""
new_check_fn = """def _check_device_kick():
    \"\"\"Check if this session was kicked by another device login. Returns response or None.\"\"\"
    device_sid = session.get('device_session_id')
    if device_sid:
        user_id = session.get('user_id')
        if user_id and not _check_device_session(user_id, device_sid):
            session.clear()
            from flask import request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json':
                return jsonify({'success': False, 'error': '다른 기기에서 로그인하여 현재 세션이 종료되었습니다.'}), 401
            return redirect('/propsheet/?error=session_expired_other_device')
    return None


def _check_device_session(user_id, device_session_id):"""

if old_check_fn in perm:
    perm = perm.replace(old_check_fn, new_check_fn, 1)
    print("4. Added _check_device_kick() helper")
else:
    print("4. WARN: _check_device_session not found")

with open(PERM_PATH, 'w') as f:
    f.write(perm)

print("\nDone!")
