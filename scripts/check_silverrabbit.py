"""silverrabbit agent 관련 전체 데이터 조회"""
import psycopg2, os

env = {}
with open('/home/webapp/goldenrabbit/backend/.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v

conn = psycopg2.connect(
    dbname='goldenrabbit_db',
    user=env.get('DB_USER', 'goldenrabbit_user'),
    password=env.get('DB_PASSWORD', ''),
    host='localhost'
)
cur = conn.cursor()

print('=== agents (silverrabbit) ===')
cur.execute("SELECT * FROM agents WHERE id = 3")
cols = [d[0] for d in cur.description]
for r in cur.fetchall():
    print(dict(zip(cols, r)))

print('\n=== workspaces ===')
cur.execute("SELECT id, name, slug, agent_id FROM workspaces WHERE agent_id = 3 OR slug LIKE 'silverrabbit%%'")
for r in cur.fetchall():
    print(r)

print('\n=== workspace_members ===')
cur.execute("SELECT wm.workspace_id, wm.user_id, wm.role FROM workspace_members wm JOIN workspaces w ON w.id = wm.workspace_id WHERE w.agent_id = 3")
for r in cur.fetchall():
    print(r)

print('\n=== databases ===')
cur.execute("SELECT d.id, d.name, d.workspace_id FROM databases d JOIN workspaces w ON w.id = d.workspace_id WHERE w.agent_id = 3")
for r in cur.fetchall():
    print(r)

print('\n=== propnet_users (agent_id=3) ===')
cur.execute("SELECT id, email, name, role, agent_id, is_active FROM propnet_users WHERE agent_id = 3")
for r in cur.fetchall():
    print(r)

print('\n=== web_users linked ===')
cur.execute("SELECT wu.id, wu.email, wu.is_active FROM web_users wu JOIN service_user_links sl ON sl.local_user_id = wu.id AND sl.service = 'propsheet' JOIN propnet_users pu ON pu.id = sl.propnet_user_id WHERE pu.agent_id = 3")
for r in cur.fetchall():
    print(r)

print('\n=== subagent_invitations ===')
cur.execute("SELECT id, email, status FROM subagent_invitations WHERE agent_id = 3")
for r in cur.fetchall():
    print(r)

print('\n=== records count per DB ===')
cur.execute("SELECT d.id, d.name, (SELECT count(*) FROM records r WHERE r.database_id = d.id) FROM databases d JOIN workspaces w ON w.id = d.workspace_id WHERE w.agent_id = 3")
for r in cur.fetchall():
    print(r)

cur.close()
conn.close()
