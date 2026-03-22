#!/usr/bin/env python3
"""Remove random suffix from cloned database slugs - use original slug as-is"""

# === 1. Workspace clone: use original slug ===
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(route_path, 'r') as f:
    content = f.read()

# In api_clone_workspace - remove random suffix
old = """            import secrets as _s
            import string as _str
            db_suffix = ''.join(_s.choice(_str.ascii_lowercase + _str.digits) for _ in range(4))
            new_db_slug = db['slug'] + '_' + db_suffix
            new_table_name = new_db_slug.replace('-', '_')"""

new = """            new_db_slug = db['slug']
            new_table_name = new_slug.replace('-', '_') + '_' + db['slug'].replace('-', '_')"""

if old in content:
    content = content.replace(old, new, 1)
    print("1. Workspace clone: clean slugs")

# === 2. DB copy-to: use provided slug directly (already clean) ===
# No change needed - the user provides the slug in the modal

# === 3. JS: DB copy modal default slug without suffix ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(js_path, 'r') as f:
    js = f.read()

old_js = "this.moveNewSlug = db.slug + (action === 'copy' ? '_copy' : '');"
new_js = "this.moveNewSlug = db.slug;"

if old_js in js:
    js = js.replace(old_js, new_js, 1)
    print("2. JS: clean default slug for copy")

with open(js_path, 'w') as f:
    f.write(js)

with open(route_path, 'w') as f:
    f.write(content)

print("Done!")
