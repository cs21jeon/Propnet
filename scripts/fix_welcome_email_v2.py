#!/usr/bin/env python3
"""환영 이메일 수정: Play Store ID 수정 + 가이드 링크 수정"""
import re

path = '/home/webapp/goldenrabbit/backend/property-manager/services/admin_dashboard_service.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Play Store 앱 ID 수정
content = content.replace(
    'play.google.com/store/apps/details?id=com.propnet.propedia',
    'play.google.com/store/apps/details?id=com.proppedia.app'
)
content = content.replace(
    'play.google.com/store/apps/details?id=com.propnet.proptalk',
    'play.google.com/store/apps/details?id=biz.goldenrabbit.proptalk'
)

# 2. 가이드 링크: proppedia 제거, proptalk → /proptalk/guide
old_guide = '''<p style="font-size:11px;margin:0;">
            <a href="https://propnet.kr/propsheet/guide" style="color:#2962FF;text-decoration:none;">PropSheet</a>
            <span style="color:#ccc;margin:0 3px;">&middot;</span>
            <a href="https://propnet.kr/app/guide" style="color:#2962FF;text-decoration:none;">Proppedia</a>
            <span style="color:#ccc;margin:0 3px;">&middot;</span>
            <a href="https://propnet.kr/proptalk/" style="color:#2962FF;text-decoration:none;">Proptalk</a>
          </p>'''

new_guide = '''<p style="font-size:11px;margin:0;">
            <a href="https://propnet.kr/propsheet/guide" style="color:#2962FF;text-decoration:none;">PropSheet 가이드</a>
            <span style="color:#ccc;margin:0 3px;">&middot;</span>
            <a href="https://propnet.kr/proptalk/guide" style="color:#2962FF;text-decoration:none;">Proptalk 가이드</a>
          </p>'''

content = content.replace(old_guide, new_guide)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed: Play Store IDs + guide links')
