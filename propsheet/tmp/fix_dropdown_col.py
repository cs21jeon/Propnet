#!/usr/bin/env python3
js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

old = """                    this.selectDropdown = {
                        show: true,
                        itemId: item.id,
                        colKey: col.key,
                        colType: col.type,
                        options: options,
                        selected: selected,
                        x: rect.left,
                        y: rect.bottom + 2
                    };"""
new = """                    this.selectDropdown = {
                        show: true,
                        itemId: item.id,
                        colKey: col.key,
                        colType: col.type,
                        options: options,
                        selected: selected,
                        col: col,
                        x: rect.left,
                        y: rect.bottom + 2
                    };"""

if old in js:
    js = js.replace(old, new, 1)
    with open(js_path, "w") as f:
        f.write(js)
    print("OK - Added col to selectDropdown")
else:
    print("WARN: pattern not found")
