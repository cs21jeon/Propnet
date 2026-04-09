#!/usr/bin/env python3
"""get_member_role_by_slug: agent_id 매칭 추가"""

path = '/home/webapp/goldenrabbit/backend/property-manager/services/permission_service.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old = '''def get_member_role_by_slug(workspace_slug: str, user_id: int) -> str:
    """Look up user's role in a workspace by slug. Returns role string or None."""
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute(\'\'\'
                SELECT wm.role FROM workspace_members wm
                JOIN workspaces w ON w.id = wm.workspace_id
                WHERE w.slug = %s AND wm.user_id = %s
            \'\'\', (workspace_slug, user_id))
            row = cursor.fetchone()
            return row['role'] if row else None'''

new = '''def get_member_role_by_slug(workspace_slug: str, user_id: int) -> str:
    """Look up user's role in a workspace by slug. Returns role string or None.
    Also checks if user is the agent owner of the workspace via agent_id.
    """
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            # 1. workspace_members 확인
            cursor.execute(\'\'\'
                SELECT wm.role FROM workspace_members wm
                JOIN workspaces w ON w.id = wm.workspace_id
                WHERE w.slug = %s AND wm.user_id = %s
            \'\'\', (workspace_slug, user_id))
            row = cursor.fetchone()
            if row:
                return row['role']

            # 2. agent owner 확인: web_users.agent_id == workspaces.agent_id
            cursor.execute(\'\'\'
                SELECT 'owner' as role FROM workspaces w
                JOIN web_users wu ON wu.agent_id = w.agent_id
                WHERE w.slug = %s AND wu.id = %s
            \'\'\', (workspace_slug, user_id))
            row = cursor.fetchone()
            return row['role'] if row else None'''

if old in c:
    c = c.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('agent owner 권한 체크 추가 완료')
else:
    print('패턴 불일치')
