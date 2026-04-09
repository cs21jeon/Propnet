#!/usr/bin/env python3
"""
Nginx 설정에 /admin/* -> port 5010 라우팅 추가
서버에서 실행: python3 patch_nginx_admin.py

주의: 실행 후 반드시
  sudo nginx -t && sudo systemctl reload nginx
"""

NGINX_PATH = '/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf'
NGINX_ENABLED = '/etc/nginx/sites-enabled/goldenrabbit'

ADMIN_BLOCK = '''
    # ── 통합 관리자 대시보드 (/admin/*) → port 5010 ──
    location /admin/ {
        proxy_pass http://127.0.0.1:5010/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
'''

for path in [NGINX_PATH, NGINX_ENABLED]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f'SKIP: {path} not found')
        continue

    if '/admin/' in content and 'port 5010' in content:
        print(f'SKIP: {path} already has /admin/ block')
        continue

    # /app/ 블록 앞에 삽입
    anchor = '    location /app/'
    if anchor in content:
        content = content.replace(anchor, ADMIN_BLOCK + anchor)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'UPDATED: {path} - /admin/ block added before /app/')
    else:
        # fallback: server { 블록 끝 근처에 추가
        # 마지막 location 블록 앞에
        last_location = content.rfind('    location ')
        if last_location >= 0:
            content = content[:last_location] + ADMIN_BLOCK + content[last_location:]
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'UPDATED: {path} - /admin/ block added (fallback position)')
        else:
            print(f'ERROR: Could not find insertion point in {path}')

print('\nNext: sudo nginx -t && sudo systemctl reload nginx')
