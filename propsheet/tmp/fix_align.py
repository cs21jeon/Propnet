#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

old = "'cell-number': col.type === 'number',"
new = "'cell-number': col.type === 'number' || (col.type === 'formula' && col.numberFormat && col.numberFormat.thousands !== undefined),"

if old in html:
    html = html.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(html)
    print("OK")
else:
    print("WARN: not found")
