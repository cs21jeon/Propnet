#!/usr/bin/env python3
"""
1. Add agent_id column to workspaces
2. Set existing workspaces: 금토끼부동산 → agent_id=1
3. Clone 금토끼부동산 → "샘플 워크스페이스" (admin only, agent_id=NULL)
4. Update workspace filtering: agent/subagent see only their agent_id workspaces
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from services.workspace_service import clone_database_full
import psycopg2.extras

# ============================================================
# Step 1: Add agent_id to workspaces
# ============================================================
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'workspaces' AND column_name = 'agent_id'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE workspaces ADD COLUMN agent_id INTEGER REFERENCES agents(id)")
            print("1. Added agent_id column to workspaces")
        else:
            print("1. agent_id already exists")

        # Set 금토끼부동산 → agent_id=1
        cur.execute("UPDATE workspaces SET agent_id = 1 WHERE id = 11")
        # 골든래빗(id=1) is legacy/admin workspace, leave agent_id=NULL
        cur.execute("UPDATE workspaces SET agent_id = NULL WHERE id = 1")
        print("1b. Set 금토끼부동산 agent_id=1, 골든래빗 agent_id=NULL")
        conn.commit()

# ============================================================
# Step 2: Clone 금토끼부동산 → 샘플 워크스페이스
# ============================================================
with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Check if template workspace already exists
        cur.execute("SELECT id FROM workspaces WHERE slug = 'template'")
        existing = cur.fetchone()
        if existing:
            print("2. Template workspace already exists (id=" + str(existing['id']) + ")")
            template_ws_id = existing['id']
        else:
            # Create template workspace
            import secrets, string
            unique_id = 'ws' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(17))
            cur.execute("""
                INSERT INTO workspaces (name, slug, description, icon, agent_id, unique_id)
                VALUES ('샘플 워크스페이스', 'template', '새 agent 등록 시 복제되는 템플릿', '📋', NULL, %s)
                RETURNING id
            """, (unique_id,))
            template_ws_id = cur.fetchone()['id']
            conn.commit()
            print(f"2a. Created template workspace (id={template_ws_id})")

            # Clone databases from 금토끼부동산 (ws_id=11)
            cur.execute("SELECT id, name, slug, table_name, icon, color FROM databases WHERE workspace_id = 11 ORDER BY id")
            source_dbs = cur.fetchall()

            for sdb in source_dbs:
                # Create new table name
                target_table = 'template_' + sdb['slug'].replace('-', '_')
                # Create database record
                db_unique_id = 'db' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(17))
                cur.execute("""
                    INSERT INTO databases (workspace_id, name, slug, table_name, icon, color, unique_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (template_ws_id, sdb['name'], sdb['slug'], target_table,
                      sdb['icon'], sdb['color'], db_unique_id))
                new_db_id = cur.fetchone()['id']
                conn.commit()

                # Clone table structure + data + field_definitions + views
                try:
                    clone_database_full(sdb['table_name'], target_table, sdb['id'], new_db_id)
                    print(f"2b. Cloned {sdb['name']} ({sdb['table_name']} → {target_table}, db_id={new_db_id})")
                except Exception as e:
                    print(f"2b. ERROR cloning {sdb['name']}: {e}")
                    # Clean up on failure
                    cur.execute("DELETE FROM databases WHERE id = %s", (new_db_id,))
                    conn.commit()

            # Clear data from template databases (keep structure only)
            cur.execute("SELECT table_name FROM databases WHERE workspace_id = %s", (template_ws_id,))
            for row in cur.fetchall():
                try:
                    cur.execute(f'DELETE FROM "{row["table_name"]}"')
                    print(f"2c. Cleared data from {row['table_name']}")
                except Exception as e:
                    print(f"2c. WARN: could not clear {row['table_name']}: {e}")
            conn.commit()

print(f"\nTemplate workspace id={template_ws_id}")

# ============================================================
# Step 3: Update workspace filtering logic
# ============================================================
PROPSHEET_ROUTE = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(PROPSHEET_ROUTE, 'r') as f:
    ps = f.read()

# Find _get_filtered_workspaces and update filtering
old_filter_fn = "grep placeholder"  # we need to read it first

import re
filter_match = re.search(r'def _get_filtered_workspaces\(\):.*?return \w+', ps, re.DOTALL)
if filter_match:
    old_fn = filter_match.group(0)
    # Check if agent_id filtering is already there
    if 'agent_id' not in old_fn:
        print("3. Need to update _get_filtered_workspaces - will do in next step")
    else:
        print("3. agent_id filtering already in _get_filtered_workspaces")

# Read the actual function
func_start = ps.find('def _get_filtered_workspaces():')
if func_start > 0:
    # Find function end (next def or end of indented block)
    lines = ps[func_start:].split('\n')
    func_lines = [lines[0]]
    for line in lines[1:]:
        if line.strip() and not line.startswith('    ') and not line.startswith('\t') and 'def ' in line:
            break
        func_lines.append(line)
    old_func = '\n'.join(func_lines)

    if 'agent_id' not in old_func:
        # Replace with updated version that filters by agent_id
        new_func = '''def _get_filtered_workspaces():
    """Get workspaces filtered by user role.
    - admin: all workspaces
    - agent: own agent_id workspaces
    - subagent: linked agent's workspaces
    - user: workspace_members based
    """
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    user_email = session.get('user_email', '')
    user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)

    logger.info(f"_get_filtered_workspaces: email={user_email}, user_id={user_id}, is_admin={is_admin}")

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if is_admin:
                # Admin sees all workspaces
                cur.execute("""
                    SELECT w.*, json_agg(
                        json_build_object('id', d.id, 'name', d.name, 'slug', d.slug,
                            'icon', d.icon, 'color', d.color, 'table_name', d.table_name)
                        ORDER BY d.display_order, d.id
                    ) FILTER (WHERE d.id IS NOT NULL) AS databases
                    FROM workspaces w
                    LEFT JOIN databases d ON d.workspace_id = w.id
                    GROUP BY w.id
                    ORDER BY w.display_order, w.id
                """)
                workspaces = [dict(r) for r in cur.fetchall()]
                logger.info(f"  Admin: returning {len(workspaces)} workspaces")
                return workspaces

            # Get user's role and agent_id
            cur.execute("SELECT role, agent_id FROM web_users WHERE id = %s", (user_id,))
            user_row = cur.fetchone()
            user_role = user_row['role'] if user_row else 'user'
            user_agent_id = user_row['agent_id'] if user_row else None

            if user_role in ('agent', 'subagent') and user_agent_id:
                # Agent/subagent: see workspaces with matching agent_id
                cur.execute("""
                    SELECT w.*, json_agg(
                        json_build_object('id', d.id, 'name', d.name, 'slug', d.slug,
                            'icon', d.icon, 'color', d.color, 'table_name', d.table_name)
                        ORDER BY d.display_order, d.id
                    ) FILTER (WHERE d.id IS NOT NULL) AS databases
                    FROM workspaces w
                    LEFT JOIN databases d ON d.workspace_id = w.id
                    WHERE w.agent_id = %s
                    GROUP BY w.id
                    ORDER BY w.display_order, w.id
                """, (user_agent_id,))
                workspaces = [dict(r) for r in cur.fetchall()]
                logger.info(f"  Agent/Subagent (agent_id={user_agent_id}): returning {len(workspaces)} workspaces")
                return workspaces

            # Regular user: workspace_members based
            cur.execute("""
                SELECT w.*, json_agg(
                    json_build_object('id', d.id, 'name', d.name, 'slug', d.slug,
                        'icon', d.icon, 'color', d.color, 'table_name', d.table_name)
                    ORDER BY d.display_order, d.id
                ) FILTER (WHERE d.id IS NOT NULL) AS databases
                FROM workspaces w
                JOIN workspace_members wm ON wm.workspace_id = w.id AND wm.user_id = %s
                LEFT JOIN databases d ON d.workspace_id = w.id
                GROUP BY w.id
                ORDER BY w.display_order, w.id
            """, (user_id,))
            workspaces = [dict(r) for r in cur.fetchall()]
            logger.info(f"  User (member): returning {len(workspaces)} workspaces")
            return workspaces

'''
        ps = ps.replace(old_func, new_func, 1)
        print("3. Updated _get_filtered_workspaces with agent_id filtering")

with open(PROPSHEET_ROUTE, 'w') as f:
    f.write(ps)

print("\nDone! Restart: sudo systemctl restart property-manager propsheet")
