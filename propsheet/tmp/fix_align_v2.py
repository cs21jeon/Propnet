#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

# number type: always right-align
# formula type: right-align if numberFormat set OR if value looks numeric (handled via JS)
old = "'cell-number': col.type === 'number' || (col.type === 'formula' && col.numberFormat && col.numberFormat.thousands !== undefined),"
new = "'cell-number': col.type === 'number' || col.type === 'formula',"

if old in html:
    html = html.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(html)
    print("OK - step 1: all number/formula cells get cell-number class")
else:
    print("WARN: old pattern not found")

# But text formulas (like 홍보문구) should NOT be right-aligned.
# Solution: use a dynamic approach - check if formula result is text-heavy
# Better: apply class based on formula content, not type alone.
# Simplest: right-align formula by default, text formulas are rare and can be overridden.
# Actually, let's check which formulas produce text vs numbers.

# For now, let's exclude known text formulas by checking if formula contains string ops
# Better approach: in JS, detect at render time and add inline style
