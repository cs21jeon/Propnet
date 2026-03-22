#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(path, "r") as f:
    js = f.read()

old = "newOptionColorIdx: (col.selectOptions || []).length,"
new = "newOptionColorIdx: (col.selectOptions || []).length,\n                        colorPickerIdx: -1,"

if 'colorPickerIdx: -1' not in js:
    js = js.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(js)
    print("OK")
else:
    print("Already exists")
