#!/usr/bin/env python3
"""Pass agent_info to workspaces template"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(path, 'r') as f:
    py = f.read()

old = """def workspaces_list():
    \"\"\"Render PropSheet workspaces overview page\"\"\"
    try:
        workspaces = _get_filtered_workspaces()
        response = make_response(render_template('propsheet/workspaces.html', workspaces=workspaces))"""

new = """def workspaces_list():
    \"\"\"Render PropSheet workspaces overview page\"\"\"
    try:
        workspaces = _get_filtered_workspaces()

        # Get agent info for broker card
        agent_info = None
        try:
            from services.database_service import get_db_connection
            from psycopg2.extras import RealDictCursor
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    ue = session.get('user_email', '')
                    cur.execute("SELECT * FROM agents WHERE email = %s AND is_active = true", (ue,))
                    agent_info = cur.fetchone()
                    if not agent_info:
                        cur.execute("SELECT agent_id FROM web_users WHERE email = %s", (ue,))
                        u = cur.fetchone()
                        if u and u.get('agent_id'):
                            cur.execute("SELECT * FROM agents WHERE id = %s AND is_active = true", (u['agent_id'],))
                            agent_info = cur.fetchone()
        except Exception:
            pass

        response = make_response(render_template('propsheet/workspaces.html', workspaces=workspaces, agent_info=agent_info))"""

if old in py:
    py = py.replace(old, new, 1)
    print("Added agent_info to workspaces_list")
else:
    print("WARN: pattern not found")

with open(path, 'w') as f:
    f.write(py)
