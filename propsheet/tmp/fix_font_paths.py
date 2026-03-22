#!/usr/bin/env python3

files = [
    '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/workspaces.css',
    '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css',
    '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/share.html',
]

for f in files:
    with open(f, 'r') as fh:
        c = fh.read()
    if '/property-manager/static/fonts/' in c:
        c = c.replace('/property-manager/static/fonts/', '/propsheet/static/fonts/')
        with open(f, 'w') as fh:
            fh.write(c)
        print(f"Fixed: {f.split('/')[-1]}")
