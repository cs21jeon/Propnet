#!/usr/bin/env python3
import re

# === 1. JS: Add column selection + update drag to move selected columns ===
js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

changes = 0

# 1a. Add selectedColumns state
old_state = "draggedHeaderIndex: null,"
new_state = "draggedHeaderIndex: null,\n                selectedColumns: [],"
if 'selectedColumns' not in js:
    js = js.replace(old_state, new_state, 1)
    changes += 1

# 1b. Add selectColumn method
select_method = '''                selectColumn(event, col) {
                    const key = col.key;
                    if (event.ctrlKey || event.metaKey) {
                        // Toggle selection
                        const idx = this.selectedColumns.indexOf(key);
                        if (idx >= 0) this.selectedColumns.splice(idx, 1);
                        else this.selectedColumns.push(key);
                    } else if (event.shiftKey && this.selectedColumns.length > 0) {
                        // Range select
                        const visibleKeys = this.visibleColumnObjects.map(c => c.key);
                        const lastSelected = this.selectedColumns[this.selectedColumns.length - 1];
                        const fromIdx = visibleKeys.indexOf(lastSelected);
                        const toIdx = visibleKeys.indexOf(key);
                        if (fromIdx >= 0 && toIdx >= 0) {
                            const start = Math.min(fromIdx, toIdx);
                            const end = Math.max(fromIdx, toIdx);
                            for (let i = start; i <= end; i++) {
                                if (!this.selectedColumns.includes(visibleKeys[i])) {
                                    this.selectedColumns.push(visibleKeys[i]);
                                }
                            }
                        }
                    } else {
                        // Single select / deselect
                        if (this.selectedColumns.length === 1 && this.selectedColumns[0] === key) {
                            this.selectedColumns = [];
                        } else {
                            this.selectedColumns = [key];
                        }
                    }
                },

'''

if 'selectColumn(event, col)' not in js:
    # Insert before dragStartHeader
    js = js.replace('                dragStartHeader(event, index) {', select_method + '                dragStartHeader(event, index) {', 1)
    changes += 1

# 1c. Update dragStartHeader to handle multi-column drag
old_drag_start = """                dragStartHeader(event, index) {
                    this.draggedHeaderIndex = index;
                    event.dataTransfer.effectAllowed = 'move';
                },"""

new_drag_start = """                dragStartHeader(event, index) {
                    const col = this.visibleColumnObjects[index];
                    // If dragged col is not in selection, select only it
                    if (!this.selectedColumns.includes(col.key)) {
                        this.selectedColumns = [col.key];
                    }
                    this.draggedHeaderIndex = index;
                    event.dataTransfer.effectAllowed = 'move';
                },"""

if old_drag_start in js:
    js = js.replace(old_drag_start, new_drag_start, 1)
    changes += 1

# 1d. Update dropHeader to move all selected columns together
old_drop = """                dropHeader(event, dropIndex) {
                    event.preventDefault();

                    if (this.draggedHeaderIndex === null || this.draggedHeaderIndex === dropIndex) {
                        return;
                    }

                    // Get visible column keys
                    const visibleKeys = this.visibleColumnObjects.map(c => c.key);

                    // Find the actual column indices in allColumns
                    const draggedKey = visibleKeys[this.draggedHeaderIndex];
                    const dropKey = visibleKeys[dropIndex];

                    const draggedColIndex = this.allColumns.findIndex(c => c.key === draggedKey);
                    const dropColIndex = this.allColumns.findIndex(c => c.key === dropKey);

                    // Reorder in allColumns
                    const draggedColumn = this.allColumns[draggedColIndex];
                    this.allColumns.splice(draggedColIndex, 1);

                    // Recalculate drop index after removal
                    const newDropIndex = this.allColumns.findIndex(c => c.key === dropKey);
                    if (this.draggedHeaderIndex < dropIndex) {
                        this.allColumns.splice(newDropIndex + 1, 0, draggedColumn);
                    } else {
                        this.allColumns.splice(newDropIndex, 0, draggedColumn);
                    }

                    this.saveColumnOrder();
                    this.draggedHeaderIndex = null;
                },"""

new_drop = """                dropHeader(event, dropIndex) {
                    event.preventDefault();
                    if (this.draggedHeaderIndex === null || this.draggedHeaderIndex === dropIndex) return;

                    const visibleKeys = this.visibleColumnObjects.map(c => c.key);
                    const dropKey = visibleKeys[dropIndex];
                    const movingKeys = this.selectedColumns.length > 0 ? [...this.selectedColumns] : [visibleKeys[this.draggedHeaderIndex]];

                    // Remove moving columns from allColumns
                    const movingCols = movingKeys.map(k => this.allColumns.find(c => c.key === k)).filter(Boolean);
                    this.allColumns = this.allColumns.filter(c => !movingKeys.includes(c.key));

                    // Find drop position
                    let insertIdx = this.allColumns.findIndex(c => c.key === dropKey);
                    if (insertIdx < 0) insertIdx = this.allColumns.length;
                    else if (this.draggedHeaderIndex < dropIndex) insertIdx += 1;

                    // Insert moving columns at drop position (preserve their relative order)
                    this.allColumns.splice(insertIdx, 0, ...movingCols);

                    // Update visibleColumns order
                    this.visibleColumns = this.allColumns
                        .filter(c => this.visibleColumns.includes(c.key))
                        .map(c => c.key);

                    this.saveColumnOrder();
                    this.draggedHeaderIndex = null;
                },"""

if old_drop in js:
    js = js.replace(old_drop, new_drop, 1)
    changes += 1

with open(js_path, "w") as f:
    f.write(js)
print(f"1. JS: {changes} changes")

# === 2. HTML: Update header template ===
html_path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(html_path, "r") as f:
    html = f.read()

html_changes = 0

# 2a. Add 'selected-col' class to th
old_class = """:class="{
                                        'dragging-header': draggedHeaderIndex === index,
                                        'sorted': sortBy === col.key,
                                        'filtered': filterRules.some(r => r.field === col.key && r.value)
                                    }">"""
new_class = """:class="{
                                        'dragging-header': draggedHeaderIndex === index,
                                        'sorted': sortBy === col.key,
                                        'filtered': filterRules.some(r => r.field === col.key && r.value),
                                        'selected-col': selectedColumns.includes(col.key)
                                    }">"""
if "'selected-col'" not in html:
    html = html.replace(old_class, new_class, 1)
    html_changes += 1

# 2b. Remove sort from label click, add column select
old_label = """<span class="th-label"
                                              @click="col.sortable && toggleSort(col.key)"
                                              :style="col.sortable ? 'cursor: pointer;' : ''"
                                              x-text="col.label"></span>"""
new_label = """<span class="th-label"
                                              @click.stop="selectColumn($event, col)"
                                              style="cursor: pointer;"
                                              x-text="col.label"></span>"""
if old_label in html:
    html = html.replace(old_label, new_label, 1)
    html_changes += 1

# 2c. Make sort icon a proper button with tooltip
old_sort = """<span class="th-sort-icon"
                                                  :class="{'active': sortBy === col.key}"
                                                  x-show="col.sortable"
                                                  x-text="sortBy === col.key ? (sortOrder === 'asc' ? '▲' : '▼') : '⬍'"></span>"""
new_sort = """<button class="th-sort-btn"
                                                    :class="{'active': sortBy === col.key}"
                                                    x-show="col.sortable"
                                                    @click.stop="toggleSort(col.key)"
                                                    title="정렬"
                                                    x-text="sortBy === col.key ? (sortOrder === 'asc' ? '▲' : '▼') : '⬍'"></button>"""
if old_sort in html:
    html = html.replace(old_sort, new_sort, 1)
    html_changes += 1

# Bump versions
html = re.sub(r'database_list\.js\?v=\w+', 'database_list.js?v=20260317m', html)
html = re.sub(r'database_list\.css\?v=\w+', 'database_list.css?v=20260317m', html)

with open(html_path, "w") as f:
    f.write(html)
print(f"2. HTML: {html_changes} changes")

# === 3. CSS: Add styles ===
css_path = "/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css"
with open(css_path, "r") as f:
    css = f.read()

if '.selected-col' not in css:
    css += """
/* Column selection */
.selected-col {
    background: #e3f2fd !important;
    border-bottom: 2px solid #1976d2 !important;
}

/* Sort button */
.th-sort-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 2px 4px;
    font-size: 11px;
    color: var(--gray-400);
    border-radius: 3px;
    line-height: 1;
    transition: background 0.15s, color 0.15s;
}
.th-sort-btn:hover {
    background: var(--gray-200);
    color: var(--gray-700);
}
.th-sort-btn.active {
    color: var(--brand-blue, #667eea);
    font-weight: bold;
}

/* Header drag visual */
.dragging-header {
    opacity: 0.4;
}
th[draggable]:not(.dragging-header) {
    transition: background 0.15s;
}
"""
    with open(css_path, "w") as f:
        f.write(css)
    print("3. CSS: Added column selection + sort button styles")

print("\nDone!")
