#!/usr/bin/env python3
"""propmap_setup_service: map.html도 자동 복사 + 좌표 업데이트"""

path = '/home/webapp/goldenrabbit/backend/property-manager/services/propmap_setup_service.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old = """    logger.info(f"PropMap page created: {target_path}")
    return {'path': target_path, 'center': [center_lat, center_lng]}"""

new = """    # map.html도 복사 (iframe용 지도)
    import shutil
    map_src = os.path.join(os.path.dirname(TEMPLATE_PATH), 'map.html')
    map_orig = '/home/webapp/goldenrabbit/frontend/public/map.html'
    map_dst = os.path.join(target_dir, 'map.html')
    if os.path.exists(map_src):
        shutil.copy2(map_src, map_dst)
    elif os.path.exists(map_orig):
        shutil.copy2(map_orig, map_dst)

    logger.info(f"PropMap page created: {target_path}")
    return {'path': target_path, 'center': [center_lat, center_lng]}"""

if old in c:
    c = c.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('map.html 자동 복사 추가 완료')
else:
    print('패턴 불일치')
