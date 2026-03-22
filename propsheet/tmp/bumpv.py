#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'rb') as f:
    raw = f.read()
raw = raw.replace(b'database_list.js?v=20260317p', b'database_list.js?v=20260317v')
raw = raw.replace(b'database_list.css?v=20260317', b'database_list.css?v=20260317v')
with open(path, 'wb') as f:
    f.write(raw)
# verify
with open(path, 'rb') as f:
    check = f.read()
print(f'js: {"20260317v" in check.decode()}')
