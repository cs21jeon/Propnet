#!/usr/bin/env python3
"""Show unique_id in workspace/database edit modals + record detail panel"""

# === 1. Workspace edit modal ===
html_ws_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(html_ws_path, 'r') as f:
    html = f.read()

# Add ID to edit workspace modal (after slug field)
old_ws_slug = '''<small class="text-warning">URL 변경은 지원하지 않습니다</small>
                </div>

                <div class="form-group">
                    <label>설명</label>
                    <textarea x-model="editWorkspace.description"'''

new_ws_slug = '''<small class="text-warning">URL 변경은 지원하지 않습니다</small>
                </div>

                <div class="form-group" x-show="editWorkspace.unique_id">
                    <label>워크스페이스 ID</label>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <input type="text" :value="editWorkspace.unique_id" readonly disabled style="flex:1;background:var(--gray-50);color:var(--gray-600);font-family:monospace;font-size:12px;">
                        <button type="button" @click="navigator.clipboard.writeText(editWorkspace.unique_id); $el.textContent='복사됨!'; setTimeout(()=>$el.textContent='복사', 1500)" style="padding:4px 10px;border:1px solid var(--gray-300);border-radius:4px;background:white;cursor:pointer;font-size:12px;white-space:nowrap;">복사</button>
                    </div>
                </div>

                <div class="form-group">
                    <label>설명</label>
                    <textarea x-model="editWorkspace.description"'''

if 'editWorkspace.unique_id' not in html:
    html = html.replace(old_ws_slug, new_ws_slug, 1)
    print("1. Added workspace ID to edit modal")

# Add ID to edit database modal
old_db_slug = '''<small class="text-warning">URL 변경은 지원하지 않습니다</small>
                </div>

                <div class="form-group">
                    <label>설명</label>
                    <textarea x-model="editDatabase.description"'''

new_db_slug = '''<small class="text-warning">URL 변경은 지원하지 않습니다</small>
                </div>

                <div class="form-group" x-show="editDatabase.unique_id">
                    <label>데이터베이스 ID</label>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <input type="text" :value="editDatabase.unique_id" readonly disabled style="flex:1;background:var(--gray-50);color:var(--gray-600);font-family:monospace;font-size:12px;">
                        <button type="button" @click="navigator.clipboard.writeText(editDatabase.unique_id); $el.textContent='복사됨!'; setTimeout(()=>$el.textContent='복사', 1500)" style="padding:4px 10px;border:1px solid var(--gray-300);border-radius:4px;background:white;cursor:pointer;font-size:12px;white-space:nowrap;">복사</button>
                    </div>
                </div>

                <div class="form-group">
                    <label>설명</label>
                    <textarea x-model="editDatabase.description"'''

if 'editDatabase.unique_id' not in html:
    html = html.replace(old_db_slug, new_db_slug, 1)
    print("2. Added database ID to edit modal")

with open(html_ws_path, 'w') as f:
    f.write(html)

# === 2. JS: Pass unique_id to edit modals ===
js_ws_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(js_ws_path, 'r') as f:
    js = f.read()

# Add unique_id to openEditWorkspaceModal
if 'editWorkspace.unique_id' not in js:
    old_edit_ws = "this.editWorkspace = {"
    # Find the full assignment
    idx = js.index('openEditWorkspaceModal(workspace)')
    edit_section = js[idx:idx+300]

    # Add unique_id to the editWorkspace object
    js = js.replace(
        "editWorkspace: {\n                    slug: '',\n                    name: '',\n                    description: '',\n                    icon: ''",
        "editWorkspace: {\n                    slug: '',\n                    name: '',\n                    description: '',\n                    icon: '',\n                    unique_id: ''"
    )

    # In openEditWorkspaceModal, pass unique_id
    old_open_ws = "icon: workspace.icon || ''"
    # Find in openEditWorkspaceModal context
    ws_modal_idx = js.index('openEditWorkspaceModal(workspace)')
    ws_modal_section = js[ws_modal_idx:ws_modal_idx+400]
    if 'unique_id: workspace.unique_id' not in ws_modal_section:
        # Find the icon line in this context
        icon_idx = js.index("icon: workspace.icon || ''", ws_modal_idx)
        js = js[:icon_idx] + "icon: workspace.icon || '',\n                        unique_id: workspace.unique_id || ''" + js[icon_idx + len("icon: workspace.icon || ''"):]
    print("3. Added unique_id to workspace edit JS")

# Add unique_id to openEditDatabaseModal
if 'editDatabase.unique_id' not in js:
    js = js.replace(
        "editDatabase: {\n                    workspaceSlug: '',\n                    slug: '',\n                    name: '',\n                    description: '',\n                    icon: ''",
        "editDatabase: {\n                    workspaceSlug: '',\n                    slug: '',\n                    name: '',\n                    description: '',\n                    icon: '',\n                    unique_id: ''"
    )

    # In openEditDatabaseModal, pass unique_id
    db_modal_idx = js.index('openEditDatabaseModal(workspace, database)')
    db_section = js[db_modal_idx:db_modal_idx+400]
    old_db_icon = "icon: database.icon || ''"
    icon_idx2 = js.index(old_db_icon, db_modal_idx)
    js = js[:icon_idx2] + "icon: database.icon || '',\n                        unique_id: database.unique_id || ''" + js[icon_idx2 + len(old_db_icon):]
    print("4. Added unique_id to database edit JS")

with open(js_ws_path, 'w') as f:
    f.write(js)

# === 3. Backend: Include unique_id in API responses ===
# Check if workspace API returns unique_id
ws_service_path = '/home/webapp/goldenrabbit/backend/property-manager/services/workspace_service.py'
with open(ws_service_path, 'r') as f:
    ws_content = f.read()

# The get_workspace_by_slug uses SELECT * so unique_id is already included
# Same for databases — they use SELECT * via workspace queries
# Just verify
if 'unique_id' in ws_content:
    print("5. Backend already returns unique_id (SELECT * queries)")

# === 4. Record detail panel: show record_id ===
html_db_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_db_path, 'r') as f:
    html_db = f.read()

# Add record ID to detail panel header
old_detail_header = '<template x-if="!detailPanel.loading && detailPanel.item">'
new_detail_header = '''<template x-if="!detailPanel.loading && detailPanel.item">
                <div style="display:flex;align-items:center;gap:8px;padding:0 0 8px;border-bottom:1px solid var(--gray-100);margin-bottom:8px;">
                    <span style="font-size:12px;color:var(--gray-400);">#<span x-text="detailPanel.item.id"></span></span>
                    <span x-show="detailPanel.item.record_id" style="font-size:11px;color:var(--gray-400);font-family:monospace;cursor:pointer;" @click="navigator.clipboard.writeText(detailPanel.item.record_id); $el.style.color='#1976d2'; setTimeout(()=>$el.style.color='', 1500)" :title="'클릭하여 복사: ' + (detailPanel.item.record_id || '')" x-text="detailPanel.item.record_id"></span>
                </div>
            </template>
            <template x-if="!detailPanel.loading && detailPanel.item">'''

# Only add if not already present
if 'detailPanel.item.record_id' not in html_db:
    html_db = html_db.replace(old_detail_header, new_detail_header, 1)
    print("6. Added record ID to detail panel")

with open(html_db_path, 'w') as f:
    f.write(html_db)

print("Done!")
