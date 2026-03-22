#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(path, 'rb') as f:
    raw = f.read()

raw = raw.replace(b'v=20260305d', b'v=20260317e')

with open(path, 'wb') as f:
    f.write(raw)

print(f'20260305d remaining: {raw.count(b"20260305d")}')
print(f'20260317e count: {raw.count(b"20260317e")}')
