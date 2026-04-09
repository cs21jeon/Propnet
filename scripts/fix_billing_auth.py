"""billing_web.py의 로그인을 통합 인증으로 교체
- create_token() → create_access_token() (propnet_auth)
- find_or_create_propnet_user + ensure_service_account 추가
- 토큰을 통합 JWT로 발급
"""
path = '/home/webapp/goldenrabbit/chat_stt/server/billing_web.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. import 정리: ensure_service_account, check_and_accept_invitation 추가
old_import = """try:
    from propnet_auth import find_or_create_propnet_user, create_access_token as propnet_create_access_token, set_propnet_cookie
    _PROPNET_AUTH = True
except ImportError:
    _PROPNET_AUTH = False"""

new_import = """try:
    from propnet_auth import (
        find_or_create_propnet_user,
        ensure_service_account,
        check_and_accept_invitation,
        create_access_token as propnet_create_access_token,
        set_propnet_cookie,
    )
    _PROPNET_AUTH = True
except ImportError:
    _PROPNET_AUTH = False"""

content = content.replace(old_import, new_import)

# 2. billing_login POST 핸들러 교체
old_login = """            user = User.create(google_id, email, name, avatar_url)
            token = create_token(user['id'])

            # propnet_token SSO 쿠키 설정 (웹 간 인증 공유)
            resp = make_response(jsonify({'ok': True, 'token': token}))
            if _PROPNET_AUTH:
                try:
                    pu = find_or_create_propnet_user(google_id, email, name, avatar_url)
                    propnet_token = propnet_create_access_token(pu['id'], email, pu.get('role', 'user'))
                    set_propnet_cookie(resp, propnet_token)
                except Exception as _e:
                    logger.warning(f"Billing SSO cookie failed: {_e}")
            return resp"""

new_login = """            # voiceroom.users 생성/업데이트 (하위 호환)
            user = User.create(google_id, email, name, avatar_url)

            # propnet_auth 통합 인증
            if _PROPNET_AUTH:
                try:
                    pu = find_or_create_propnet_user(google_id, email, name, avatar_url)
                    ensure_service_account(pu['id'], 'proptalk')
                    check_and_accept_invitation(email)
                    # 통합 JWT 발급
                    token = propnet_create_access_token(pu['id'], email, pu.get('role', 'user'))
                    resp = make_response(jsonify({'ok': True, 'token': token}))
                    set_propnet_cookie(resp, token)
                    logger.info(f"Billing login (unified): {email} (propnet_id={pu['id']})")
                    return resp
                except Exception as _e:
                    logger.warning(f"Billing propnet_auth failed, fallback to legacy: {_e}")

            # fallback: 레거시 JWT (propnet_auth 실패 시)
            token = create_token(user['id'])
            return jsonify({'ok': True, 'token': token})"""

content = content.replace(old_login, new_login)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('billing_web.py updated')
