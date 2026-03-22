#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
정규식 백레퍼런스 버그 수정
- f'\1 ...' 를 r'\1' + f' ...' 로 변경
"""

filepath = '/home/webapp/goldenrabbit/backend/property-manager/routes/app_api.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 문제가 되는 코드:
# replacement = f'\1 {new_district} '
# \1이 SOH 제어문자로 해석됨

# 수정할 코드:
# replacement = r'\1' + f' {new_district} '
# raw string으로 백레퍼런스 처리

old_code = """    # "화성시 " 뒤에 구 이름 삽입
    pattern = r'(화성시)\s+'
    replacement = f'\\1 {new_district} '
    return re.sub(pattern, replacement, address)"""

new_code = """    # "화성시 " 뒤에 구 이름 삽입
    pattern = r'(화성시)\\s+'
    replacement = r'\\1' + f' {new_district} '
    return re.sub(pattern, replacement, address)"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("수정 완료: 정규식 백레퍼런스 버그 수정됨")
else:
    print("기존 코드를 찾을 수 없음. 현재 상태 확인...")
    # 현재 replacement 라인 찾기
    import re
    match = re.search(r'replacement = .*', content)
    if match:
        print(f"현재 replacement 라인: {repr(match.group(0))}")
