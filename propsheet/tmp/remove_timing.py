#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Remove all timing code
js = js.replace("const _fetchStart = performance.now();\n                        ", "")
js = js.replace("console.log(`API fetch: ${(performance.now() - _fetchStart).toFixed(0)}ms`);\n                        ", "")
js = js.replace("console.log(`Received ${data.items ? data.items.length : 0} items, ${JSON.stringify(data).length/1024|0}KB`);\n\n", "")
js = js.replace("const _renderStart = performance.now();\n                            ", "")
js = js.replace("                        // Measure render time after Alpine processes the items\n                        requestAnimationFrame(() => {\n                            requestAnimationFrame(() => {\n                                console.log(`DOM render: ${(performance.now() - _renderStart).toFixed(0)}ms`);\n                            });\n                        });\n", "")

with open(path, 'w') as f:
    f.write(js)

path2 = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path2, 'rb') as f:
    r = f.read()
r = r.replace(b'v=20260317y', b'v=20260317z')
with open(path2, 'wb') as f:
    f.write(r)
print("OK")
