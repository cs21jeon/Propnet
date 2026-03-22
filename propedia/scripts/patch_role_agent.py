import os

changes = []

# 1. proppedia/app.py: editor → agent, subagent
path1 = '/home/webapp/goldenrabbit/backend/proppedia/app.py'
with open(path1, 'r') as f:
    content = f.read()
old1 = "@role_required('editor', 'admin')"
new1 = "@role_required('agent', 'subagent', 'admin')"
cnt = content.count(old1)
if cnt > 0:
    content = content.replace(old1, new1)
    content = content.replace('(editor/admin 전용)', '(agent/subagent/admin 전용)')
    with open(path1, 'w') as f:
        f.write(content)
    changes.append(f'1. proppedia/app.py: {cnt}곳 수정')

# 2. app_user_service.py: update_user_role 유효값
path2 = '/home/webapp/goldenrabbit/backend/property-manager/services/app_user_service.py'
with open(path2, 'r') as f:
    content = f.read()
old2 = "if role not in ('user', 'editor', 'admin'):"
new2 = "if role not in ('user', 'agent', 'subagent', 'admin'):"
if old2 in content:
    content = content.replace(old2, new2)
    with open(path2, 'w') as f:
        f.write(content)
    changes.append('2. app_user_service.py: role 유효값 수정')

# 3. admin_dashboard.html: editor → agent/subagent 스타일 + 드롭다운 옵션
path3 = '/home/webapp/goldenrabbit/backend/property-manager/templates/admin_dashboard.html'
with open(path3, 'r') as f:
    content = f.read()

# CSS: editor 스타일 → agent/subagent 스타일
content = content.replace(
    ".role-select.role-editor { border-color: #28a745; background: #f5fff5; }",
    ".role-select.role-agent { border-color: #28a745; background: #f5fff5; }\n        .role-select.role-subagent { border-color: #fd7e14; background: #fff8f0; }"
)

# JS roleClass: editor → agent/subagent
content = content.replace(
    "const roleClass = role === 'admin' ? 'role-admin' : (role === 'editor' ? 'role-editor' : '');",
    "const roleClass = role === 'admin' ? 'role-admin' : (role === 'agent' ? 'role-agent' : (role === 'subagent' ? 'role-subagent' : ''));"
)
content = content.replace(
    "selectEl.className = 'role-select ' + (newRole === 'admin' ? 'role-admin' : (newRole === 'editor' ? 'role-editor' : ''));",
    "selectEl.className = 'role-select ' + (newRole === 'admin' ? 'role-admin' : (newRole === 'agent' ? 'role-agent' : (newRole === 'subagent' ? 'role-subagent' : '')));"
)

# 드롭다운 옵션: editor → agent/subagent
content = content.replace(
    """<option value="user" ${role==='user'?'selected':''}>user</option>
                    <option value="editor" ${role==='editor'?'selected':''}>editor</option>
                    <option value="admin" ${role==='admin'?'selected':''}>admin</option>""",
    """<option value="user" ${role==='user'?'selected':''}>user</option>
                    <option value="subagent" ${role==='subagent'?'selected':''}>subagent</option>
                    <option value="agent" ${role==='agent'?'selected':''}>agent</option>
                    <option value="admin" ${role==='admin'?'selected':''}>admin</option>"""
)

with open(path3, 'w') as f:
    f.write(content)
changes.append('3. admin_dashboard.html: editor → agent/subagent')

# 4. Flutter User entity (local)
path4 = '/home/webapp/goldenrabbit/frontend/public/app/result.html'
with open(path4, 'r') as f:
    content = f.read()
# result.html은 이미 agent/subagent 포함되어 있으므로 editor만 제거
content = content.replace(
    "['admin', 'editor', 'agent', 'subagent']",
    "['admin', 'agent', 'subagent']"
)
with open(path4, 'w') as f:
    f.write(content)
changes.append('4. result.html: editor 제거')

for c in changes:
    print(c)
print(f'DONE: {len(changes)} files updated')
