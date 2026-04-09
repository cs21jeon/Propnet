#!/usr/bin/env python3
"""PropMap 생성 시 logo_url + 좌표 문제 수정"""

path = '/home/webapp/goldenrabbit/backend/property-manager/services/admin_dashboard_service.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. PropMap 생성 시 logo_url을 agent 객체 대신 req에서 직접 가져오기
old = """        propmap_result = create_propmap_page(
            slug, agency_name,
            agent.get('license_no', ''),
            agent_request.get('office_address', ''),
            logo_url=agent.get('logo_url'))"""

new = """        # logo_url: 4.5에서 agents에 저장했으므로 req에서 직접 가져옴
        _logo = agent_request.get('logo_file_path') or agent.get('logo_url')
        propmap_result = create_propmap_page(
            slug, agency_name,
            agent.get('license_no', ''),
            agent_request.get('office_address', ''),
            logo_url=_logo)"""

if old in c:
    c = c.replace(old, new)
    print('[1] logo_url 전달 수정 완료')
else:
    print('[1] 패턴 불일치')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

# 2. propmap_setup_service: 지오코딩 전 상세주소 제거 (숫자-숫자 패턴)
svc_path = '/home/webapp/goldenrabbit/backend/property-manager/services/propmap_setup_service.py'
with open(svc_path, 'r', encoding='utf-8') as f:
    s = f.read()

old_geo = "    if center_lat == 37.5665 and center_lng == 126.9780 and office_address:"
new_geo = """    if center_lat == 37.5665 and center_lng == 126.9780 and office_address:
        # 상세주소 제거 (지오코딩 정확도 향상)
        import re as _re
        clean_addr = _re.split(r'\\s+\\d{1,5}-\\d{1,5}$|\\s+\\d+층|\\s+\\d+호', office_address)[0].strip()
        if clean_addr:
            office_address = clean_addr"""

if old_geo in s and 'clean_addr' not in s:
    s = s.replace(old_geo, new_geo)
    with open(svc_path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('[2] 지오코딩 상세주소 제거 추가 완료')
else:
    print('[2] 이미 존재하거나 패턴 불일치')

# 3. 기본 로고 파일 생성 (propnet-logo.png가 없으므로)
import shutil, os
fallback_src = '/home/webapp/goldenrabbit/backend/property-manager/static/images/propsheet-logo.png'
fallback_dst = '/home/webapp/goldenrabbit/frontend/public/images/propnet-logo.png'
if os.path.exists(fallback_src) and not os.path.exists(fallback_dst):
    shutil.copy2(fallback_src, fallback_dst)
    print(f'[3] 기본 로고 복사: {fallback_dst}')
elif os.path.exists(fallback_dst):
    print('[3] 이미 존재')
else:
    # 대체: 금토끼 로고라도 복사
    alt = '/home/webapp/goldenrabbit/frontend/public/images/logo_goldenrabbit.jpg'
    if os.path.exists(alt):
        shutil.copy2(alt, fallback_dst)
        print(f'[3] 금토끼 로고로 대체 복사')
    else:
        print('[3] 로고 파일 없음')

print('완료')
