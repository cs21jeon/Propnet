#!/usr/bin/env python3
"""Add bulk delete/clone for selected columns"""

# === 1. JS: Add bulk column functions ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

if 'deleteSelectedColumns' not in js:
    bulk_methods = '''
                async deleteSelectedColumns() {
                    if (this.selectedColumns.length === 0) return;
                    const systemCols = ['id', 'database_id', 'created_at', 'updated_at'];
                    const deletable = this.selectedColumns.filter(k => !systemCols.includes(k));
                    if (deletable.length === 0) {
                        this.showToast('시스템 필드는 삭제할 수 없습니다', 'error');
                        return;
                    }
                    const names = deletable.map(k => {
                        const col = this.allColumns.find(c => c.key === k);
                        return col ? col.label : k;
                    });
                    if (!confirm(`선택한 ${names.length}개 필드를 삭제하시겠습니까?\\n\\n${names.join(', ')}\\n\\n이 작업은 되돌릴 수 없으며 해당 필드의 모든 데이터가 삭제됩니다.`)) return;

                    let deleted = 0;
                    for (const colKey of deletable) {
                        try {
                            const res = await fetch(`${basePath}/api/database/delete-column`, {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({ db: this.databaseId, column_name: colKey })
                            });
                            const data = await res.json();
                            if (data.success) deleted++;
                        } catch (e) {}
                    }
                    this.selectedColumns = [];
                    this.showToast(`${deleted}개 필드 삭제 완료`, 'success');
                    await this.loadColumns();
                    this.applyColumnOrder();
                    this.visibleColumns = this.visibleColumns.filter(k => !deletable.includes(k));
                    await this.loadData();
                },

                async cloneSelectedColumns() {
                    if (this.selectedColumns.length === 0) return;
                    if (!confirm(`선택한 ${this.selectedColumns.length}개 필드를 복제하시겠습니까?`)) return;

                    let cloned = 0;
                    for (const colKey of this.selectedColumns) {
                        const col = this.allColumns.find(c => c.key === colKey);
                        if (!col) continue;
                        const newName = col.label + ' (복사본)';
                        try {
                            const res = await fetch(`${basePath}/api/database/clone-column`, {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({ db: this.databaseId, column_name: colKey, new_name: newName })
                            });
                            const data = await res.json();
                            if (data.success) cloned++;
                        } catch (e) {}
                    }
                    this.selectedColumns = [];
                    this.showToast(`${cloned}개 필드 복제 완료`, 'success');
                    await this.loadColumns();
                    this.applyColumnOrder();
                    await this.loadData();
                },

'''
    # Insert before selectColumn function
    js = js.replace('                selectColumn(event, col) {', bulk_methods + '                selectColumn(event, col) {', 1)
    print("1. Added bulk column delete/clone functions")

with open(js_path, 'w') as f:
    f.write(js)

# === 2. HTML: Add bulk action bar for columns (above table, when columns selected) ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

if 'deleteSelectedColumns' not in html:
    # Find the existing row bulk actions bar and add column bar next to it
    old_bulk = '<div class="bulk-actions" x-show="selectedRows.length > 0"'
    new_bulk = '''<div class="bulk-actions" x-show="selectedColumns.length > 0" style="display:flex;align-items:center;gap:8px;padding:6px 12px;background:#e8f5e9;border-radius:6px;font-size:13px;">
                    <span x-text="selectedColumns.length + '개 필드 선택'" style="font-weight:600;color:#2e7d32;"></span>
                    <button @click="cloneSelectedColumns()" style="padding:4px 10px;border:1px solid #2e7d32;background:white;color:#2e7d32;border-radius:4px;cursor:pointer;font-size:12px;">복제</button>
                    <button @click="deleteSelectedColumns()" style="padding:4px 10px;border:1px solid #e53935;background:white;color:#e53935;border-radius:4px;cursor:pointer;font-size:12px;">삭제</button>
                    <button @click="selectedColumns = []" style="padding:4px 10px;border:1px solid #999;background:white;color:#666;border-radius:4px;cursor:pointer;font-size:12px;">선택 해제</button>
                </div>
                <div class="bulk-actions" x-show="selectedRows.length > 0"'''

    html = html.replace(old_bulk, new_bulk, 1)
    print("2. Added column bulk action bar")

with open(html_path, 'w') as f:
    f.write(html)

print("Done!")
