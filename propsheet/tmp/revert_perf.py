#!/usr/bin/env python3
"""
Revert all performance optimizations EXCEPT:
1. Scroll-to-save (editing auto-saves on scroll)
2. Remove "전체" option from per_page

Restore original JS/HTML/CSS from git, then re-apply only the two features above.
"""
import subprocess

BASE = '/home/webapp/goldenrabbit'
JS_PATH = f'{BASE}/backend/property-manager/static/js/propsheet/database_list.js'
HTML_PATH = f'{BASE}/backend/property-manager/templates/propsheet/database_list.html'
CSS_PATH = f'{BASE}/backend/property-manager/static/css/propsheet/database_list.css'

# Step 1: Restore files from last git commit
print("=== Step 1: Restoring from git ===")
subprocess.run(['git', 'checkout', 'HEAD', '--',
    'backend/property-manager/static/js/propsheet/database_list.js',
    'backend/property-manager/templates/propsheet/database_list.html',
    'backend/property-manager/static/css/propsheet/database_list.css',
], cwd=BASE)
print("Restored JS, HTML, CSS from git")

# Remove v2 files
import os
for f in ['database_list_v2.js', 'database_list_v2.css']:
    d = 'js/propsheet' if f.endswith('.js') else 'css/propsheet'
    p = f'{BASE}/backend/property-manager/static/{d}/{f}'
    if os.path.exists(p):
        os.remove(p)
        print(f"Removed {f}")

# Step 2: Fix HTML to reference original files (not v2)
with open(HTML_PATH, 'r') as f:
    html = f.read()

# Make sure it references original files
html = html.replace('database_list_v2.css', 'database_list.css')
html = html.replace('database_list_v2.js', 'database_list.js')

# Bump version to force cache refresh
import time
ts = str(int(time.time()))
import re
# Handle any version format
html = re.sub(r"database_list\.css'\)\s*\}\}(\?v=[^\"']*)?", f"database_list.css') }}?v={ts}", html)
html = re.sub(r"database_list\.js'\)\s*\}\}(\?v=[^\"']*)?", f"database_list.js') }}?v={ts}", html)

with open(HTML_PATH, 'w') as f:
    f.write(html)
print(f"Fixed HTML references, bumped to v={ts}")

# Step 3: Add scroll-to-save feature to original JS
with open(JS_PATH, 'r') as f:
    js = f.read()

scroll_listener = """                    // Scroll closes inline editor (auto-save)
                    const _scrollContainer = document.querySelector('.spreadsheet-wrapper');
                    if (_scrollContainer) {
                        _scrollContainer.addEventListener('scroll', () => {
                            if (this.editingCell.itemId !== null) {
                                this.saveInlineEdit();
                            }
                        });
                    }

"""

# Insert before Ctrl+Z listener
if 'Scroll closes inline editor' not in js:
    js = js.replace('                    // Ctrl+Z undo listener', scroll_listener + '                    // Ctrl+Z undo listener', 1)
    print("Added scroll-to-save listener")
else:
    print("Scroll-to-save already exists")

with open(JS_PATH, 'w') as f:
    f.write(js)

# Step 4: Remove "전체" option from per_page dropdown in HTML
with open(HTML_PATH, 'r') as f:
    html = f.read()

# Find and remove the 전체/10000 option
# Common patterns: <option value="10000">전체</option> or similar
html = re.sub(r'\s*<option[^>]*value="10000"[^>]*>전체</option>', '', html)
html = re.sub(r'\s*<option[^>]*value="9999"[^>]*>전체</option>', '', html)
# Also check JS for perPage options
print("Removed 전체 option from HTML (if present)")

with open(HTML_PATH, 'w') as f:
    f.write(html)

# Check JS for per_page 10000 references
with open(JS_PATH, 'r') as f:
    js = f.read()

# Remove 전체 from JS perPage options if exists
if '10000' in js:
    # Find perPage related 10000 values
    # Common: perPage dropdown change handler or initial value
    pass  # We'll handle this in HTML only

with open(JS_PATH, 'w') as f:
    f.write(js)

# Step 5: Verify JS syntax
result = subprocess.run(['node', '-c', JS_PATH], capture_output=True, text=True)
if result.returncode == 0:
    print("\nJS syntax: OK")
else:
    print(f"\nJS ERROR:\n{result.stderr}")

print("\nDone! Restart: sudo systemctl restart property-manager propsheet")
