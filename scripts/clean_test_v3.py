"""테스트 계정 삭제 v3 - FK 순서 준수"""
import psycopg2, os

env = {}
with open('/home/webapp/goldenrabbit/backend/.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v

TARGET_EMAILS = ('cs21.jeonsms@gmail.com', 'cs21jeonprop@gmail.com')

conn = psycopg2.connect(dbname='goldenrabbit_db', user=env.get('DB_USER','goldenrabbit_user'), password=env.get('DB_PASSWORD',''), host='localhost')
cur = conn.cursor()

cur.execute("SELECT id FROM propnet_users WHERE email IN %s", (TARGET_EMAILS,))
pn_ids = tuple(r[0] for r in cur.fetchall())
print(f'propnet_user_ids: {pn_ids}')

if pn_ids:
    # FK 자식 먼저 삭제
    cur.execute("DELETE FROM propnet_consents WHERE propnet_user_id IN %s", (pn_ids,))
    print(f'propnet_consents: {cur.rowcount}')
    cur.execute("DELETE FROM service_user_links WHERE propnet_user_id IN %s", (pn_ids,))
    print(f'service_user_links: {cur.rowcount}')
    cur.execute("DELETE FROM agent_requests WHERE propnet_user_id IN %s", (pn_ids,))
    print(f'agent_requests: {cur.rowcount}')
    # app_users, web_users (propnet_user_id FK)
    cur.execute("DELETE FROM app_users WHERE email IN %s", (TARGET_EMAILS,))
    print(f'app_users: {cur.rowcount}')
    cur.execute("DELETE FROM web_users WHERE email IN %s", (TARGET_EMAILS,))
    print(f'web_users: {cur.rowcount}')
    # propnet_users 마지막
    cur.execute("DELETE FROM propnet_users WHERE id IN %s", (pn_ids,))
    print(f'propnet_users: {cur.rowcount}')
else:
    cur.execute("DELETE FROM app_users WHERE email IN %s", (TARGET_EMAILS,))
    print(f'app_users: {cur.rowcount}')
    cur.execute("DELETE FROM web_users WHERE email IN %s", (TARGET_EMAILS,))
    print(f'web_users: {cur.rowcount}')

conn.commit()
print('[goldenrabbit_db] done')

# voiceroom
venv = {}
with open('/home/webapp/goldenrabbit/chat_stt/server/.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            venv[k] = v

vconn = psycopg2.connect(dbname='voiceroom', user=venv.get('DB_USER','goldenrabbit_user'), password=venv.get('DB_PASS',''), host='localhost')
vcur = vconn.cursor()

vcur.execute("SELECT id FROM users WHERE email IN %s", (TARGET_EMAILS,))
vr_ids = tuple(r[0] for r in vcur.fetchall())
print(f'\nvoiceroom user_ids: {vr_ids}')

if vr_ids:
    vcur.execute("DELETE FROM usage_logs WHERE audio_file_id IN (SELECT id FROM audio_files WHERE user_id IN %s)", (vr_ids,))
    vcur.execute("DELETE FROM audio_files WHERE user_id IN %s", (vr_ids,))
    vcur.execute("DELETE FROM room_members WHERE user_id IN %s", (vr_ids,))
    vcur.execute("DELETE FROM messages WHERE user_id IN %s", (vr_ids,))
    try:
        vcur.execute("DELETE FROM user_consents WHERE user_id IN %s", (vr_ids,))
    except: vconn.rollback()
    try:
        vcur.execute("DELETE FROM device_tokens WHERE user_id IN %s", (vr_ids,))
    except: vconn.rollback()
    vcur.execute("DELETE FROM users WHERE id IN %s", (vr_ids,))
    print(f'voiceroom users deleted: {vcur.rowcount}')

vconn.commit()

# 검증
cur.execute("SELECT count(*) FROM propnet_users WHERE email IN %s", (TARGET_EMAILS,))
print(f'\npropnet_users: {cur.fetchone()[0]}')
vcur.execute("SELECT count(*) FROM users WHERE email IN %s", (TARGET_EMAILS,))
print(f'voiceroom.users: {vcur.fetchone()[0]}')
cur.execute("SELECT id, email, role FROM propnet_users WHERE email = 'cs21.jeon@gmail.com'")
print(f'admin: {cur.fetchone()}')

cur.close(); conn.close(); vcur.close(); vconn.close()
print('\n테스트 계정 삭제 완료')
