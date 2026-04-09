"""테스트 계정 삭제 전 전체 현황 파악"""
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

# voiceroom DB 연결
vconn = psycopg2.connect(
    dbname='voiceroom',
    user=env.get('DB_USER', 'goldenrabbit_user'),
    password=env.get('DB_PASSWORD', ''),
    host='localhost'
)
vcur = vconn.cursor()

target_emails = ['cs21.jeonsms@gmail.com', 'cs21jeonprop@gmail.com']

print('=== propnet_users ===')
cur.execute("SELECT id, email, name, role, agent_id, is_active FROM propnet_users WHERE email IN %s", (tuple(target_emails),))
for r in cur.fetchall():
    print(r)

print('\n=== service_user_links ===')
cur.execute("SELECT sl.* FROM service_user_links sl JOIN propnet_users pu ON pu.id = sl.propnet_user_id WHERE pu.email IN %s", (tuple(target_emails),))
for r in cur.fetchall():
    print(r)

print('\n=== propnet_consents ===')
cur.execute("SELECT pc.id, pc.propnet_user_id, pc.consent_type FROM propnet_consents pc JOIN propnet_users pu ON pu.id = pc.propnet_user_id WHERE pu.email IN %s", (tuple(target_emails),))
for r in cur.fetchall():
    print(r)

print('\n=== web_users ===')
cur.execute("SELECT id, email, is_active FROM web_users WHERE email IN %s", (tuple(target_emails),))
for r in cur.fetchall():
    print(r)

print('\n=== app_users ===')
cur.execute("SELECT id, email, is_active FROM app_users WHERE email IN %s", (tuple(target_emails),))
for r in cur.fetchall():
    print(r)

print('\n=== agent_requests ===')
cur.execute("SELECT id, propnet_user_id, agent_name, agent_slug, status FROM agent_requests WHERE propnet_user_id IN (SELECT id FROM propnet_users WHERE email IN %s)", (tuple(target_emails),))
for r in cur.fetchall():
    print(r)

print('\n=== agents (silverrabbit) ===')
cur.execute("SELECT id, name, slug, is_active FROM agents WHERE slug = 'silverrabbit'")
for r in cur.fetchall():
    print(r)

print('\n=== workspaces (agent_id=3) ===')
cur.execute("SELECT id, name, slug FROM workspaces WHERE agent_id = 3")
for r in cur.fetchall():
    print(r)

print('\n=== databases (workspace agent_id=3) ===')
cur.execute("SELECT d.id, d.name, (SELECT count(*) FROM records r WHERE r.database_id = d.id) as rec_count FROM databases d JOIN workspaces w ON w.id = d.workspace_id WHERE w.agent_id = 3")
for r in cur.fetchall():
    print(r)

print('\n=== file_attachments (silverrabbit DBs) ===')
cur.execute("SELECT count(*) FROM file_attachments fa WHERE fa.database_id IN (SELECT d.id FROM databases d JOIN workspaces w ON w.id = d.workspace_id WHERE w.agent_id = 3)")
print(cur.fetchone())

print('\n=== voiceroom.users ===')
vcur.execute("SELECT id, email, name FROM users WHERE email IN %s", (tuple(target_emails),))
for r in vcur.fetchall():
    print(r)

print('\n=== voiceroom.room_members ===')
vcur.execute("SELECT rm.room_id, rm.user_id FROM room_members rm JOIN users u ON u.id = rm.user_id WHERE u.email IN %s", (tuple(target_emails),))
for r in vcur.fetchall():
    print(r)

print('\n=== proptalk_room (agent silverrabbit) ===')
cur.execute("SELECT proptalk_room_id, proptalk_invite_code FROM agents WHERE id = 3")
print(cur.fetchone())

# 안전 확인: goldenrabbit/admin 유저는 건드리지 않음
print('\n=== SAFE CHECK: admin user ===')
cur.execute("SELECT id, email, role FROM propnet_users WHERE email = 'cs21.jeon@gmail.com'")
print(cur.fetchone())

cur.close()
conn.close()
vcur.close()
vconn.close()
