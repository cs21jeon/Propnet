#!/usr/bin/env python3
"""Fix overlay timing: use double requestAnimationFrame after $nextTick"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Replace all $nextTick overlay dismiss patterns
old1 = "this.$nextTick(() => { this.showOverlay = false; });"
new1 = "this.$nextTick(() => { requestAnimationFrame(() => { requestAnimationFrame(() => { this.showOverlay = false; }); }); });"

count = js.count(old1)
js = js.replace(old1, new1)
print(f"Replaced {count} overlay dismiss patterns with double rAF")

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')
