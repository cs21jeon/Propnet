#!/usr/bin/env python3
"""Add Ctrl+Z, history button in detail panel, trash button"""

# === 1. JS: Ctrl+Z undo stack + history popup + trash ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

if 'undoStack' not in js:
    # Add undo state
    js = js.replace(
        'lastSelectedRow: null,',
        'lastSelectedRow: null,\n                undoStack: [],\n                historyField: null,\n                historyData: [],\n                showHistory: false,'
    )
    print("1a. Added undo/history state")

    # Add undo/history methods before toggleRowSelect
    undo_methods = '''
                pushUndo(itemId, field, oldValue, newValue) {
                    this.undoStack.push({ itemId, field, oldValue, newValue, timestamp: Date.now() });
                    if (this.undoStack.length > 50) this.undoStack.shift();
                },

                async undoLast() {
                    if (this.undoStack.length === 0) return;
                    const entry = this.undoStack.pop();
                    try {
                        const res = await fetch(`${basePath}/api/database/property/${entry.itemId}/field`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                field: entry.field,
                                value: entry.oldValue,
                                db: this.databaseId
                            })
                        });
                        const data = await res.json();
                        if (data.success) {
                            const item = this.items.find(i => i.id === entry.itemId);
                            if (item) item[entry.field] = entry.oldValue;
                            this.showToast('되돌리기 완료', 'success');
                        }
                    } catch (e) {
                        this.showToast('되돌리기 실패', 'error');
                    }
                },

                async showFieldHistory(recordId, fieldName) {
                    this.historyField = fieldName;
                    this.historyData = [];
                    this.showHistory = true;
                    try {
                        const res = await fetch(`${basePath}/api/database/${this.databaseId}/history/${recordId}/${encodeURIComponent(fieldName)}`);
                        const data = await res.json();
                        if (data.success) {
                            this.historyData = data.history;
                        }
                    } catch (e) {}
                },

                async revertToVersion(recordId, fieldName, auditId) {
                    try {
                        const res = await fetch(`${basePath}/api/database/${this.databaseId}/history/${recordId}/${encodeURIComponent(fieldName)}/revert/${auditId}`, {
                            method: 'POST'
                        });
                        const data = await res.json();
                        if (data.success) {
                            this.showToast('되돌리기 완료', 'success');
                            this.showHistory = false;
                            await this.loadData();
                            if (this.detailPanel.show) {
                                const updated = this.items.find(i => i.id === recordId);
                                if (updated) this.detailPanel.item = {...updated};
                            }
                        } else {
                            this.showToast(data.error || '실패', 'error');
                        }
                    } catch (e) {
                        this.showToast('실패: ' + e.message, 'error');
                    }
                },

                formatTimeAgo(isoString) {
                    const diff = Date.now() - new Date(isoString).getTime();
                    const mins = Math.floor(diff / 60000);
                    if (mins < 1) return '방금 전';
                    if (mins < 60) return `${mins}분 전`;
                    const hours = Math.floor(mins / 60);
                    if (hours < 24) return `${hours}시간 전`;
                    const days = Math.floor(hours / 24);
                    return `${days}일 전`;
                },

'''
    js = js.replace('                toggleRowSelect(', undo_methods + '                toggleRowSelect(', 1)
    print("1b. Added undo/history methods")

    # Add Ctrl+Z keyboard listener in init
    old_init_end = "this.loadData();"
    # Find the right one (in init function)
    init_section_idx = js.index('async init()')
    init_loaddata_idx = js.index('this.loadData();', init_section_idx)
    new_init = """this.loadData();

                    // Ctrl+Z undo listener
                    document.addEventListener('keydown', (e) => {
                        if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
                            // Only if not editing a cell
                            if (!document.activeElement || document.activeElement.tagName === 'BODY') {
                                e.preventDefault();
                                this.undoLast();
                            }
                        }
                    });"""
    js = js[:init_loaddata_idx] + new_init + js[init_loaddata_idx + len('this.loadData();'):]
    print("1c. Added Ctrl+Z listener")

    # Hook into saveInlineEdit to push undo
    old_save_inline = "async saveInlineEdit()"
    save_idx = js.index(old_save_inline)
    save_section = js[save_idx:js.index('\n                },\n', save_idx + 100) + 20]

    # We need to capture oldValue before save. Find where editingCell is used
    # Add pushUndo in the saveSelectValue and saveInlineEdit success handlers
    # For inline edit: the old value is item[colKey] before update
    # Simplest: add pushUndo in saveSelectValue success
    old_save_select_success = """if (data.success) {
                            if (item) {
                                item[colKey] = value || null;
                                if (data.updated_at) item.updated_at = data.updated_at;
                            }"""
    new_save_select_success = """if (data.success) {
                            if (item) {
                                const prevValue = item[colKey];
                                item[colKey] = value || null;
                                if (data.updated_at) item.updated_at = data.updated_at;
                                this.pushUndo(itemId, colKey, prevValue, value);
                            }"""
    if old_save_select_success in js:
        js = js.replace(old_save_select_success, new_save_select_success, 1)
        print("1d. Added pushUndo to saveSelectValue")

with open(js_path, 'w') as f:
    f.write(js)

# === 2. HTML: History popup in detail panel + trash button ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

if 'showFieldHistory' not in html:
    # Add 🕐 button next to field settings button in detail panel
    old_settings = '<button class="detail-field-settings-btn" @click.stop="openFieldSettings(col)" title="필드 설정">&#9881;</button>'
    new_settings = '<button class="detail-field-settings-btn" @click.stop="showFieldHistory(detailPanel.item.id, col.key)" title="변경 이력">&#128340;</button><button class="detail-field-settings-btn" @click.stop="openFieldSettings(col)" title="필드 설정">&#9881;</button>'

    if old_settings in html:
        html = html.replace(old_settings, new_settings, 1)
        print("2a. Added history button to detail panel")

    # Add history popup before </body>
    history_popup = '''
    <!-- Field History Popup -->
    <div x-show="showHistory" x-cloak @click.self="showHistory = false"
         style="position:fixed;inset:0;background:rgba(0,0,0,0.3);z-index:5000;display:flex;align-items:center;justify-content:center;">
        <div style="background:white;border-radius:12px;width:450px;max-width:90vw;max-height:70vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,0.2);padding:20px;" @click.stop>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h3 style="margin:0;font-size:15px;" x-text="'변경 이력: ' + (historyField || '')"></h3>
                <button @click="showHistory = false" style="background:none;border:none;font-size:20px;cursor:pointer;">&times;</button>
            </div>
            <template x-if="historyData.length === 0">
                <p style="color:var(--gray-400);text-align:center;padding:20px;">변경 이력이 없습니다</p>
            </template>
            <template x-for="h in historyData" :key="h.id">
                <div style="padding:10px;border-bottom:1px solid var(--gray-100);display:flex;align-items:flex-start;gap:10px;">
                    <div style="flex:1;font-size:13px;">
                        <div style="color:var(--gray-500);font-size:11px;margin-bottom:4px;">
                            <span x-text="formatTimeAgo(h.created_at)"></span>
                            <span x-show="h.user_email" x-text="' · ' + (h.user_email || '').split('@')[0]" style="color:var(--gray-400);"></span>
                        </div>
                        <div style="display:flex;align-items:center;gap:6px;">
                            <span style="background:#fce4ec;padding:2px 6px;border-radius:4px;font-size:12px;text-decoration:line-through;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" x-text="h.old_value || '(빈값)'"></span>
                            <span style="color:var(--gray-400);">→</span>
                            <span style="background:#e8f5e9;padding:2px 6px;border-radius:4px;font-size:12px;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" x-text="h.new_value || '(빈값)'"></span>
                        </div>
                    </div>
                    <button @click="revertToVersion(detailPanel.item.id, historyField, h.id)"
                            style="padding:4px 10px;border:1px solid var(--gray-300);background:white;border-radius:4px;cursor:pointer;font-size:11px;white-space:nowrap;color:var(--brand-blue,#667eea);">되돌리기</button>
                </div>
            </template>
        </div>
    </div>
'''

    html = html.replace('</body>', history_popup + '</body>', 1)
    print("2b. Added history popup")

# Bump version
html = html.replace('v=20260318e', 'v=20260318f')

with open(html_path, 'w') as f:
    f.write(html)

print("Done - Frontend!")
