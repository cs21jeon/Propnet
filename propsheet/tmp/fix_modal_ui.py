#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(path, 'r') as f:
    html = f.read()

# Fix checkbox layout in clone modal
old_label = """<label style="display:flex;align-items:center;gap:8px;padding:6px 4px;cursor:pointer;font-size:13px;">
                                        <input type="checkbox" x-model="cloneDbSelection[db.id]">
                                        <span x-text="db.icon || '\\ud83d\\udcca'"></span>
                                        <span x-text="db.name"></span>
                                    </label>"""

new_label = """<label style="display:flex;align-items:center;gap:8px;padding:6px 8px;cursor:pointer;font-size:13px;white-space:nowrap;">
                                        <input type="checkbox" x-model="cloneDbSelection[db.id]" style="flex-shrink:0;width:16px;height:16px;">
                                        <span x-text="db.icon || '📊'" style="flex-shrink:0;"></span>
                                        <span x-text="db.name" style="overflow:hidden;text-overflow:ellipsis;"></span>
                                    </label>"""

if old_label in html:
    html = html.replace(old_label, new_label, 1)
    print("1. Fixed checkbox layout")
else:
    print("1. WARN: old label not found, trying alternate")
    # Try without the unicode escape
    old2 = 'x-model="cloneDbSelection[db.id]">'
    if old2 in html:
        html = html.replace(
            '<label style="display:flex;align-items:center;gap:8px;padding:6px 4px;cursor:pointer;font-size:13px;">',
            '<label style="display:flex;align-items:center;gap:8px;padding:6px 8px;cursor:pointer;font-size:13px;white-space:nowrap;">'
        )
        html = html.replace(
            '<input type="checkbox" x-model="cloneDbSelection[db.id]">',
            '<input type="checkbox" x-model="cloneDbSelection[db.id]" style="flex-shrink:0;width:16px;height:16px;">'
        )
        print("1b. Fixed via partial match")

import re
html = re.sub(r'workspaces\.js\?v=\w+', 'workspaces.js?v=20260318d', html)

with open(path, 'w') as f:
    f.write(html)
print("Done")
