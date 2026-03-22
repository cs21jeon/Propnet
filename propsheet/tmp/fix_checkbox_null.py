#!/usr/bin/env python3
"""Fix: checkbox shows empty checkbox when value is null"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Fix formatCell null check (line 1077)
old = "                    if (value === null || value === undefined) return '-';\n"
# Only replace first occurrence (in formatCell, not formatCellWithColor)
idx = js.index(old)
new = """                    if (value === null || value === undefined) {
                        if (col && col.type === 'checkbox') return '<span style="color:#999;font-size:16px;">&#9744;</span>';
                        return '-';
                    }
"""
js = js[:idx] + new + js[idx + len(old):]
print("1. Fixed formatCell null → empty checkbox")

# Also fix getDetailDisplayValue for checkbox
old_detail = """                    if (val === null || val === undefined) return '-';"""
# Find in getDetailDisplayValue (should be the second occurrence or near line 2189+)
detail_idx = js.index(old_detail, js.index('getDetailDisplayValue'))
new_detail = """                    if (val === null || val === undefined) {
                        if (col && col.type === 'checkbox') return '아니오';
                        return '-';
                    }"""
js = js[:detail_idx] + new_detail + js[detail_idx + len(old_detail):]
print("2. Fixed getDetailDisplayValue null → checkbox '아니오'")

# Bump version
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()
html = html.replace("database_list.js') }}?v=1774004500", "database_list.js') }}?v=1774004600")
with open(html_path, 'w') as f:
    f.write(html)

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')
