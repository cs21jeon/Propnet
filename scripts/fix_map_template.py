#!/usr/bin/env python3
"""
1. map.html 템플릿 생성 (_template/map.html)
2. propmap_setup_service: 복사 대신 치환 후 저장
3. silverrabbit map.html 재생성
"""
import os, shutil

# 1. 원본 map.html → _template/map.html (치환 변수 포함)
src = '/home/webapp/goldenrabbit/frontend/public/map.html'
tpl = '/home/webapp/goldenrabbit/frontend/public/propmap/_template/map.html'

with open(src, 'r', encoding='utf-8') as f:
    c = f.read()

# API에 agent_slug 추가
c = c.replace(
    "fetch('/propsheet/api/propsheet/map-data?status=%EB%93%B1%EB%A1%9D&_t=' + Date.now())",
    "fetch('/propsheet/api/propsheet/map-data?agent_slug={{AGENT_SLUG}}&status=%EB%93%B1%EB%A1%9D&_t=' + Date.now())"
)

# 지도 중심 좌표 템플릿화
c = c.replace(
    'center: new kakao.maps.LatLng(37.4834458778777, 126.970207234818)',
    'center: new kakao.maps.LatLng({{CENTER_LAT}}, {{CENTER_LNG}})'
)

with open(tpl, 'w', encoding='utf-8') as f:
    f.write(c)
print(f'[1] map.html 템플릿 생성: {tpl}')

# 2. propmap_setup_service: shutil.copy → 치환 후 저장
svc_path = '/home/webapp/goldenrabbit/backend/property-manager/services/propmap_setup_service.py'
with open(svc_path, 'r', encoding='utf-8') as f:
    s = f.read()

old_map = """    # map.html도 복사 (iframe용 지도)
    import shutil
    map_src = os.path.join(os.path.dirname(TEMPLATE_PATH), 'map.html')
    map_orig = '/home/webapp/goldenrabbit/frontend/public/map.html'
    map_dst = os.path.join(target_dir, 'map.html')
    if os.path.exists(map_src):
        shutil.copy2(map_src, map_dst)
    elif os.path.exists(map_orig):
        shutil.copy2(map_orig, map_dst)"""

new_map = """    # map.html도 생성 (iframe용 지도 - 템플릿 치환)
    map_tpl = os.path.join(os.path.dirname(TEMPLATE_PATH), 'map.html')
    map_dst = os.path.join(target_dir, 'map.html')
    if os.path.exists(map_tpl):
        with open(map_tpl, 'r', encoding='utf-8') as mf:
            map_html = mf.read()
        map_html = map_html.replace('{{AGENT_SLUG}}', agent_slug)
        map_html = map_html.replace('{{CENTER_LAT}}', str(center_lat))
        map_html = map_html.replace('{{CENTER_LNG}}', str(center_lng))
        with open(map_dst, 'w', encoding='utf-8') as mf:
            mf.write(map_html)"""

if old_map in s:
    s = s.replace(old_map, new_map)
    with open(svc_path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('[2] propmap_setup_service map.html 치환 로직 수정')
else:
    print('[2] 패턴 불일치')

# 3. silverrabbit + goldenrabbit map.html 재생성
for slug, lat, lng in [
    ('silverrabbit', '37.2102285256765', '127.112261752152'),
    ('goldenrabbit', '37.4834458778777', '126.970207234818'),
]:
    with open(tpl, 'r', encoding='utf-8') as f:
        m = f.read()
    m = m.replace('{{AGENT_SLUG}}', slug)
    m = m.replace('{{CENTER_LAT}}', lat)
    m = m.replace('{{CENTER_LNG}}', lng)
    dst = f'/home/webapp/goldenrabbit/frontend/public/propmap/{slug}/map.html'
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(m)
    print(f'[3] {slug}/map.html 재생성 완료')

print('완료')
