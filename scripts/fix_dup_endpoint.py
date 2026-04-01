#!/usr/bin/env python3
"""Remove duplicate property_share_page from propnet_api.py"""

FILE = '/home/webapp/goldenrabbit/backend/property-manager/routes/propnet_api.py'

with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the second occurrence of the duplicate block
# It starts at "# ===== SNS 공유용 동적 메타 태그 엔드포인트 =====" (around line 957)
# and ends before "# ===== 블로그 관련 API =====" (around line 1068)

first_sns_idx = None
second_sns_idx = None
blog_api_idx = None

for i, line in enumerate(lines):
    if '# ===== SNS 공유용 동적 메타 태그 엔드포인트 =====' in line:
        if first_sns_idx is None:
            first_sns_idx = i
        else:
            second_sns_idx = i
    if '# ===== 블로그 관련 API =====' in line:
        blog_api_idx = i

if second_sns_idx is not None and blog_api_idx is not None:
    # Remove lines from second_sns_idx to blog_api_idx (exclusive)
    print(f"Removing duplicate block: lines {second_sns_idx+1} to {blog_api_idx}")
    new_lines = lines[:second_sns_idx] + lines[blog_api_idx:]
    with open(FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"SUCCESS: Removed {blog_api_idx - second_sns_idx} lines")
else:
    print(f"first_sns={first_sns_idx}, second_sns={second_sns_idx}, blog_api={blog_api_idx}")
    print("Could not determine block to remove")
