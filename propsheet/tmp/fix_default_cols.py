#!/usr/bin/env python3
"""Show all columns by default when no saved preference exists"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Change default from first 12 to all columns
old1 = "this.visibleColumns = this.allColumns.slice(0, 12).map(col => col.key);"
new1 = "this.visibleColumns = this.allColumns.map(col => col.key);"

old2 = "this.visibleColumns = this.allColumns.slice(0, Math.min(12, this.allColumns.length)).map(col => col.key);"
new2 = "this.visibleColumns = this.allColumns.map(col => col.key);"

count = 0
if old1 in js:
    js = js.replace(old1, new1)
    count += 1
if old2 in js:
    js = js.replace(old2, new2)
    count += 1

print(f"Changed {count} defaults to show all columns")

with open(path, 'w') as f:
    f.write(js)
