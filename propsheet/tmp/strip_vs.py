#!/usr/bin/env python3
"""Remove variation selectors from emoji strings in JS"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(path, 'r') as f:
    js = f.read()

# Remove U+FE0F (variation selector) - emojis work fine without it
before = js.count('\uFE0F')
js = js.replace('\uFE0F', '')
after = js.count('\uFE0F')
print(f'Removed {before - after} variation selectors')

with open(path, 'w') as f:
    f.write(js)

# Bump version
path2 = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(path2, 'rb') as f:
    raw = f.read()
raw = raw.replace(b'v=20260317e', b'v=20260317f')
with open(path2, 'wb') as f:
    f.write(raw)
print(f'Version bumped to 20260317f')
