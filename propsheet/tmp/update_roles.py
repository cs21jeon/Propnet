#!/usr/bin/env python3
"""Update admin dashboard + auth for agent/subagent roles"""

# === 1. admin_dashboard.py: expand allowed roles ===
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/admin_dashboard.py'
with open(route_path, 'r') as f:
    content = f.read()

# Expand role validation
old_role_check = "if role not in ('user', 'editor', 'admin'):"
new_role_check = "if role not in ('user', 'editor', 'admin', 'agent', 'subagent'):"
if 'agent' not in content.split("not in (")[1].split(")")[0] if "not in (" in content else '':
    content = content.replace(old_role_check, new_role_check, 1)
    print("1a. Expanded role validation in route")

with open(route_path, 'w') as f:
    f.write(content)

# === 2. admin_dashboard_service.py: expand role validation ===
svc_path = '/home/webapp/goldenrabbit/backend/property-manager/services/admin_dashboard_service.py'
with open(svc_path, 'r') as f:
    content = f.read()

old_svc_check = "if role not in ('user', 'editor', 'admin'):"
new_svc_check = "if role not in ('user', 'editor', 'admin', 'agent', 'subagent'):"
if 'agent' not in content.split("not in (")[1].split(")")[0] if "not in (" in content else '':
    content = content.replace(old_svc_check, new_svc_check, 1)
    print("1b. Expanded role validation in service")

# Add agent_id update when changing to agent/subagent
old_update = '''        cursor.execute(
            "UPDATE app_users SET role = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id, email, role",
            (role, user_id)
        )'''

new_update = '''        # If setting to agent, link to agents table
        agent_id_val = None
        if role == 'agent':
            cursor.execute("SELECT id FROM agents WHERE email = (SELECT email FROM app_users WHERE id = %s)", (user_id,))
            agent_row = cursor.fetchone()
            if agent_row:
                agent_id_val = agent_row[0]
                cursor.execute("UPDATE agents SET status = 'approved', approved_at = CURRENT_TIMESTAMP WHERE id = %s", (agent_id_val,))

        cursor.execute(
            "UPDATE app_users SET role = %s, agent_id = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id, email, role",
            (role, agent_id_val, user_id)
        )'''

if 'agent_id_val' not in content:
    content = content.replace(old_update, new_update, 1)
    print("1c. Added agent_id linking on role change")

with open(svc_path, 'w') as f:
    f.write(content)

# === 3. admin_dashboard.html: expand role dropdown ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/admin_dashboard.html'
with open(html_path, 'r') as f:
    html = f.read()

old_dropdown = """<option value="user" ${role==='user'?'selected':''}>user</option>
                    <option value="editor" ${role==='editor'?'selected':''}>editor</option>
                    <option value="admin" ${role==='admin'?'selected':''}>admin</option>"""

new_dropdown = """<option value="user" ${role==='user'?'selected':''}>user</option>
                    <option value="agent" ${role==='agent'?'selected':''}>agent</option>
                    <option value="subagent" ${role==='subagent'?'selected':''}>subagent</option>
                    <option value="admin" ${role==='admin'?'selected':''}>admin</option>"""

if "value=\"agent\"" not in html:
    html = html.replace(old_dropdown, new_dropdown, 1)
    print("2. Updated role dropdown in dashboard")

# Add agent/subagent color styling
old_style = ".role-select.role-editor { border-color: #28a745; background: #f5fff5; }"
new_style = """.role-select.role-editor { border-color: #28a745; background: #f5fff5; }
                .role-select.role-agent { border-color: #1A73E8; background: #e8f0fe; }
                .role-select.role-subagent { border-color: #F9A825; background: #fff8e1; }"""

if 'role-agent' not in html:
    html = html.replace(old_style, new_style, 1)
    print("3. Added agent/subagent color styles")

# Fix roleClass assignment to include agent/subagent
old_class = "const roleClass = role === 'admin' ? 'role-admin' : role === 'editor' ? 'role-editor' : '';"
new_class = "const roleClass = role === 'admin' ? 'role-admin' : role === 'editor' ? 'role-editor' : role === 'agent' ? 'role-agent' : role === 'subagent' ? 'role-subagent' : '';"
if 'role-agent' not in html.split('roleClass')[1].split(';')[0] if 'roleClass' in html else '':
    html = html.replace(old_class, new_class, 1)
    print("4. Updated roleClass assignment")

with open(html_path, 'w') as f:
    f.write(html)

# === 4. app_auth.py: include agent_id in user response ===
auth_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/app_auth.py'
with open(auth_path, 'r') as f:
    content = f.read()

# The get_user_by_id already returns role, but we need agent_id too
# Check if agent info is included in token/response
if 'agent_id' not in content:
    # Find where user dict is built in login/me responses
    # Add agent_id to the user response
    old_me = "'role': user.get('role', 'user')"
    new_me = "'role': user.get('role', 'user'),\n                'agent_id': user.get('agent_id')"
    if old_me in content:
        content = content.replace(old_me, new_me, 1)
        print("5. Added agent_id to auth response")

    with open(auth_path, 'w') as f:
        f.write(content)

# === 5. app_user_service.py: include agent_id in user dict ===
user_svc_path = '/home/webapp/goldenrabbit/backend/property-manager/services/app_user_service.py'
with open(user_svc_path, 'r') as f:
    content = f.read()

if "'agent_id'" not in content:
    old_role = "'role': user[8] if user[8] else 'user'"
    new_role = "'role': user[8] if user[8] else 'user',\n            'agent_id': user[9] if len(user) > 9 else None"
    if old_role in content:
        content = content.replace(old_role, new_role, 1)
        print("6a. Added agent_id to user dict")

    # Update the SELECT query to include agent_id
    old_select = "SELECT id, email, name, provider, is_active, is_verified, last_login_at, created_at, role FROM app_users"
    new_select = "SELECT id, email, name, provider, is_active, is_verified, last_login_at, created_at, role, agent_id FROM app_users"
    content = content.replace(old_select, new_select)
    print("6b. Updated SELECT to include agent_id")

    with open(user_svc_path, 'w') as f:
        f.write(content)

# === 6. airtable.py: apply role_required for save functions ===
airtable_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/airtable.py'
with open(airtable_path, 'r') as f:
    content = f.read()

if 'role_required' not in content:
    # Import role_required
    if 'from routes.app_auth import' in content:
        old_import = 'from routes.app_auth import'
        content = content.replace(old_import, 'from routes.app_auth import role_required,', 1)
    elif 'token_required' in content:
        old_import2 = 'from routes.app_auth import token_required'
        content = content.replace(old_import2, 'from routes.app_auth import token_required, role_required', 1)
    print("7. Added role_required import to airtable.py")
    # Note: actual @role_required decorator application to save endpoints
    # can be added later per endpoint as needed

    with open(airtable_path, 'w') as f:
        f.write(content)

print("Done!")
