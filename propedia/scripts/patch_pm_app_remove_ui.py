path = '/home/webapp/goldenrabbit/backend/property-manager/app.py'
with open(path, 'r') as f:
    content = f.read()

changes = 0

# 1. Remove PM-only blueprint imports and registrations
# Remove auth, search, property_route from import line
old_import = "from routes import search, property as property_route, airtable, auth, search_map, blog, instagram, address_finder, geocoding, database, workspace, propsheet, app_api, app_auth, app_user_data, admin_dashboard, workspace_members, oauth, share, propnet_api"
new_import = "from routes import airtable, search_map, blog, instagram, address_finder, geocoding, database, workspace, propsheet, app_api, app_auth, app_user_data, admin_dashboard, workspace_members, oauth, share, propnet_api"
if old_import in content:
    content = content.replace(old_import, new_import)
    changes += 1
    print('1. Import line updated')

# Remove login_required import (PM auth)
old_login_req = "\nfrom routes.auth import login_required\n"
new_login_req = "\n"
if old_login_req in content:
    content = content.replace(old_login_req, new_login_req)
    changes += 1
    print('2. login_required import removed')

# Remove PM blueprint registrations
old_bp = """# Property Manager routes (기존 부동산 조회 서비스)
app.register_blueprint(auth.bp)
app.register_blueprint(search.bp, url_prefix='/api')
app.register_blueprint(property_route.bp, url_prefix='/api')
app.register_blueprint(airtable.bp, url_prefix='/api')
app.register_blueprint(search_map.bp, url_prefix='/api')
app.register_blueprint(blog.bp, url_prefix='/api')
app.register_blueprint(instagram.instagram_bp)
app.register_blueprint(address_finder.bp, url_prefix='/api')
app.register_blueprint(geocoding.bp, url_prefix='/api')
app.register_blueprint(database.bp, url_prefix='/api')
app.register_blueprint(workspace.bp, url_prefix='/api')"""

new_bp = """# API routes (Property Manager UI 제거, API만 유지)
app.register_blueprint(airtable.bp, url_prefix='/api')
app.register_blueprint(search_map.bp, url_prefix='/api')
app.register_blueprint(blog.bp, url_prefix='/api')
app.register_blueprint(instagram.instagram_bp)
app.register_blueprint(address_finder.bp, url_prefix='/api')
app.register_blueprint(geocoding.bp, url_prefix='/api')
app.register_blueprint(database.bp, url_prefix='/api')
app.register_blueprint(workspace.bp, url_prefix='/api')"""

if old_bp in content:
    content = content.replace(old_bp, new_bp)
    changes += 1
    print('3. PM blueprint registrations removed (auth.bp, search.bp, property_route.bp)')

# 2. Remove / route (PM index) - keep propsheet part
old_index = """@app.route('/')
def index():
    prefix = request.environ.get('SCRIPT_NAME', '')
    if prefix == '/propsheet':
        # Propsheet landing page
        if session.get('logged_in'):
            return redirect('/propsheet/workspaces')
        error = request.args.get('error')
        return render_template('propsheet/landing.html', error=error)
    # Property Manager index
    if not session.get('logged_in'):
        return redirect('/propsheet/auth/google')
    return render_template('index.html')"""

new_index = """@app.route('/')
def index():
    prefix = request.environ.get('SCRIPT_NAME', '')
    if prefix == '/propsheet':
        # Propsheet landing page
        if session.get('logged_in'):
            return redirect('/propsheet/workspaces')
        error = request.args.get('error')
        return render_template('propsheet/landing.html', error=error)
    # Property Manager 제거됨 - PropSheet으로 리다이렉트
    return redirect('/propsheet/')"""

if old_index in content:
    content = content.replace(old_index, new_index)
    changes += 1
    print('4. / route updated (PM index -> redirect to propsheet)')

# 3. Remove /public/ and /address-finder routes
old_public = """@app.route('/public/')
def public_index():
    \"\"\"공개용 조회 페이지 (로그인 불필요, 저장 기능 없음)\"\"\"
    return render_template('public.html')

@app.route('/address-finder')
def address_finder_page():
    \"\"\"도로명 + 연면적으로 주소 찾기 (로그인 불필요)\"\"\"
    return render_template('address_finder.html')"""

new_public = """# /public/ 및 /address-finder 제거됨 (2026-03-16)"""

if old_public in content:
    content = content.replace(old_public, new_public)
    changes += 1
    print('5. /public/ and /address-finder routes removed')

with open(path, 'w') as f:
    f.write(content)
print(f'DONE: {changes} changes applied')
