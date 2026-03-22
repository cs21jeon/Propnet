#!/usr/bin/env python3
"""Fix the gap between checkbox and expand columns in thead.

Problem: When scrolling horizontally, a thin gap appears between the
checkbox <th> and expand <th> in the header row. The tbody <td> cells
don't have this gap because the expand cell slides to fill it.

Solution: Use box-shadow on the checkbox <th> to cover the gap, and
ensure both th elements have matching left positions with no sub-pixel gaps.
Also ensure the expand <th> background covers any gap on its left edge.
"""

# Fix CSS
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(css_path, 'r') as f:
    css = f.read()

# Add a rule for thead sticky cells to eliminate gaps
# The key insight: use box-shadow on checkbox th to extend its background rightward
# and ensure expand th overlaps slightly

# Check current .cell-checkbox style
if '.cell-checkbox' in css:
    # Update cell-checkbox to add box-shadow that covers the gap
    css = css.replace(
        """.cell-checkbox {
    position: sticky;
    left: 0;""",
        """.cell-checkbox {
    position: sticky;
    left: 0;
    box-shadow: 1px 0 0 0 var(--surface, #fff);"""
    )
    print("1. Added box-shadow to .cell-checkbox")

# Also fix in thead specifically - add a rule for thead th sticky cells
thead_rule = """
/* Eliminate gap between sticky header columns */
thead th.cell-checkbox,
thead th[style*="left:0"] {
    box-shadow: 1px 0 0 0 var(--surface, #fff);
}
"""

# Only add if not already present
if 'Eliminate gap between sticky header columns' not in css:
    css += thead_rule
    print("2. Added thead gap fix rule")

with open(css_path, 'w') as f:
    f.write(css)

# Fix HTML - ensure the header th elements have no gap
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

# The checkbox th should be exactly 32px with the expand th starting at exactly 32px
# Check current thead markup and fix left positions

# Fix: ensure checkbox th has border-right:none and expand th left matches exactly
# The checkbox th width is 32px, so expand th should be at left:32px
# But if there's a border, it adds 1px. Remove border-right from checkbox th header

# Find the checkbox th in thead and ensure it has the right styles
# Current: left:0, width:32px
# Expand: left:32px (or left:31px from previous fix)

# Let's fix by ensuring expand th is at left:32px and using box-shadow approach
if 'left:31px' in html:
    html = html.replace(
        'left:31px;z-index:11;background:var(--surface,#fff);"></th>',
        'left:32px;z-index:11;background:var(--surface,#fff);"></th>'
    )
    print("3. Fixed expand th left from 31px to 32px")

# Remove any border-right on checkbox th that could cause the gap
if 'border-right:1px solid var(--border-light)' in html:
    html = html.replace('border-right:1px solid var(--border-light);', '')
    print("4. Removed border-right from checkbox th")

with open(html_path, 'w') as f:
    f.write(html)

# Bump CSS version
import time
ts = str(int(time.time()))

js_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(js_path, 'r') as f:
    content = f.read()

# Bump CSS version
import re
content = re.sub(r'database_list\.css\?v=\d+', f'database_list.css?v={ts}', content)
with open(js_path, 'w') as f:
    f.write(content)
print(f"5. Bumped CSS version to {ts}")

print("\nDone! Restart both services: systemctl restart property-manager propsheet")
