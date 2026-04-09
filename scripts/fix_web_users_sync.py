#!/usr/bin/env python3
"""승인 시 web_users도 agent role + agent_id 업데이트"""

path = '/home/webapp/goldenrabbit/backend/property-manager/services/admin_dashboard_service.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old = """        # 3. propnet_users.agent_id 연결
        if agent:
            execute(
                "UPDATE propnet_users SET agent_id = %s WHERE id = %s",
                (agent['id'], user_id)
            )"""

new = """        # 3. propnet_users.agent_id 연결
        if agent:
            execute(
                "UPDATE propnet_users SET agent_id = %s WHERE id = %s",
                (agent['id'], user_id)
            )

            # 3.5. web_users(PropSheet 로그인)도 agent 연결
            try:
                execute(
                    "UPDATE web_users SET role = 'agent', agent_id = %s WHERE email = %s",
                    (agent['id'], user['email'])
                )
                logger.info(f"[Admin] web_users updated: email={user['email']} agent_id={agent['id']}")
            except Exception as e:
                logger.warning(f"[Admin] web_users update failed: {e}")"""

if old in c:
    c = c.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('web_users 동기화 추가 완료')
else:
    print('패턴 불일치')
