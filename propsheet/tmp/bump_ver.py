#!/usr/bin/env python3
import re, time
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()
ts = str(int(time.time()))
# Match any version string after ?v= until the closing quote
html = re.sub(r"database_list\.js\?v=[^'\"]+", f"database_list.js?v={ts}", html)
html = re.sub(r"database_list\.css\?v=[^'\"]+", f"database_list.css?v={ts}", html)
with open(path, 'w') as f:
    f.write(html)
print(f'Bumped to v={ts}')
