#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'rb') as f:
    r = f.read()

# Replace any existing version
import re
r2 = re.sub(rb'database_list\.js\?v=\w+', b'database_list.js?v=20260318b', r)
r2 = re.sub(rb'database_list\.css\?v=\w+', b'database_list.css?v=20260318b', r2)

with open(path, 'wb') as f:
    f.write(r2)

# Verify
with open(path, 'rb') as f:
    check = f.read()
print(f'js ok: {b"20260318b" in check}')
