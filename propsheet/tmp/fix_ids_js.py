#!/usr/bin/env python3
"""Add unique_id to workspace/database edit modals in JS"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(path, 'r') as f:
    js = f.read()

# 1. Workspace: add unique_id to openEditWorkspaceModal
old_ws = """                    this.editWorkspace = {
                        slug: workspace.slug,
                        name: workspace.name,
                        description: workspace.description || '',
                        icon: workspace.icon || '"""

if 'unique_id: workspace.unique_id' not in js:
    # Find and insert unique_id after icon line
    ws_idx = js.index("this.editWorkspace = {")
    # Find the closing }; of this object
    ws_end = js.index("};", ws_idx)
    # Insert unique_id before the closing
    insert_line = "\n                        unique_id: workspace.unique_id || ''"
    js = js[:ws_end] + "," + insert_line + "\n                    " + js[ws_end:]
    print("1. Added unique_id to editWorkspace")

# 2. Database: add unique_id to openEditDatabaseModal
if 'unique_id: database.unique_id' not in js:
    db_idx = js.index("this.editDatabase = {")
    db_end = js.index("};", db_idx)
    insert_line2 = "\n                        unique_id: database.unique_id || ''"
    js = js[:db_end] + "," + insert_line2 + "\n                    " + js[db_end:]
    print("2. Added unique_id to editDatabase")

with open(path, 'w') as f:
    f.write(js)

# 3. Record detail panel
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

if 'detailPanel.item.record_id' not in html:
    old = '<template x-if="!detailPanel.loading && detailPanel.item">'
    new = '''<template x-if="!detailPanel.loading && detailPanel.item">
                <div style="display:flex;align-items:center;gap:8px;padding:0 0 8px;border-bottom:1px solid var(--gray-100);margin-bottom:8px;">
                    <span style="font-size:12px;color:var(--gray-400);">#<span x-text="detailPanel.item.id"></span></span>
                    <span x-show="detailPanel.item.record_id" style="font-size:11px;color:var(--gray-400);font-family:monospace;cursor:pointer;" @click="navigator.clipboard.writeText(detailPanel.item.record_id); $el.style.color='#1976d2'; setTimeout(()=>$el.style.color='', 1500)" :title="'클릭하여 복사'" x-text="detailPanel.item.record_id"></span>
                </div>
            </template>
            <template x-if="!detailPanel.loading && detailPanel.item">'''
    html = html.replace(old, new, 1)
    print("3. Added record ID to detail panel")

with open(html_path, 'w') as f:
    f.write(html)

print("Done!")
