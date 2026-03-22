#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(path, "r") as f:
    content = f.read()

old = "const response = await fetch(`${basePath}/api/database/export-csv?db=${this.databaseId}`);"
new = "const viewParam = this.currentViewId ? `&view_id=${this.currentViewId}` : '';\n                        const response = await fetch(`${basePath}/api/database/export-csv?db=${this.databaseId}${viewParam}`);"

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print("OK - exportCSV updated with view_id param")
else:
    print("NOT FOUND")
