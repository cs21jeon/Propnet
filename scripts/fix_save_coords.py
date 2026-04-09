#!/usr/bin/env python3
"""승인 시 PropMap 생성 후 좌표를 agents에 저장"""

path = '/home/webapp/goldenrabbit/backend/property-manager/services/admin_dashboard_service.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old = """        from services.propmap_setup_service import create_propmap_page
        results['propmap'] = create_propmap_page(
            slug, agency_name,
            agent.get('license_no', ''),
            agent_request.get('office_address', ''))
        logger.info(f"[Setup] PropMap OK: {slug}")"""

new = """        from services.propmap_setup_service import create_propmap_page
        propmap_result = create_propmap_page(
            slug, agency_name,
            agent.get('license_no', ''),
            agent_request.get('office_address', ''))
        results['propmap'] = propmap_result
        # 좌표를 agents 테이블에 저장
        if propmap_result and 'center' in propmap_result:
            lat, lng = propmap_result['center']
            try:
                from propnet_auth.db import execute as _exec
                _exec("UPDATE agents SET latitude = %s, longitude = %s WHERE id = %s",
                      (lat, lng, agent['id']))
                logger.info(f"[Setup] Agent coords saved: {lat}, {lng}")
            except Exception as coord_err:
                logger.warning(f"[Setup] Coord save failed: {coord_err}")
        logger.info(f"[Setup] PropMap OK: {slug}")"""

if old in c:
    c = c.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('좌표 저장 로직 추가 완료')
else:
    print('패턴 불일치')
