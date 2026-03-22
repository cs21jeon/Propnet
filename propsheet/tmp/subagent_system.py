#!/usr/bin/env python3
"""
Implement subagent invitation system:
1. Add role + agent_id to web_users
2. Link existing agent (cs21.jeon) to agents table
3. Add subagent invite/manage API
4. Auto-add subagent to agent's workspaces on login
5. Show agent info dynamically in broker card
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

# ============================================================
# Step 1: Add role + agent_id columns to web_users
# ============================================================
with get_db_connection() as conn:
    with conn.cursor() as cur:
        for col, col_type, default in [
            ('role', 'VARCHAR(20)', "'user'"),
            ('agent_id', 'INTEGER', 'NULL'),
        ]:
            cur.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'web_users' AND column_name = %s
            """, (col,))
            if not cur.fetchone():
                cur.execute(f"ALTER TABLE web_users ADD COLUMN {col} {col_type} DEFAULT {default}")
                print(f"1. Added {col} column to web_users")
            else:
                print(f"1. {col} already exists")

        # Set cs21.jeon as agent, linked to agents.id=1
        cur.execute("""
            UPDATE web_users SET role = 'admin', agent_id = 1
            WHERE email = 'cs21.jeon@gmail.com'
        """)
        print("1b. Set cs21.jeon as admin + agent_id=1")

        conn.commit()

# ============================================================
# Step 2: Add subagent invite API to database.py (or propsheet.py)
# ============================================================
PROPSHEET_ROUTE = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(PROPSHEET_ROUTE, 'r') as f:
    ps = f.read()

subagent_api = '''

# ===== Subagent Management =====

@bp.route('/api/agent/subagents', methods=['GET'])
@propsheet_login_required
def list_subagents():
    """List subagents for the current agent"""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    user_id = session.get('user_id')
    # Find agent record for this user
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM agents WHERE email = %s AND is_active = true", (session.get('user_email'),))
            agent = cur.fetchone()
            if not agent:
                return jsonify({'success': False, 'error': 'Agent 권한이 없습니다'}), 403

            agent_id = agent['id']

            # Get subagents (web_users with agent_id = this agent)
            cur.execute("""
                SELECT wu.id, wu.email, wu.name, wu.role, wu.avatar_url, wu.is_active, wu.created_at
                FROM web_users wu
                WHERE wu.agent_id = %s AND wu.role = 'subagent'
                ORDER BY wu.created_at
            """, (agent_id,))
            subagents = [dict(r) for r in cur.fetchall()]

            # Get pending requests
            cur.execute("""
                SELECT id, email, name, status, requested_at
                FROM subagent_requests
                WHERE agent_id = %s
                ORDER BY requested_at DESC
            """, (agent_id,))
            requests = [dict(r) for r in cur.fetchall()]
            for r in requests:
                if r.get('requested_at'):
                    r['requested_at'] = r['requested_at'].isoformat()

            # Get agent info
            cur.execute("SELECT max_subagents, remaining_subagent_slots FROM agents WHERE id = %s", (agent_id,))
            agent_info = cur.fetchone()

    return jsonify({
        'success': True,
        'subagents': subagents,
        'requests': requests,
        'max_subagents': agent_info['max_subagents'] if agent_info else 2,
        'remaining_slots': agent_info['remaining_subagent_slots'] if agent_info else 0
    })


@bp.route('/api/agent/invite-subagent', methods=['POST'])
@propsheet_login_required
def invite_subagent():
    """Invite a subagent by email"""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    data = request.get_json()
    invite_email = data.get('email', '').strip().lower()
    invite_name = data.get('name', '').strip()

    if not invite_email:
        return jsonify({'success': False, 'error': '이메일을 입력해주세요'}), 400

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verify caller is agent
            cur.execute("SELECT id, remaining_subagent_slots FROM agents WHERE email = %s AND is_active = true",
                        (session.get('user_email'),))
            agent = cur.fetchone()
            if not agent:
                return jsonify({'success': False, 'error': 'Agent 권한이 없습니다'}), 403

            if agent['remaining_subagent_slots'] <= 0:
                return jsonify({'success': False, 'error': '서브에이전트 슬롯이 부족합니다'}), 400

            agent_id = agent['id']

            # Check if already invited or exists as subagent
            cur.execute("SELECT id FROM web_users WHERE email = %s AND agent_id = %s", (invite_email, agent_id))
            if cur.fetchone():
                return jsonify({'success': False, 'error': '이미 등록된 서브에이전트입니다'}), 400

            cur.execute("SELECT id FROM subagent_requests WHERE email = %s AND agent_id = %s AND status = 'pending'",
                        (invite_email, agent_id))
            if cur.fetchone():
                return jsonify({'success': False, 'error': '이미 초대 대기 중입니다'}), 400

            # Create invitation
            cur.execute("""
                INSERT INTO subagent_requests (agent_id, email, name, status)
                VALUES (%s, %s, %s, 'pending')
                RETURNING id
            """, (agent_id, invite_email, invite_name or invite_email.split('@')[0]))

            # Decrease remaining slots
            cur.execute("UPDATE agents SET remaining_subagent_slots = remaining_subagent_slots - 1 WHERE id = %s",
                        (agent_id,))

            conn.commit()

    return jsonify({'success': True, 'message': f'{invite_email}에 초대를 보냈습니다'})


@bp.route('/api/agent/remove-subagent/<int:user_id>', methods=['DELETE'])
@propsheet_login_required
def remove_subagent(user_id):
    """Remove a subagent"""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM agents WHERE email = %s AND is_active = true",
                        (session.get('user_email'),))
            agent = cur.fetchone()
            if not agent:
                return jsonify({'success': False, 'error': 'Agent 권한이 없습니다'}), 403

            # Remove subagent role
            cur.execute("""
                UPDATE web_users SET role = 'user', agent_id = NULL
                WHERE id = %s AND agent_id = %s AND role = 'subagent'
            """, (user_id, agent['id']))

            if cur.rowcount > 0:
                # Remove from workspace_members
                cur.execute("""
                    DELETE FROM workspace_members
                    WHERE user_id = %s AND workspace_id IN (
                        SELECT w.id FROM workspaces w WHERE w.slug LIKE %s
                    )
                """, (user_id, agent.get('slug', '') + '%'))

                # Restore slot
                cur.execute("UPDATE agents SET remaining_subagent_slots = remaining_subagent_slots + 1 WHERE id = %s",
                            (agent['id'],))

            conn.commit()

    return jsonify({'success': True, 'message': '서브에이전트가 해제되었습니다'})


@bp.route('/api/agent/cancel-invite/<int:request_id>', methods=['DELETE'])
@propsheet_login_required
def cancel_subagent_invite(request_id):
    """Cancel a pending subagent invitation"""
    from services.database_service import get_db_connection

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM agents WHERE email = %s AND is_active = true",
                        (session.get('user_email'),))
            agent = cur.fetchone()
            if not agent:
                return jsonify({'success': False, 'error': 'Agent 권한이 없습니다'}), 403

            cur.execute("""
                DELETE FROM subagent_requests
                WHERE id = %s AND agent_id = %s AND status = 'pending'
            """, (request_id, agent[0]))

            if cur.rowcount > 0:
                cur.execute("UPDATE agents SET remaining_subagent_slots = remaining_subagent_slots + 1 WHERE id = %s",
                            (agent[0],))

            conn.commit()

    return jsonify({'success': True, 'message': '초대가 취소되었습니다'})


@bp.route('/api/agent/info', methods=['GET'])
@propsheet_login_required
def get_agent_info():
    """Get agent info for the current user (or their agent)"""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            user_email = session.get('user_email')

            # Check if user is an agent directly
            cur.execute("SELECT * FROM agents WHERE email = %s AND is_active = true", (user_email,))
            agent = cur.fetchone()

            if not agent:
                # Check if user is a subagent
                cur.execute("SELECT agent_id FROM web_users WHERE email = %s AND role = 'subagent'", (user_email,))
                user = cur.fetchone()
                if user and user['agent_id']:
                    cur.execute("SELECT * FROM agents WHERE id = %s AND is_active = true", (user['agent_id'],))
                    agent = cur.fetchone()

            if agent:
                return jsonify({
                    'success': True,
                    'agent': {
                        'name': agent['name'],
                        'agency_name': agent['agency_name'],
                        'slug': agent['slug'],
                        'phone': agent['phone'],
                        'address': agent['address'],
                        'license_no': agent['license_no'],
                    }
                })

    return jsonify({'success': True, 'agent': None})

'''

if 'invite_subagent' not in ps:
    ps += subagent_api
    print("2. Added subagent management APIs to propsheet.py")
else:
    print("2. Subagent APIs already exist")

# Make sure imports are available
if 'from flask import' in ps:
    if 'jsonify' not in ps.split('from flask import')[1].split('\n')[0]:
        ps = ps.replace('from flask import ', 'from flask import jsonify, ', 1)

with open(PROPSHEET_ROUTE, 'w') as f:
    f.write(ps)

# ============================================================
# Step 3: Auto-link subagent on Google login
# ============================================================
OAUTH_PATH = '/home/webapp/goldenrabbit/backend/property-manager/routes/oauth.py'
with open(OAUTH_PATH, 'r') as f:
    oauth = f.read()

# After login, check if this user has a pending subagent invitation
auto_link = """
    # Auto-link subagent: check pending invitations
    try:
        from services.database_service import get_db_connection as _get_conn
        with _get_conn() as _conn:
            with _conn.cursor() as _cur:
                _cur.execute(
                    "SELECT id, agent_id FROM subagent_requests WHERE email = %s AND status = 'pending'",
                    (user['email'],))
                _invite = _cur.fetchone()
                if _invite:
                    invite_id, agent_id = _invite
                    # Set user as subagent
                    _cur.execute(
                        "UPDATE web_users SET role = 'subagent', agent_id = %s WHERE id = %s",
                        (agent_id, user['id']))
                    # Mark invitation as approved
                    _cur.execute(
                        "UPDATE subagent_requests SET status = 'approved', user_id = %s, responded_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (user['id'], invite_id))
                    # Add to agent's workspaces
                    _cur.execute("SELECT slug FROM agents WHERE id = %s", (agent_id,))
                    _agent_slug = _cur.fetchone()
                    if _agent_slug:
                        _cur.execute(
                            "SELECT id FROM workspaces WHERE slug LIKE %s",
                            (_agent_slug[0] + '%',))
                        for _ws in _cur.fetchall():
                            _cur.execute(\"\"\"
                                INSERT INTO workspace_members (workspace_id, user_id, role, invited_at, accepted_at)
                                VALUES (%s, %s, 'editor', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                                ON CONFLICT (workspace_id, user_id) DO NOTHING
                            \"\"\", (_ws[0], user['id']))
                    _conn.commit()
                    logger.info(f"Auto-linked subagent {user['email']} to agent_id={agent_id}")

                # Also store role in session
                _cur.execute("SELECT role, agent_id FROM web_users WHERE id = %s", (user['id'],))
                _role_row = _cur.fetchone()
                if _role_row:
                    session['user_role'] = _role_row[0] or 'user'
                    session['agent_id'] = _role_row[1]
    except Exception as _e:
        logger.warning(f"Subagent auto-link check failed: {_e}")

"""

if 'Auto-link subagent' not in oauth:
    # Insert before the final redirect
    oauth = oauth.replace(
        "    logger.info(f\"Google OAuth login: {user['email']}",
        auto_link + "    logger.info(f\"Google OAuth login: {user['email']}",
        1
    )
    print("3. Added subagent auto-link to OAuth callback")
else:
    print("3. Auto-link already exists")

with open(OAUTH_PATH, 'w') as f:
    f.write(oauth)

# ============================================================
# Step 4: Dynamic broker card from agent info
# ============================================================
WS_HTML = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(WS_HTML, 'r') as f:
    ws_html = f.read()

# Replace hardcoded broker card with dynamic one
old_broker = """            <div class="broker-card">
                <img src="{{ url_for('static', filename='images/logo_goldenrabbit.png') }}" alt="금토끼부동산" class="broker-logo">
                <div class="broker-name">금토끼부동산</div>
                <div class="broker-row">대표 전창성</div>
                <div class="broker-row"><span style="color:var(--brand-blue,#667eea);cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;" onclick="navigator.clipboard.writeText('02-3471-7377'); this.dataset.orig=this.textContent; this.textContent='클립보드에 복사됨'; setTimeout(()=>this.textContent=this.dataset.orig, 1500);" title="클릭하여 복사">02.3471.7377</span></div>
                <div class="broker-row">서울특별시 동작구<br>사당로16나길 55, 1층</div>
                <div class="broker-row">등록번호 11590-2024-00048</div>
            </div>"""

new_broker = """            {% if agent_info %}
            <div class="broker-card">
                <img src="{{ url_for('static', filename='images/logo_' + agent_info.slug + '.png') }}" alt="{{ agent_info.agency_name }}" class="broker-logo"
                     onerror="this.style.display='none'">
                <div class="broker-name">{{ agent_info.agency_name }}</div>
                <div class="broker-row">대표 {{ agent_info.name }}</div>
                <div class="broker-row"><span style="color:var(--brand-blue,#667eea);cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;" onclick="navigator.clipboard.writeText('{{ agent_info.phone }}'); this.dataset.orig=this.textContent; this.textContent='클립보드에 복사됨'; setTimeout(()=>this.textContent=this.dataset.orig, 1500);" title="클릭하여 복사">{{ agent_info.phone }}</span></div>
                <div class="broker-row">{{ agent_info.address }}</div>
                <div class="broker-row">등록번호 {{ agent_info.license_no }}</div>
            </div>
            {% endif %}"""

if old_broker in ws_html:
    ws_html = ws_html.replace(old_broker, new_broker, 1)
    print("4. Made broker card dynamic from agent_info")
else:
    print("4. WARN: broker card pattern not found")

with open(WS_HTML, 'w') as f:
    f.write(ws_html)

# ============================================================
# Step 5: Pass agent_info to workspaces template
# ============================================================
with open(PROPSHEET_ROUTE, 'r') as f:
    ps = f.read()

# Find workspaces_list route and add agent_info
old_ws_render = "return render_template('propsheet/workspaces.html'"
if old_ws_render in ps:
    # Read the full render_template call
    import re
    render_match = re.search(r"return render_template\('propsheet/workspaces\.html'.*?\)", ps, re.DOTALL)
    if render_match:
        old_render = render_match.group(0)
        if 'agent_info' not in old_render:
            # Add agent_info lookup before the return
            agent_lookup = """
    # Get agent info for broker card
    agent_info = None
    try:
        from services.database_service import get_db_connection as _gdc
        from psycopg2.extras import RealDictCursor as _RDC
        with _gdc() as _c:
            with _c.cursor(cursor_factory=_RDC) as _cur:
                _ue = session.get('user_email', '')
                _cur.execute("SELECT * FROM agents WHERE email = %s AND is_active = true", (_ue,))
                agent_info = _cur.fetchone()
                if not agent_info:
                    _cur.execute("SELECT agent_id FROM web_users WHERE email = %s", (_ue,))
                    _u = _cur.fetchone()
                    if _u and _u.get('agent_id'):
                        _cur.execute("SELECT * FROM agents WHERE id = %s AND is_active = true", (_u['agent_id'],))
                        agent_info = _cur.fetchone()
    except Exception:
        pass

    """
            # Insert before the return
            ps = ps.replace(old_render, agent_lookup + old_render, 1)
            # Add agent_info to render_template args
            if old_render.endswith(')'):
                new_render = old_render[:-1] + ", agent_info=agent_info)"
            else:
                new_render = old_render.replace(')', ', agent_info=agent_info)', 1)
            ps = ps.replace(old_render, new_render, 1)
            print("5. Added agent_info to workspaces template")
        else:
            print("5. agent_info already in render")
    else:
        print("5. WARN: render_template not found")

with open(PROPSHEET_ROUTE, 'w') as f:
    f.write(ps)

print("\nDone! Restart: sudo systemctl restart property-manager propsheet")
