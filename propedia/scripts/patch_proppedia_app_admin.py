#!/usr/bin/env python3
"""
proppedia app.py에 통합 admin_dashboard Blueprint 등록
서버에서 실행: python3 patch_proppedia_app_admin.py
"""
import re

APP_PATH = '/home/webapp/goldenrabbit/backend/proppedia/app.py'

with open(APP_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

changes = []

# 1. admin_dashboard import 확인/추가
# 기존에 admin_dashboard가 import되어 있으면 그대로 사용
if 'admin_dashboard' not in content:
    # routes import 라인 찾아서 admin_dashboard 추가
    old_import = 'from routes import'
    if old_import in content:
        # import 줄 끝에 admin_dashboard 추가
        import_line_match = re.search(r'from routes import (.+?)(?:\n)', content)
        if import_line_match:
            old_line = import_line_match.group(0)
            modules = import_line_match.group(1).strip()
            if not modules.endswith(','):
                new_line = old_line.rstrip('\n') + ', admin_dashboard\n'
            else:
                new_line = old_line.rstrip('\n') + ' admin_dashboard\n'
            content = content.replace(old_line, new_line)
            changes.append('1. admin_dashboard import added')
    else:
        changes.append('1. SKIP - could not find "from routes import" line')
else:
    changes.append('1. admin_dashboard already imported')

# 2. Blueprint 등록 확인/추가
if "admin_dashboard.bp" not in content and "admin_dashboard'" not in content:
    # register_blueprint 라인들 찾기
    # 마지막 register_blueprint 뒤에 추가
    last_register = content.rfind('app.register_blueprint(')
    if last_register >= 0:
        # 그 줄의 끝 찾기
        end_of_line = content.find('\n', last_register)
        if end_of_line >= 0:
            insert_point = end_of_line + 1
            new_bp = "\n# 통합 관리자 대시보드 (/admin/*)\napp.register_blueprint(admin_dashboard.bp)\n"
            content = content[:insert_point] + new_bp + content[insert_point:]
            changes.append('2. admin_dashboard Blueprint registered')
    else:
        changes.append('2. SKIP - no register_blueprint found')
else:
    changes.append('2. admin_dashboard Blueprint already registered')

# 3. Flask session secret 확인
if 'secret_key' not in content.lower() and 'SECRET_KEY' not in content:
    # app 생성 후에 secret_key 설정
    app_create = content.find("app = Flask(")
    if app_create >= 0:
        end_of_app = content.find('\n', app_create)
        if end_of_app >= 0:
            insert_point = end_of_app + 1
            secret_line = "app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.environ.get('JWT_SECRET_KEY', 'propnet-admin-session'))\n"
            content = content[:insert_point] + secret_line + content[insert_point:]
            changes.append('3. Flask secret_key added for session support')
    else:
        changes.append('3. SKIP - could not find Flask app creation')
else:
    changes.append('3. secret_key already exists')

# 4. os import 확인
if 'import os' not in content:
    content = 'import os\n' + content
    changes.append('4. import os added')
else:
    changes.append('4. import os already present')

with open(APP_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

for c in changes:
    print(c)
print(f'\nDone: {len(changes)} checks performed on {APP_PATH}')
