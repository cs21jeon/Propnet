#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf"
with open(path, "r") as f:
    content = f.read()

old = """    # 블로그 업로드 파일 (이미지, 동영상, 첨부파일)
    location ^~ /uploads/blog/ {"""

new = """    # Propsheet 이미지 (에어테이블 백업 + 업로드)
    location ^~ /uploads/airtable/ {
        alias /home/webapp/goldenrabbit/uploads/airtable/;
        autoindex off;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # 블로그 업로드 파일 (이미지, 동영상, 첨부파일)
    location ^~ /uploads/blog/ {"""

if '/uploads/airtable/' not in content:
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print("OK - Nginx config updated")
else:
    print("Already exists")
