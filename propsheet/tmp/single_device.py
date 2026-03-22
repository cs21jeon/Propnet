#!/usr/bin/env python3
"""
Single device session: Only one device can be logged in per account.
New login invalidates previous session.

Changes:
1. Add active_session_id column to web_users
2. On login (Google OAuth callback): generate session ID, save to DB
3. On every request (login_required): check session ID matches DB
4. Mismatch → force logout with message
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

# Step 1: Add active_session_id column
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'web_users' AND column_name = 'active_session_id'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE web_users ADD COLUMN active_session_id VARCHAR(64)")
            print("1. Added active_session_id column to web_users")
        else:
            print("1. active_session_id already exists")
        conn.commit()

# Step 2: Modify OAuth callback to save session ID
OAUTH_PATH = '/home/webapp/goldenrabbit/backend/property-manager/routes/oauth.py'
with open(OAUTH_PATH, 'r') as f:
    oauth = f.read()

# Add import for uuid at the top if not present
if 'import uuid' not in oauth:
    oauth = oauth.replace('from flask import', 'import uuid\nfrom flask import', 1)
    print("2a. Added uuid import to oauth.py")

# After session.clear(), generate and save session ID
old_login = """    session['avatar_url'] = user.get('avatar_url', '')

    logger.info(f"Google OAuth login: {user['email']} (id={user['id']}, new={is_new}, is_admin={is_admin})")
    return redirect('/propsheet/workspaces')"""

new_login = """    session['avatar_url'] = user.get('avatar_url', '')

    # Single device session: save unique session ID to DB
    device_session_id = uuid.uuid4().hex
    session['device_session_id'] = device_session_id
    try:
        from services.database_service import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE web_users SET active_session_id = %s WHERE id = %s",
                            (device_session_id, user['id']))
                conn.commit()
    except Exception as e:
        logger.warning(f"Failed to save device session: {e}")

    logger.info(f"Google OAuth login: {user['email']} (id={user['id']}, new={is_new}, is_admin={is_admin})")
    return redirect('/propsheet/workspaces')"""

if old_login in oauth:
    oauth = oauth.replace(old_login, new_login, 1)
    print("2b. Added device session ID generation to OAuth callback")
else:
    print("2b. WARN: OAuth callback pattern not found")

with open(OAUTH_PATH, 'w') as f:
    f.write(oauth)

# Step 3: Modify login_required to check session ID
PERM_PATH = '/home/webapp/goldenrabbit/backend/property-manager/services/permission_service.py'
with open(PERM_PATH, 'r') as f:
    perm = f.read()

old_login_required = """def propsheet_login_required(f):
    \"\"\"Decorator: require login, redirect to /propsheet/ landing if not authenticated.\"\"\"
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return _handle_unauthenticated()
        return f(*args, **kwargs)
    return decorated"""

new_login_required = """def propsheet_login_required(f):
    \"\"\"Decorator: require login, redirect to /propsheet/ landing if not authenticated.\"\"\"
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return _handle_unauthenticated()
        # Single device check: verify this session is still active
        device_sid = session.get('device_session_id')
        if device_sid:
            user_id = session.get('user_id')
            if user_id and not _check_device_session(user_id, device_sid):
                session.clear()
                from flask import request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json':
                    return jsonify({'success': False, 'error': '다른 기기에서 로그인하여 현재 세션이 종료되었습니다.'}), 401
                return redirect('/propsheet/?error=session_expired_other_device')
        return f(*args, **kwargs)
    return decorated


def _check_device_session(user_id, device_session_id):
    \"\"\"Check if the device session ID matches the active one in DB.\"\"\"
    try:
        from services.database_service import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT active_session_id FROM web_users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if row and row[0] == device_session_id:
                    return True
                return False
    except Exception:
        return True  # On DB error, allow access (fail-open)"""

if old_login_required in perm:
    perm = perm.replace(old_login_required, new_login_required, 1)
    print("3. Added single device check to propsheet_login_required")
else:
    print("3. WARN: login_required pattern not found")

# Make sure jsonify is imported
if 'from flask import' in perm and 'jsonify' not in perm.split('from flask import')[1].split('\n')[0]:
    perm = perm.replace('from flask import session', 'from flask import session, jsonify', 1)
    print("3b. Added jsonify import")

with open(PERM_PATH, 'w') as f:
    f.write(perm)

# Step 4: Add landing page message for session_expired_other_device
LANDING_PATH = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/landing.html'
with open(LANDING_PATH, 'r') as f:
    landing = f.read()

if 'session_expired_other_device' not in landing:
    # Find existing error handling
    if 'error=auth_failed' in landing or 'error' in landing:
        # Add new error message
        old_err = "error === 'session_expired'"
        new_err = "error === 'session_expired' || error === 'session_expired_other_device'"
        if old_err in landing:
            landing = landing.replace(old_err, new_err, 1)
            print("4a. Added other_device error to landing page")
        else:
            # Try to find any error display and add our message
            if "const error = " in landing or "error" in landing:
                print("4a. Landing has error handling, manual check needed")
            else:
                print("4a. No error handling in landing, skipping")
    else:
        print("4a. No error handling found in landing page")

with open(LANDING_PATH, 'w') as f:
    f.write(landing)

print("\nDone! Restart: sudo systemctl restart property-manager propsheet")
