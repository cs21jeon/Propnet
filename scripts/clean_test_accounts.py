"""
테스트 계정 (sms, prop) + silverrabbit agent 완전 삭제
- cs21.jeonsms@gmail.com (propnet_user_id=8)
- cs21jeonprop@gmail.com (propnet_user_id=71)
- silverrabbit agent (agent_id=3)

안전장치: cs21.jeon@gmail.com (admin)과 goldenrabbit agent(id=1)는 절대 건드리지 않음
"""
import psycopg2
import os
import sys

env = {}
with open('/home/webapp/goldenrabbit/backend/.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v

DB_PARAMS = dict(
    dbname='goldenrabbit_db',
    user=env.get('DB_USER', 'goldenrabbit_user'),
    password=env.get('DB_PASSWORD', ''),
    host='localhost'
)
VR_PARAMS = dict(
    dbname='voiceroom',
    user=env.get('DB_USER', 'goldenrabbit_user'),
    password=env.get('DB_PASSWORD', ''),
    host='localhost'
)

TARGET_EMAILS = ('cs21.jeonsms@gmail.com', 'cs21jeonprop@gmail.com')
TARGET_PROPNET_IDS = (8, 71)
SILVERRABBIT_AGENT_ID = 3
SILVERRABBIT_WS_ID = 14
SILVERRABBIT_DB_IDS = (75, 76, 77, 78, 79, 80)

# ============================================================
# 안전 확인
# ============================================================
conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

# admin 보호 확인
cur.execute("SELECT id, email, role FROM propnet_users WHERE id IN %s", (TARGET_PROPNET_IDS,))
targets = cur.fetchall()
for t in targets:
    if t[1] == 'cs21.jeon@gmail.com':
        print("ERROR: admin 계정이 삭제 대상에 포함됨! 중단.")
        sys.exit(1)
    print(f"  삭제 대상: propnet_user id={t[0]}, email={t[1]}, role={t[2]}")

# goldenrabbit agent 보호
cur.execute("SELECT id FROM agents WHERE id = 1")
if not cur.fetchone():
    print("ERROR: goldenrabbit agent 없음! 중단.")
    sys.exit(1)

print("\n=== 삭제 시작 ===\n")

# ============================================================
# 1. goldenrabbit_db: silverrabbit PropSheet 데이터 삭제
# ============================================================
print("[1] PropSheet 데이터 삭제 (silverrabbit)")

# silverrabbit_proptalk 테이블 (있으면)
try:
    cur.execute("DROP TABLE IF EXISTS silverrabbit_proptalk")
    print("  - silverrabbit_proptalk 테이블 삭제")
except Exception as e:
    conn.rollback()
    print(f"  - silverrabbit_proptalk: {e}")

# file_attachments
cur.execute("DELETE FROM file_attachments WHERE database_id IN %s", (SILVERRABBIT_DB_IDS,))
print(f"  - file_attachments: {cur.rowcount}건 삭제")

# deleted_records
cur.execute("DELETE FROM deleted_records WHERE database_id IN %s", (SILVERRABBIT_DB_IDS,))
print(f"  - deleted_records: {cur.rowcount}건 삭제")

# field_definitions
cur.execute("DELETE FROM field_definitions WHERE database_id IN %s", (SILVERRABBIT_DB_IDS,))
print(f"  - field_definitions: {cur.rowcount}건 삭제")

# database_shares
try:
    cur.execute("DELETE FROM database_shares WHERE database_id IN %s", (SILVERRABBIT_DB_IDS,))
    print(f"  - database_shares: {cur.rowcount}건 삭제")
except Exception as e:
    conn.rollback()
    print(f"  - database_shares: {e}")

# databases
cur.execute("DELETE FROM databases WHERE id IN %s", (SILVERRABBIT_DB_IDS,))
print(f"  - databases: {cur.rowcount}건 삭제")

# workspace_members
cur.execute("DELETE FROM workspace_members WHERE workspace_id = %s", (SILVERRABBIT_WS_ID,))
print(f"  - workspace_members: {cur.rowcount}건 삭제")

# workspaces
cur.execute("DELETE FROM workspaces WHERE id = %s", (SILVERRABBIT_WS_ID,))
print(f"  - workspaces: {cur.rowcount}건 삭제")

# ============================================================
# 2. agent_requests + agents
# ============================================================
print("\n[2] Agent 데이터 삭제")

cur.execute("DELETE FROM agent_requests WHERE propnet_user_id IN %s", (TARGET_PROPNET_IDS,))
print(f"  - agent_requests: {cur.rowcount}건 삭제")

cur.execute("DELETE FROM agents WHERE id = %s", (SILVERRABBIT_AGENT_ID,))
print(f"  - agents (silverrabbit): {cur.rowcount}건 삭제")

# ============================================================
# 3. 통합 인증 데이터 삭제
# ============================================================
print("\n[3] 통합 인증 데이터 삭제")

cur.execute("DELETE FROM propnet_consents WHERE propnet_user_id IN %s", (TARGET_PROPNET_IDS,))
print(f"  - propnet_consents: {cur.rowcount}건 삭제")

cur.execute("DELETE FROM service_user_links WHERE propnet_user_id IN %s", (TARGET_PROPNET_IDS,))
print(f"  - service_user_links: {cur.rowcount}건 삭제")

# subagent_invitations (agent_id=3 또는 invitee)
try:
    cur.execute("DELETE FROM subagent_invitations WHERE agent_id = %s", (SILVERRABBIT_AGENT_ID,))
    print(f"  - subagent_invitations: {cur.rowcount}건 삭제")
except Exception as e:
    conn.rollback()
    print(f"  - subagent_invitations: {e}")

# ============================================================
# 4. 서비스별 로컬 유저 삭제
# ============================================================
print("\n[4] 서비스별 로컬 유저 삭제")

# web_users (PropSheet)
cur.execute("DELETE FROM web_users WHERE email IN %s", (TARGET_EMAILS,))
print(f"  - web_users: {cur.rowcount}건 삭제")

# app_users (Propedia)
cur.execute("DELETE FROM app_users WHERE email IN %s", (TARGET_EMAILS,))
print(f"  - app_users: {cur.rowcount}건 삭제")

# ============================================================
# 5. propnet_users 삭제
# ============================================================
print("\n[5] propnet_users 삭제")
cur.execute("DELETE FROM propnet_users WHERE id IN %s", (TARGET_PROPNET_IDS,))
print(f"  - propnet_users: {cur.rowcount}건 삭제")

conn.commit()
print("\n[goldenrabbit_db] 커밋 완료")

# ============================================================
# 6. voiceroom DB (Proptalk)
# ============================================================
print("\n[6] voiceroom 데이터 삭제")
vconn = psycopg2.connect(**VR_PARAMS)
vcur = vconn.cursor()

# voiceroom users 찾기
vcur.execute("SELECT id FROM users WHERE email IN %s", (TARGET_EMAILS,))
vr_user_ids = [r[0] for r in vcur.fetchall()]
print(f"  - voiceroom user_ids: {vr_user_ids}")

if vr_user_ids:
    vr_ids_tuple = tuple(vr_user_ids)

    # room_members
    vcur.execute("DELETE FROM room_members WHERE user_id IN %s", (vr_ids_tuple,))
    print(f"  - room_members: {vcur.rowcount}건 삭제")

    # messages
    vcur.execute("DELETE FROM messages WHERE user_id IN %s", (vr_ids_tuple,))
    print(f"  - messages: {vcur.rowcount}건 삭제")

    # user_consents
    try:
        vcur.execute("DELETE FROM user_consents WHERE user_id IN %s", (vr_ids_tuple,))
        print(f"  - user_consents: {vcur.rowcount}건 삭제")
    except Exception as e:
        vconn.rollback()
        print(f"  - user_consents: {e}")

    # device_tokens
    try:
        vcur.execute("DELETE FROM device_tokens WHERE user_id IN %s", (vr_ids_tuple,))
        print(f"  - device_tokens: {vcur.rowcount}건 삭제")
    except Exception as e:
        vconn.rollback()
        print(f"  - device_tokens: {e}")

    # proptalk room (agent silverrabbit의 room_id=13)
    # room_members 먼저 삭제 후 room 삭제
    vcur.execute("DELETE FROM room_members WHERE room_id = 13")
    print(f"  - room_members (room 13): {vcur.rowcount}건 삭제")
    vcur.execute("DELETE FROM messages WHERE room_id = 13")
    print(f"  - messages (room 13): {vcur.rowcount}건 삭제")
    vcur.execute("DELETE FROM rooms WHERE id = 13")
    print(f"  - rooms (id=13): {vcur.rowcount}건 삭제")

    # users
    vcur.execute("DELETE FROM users WHERE id IN %s", (vr_ids_tuple,))
    print(f"  - users: {vcur.rowcount}건 삭제")

vconn.commit()
print("\n[voiceroom] 커밋 완료")

# ============================================================
# 7. 검증
# ============================================================
print("\n=== 검증 ===")
cur.execute("SELECT count(*) FROM propnet_users WHERE email IN %s", (TARGET_EMAILS,))
print(f"  propnet_users 잔여: {cur.fetchone()[0]}")
cur.execute("SELECT count(*) FROM agents WHERE id = %s", (SILVERRABBIT_AGENT_ID,))
print(f"  agents(silverrabbit) 잔여: {cur.fetchone()[0]}")
cur.execute("SELECT count(*) FROM workspaces WHERE agent_id = %s", (SILVERRABBIT_AGENT_ID,))
print(f"  workspaces 잔여: {cur.fetchone()[0]}")

# admin 무사 확인
cur.execute("SELECT id, email, role FROM propnet_users WHERE email = 'cs21.jeon@gmail.com'")
admin = cur.fetchone()
print(f"\n  SAFE: admin = {admin}")
cur.execute("SELECT id, slug, is_active FROM agents WHERE id = 1")
gr = cur.fetchone()
print(f"  SAFE: goldenrabbit agent = {gr}")

cur.close()
conn.close()
vcur.close()
vconn.close()
print("\n=== 삭제 완료 ===")
