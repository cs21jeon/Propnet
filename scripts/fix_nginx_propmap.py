#!/usr/bin/env python3
"""Nginx: propmap/goldenrabbit를 새 템플릿 경로로 변경 + 범용 propmap 라우트 추가"""

path = '/etc/nginx/sites-enabled/propnet'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. 기존 goldenrabbit 전용 블록을 범용 propmap 패턴으로 교체
old = """    # /propmap/goldenrabbit \xe2\x86\x92 \xea\xb8\x88\xed\x86\xa0\xeb\x81\xbc\xeb\xb6\x80\xeb\x8f\x99\xec\x82\xb0 \xed\x99\x88\xed\x8e\x98\xec\x9d\xb4\xec\xa7\x80
    location = /propmap/goldenrabbit {
        return 301 /propmap/goldenrabbit/;
    }

    location /propmap/goldenrabbit/ {
        alias /home/webapp/goldenrabbit/frontend/public/;
        index index.html;

        location ~* \\.html$ {
            expires 0;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
        }
    }"""

new = """    # PropMap - agent별 매물지도 (범용)
    location ~ ^/propmap/([a-zA-Z0-9_-]+)/$ {
        alias /home/webapp/goldenrabbit/frontend/public/propmap/$1/;
        index index.html;
        try_files $uri $uri/ /propmap/$1/index.html;

        location ~* \\.html$ {
            expires 0;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
        }
    }

    # /propmap/{slug} -> /propmap/{slug}/ 리다이렉트
    location ~ ^/propmap/([a-zA-Z0-9_-]+)$ {
        return 301 /propmap/$1/;
    }"""

if old in c:
    c = c.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('Nginx propmap 라우트 교체 완료')
else:
    print('패턴 불일치 - 수동 확인 필요')
    # 디버그
    if '/propmap/goldenrabbit' in c:
        print('goldenrabbit 블록은 존재하지만 정확한 패턴이 다름')
