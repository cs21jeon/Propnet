#!/usr/bin/env python3
"""propmap_setup_service: agents DB 좌표 우선 사용 + .env 로드"""

path = '/home/webapp/goldenrabbit/backend/property-manager/services/propmap_setup_service.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. .env 로드 추가
if 'load_dotenv' not in c:
    c = c.replace('import os', 'import os\nfrom dotenv import load_dotenv\nload_dotenv(\'/home/webapp/goldenrabbit/backend/.env\')')
    print('[1] .env 로드 추가')

# 2. 좌표 로직: agents DB 우선 → 지오코딩 fallback
old_geo = """    # 2. 주소 → 좌표 변환 (Kakao 지오코딩)
    center_lat, center_lng = 37.5665, 126.9780  # 서울 기본값
    if office_address:"""

new_geo = """    # 2. 좌표: agents DB 우선 → Kakao 지오코딩 fallback → 서울 기본값
    center_lat, center_lng = 37.5665, 126.9780  # 서울 기본값
    try:
        from services.database_service import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT latitude, longitude FROM agents WHERE slug = %s", (agent_slug,))
                row = cur.fetchone()
                if row and row[0] and row[1]:
                    center_lat, center_lng = float(row[0]), float(row[1])
                    logger.info(f"Using DB coords for {agent_slug}: {center_lat}, {center_lng}")
    except Exception as e:
        logger.warning(f"DB coord lookup failed: {e}")

    if center_lat == 37.5665 and center_lng == 126.9780 and office_address:"""

if old_geo in c:
    c = c.replace(old_geo, new_geo)
    print('[2] DB 좌표 우선 로직 추가')
else:
    print('[2] 패턴 불일치')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('완료')
