#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Replace the broken timer with simple performance.now()
js = js.replace(
    "const _t = 'fetch-' + Date.now(); console.time(_t);",
    "const _fetchStart = performance.now();"
)
js = js.replace(
    "console.timeEnd(_t);",
    "console.log(`API fetch: ${(performance.now() - _fetchStart).toFixed(0)}ms`);"
)
js = js.replace(
    "const _tr = 'render-' + Date.now(); console.time(_tr);",
    "const _renderStart = performance.now();"
)
js = js.replace(
    "console.timeEnd(_tr);",
    "console.log(`DOM render: ${(performance.now() - _renderStart).toFixed(0)}ms`);"
)

with open(path, 'w') as f:
    f.write(js)

path2 = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path2, 'rb') as f:
    r = f.read()
r = r.replace(b'v=20260317x', b'v=20260317y')
with open(path2, 'wb') as f:
    f.write(r)
print("OK")
