#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(path, 'r') as f:
    html = f.read()

if 'showCloneModal' in html:
    print("Already has clone modal")
else:
    clone_modal = '''        <!-- Clone Workspace Modal -->
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
                                        <span x-text="db.icon || \'\\ud83d\\udcca\'"></span>
                                        <span x-text="db.name"></span>
                                    </label>
                                </template>
                            </div>
                        </template>
                    </div>
                </div>

                <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
                    <button class="btn-cancel" @click="showCloneModal = false">취소</button>
                    <button class="btn-save" @click="submitClone()">복제</button>
                </div>
            </div>
        </div>

'''
    # Insert before Members Modal line
    html = html.replace('        <!-- Members Modal -->', clone_modal + '        <!-- Members Modal -->')

    with open(path, 'w') as f:
        f.write(html)
    print("Added clone modal HTML")
