#!/usr/bin/env python3
"""Add row checkbox selection + bulk delete/duplicate"""

# === 1. JS: Add selection state + functions ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

if 'selectedRows' not in js:
    # Add state
    js = js.replace(
        'selectedColumns: [],',
        'selectedColumns: [],\n                selectedRows: [],\n                lastSelectedRow: null,'
    )
    print("1a. Added selectedRows state")

    # Add selection methods before triggerFileUpload
    selection_methods = '''
                toggleRowSelect(event, itemId) {
                    if (event.shiftKey && this.lastSelectedRow !== null) {
                        // Shift+click: range select
                        const ids = this.items.map(i => i.id);
                        const from = ids.indexOf(this.lastSelectedRow);
                        const to = ids.indexOf(itemId);
                        if (from >= 0 && to >= 0) {
                            const start = Math.min(from, to);
                            const end = Math.max(from, to);
                            for (let i = start; i <= end; i++) {
                                if (!this.selectedRows.includes(ids[i])) {
                                    this.selectedRows.push(ids[i]);
                                }
                            }
                        }
                    } else if (event.ctrlKey || event.metaKey) {
                        // Ctrl+click: toggle individual
                        const idx = this.selectedRows.indexOf(itemId);
                        if (idx >= 0) this.selectedRows.splice(idx, 1);
                        else this.selectedRows.push(itemId);
                    } else {
                        // Plain click: toggle individual
                        const idx = this.selectedRows.indexOf(itemId);
                        if (idx >= 0) this.selectedRows.splice(idx, 1);
                        else this.selectedRows.push(itemId);
                    }
                    this.lastSelectedRow = itemId;
                },

                toggleAllRows() {
                    if (this.selectedRows.length === this.items.length) {
                        this.selectedRows = [];
                    } else {
                        this.selectedRows = this.items.map(i => i.id);
                    }
                },

                async deleteSelectedRows() {
                    if (this.selectedRows.length === 0) return;
                    if (!confirm(`선택한 ${this.selectedRows.length}개 레코드를 삭제하시겠습니까?\\n\\n이 작업은 되돌릴 수 없습니다.`)) return;

                    let deleted = 0;
                    let errors = 0;
                    for (const id of this.selectedRows) {
                        try {
                            const res = await fetch(`${basePath}/api/database/property/${id}?db=${this.databaseId}`, {
                                method: 'DELETE'
                            });
                            const data = await res.json();
                            if (data.success) deleted++;
                            else errors++;
                        } catch (e) {
                            errors++;
                        }
                    }
                    this.selectedRows = [];
                    this.showToast(`${deleted}개 삭제 완료${errors ? `, ${errors}개 실패` : ''}`, deleted ? 'success' : 'error');
                    await this.loadData();
                },

                async duplicateSelectedRows() {
                    if (this.selectedRows.length === 0) return;
                    if (!confirm(`선택한 ${this.selectedRows.length}개 레코드를 복제하시겠습니까?`)) return;

                    let duplicated = 0;
                    for (const id of this.selectedRows) {
                        try {
                            const res = await fetch(`${basePath}/api/database/property/new?db=${this.databaseId}`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ source_id: id })
                            });
                            const data = await res.json();
                            if (data.success) duplicated++;
                        } catch (e) {}
                    }
                    this.selectedRows = [];
                    this.showToast(`${duplicated}개 복제 완료`, 'success');
                    await this.loadData();
                },

'''
    js = js.replace('                triggerFileUpload(', selection_methods + '                triggerFileUpload(', 1)
    print("1b. Added selection methods")

with open(js_path, 'w') as f:
    f.write(js)

# === 2. HTML: Add checkbox column + bulk action bar ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

if 'selectedRows' not in html:
    # Add header checkbox in thead
    old_th = '<th class="th-expand" style="width:30px;min-width:30px;max-width:30px;"></th>'
    new_th = '''<th class="th-expand" style="width:30px;min-width:30px;max-width:30px;"></th>
                                <th class="th-checkbox" style="width:32px;min-width:32px;max-width:32px;padding:0;text-align:center;">
                                    <input type="checkbox" @click="toggleAllRows()" :checked="selectedRows.length > 0 && selectedRows.length === items.length" :indeterminate.prop="selectedRows.length > 0 && selectedRows.length < items.length" style="cursor:pointer;">
                                </th>'''
    if old_th in html:
        html = html.replace(old_th, new_th, 1)
        print("2a. Added header checkbox")

    # Add row checkbox before cells
    old_expand = '''<td class="cell-expand" @click.stop="openDetailPanel(item.id)" title="상세 보기" style="width:30px;min-width:30px;max-width:30px;text-align:center;cursor:pointer;color:var(--gray-400);">
                                    <span style="font-size:14px">▶</span>
                                </td>'''
    new_expand = '''<td class="cell-expand" @click.stop="openDetailPanel(item.id)" title="상세 보기" style="width:30px;min-width:30px;max-width:30px;text-align:center;cursor:pointer;color:var(--gray-400);">
                                    <span style="font-size:14px">▶</span>
                                </td>
                                <td class="cell-checkbox" @click.stop="toggleRowSelect($event, item.id)" style="width:32px;min-width:32px;max-width:32px;padding:0;text-align:center;">
                                    <input type="checkbox" :checked="selectedRows.includes(item.id)" @click.stop="toggleRowSelect($event, item.id)" style="cursor:pointer;">
                                </td>'''
    if old_expand in html:
        html = html.replace(old_expand, new_expand, 1)
        print("2b. Added row checkboxes")

    # Add bulk action bar (above table, shown when rows selected)
    old_toolbar_end = '<div class="stats">'
    new_toolbar_end = '''<div class="bulk-actions" x-show="selectedRows.length > 0" style="display:flex;align-items:center;gap:8px;padding:6px 12px;background:#e3f2fd;border-radius:6px;font-size:13px;">
                    <span x-text="selectedRows.length + '개 선택됨'" style="font-weight:600;color:#1976d2;"></span>
                    <button @click="duplicateSelectedRows()" style="padding:4px 10px;border:1px solid #1976d2;background:white;color:#1976d2;border-radius:4px;cursor:pointer;font-size:12px;">복제</button>
                    <button @click="deleteSelectedRows()" style="padding:4px 10px;border:1px solid #e53935;background:white;color:#e53935;border-radius:4px;cursor:pointer;font-size:12px;">삭제</button>
                    <button @click="selectedRows = []" style="padding:4px 10px;border:1px solid #999;background:white;color:#666;border-radius:4px;cursor:pointer;font-size:12px;">선택 해제</button>
                </div>
                <div class="stats">'''
    if 'bulk-actions' not in html:
        html = html.replace(old_toolbar_end, new_toolbar_end, 1)
        print("2c. Added bulk action bar")

# Bump version
html = html.replace('v=20260318d', 'v=20260318e')

with open(html_path, 'w') as f:
    f.write(html)

# === 3. CSS: checkbox styling ===
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(css_path, 'r') as f:
    css = f.read()

if '.cell-checkbox' not in css:
    css += """
/* Row checkbox */
.cell-checkbox {
    position: sticky;
    left: 36px;
    z-index: 2;
    background: var(--surface, #fff);
}
tr:hover .cell-checkbox {
    background: var(--primary-50, #f0f4ff);
}
.th-checkbox {
    position: sticky;
    left: 36px;
    z-index: 11;
    background: var(--surface, #fff);
}
tr.row-selected td {
    background: #e3f2fd !important;
}
"""
    with open(css_path, 'w') as f:
        f.write(css)
    print("3. Added checkbox CSS")

print("Done!")
