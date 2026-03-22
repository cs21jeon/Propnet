#!/usr/bin/env python3
"""
Fix 1: Add 'description' to json_build_object in all workspace queries
Fix 2: Workspaces page dark mode init from localStorage
"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(path, 'r') as f:
    py = f.read()

# Fix 1: Add description to all json_build_object calls
old_obj = "'id', d.id, 'name', d.name, 'slug', d.slug,\n                            'icon', d.icon, 'color', d.color, 'table_name', d.table_name"
new_obj = "'id', d.id, 'name', d.name, 'slug', d.slug,\n                            'icon', d.icon, 'color', d.color, 'description', d.description, 'table_name', d.table_name"

count = py.count(old_obj)
py = py.replace(old_obj, new_obj)
print(f"1. Added 'description' to {count} json_build_object calls")

# Also check the workspaces_list query (separate pattern)
old_obj2 = "'id', d.id, 'name', d.name, 'slug', d.slug,\n                    'icon', d.icon, 'color', d.color, 'table_name', d.table_name"
new_obj2 = "'id', d.id, 'name', d.name, 'slug', d.slug,\n                    'icon', d.icon, 'color', d.color, 'description', d.description, 'table_name', d.table_name"
count2 = py.count(old_obj2)
if count2 > 0:
    py = py.replace(old_obj2, new_obj2)
    print(f"1b. Fixed {count2} more queries with different indentation")

with open(path, 'w') as f:
    f.write(py)

# Fix 2: workspaces.html toggle button — check init script uses localStorage correctly
ws_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(ws_path, 'r') as f:
    ws = f.read()

# The toggle button uses inline onclick, need to also read localStorage on page load
# Check if init script exists
if "propsheet-theme" in ws and "data-theme" in ws:
    print("2. Workspaces init script already exists")
    # But the toggle button sets textContent on click — on reload it resets to 🌙
    # Fix: set correct initial icon based on localStorage
    old_toggle = """<button class="theme-toggle" onclick="const d=document.documentElement;const isDark=d.getAttribute('data-theme')==='dark';d.setAttribute('data-theme',isDark?'':'dark');localStorage.setItem('propsheet-theme',isDark?'light':'dark');this.textContent=isDark?'🌙':'☀️';">🌙</button>"""
    new_toggle = """<button class="theme-toggle" id="ws-theme-toggle" onclick="const d=document.documentElement;const isDark=d.getAttribute('data-theme')==='dark';d.setAttribute('data-theme',isDark?'':'dark');localStorage.setItem('propsheet-theme',isDark?'light':'dark');this.textContent=isDark?'🌙':'☀️';">🌙</button>
                        <script>document.addEventListener('DOMContentLoaded',function(){if(localStorage.getItem('propsheet-theme')==='dark'){document.getElementById('ws-theme-toggle').textContent='☀️';}});</script>"""
    if old_toggle in ws:
        ws = ws.replace(old_toggle, new_toggle, 1)
        print("2b. Fixed toggle button initial icon")

with open(ws_path, 'w') as f:
    f.write(ws)

print("Done!")
