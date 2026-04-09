#!/usr/bin/env python3
"""복제 DB 이름 매핑 추가: 샘플채팅방→채팅방, 샘플일정→일정, 샘플상담→상담신청"""

path = '/home/webapp/goldenrabbit/backend/property-manager/services/admin_dashboard_service.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. NAME_MAP 추가 (SLUG_MAP 닫는 } 다음)
old_slug_end = "        'sample-inquiry': 'inquiry',\n    }"
new_slug_end = """        'sample-inquiry': 'inquiry',
    }

    # 이름 매핑: 템플릿 DB slug → 새 DB 이름 (샘플 제거)
    NAME_MAP = {
        'sample-talk': '채팅방',
        'sample-schedule': '일정',
        'sample-inquiry': '상담신청',
    }"""

if 'NAME_MAP' not in c:
    c = c.replace(old_slug_end, new_slug_end)
    print('[1] NAME_MAP 추가')
else:
    print('[1] 이미 존재')

# 2. name 할당: tdb['name'] → NAME_MAP.get(src_slug, tdb['name'])
old_name = "                name=tdb['name'],"
new_name = "                name=NAME_MAP.get(src_slug, tdb['name']),"

if 'NAME_MAP.get' not in c:
    c = c.replace(old_name, new_name)
    print('[2] name 매핑 적용')
else:
    print('[2] 이미 적용됨')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('완료')
