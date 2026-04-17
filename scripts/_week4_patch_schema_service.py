#!/usr/bin/env python3
"""
Week 4 — schema_service.py 내부 필드 숨김 패치.

get_table_columns의 column_name NOT IN 리스트에 다음 필드 추가:
  - bd_mgt_sn
  - coordinates_lat
  - coordinates_lon
  - coordinates_lat_orig
  - coordinates_lon_orig

이 필드들은 API 응답(SELECT *)에서는 반환되지만, PropSheet UI의 컬럼 목록에는
표시되지 않음 (사용자가 스프레드시트 뷰/편집 뷰에서 볼 수 없음).
"""
import re
import sys

TARGET = '/home/webapp/goldenrabbit/backend/property-manager/services/schema_service.py'

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# 기존: AND column_name NOT IN ('id', 'database_id', 'created_at', 'updated_at', 'fields_hash', 'synced_at', 'proptalk_audio_id')
old_line = "AND column_name NOT IN ('id', 'database_id', 'created_at', 'updated_at', 'fields_hash', 'synced_at', 'proptalk_audio_id')"
new_line = (
    "AND column_name NOT IN ("
    "'id', 'database_id', 'created_at', 'updated_at', "
    "'fields_hash', 'synced_at', 'proptalk_audio_id', "
    # Week 4: 내부 필드 숨김
    "'bd_mgt_sn', 'coordinates_lat', 'coordinates_lon', "
    "'coordinates_lat_orig', 'coordinates_lon_orig'"
    ")"
)

if old_line not in content:
    print(f'ERROR: 기존 라인을 찾을 수 없음')
    print(f'패턴: {old_line}')
    sys.exit(1)

# 중복 패치 방지
if "'bd_mgt_sn'" in content:
    print('ALREADY PATCHED: bd_mgt_sn 이미 포함됨')
    sys.exit(0)

new_content = content.replace(old_line, new_line)

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('PATCHED: schema_service.py - 내부 필드 숨김 추가 완료')
print(f'추가된 필드: bd_mgt_sn, coordinates_lat, coordinates_lon, coordinates_lat_orig, coordinates_lon_orig')
