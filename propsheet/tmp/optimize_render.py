#!/usr/bin/env python3
"""Optimize table rendering: replace Alpine x-for with direct innerHTML for tbody"""

js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

# Add renderTable method that builds HTML string directly
render_method = '''                renderTable() {
                    const tbody = document.getElementById('data-tbody');
                    if (!tbody) return;

                    const cols = this.visibleColumnObjects;
                    const widths = this.columnWidths;
                    const rows = this.items;

                    if (!rows || rows.length === 0) {
                        tbody.innerHTML = `<tr><td colspan="${cols.length + 1}" class="loading"><p>데이터가 없습니다</p></td></tr>`;
                        return;
                    }

                    const html = [];
                    for (let r = 0; r < rows.length; r++) {
                        const item = rows[r];
                        html.push('<tr>');
                        html.push(`<td class="cell-expand" data-id="${item.id}" style="width:30px;min-width:30px;max-width:30px;text-align:center;cursor:pointer;color:var(--gray-400);"><span style="font-size:14px">▶</span></td>`);

                        for (let c = 0; c < cols.length; c++) {
                            const col = cols[c];
                            const w = widths[col.key] || col.defaultWidth || 150;
                            const val = item[col.key];

                            let cls = '';
                            if (col.type === 'number') cls = 'cell-number';
                            else if (col.formula) cls = 'cell-formula';
                            else if (col.type === 'url') cls = 'cell-url';
                            else if (col.type === 'single-select' || col.type === 'multi-select') cls = 'cell-select';
                            if (!col.readOnly && !col.formula && col.type !== 'formula' && col.type !== 'system_generated_value' && col.type !== 'system' && col.key !== 'id') {
                                cls += ' cell-editable';
                            }

                            let content;
                            if (col.type === 'single-select' || col.type === 'multi-select') {
                                content = `<div class="select-tag-cell" style="cursor:pointer;min-height:24px;">${this.formatCellWithColor(val, col)}</div>`;
                            } else {
                                content = this.formatCell(val, col, item);
                            }

                            html.push(`<td data-col-key="${col.key}" data-item-id="${item.id}" class="${cls}" style="width:${w}px;min-width:${w}px;max-width:${w}px;">${content}</td>`);
                        }
                        html.push('</tr>');
                    }

                    tbody.innerHTML = html.join('');

                    // Attach event listeners via delegation (already handled by tbody click)
                },

'''

if 'renderTable()' not in js:
    # Insert before loadData
    js = js.replace('                async loadData() {', render_method + '                async loadData() {', 1)
    print("1. Added renderTable method")

# Modify loadData to call renderTable after setting items
old_items = """                        if (data.success) {
                            console.time('DOM render');
                            this.items = data.items;"""

new_items = """                        if (data.success) {
                            console.time('DOM render');
                            this.items = data.items;
                            this.$nextTick(() => { this.renderTable(); });"""

if 'this.renderTable()' not in js:
    js = js.replace(old_items, new_items, 1)
    print("2. Added renderTable call in loadData")

with open(js_path, 'w') as f:
    f.write(js)

# Update HTML: replace Alpine x-for tbody with a plain tbody with id
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

# Replace the entire tbody section with a simple container
old_tbody_start = """                    <tbody>
                        <template x-if="loading">
                            <tr>
                                <td :colspan="visibleColumns.length + 1" class="loading">
                                    <div class="loading-spinner"></div>
                                    <p>로딩 중...</p>
                                </td>"""

new_tbody_start = """                    <tbody id="data-tbody">
                        <template x-if="loading">
                            <tr>
                                <td :colspan="visibleColumns.length + 1" class="loading">
                                    <div class="loading-spinner"></div>
                                    <p>로딩 중...</p>
                                </td>"""

# Just add id to tbody - keep the Alpine templates as fallback but they'll be overwritten by renderTable
if 'id="data-tbody"' not in html:
    html = html.replace(old_tbody_start, new_tbody_start, 1)
    print("3. Added id to tbody")

# Add event delegation for tbody clicks
delegation_script = """
    <script>
    // Event delegation for table body clicks
    document.addEventListener('click', function(e) {
        const tbody = document.getElementById('data-tbody');
        if (!tbody || !tbody.contains(e.target)) return;

        const expandCell = e.target.closest('.cell-expand');
        if (expandCell) {
            const id = parseInt(expandCell.dataset.id);
            if (id) {
                const app = document.querySelector('[x-data]').__x.$data;
                app.openDetailPanel(id);
            }
            return;
        }

        const td = e.target.closest('td[data-col-key]');
        if (td && td.classList.contains('cell-editable')) {
            const itemId = parseInt(td.dataset.itemId);
            const colKey = td.dataset.colKey;
            const app = document.querySelector('[x-data]').__x.$data;
            const item = app.items.find(i => i.id === itemId);
            const col = app.allColumns.find(c => c.key === colKey);
            if (item && col) {
                if (col.type === 'single-select' || col.type === 'multi-select') {
                    app.openSelectDropdown(e, item, col);
                } else {
                    app.startInlineEdit(item, col);
                }
            }
            return;
        }

        // Select dropdown click
        const selectCell = e.target.closest('.select-tag-cell');
        if (selectCell) {
            const td2 = selectCell.closest('td[data-col-key]');
            if (td2) {
                const itemId = parseInt(td2.dataset.itemId);
                const colKey = td2.dataset.colKey;
                const app = document.querySelector('[x-data]').__x.$data;
                const item = app.items.find(i => i.id === itemId);
                const col = app.allColumns.find(c => c.key === colKey);
                if (item && col) app.openSelectDropdown(e, item, col);
            }
        }
    });
    </script>
"""

if 'Event delegation for table body' not in html:
    html = html.replace('</body>', delegation_script + '</body>', 1)
    print("4. Added event delegation script")

import re
html = re.sub(rb'database_list\.js\?v=\w+'.decode(), 'database_list.js?v=20260317v', html)

with open(html_path, 'w') as f:
    f.write(html)

print("Done!")
