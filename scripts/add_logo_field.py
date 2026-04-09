#!/usr/bin/env python3
"""agent 등록 폼에 로고 업로드 필드 추가 + register.py에 로고 처리 추가"""

# 1. 템플릿에 로고 필드 추가
tpl_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/register/step4_agent.html'
with open(tpl_path, 'r', encoding='utf-8') as f:
    c = f.read()

# 등록증 파일 블록 끝 찾기 (제출 버튼 앞)
logo_field = '''
        <!-- 로고 이미지 (선택) -->
        <div class="form-group">
            <label>사무소 로고 <span style="color:#888;font-size:12px;font-weight:normal;">(선택사항)</span></label>
            <small style="color:#666;font-size:12px;">매물지도에 표시됩니다. 없으면 기본 로고가 사용됩니다.</small>
            <div style="display:flex;align-items:center;gap:12px;margin-top:8px;">
                <img id="logoPreview" src="" alt="" style="width:48px;height:48px;border-radius:8px;object-fit:cover;border:1px solid #ddd;display:none;">
                <div style="flex:1;">
                    <input type="file" id="logo_file" name="logo_file"
                           accept=".jpg,.jpeg,.png,.webp"
                           @change="handleLogoFile($event)"
                           style="display:none">
                    <button type="button" onclick="document.getElementById('logo_file').click()"
                            style="padding:6px 14px;border:1px solid #ccc;border-radius:6px;font-size:13px;cursor:pointer;background:white;">
                        로고 선택
                    </button>
                    <span id="logoFileName" style="margin-left:8px;font-size:12px;color:#666;" x-text="logoFileName || ''"></span>
                </div>
            </div>
        </div>
'''

# 제출 버튼 앞에 삽입
submit_marker = '        <button type="submit"'
if '로고 이미지' not in c and submit_marker in c:
    c = c.replace(submit_marker, logo_field + '\n        <button type="submit"')
    print('[1] 로고 필드 추가 완료')
else:
    print('[1] 이미 존재하거나 마커 없음')

# Alpine data에 logoFileName 추가
if 'logoFileName' not in c.split('return {')[1].split('}')[0] if 'return {' in c else '':
    c = c.replace("addressDetail: '',", "addressDetail: '',\n                logoFileName: '',")
    print('[2] logoFileName data 추가')

# handleLogoFile 함수 추가
logo_js = '''
            handleLogoFile(event) {
                const file = event.target.files[0];
                if (file) {
                    this.logoFileName = file.name;
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        var img = document.getElementById('logoPreview');
                        img.src = e.target.result;
                        img.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
            },
'''

# handleFile 함수 앞에 추가
if 'handleLogoFile' not in c:
    c = c.replace('            handleFile(event) {', logo_js + '            handleFile(event) {')
    print('[3] handleLogoFile JS 추가')

with open(tpl_path, 'w', encoding='utf-8') as f:
    f.write(c)

# 2. register.py에 로고 파일 처리 추가
reg_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/register.py'
with open(reg_path, 'r', encoding='utf-8') as f:
    r = f.read()

# 등록증 파일 처리 후에 로고 처리 추가
old_insert = """        # agent_requests 테이블에 INSERT
        execute(
            \"\"\"INSERT INTO agent_requests
               (propnet_user_id, agent_name, agent_slug, representative_name,
                phone, office_address, license_no, license_file_path, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')\"\"\",
            (propnet_user_id, company_name, slug, representative,
             phone, address, license_no, registration_cert)
        )"""

new_insert = """        # 로고 파일 처리 (선택사항)
        logo_path = None
        logo_file = request.files.get('logo_file')
        if logo_file and logo_file.filename:
            import uuid as _uuid
            ext = logo_file.filename.rsplit('.', 1)[-1].lower() if '.' in logo_file.filename else 'png'
            logo_name = f'logo_{_uuid.uuid4().hex[:8]}.{ext}'
            logo_filepath = upload_dir / logo_name
            logo_file.save(str(logo_filepath))
            logo_path = f'/uploads/agent_requests/{propnet_user_id}/{logo_name}'

        # agent_requests 테이블에 INSERT
        execute(
            \"\"\"INSERT INTO agent_requests
               (propnet_user_id, agent_name, agent_slug, representative_name,
                phone, office_address, license_no, license_file_path, logo_file_path, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')\"\"\",
            (propnet_user_id, company_name, slug, representative,
             phone, address, license_no, registration_cert, logo_path)
        )"""

if old_insert in r:
    r = r.replace(old_insert, new_insert)
    with open(reg_path, 'w', encoding='utf-8') as f:
        f.write(r)
    print('[4] register.py 로고 처리 추가 완료')
else:
    print('[4] register.py 패턴 불일치')

# 3. 승인 시 logo_url을 agents에 저장
# admin_dashboard_service.py의 approve에서 logo_file_path를 agents.logo_url로 복사
svc_path = '/home/webapp/goldenrabbit/backend/property-manager/services/admin_dashboard_service.py'
with open(svc_path, 'r', encoding='utf-8') as f:
    s = f.read()

# agents INSERT에 logo_url 추가 - approve_agent_request 내 INSERT INTO agents
if 'logo_url' not in s.split('INSERT INTO agents')[1].split('RETURNING')[0] if 'INSERT INTO agents' in s else '':
    # 복잡하므로 승인 후 별도 UPDATE로 처리
    old_setup = "        # 5. 전체 환경 자동 셋업"
    new_setup = """        # 4.5. 로고 URL을 agents에 저장
        logo_url = req.get('logo_file_path')
        if logo_url and agent:
            try:
                execute("UPDATE agents SET logo_url = %s WHERE id = %s", (logo_url, agent['id']))
            except Exception:
                pass

        # 5. 전체 환경 자동 셋업"""
    if old_setup in s:
        s = s.replace(old_setup, new_setup)
        with open(svc_path, 'w', encoding='utf-8') as f:
            f.write(s)
        print('[5] 승인 시 logo_url 저장 추가')
    else:
        print('[5] 마커 없음')
else:
    print('[5] 이미 logo_url 처리 있음')

# 4. PropMap 생성 시 logo_url 전달
with open(svc_path, 'r', encoding='utf-8') as f:
    s = f.read()

old_propmap_call = """        propmap_result = create_propmap_page(
            slug, agency_name,
            agent.get('license_no', ''),
            agent_request.get('office_address', ''))"""

new_propmap_call = """        propmap_result = create_propmap_page(
            slug, agency_name,
            agent.get('license_no', ''),
            agent_request.get('office_address', ''),
            logo_url=agent.get('logo_url'))"""

if old_propmap_call in s:
    s = s.replace(old_propmap_call, new_propmap_call)
    with open(svc_path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('[6] PropMap 생성에 logo_url 전달 추가')
else:
    print('[6] 패턴 불일치')

print('\n완료!')
