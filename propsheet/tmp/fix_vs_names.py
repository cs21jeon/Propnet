#!/usr/bin/env python3
"""Fix: Alpine.js can't access _ prefixed properties in templates.
Rename _visibleItems -> vsItems, _useVirtualScroll -> vsEnabled, etc."""

JS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list_v2.js'
HTML_PATH = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'

# Rename map
renames = {
    '_useVirtualScroll': 'vsEnabled',
    '_visibleItems': 'vsItems',
    '_spacerTop': 'vsSpacerTop',
    '_totalHeight': 'vsTotalHeight',
    '_ROW_HEIGHT': 'vsRowHeight',
    '_BUFFER_ROWS': 'vsBufferRows',
    '_scrollTop': 'vsScrollTop',
    '_containerHeight': 'vsContainerHeight',
}

# Fix JS
with open(JS_PATH, 'r') as f:
    js = f.read()

for old, new in renames.items():
    count = js.count(old)
    js = js.replace(old, new)
    if count > 0:
        print(f'JS: {old} -> {new} ({count} occurrences)')

with open(JS_PATH, 'w') as f:
    f.write(js)

# Fix HTML
with open(HTML_PATH, 'r') as f:
    html = f.read()

for old, new in renames.items():
    count = html.count(old)
    html = html.replace(old, new)
    if count > 0:
        print(f'HTML: {old} -> {new} ({count} occurrences)')

with open(HTML_PATH, 'w') as f:
    f.write(html)

# Verify JS syntax
import subprocess
result = subprocess.run(['node', '-c', JS_PATH], capture_output=True, text=True)
if result.returncode == 0:
    print('\nJS syntax: OK')
else:
    print(f'\nJS ERROR:\n{result.stderr}')

# Copy to original files too
import shutil
shutil.copy(JS_PATH, JS_PATH.replace('_v2', ''))
shutil.copy('/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list_v2.css',
            '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css')
print('Synced v2 -> original files')
