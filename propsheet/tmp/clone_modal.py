#!/usr/bin/env python3
"""Replace prompt-based clone with modal + database selection"""

# === 1. JS: Add clone modal state + replace cloneWorkspace ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(js_path, 'r') as f:
    js = f.read()

# Add state vars
old_state = "showMembersModal: false,"
new_state = """showMembersModal: false,
                showCloneModal: false,
                cloneSource: null,
                cloneName: '',
                cloneSlug: '',
                cloneDbSelection: {},"""

if 'showCloneModal' not in js:
    js = js.replace(old_state, new_state, 1)
    print("1a. Added clone modal state")

# Replace cloneWorkspace function
old_clone = """                async cloneWorkspace(workspace) {
                    const newName = prompt('복제할 워크스페이스 이름:', workspace.name + ' (복제)');
                    if (!newName) return;

                    const newSlug = prompt('영문 이름 (URL):', workspace.slug + '-copy');
                    if (!newSlug) return;

                    try {
                        const res = await fetch(`/propsheet/api/workspace/${workspace.slug}/clone`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ name: newName, slug: newSlug })
                        });
                        const data = await res.json();
                        if (data.success) {
                            alert(`워크스페이스가 복제되었습니다. (${data.databases_cloned}개 데이터베이스)`);
                            this.loadWorkspaces();
                        } else {
                            alert('복제 실패: ' + (data.error || '알 수 없는 오류'));
                        }
                    } catch (e) {
                        alert('복제 실패: ' + e.message);
                    }
                },"""

new_clone = """                openCloneModal(workspace) {
                    this.cloneSource = workspace;
                    this.cloneName = workspace.name + ' (복제)';
                    this.cloneSlug = workspace.slug + '-copy';
                    this.cloneDbSelection = {};
                    (workspace.databases || []).forEach(db => {
                        this.cloneDbSelection[db.id] = true;
                    });
                    this.showCloneModal = true;
                    this.error = '';
                },

                async submitClone() {
                    if (!this.cloneName || !this.cloneSlug) {
                        this.error = '이름과 영문 이름을 입력하세요';
                        return;
                    }
                    const selectedDbIds = Object.entries(this.cloneDbSelection)
                        .filter(([k, v]) => v)
                        .map(([k]) => parseInt(k));

                    try {
                        const res = await fetch(`/propsheet/api/workspace/${this.cloneSource.slug}/clone`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                name: this.cloneName,
                                slug: this.cloneSlug,
                                database_ids: selectedDbIds
                            })
                        });
                        const data = await res.json();
                        if (data.success) {
                            this.showCloneModal = false;
                            alert(`워크스페이스가 복제되었습니다. (${data.databases_cloned}개 데이터베이스)`);
                            this.loadWorkspaces();
                        } else {
                            this.error = data.error || '복제 실패';
                        }
                    } catch (e) {
                        this.error = '복제 실패: ' + e.message;
                    }
                },"""

if old_clone in js:
    js = js.replace(old_clone, new_clone, 1)
    print("1b. Replaced clone function with modal version")

with open(js_path, 'w') as f:
    f.write(js)

# === 2. HTML: Add clone modal + update button call ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(html_path, 'r') as f:
    html = f.read()

# Update button to open modal
html = html.replace('cloneWorkspace(workspace)', 'openCloneModal(workspace)')
print("2a. Updated button to openCloneModal")

# Add clone modal before </div> container closing
clone_modal = """
        <!-- Clone Workspace Modal -->
        <div class="modal-overlay" x-show="showCloneModal" x-cloak @click.self="showCloneModal = false" style="display:none;">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>워크스페이스 복제</h2>
                    <button class="btn-close" @click="showCloneModal = false">&times;</button>
                </div>

                <div class="error-message" x-show="error" x-text="error"></div>

                <div class="form-group">
                    <label>새 워크스페이스 이름 *</label>
                    <input type="text" x-model="cloneName" placeholder="예: 골든래빗 (복제)">
                </div>

                <div class="form-group">
                    <label>영문 URL *</label>
                    <input type="text" x-model="cloneSlug" placeholder="예: goldenrabbit-copy">
                </div>

                <div class="form-group">
                    <label>복제할 데이터베이스 선택</label>
                    <div style="max-height:200px;overflow-y:auto;border:1px solid var(--border);border-radius:6px;padding:8px;">
                        <template x-if="cloneSource && cloneSource.databases">
                            <div>
                                <template x-for="db in cloneSource.databases" :key="db.id">
                                    <label style="display:flex;align-items:center;gap:8px;padding:6px 4px;cursor:pointer;font-size:13px;">
                                        <input type="checkbox" x-model="cloneDbSelection[db.id]">
                                        <span x-text="db.icon || '📊'"></span>
                                        <span x-text="db.name"></span>
                                    </label>
                                </template>
                            </div>
                        </template>
                    </div>
                </div>

                <div class="modal-footer" style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
                    <button class="btn-cancel" @click="showCloneModal = false">취소</button>
                    <button class="btn-save" @click="submitClone()">복제</button>
                </div>
            </div>
        </div>
"""

if '워크스페이스 복제' not in html:
    # Insert before the members modal
    html = html.replace('        <!-- Members Modal -->', clone_modal + '        <!-- Members Modal -->', 1)
    print("2b. Added clone modal HTML")

import re
html = re.sub(r'workspaces\.js\?v=\w+', 'workspaces.js?v=20260318c', html)

with open(html_path, 'w') as f:
    f.write(html)

# === 3. Backend: Accept database_ids filter ===
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(route_path, 'r') as f:
    content = f.read()

# Add database_ids filtering
old_dbs = "        # Clone all databases in this workspace\n        databases = workspace.get('databases', [])"
new_dbs = """        # Clone selected databases (or all if not specified)
        all_databases = workspace.get('databases', [])
        selected_ids = data.get('database_ids')
        if selected_ids:
            databases = [db for db in all_databases if db['id'] in selected_ids]
        else:
            databases = all_databases"""

if 'selected_ids' not in content:
    content = content.replace(old_dbs, new_dbs, 1)
    with open(route_path, 'w') as f:
        f.write(content)
    print("3. Backend: Added database_ids filter")

print("Done!")
