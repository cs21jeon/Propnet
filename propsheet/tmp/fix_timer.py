#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Fix duplicate timer by using unique names
js = js.replace(
    "console.time('API fetch');",
    "const _t = 'fetch-' + Date.now(); console.time(_t);"
)
js = js.replace(
    "console.timeEnd('API fetch');",
    "console.timeEnd(_t);"
)
js = js.replace(
    "console.time('DOM render');",
    "const _tr = 'render-' + Date.now(); console.time(_tr);"
)
js = js.replace(
    "console.timeEnd('DOM render');",
    "console.timeEnd(_tr);"
)

with open(path, 'w') as f:
    f.write(js)
print("OK")
