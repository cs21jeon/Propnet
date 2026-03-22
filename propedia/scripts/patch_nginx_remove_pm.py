path = '/etc/nginx/sites-enabled/goldenrabbit'
with open(path, 'r') as f:
    content = f.read()

old = """    # ========================================
    # Property Manager (포트 5000)
    # ========================================

    # Property Manager static 파일
    location ^~ /property-manager/static/ {
        alias /home/webapp/goldenrabbit/backend/property-manager/static/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # Property Manager 애플리케이션
    location /property-manager {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }"""

new = """    # ========================================
    # Property Manager - 제거됨 (2026-03-16)
    # ========================================"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('SUCCESS: nginx property-manager routes removed')
else:
    print('ERROR: pattern not found')
