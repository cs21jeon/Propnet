#!/usr/bin/env python3
"""
Fix dark mode:
1. Add init script to <head> of both pages (before any rendering)
2. Fix light text colors for headers/titles in dark mode
3. Fix workspaces.css version bump
"""

# ============================================================
# Fix workspaces.html
# ============================================================
ws_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(ws_path, 'r') as f:
    ws = f.read()

# Add theme init to <head> (before </head>)
init_script = """    <script>
        (function(){
            if(localStorage.getItem('propsheet-theme')==='dark'){
                document.documentElement.setAttribute('data-theme','dark');
            }
        })();
    </script>
"""

if "document.documentElement.setAttribute('data-theme'" not in ws.split('</head>')[0]:
    ws = ws.replace('</head>', init_script + '</head>', 1)
    print("1a. Added theme init to workspaces.html <head>")

# Fix DOMContentLoaded to also set data-theme (in case head script didn't run)
old_dom = """<script>document.addEventListener('DOMContentLoaded',function(){if(localStorage.getItem('propsheet-theme')==='dark'){document.getElementById('ws-theme-toggle').textContent='☀️';}});</script>"""
new_dom = """<script>document.addEventListener('DOMContentLoaded',function(){if(localStorage.getItem('propsheet-theme')==='dark'){document.documentElement.setAttribute('data-theme','dark');document.getElementById('ws-theme-toggle').textContent='☀️';}});</script>"""

if old_dom in ws:
    ws = ws.replace(old_dom, new_dom, 1)
    print("1b. Fixed DOMContentLoaded to also set data-theme")

# Bump workspaces CSS/JS version
ws = ws.replace("workspaces.css') }}?v=20260317j", "workspaces.css') }}?v=20260322")
ws = ws.replace("workspaces.js') }}?v=20260317j", "workspaces.js') }}?v=20260322")
print("1c. Bumped workspaces CSS/JS version")

with open(ws_path, 'w') as f:
    f.write(ws)

# ============================================================
# Fix database_list.html — same init check
# ============================================================
db_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(db_path, 'r') as f:
    db = f.read()

if "document.documentElement.setAttribute('data-theme'" not in db.split('</head>')[0]:
    db = db.replace('</head>', init_script + '</head>', 1)
    print("2a. Added theme init to database_list.html <head>")
else:
    print("2a. database_list.html already has theme init")

with open(db_path, 'w') as f:
    f.write(db)

# ============================================================
# Fix CSS: light text for headers/titles in dark mode
# ============================================================
ws_css = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/workspaces.css'
with open(ws_css, 'r') as f:
    css = f.read()

dark_text_fixes = """
/* Dark mode text fixes */
[data-theme="dark"] h1,
[data-theme="dark"] h2,
[data-theme="dark"] h3,
[data-theme="dark"] .header h1,
[data-theme="dark"] .header p,
[data-theme="dark"] .workspace-name,
[data-theme="dark"] .database-name,
[data-theme="dark"] .database-desc,
[data-theme="dark"] .broker-name,
[data-theme="dark"] .broker-row,
[data-theme="dark"] .broker-card * {
    color: #e2e8f0 !important;
}
[data-theme="dark"] .broker-name {
    color: #f1f5f9 !important;
}
[data-theme="dark"] .header p {
    color: #94a3b8 !important;
}
[data-theme="dark"] .user-name {
    color: #e2e8f0 !important;
}
"""

if 'Dark mode text fixes' not in css:
    css += dark_text_fixes
    with open(ws_css, 'w') as f:
        f.write(css)
    print("3a. Added dark mode text fixes to workspaces.css")

# Also add to database_list.css
db_css = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(db_css, 'r') as f:
    css2 = f.read()

dark_db_text = """
/* Dark mode text fixes */
[data-theme="dark"] .header h1,
[data-theme="dark"] .header a {
    color: #e2e8f0 !important;
}
[data-theme="dark"] .btn-secondary {
    background: #252836;
    color: #e2e8f0;
    border-color: #3a3d4a;
}
"""

if 'Dark mode text fixes' not in css2:
    css2 += dark_db_text
    with open(db_css, 'w') as f:
        f.write(css2)
    print("3b. Added dark mode text fixes to database_list.css")

# Bump database_list CSS version
with open(db_path, 'r') as f:
    db = f.read()
db = db.replace("database_list.css') }}?v=1774005000", "database_list.css') }}?v=1774005100")
with open(db_path, 'w') as f:
    f.write(db)

print("\nDone!")
