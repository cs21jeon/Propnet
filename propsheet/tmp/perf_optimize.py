#!/usr/bin/env python3
"""
Propsheet rendering performance optimization - Steps 1-3
Safe, incremental changes that don't break Alpine.js reactivity.

Step 1: Cache visibleColumnObjects (getter -> cached array)
Step 2: Pre-compute formatted cell HTML after loadData()
Step 3: Simplify per-cell :class binding
"""

JS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
HTML_PATH = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'

# ============================================================
# STEP 1: Replace visibleColumnObjects getter with cached array
# ============================================================

with open(JS_PATH, 'r') as f:
    js = f.read()

# 1a. Replace getter with cached property + update method
old_getter = """                get visibleColumnObjects() {
                    return this.allColumns.filter(col => this.visibleColumns.includes(col.key));
                },"""

new_getter = """                _visibleColumnObjects: [],

                _updateVisibleColumnObjects() {
                    this._visibleColumnObjects = this.allColumns
                        .filter(col => this.visibleColumns.includes(col.key))
                        .map(col => {
                            // Pre-compute CSS class per column (Step 3)
                            let cls = '';
                            if (col.type === 'number') cls += 'cell-number ';
                            if (col.formula) cls += 'cell-formula ';
                            if (col.type === 'url') cls += 'cell-url ';
                            if (col.type === 'single-select' || col.type === 'multi-select') cls += 'cell-select ';
                            if (!col.readOnly && !col.formula && col.type !== 'formula' && col.type !== 'system_generated_value' && col.type !== 'system' && col.key !== 'id') cls += 'cell-editable ';
                            col._cellClass = cls.trim();
                            return col;
                        });
                },

                get visibleColumnObjects() {
                    // Use cached version; fallback to recompute if empty
                    if (this._visibleColumnObjects.length === 0 && this.allColumns.length > 0) {
                        this._updateVisibleColumnObjects();
                    }
                    return this._visibleColumnObjects;
                },"""

if old_getter in js:
    js = js.replace(old_getter, new_getter, 1)
    print("Step 1a: Replaced getter with cached version + _updateVisibleColumnObjects()")
else:
    print("Step 1a: WARN - getter pattern not found")

# 1b. Add _updateVisibleColumnObjects() calls after visibleColumns changes
# After loadColumns() sets allColumns
update_call = 'this._updateVisibleColumnObjects();'

# Find key places where visibleColumns is set and add update calls
# We need to add the call after the main init sequence
# The init() calls loadColumns() then applyColumnOrder() then sets visibleColumns
# Best approach: add after applyColumnOrder in init, and after any visibleColumns assignment

# In toggleColumn:
old_toggle = """                toggleColumn(key) {"""
# Read the full toggleColumn
import re

# Add update call after every this.visibleColumns = ... assignment
# We'll do a targeted approach: after key assignment blocks

# After "this.visibleColumns = this.allColumns.map(col => col.key);" (select all)
js = js.replace(
    "this.visibleColumns = this.allColumns.map(col => col.key);",
    "this.visibleColumns = this.allColumns.map(col => col.key);\n                    this._updateVisibleColumnObjects();",
    1  # only first occurrence (selectAll)
)

# After "this.visibleColumns = ['id'];" (deselectAll)
js = js.replace(
    "this.visibleColumns = ['id'];  // Keep at least ID column visible",
    "this.visibleColumns = ['id'];  // Keep at least ID column visible\n                    this._updateVisibleColumnObjects();"
)

# In toggleColumn function - need to find where it pushes/splices
# toggleColumn modifies this.visibleColumns via push/splice - add update after

# Find toggleColumn function and add update call at the end
toggle_match = re.search(r'(toggleColumn\(key\)\s*\{.*?)(saveColumnOrder)', js, re.DOTALL)
if toggle_match:
    # Add update call before saveColumnOrder
    old_block = toggle_match.group(0)
    new_block = old_block.replace('saveColumnOrder', '_updateVisibleColumnObjects();\n                    this.saveColumnOrder', 1)
    js = js.replace(old_block, new_block, 1)
    print("Step 1b: Added _updateVisibleColumnObjects() to toggleColumn")

# In loadData(), after data loads - add cell cache build (Step 2)
old_load_success = """                        if (data.success) {
                            this.items = data.items;
                            this.total = data.total;
                            this.pages = data.pages;
                        }"""

new_load_success = """                        if (data.success) {
                            this.items = data.items;
                            this.total = data.total;
                            this.pages = data.pages;
                            this._buildCellCache();
                        }"""

if old_load_success in js:
    js = js.replace(old_load_success, new_load_success, 1)
    print("Step 2a: Added _buildCellCache() call in loadData()")
else:
    print("Step 2a: WARN - loadData success pattern not found")

# ============================================================
# STEP 2: Add cell cache methods
# ============================================================

# Find a good place to add - after the loadData function
cell_cache_code = """
                // ===== Cell Format Cache (Performance) =====
                _cellCache: {},

                _buildCellCache() {
                    const cache = {};
                    const cols = this.visibleColumnObjects;
                    for (const item of this.items) {
                        for (const col of cols) {
                            const key = item.id + '__' + col.key;
                            if (col.type === 'single-select' || col.type === 'multi-select') {
                                cache[key] = this.formatCellWithColor(item[col.key], col);
                            } else {
                                cache[key] = this.formatCell(item[col.key], col, item);
                            }
                        }
                    }
                    this._cellCache = cache;
                },

                _getCachedCell(itemId, colKey) {
                    const key = itemId + '__' + colKey;
                    return this._cellCache[key] !== undefined ? this._cellCache[key] : '-';
                },

                _invalidateCellCache(itemId, colKey, newValue, col, item) {
                    // Update single cell in cache
                    const key = itemId + '__' + colKey;
                    if (col.type === 'single-select' || col.type === 'multi-select') {
                        this._cellCache[key] = this.formatCellWithColor(newValue, col);
                    } else {
                        this._cellCache[key] = this.formatCell(newValue, col, item);
                    }
                    // Also update formula cells for this row
                    for (const c of this.visibleColumnObjects) {
                        if (c.formula || c.type === 'formula') {
                            const fKey = itemId + '__' + c.key;
                            this._cellCache[fKey] = this.formatCell(item[c.key], c, item);
                        }
                    }
                },

"""

# Insert before formatCell function
if 'formatCell(value, col, row)' in js:
    js = js.replace(
        '                formatCell(value, col, row) {',
        cell_cache_code + '                formatCell(value, col, row) {',
        1
    )
    print("Step 2b: Added _buildCellCache, _getCachedCell, _invalidateCellCache methods")
else:
    print("Step 2b: WARN - formatCell pattern not found")

# 2c. Update saveInlineEdit to invalidate cache for the edited cell
# Find where it updates item value after save
old_save_pattern = "this.showToast('저장 실패: ' + err.message, 'error');"
# This is in a catch block. Let's find where it sets the item value after successful save
# Look for the pattern where it updates this.items after inline edit save

# Actually, after a successful inline edit, loadData() is often NOT called.
# The item is updated locally. Let's find that pattern.
save_update = re.search(r'(item\[col\.key\]\s*=\s*\w+;)', js)
# Let's search more specifically for the saveInlineEdit function
save_fn_match = re.search(r'async saveInlineEdit\(\)\s*\{', js)
if save_fn_match:
    # After save, the item value is updated and we need to invalidate cache
    # The function calls loadData() at the end in many cases
    # Let's check if loadData is called (which would rebuild cache)
    pass

# Since loadData() is called after save (which rebuilds cache), we just need
# to handle the select dropdown close case where loadData is also called.
# Actually, let's check:
save_inline = re.search(r'saveInlineEdit.*?loadData', js, re.DOTALL)
if save_inline and len(save_inline.group(0)) < 2000:
    print("Step 2c: saveInlineEdit calls loadData (cache auto-rebuilt)")
else:
    print("Step 2c: WARN - check if saveInlineEdit calls loadData manually")

with open(JS_PATH, 'w') as f:
    f.write(js)

print("JS changes saved")

# ============================================================
# STEP 2d + 3: Update HTML template
# ============================================================

with open(HTML_PATH, 'r') as f:
    html = f.read()

# Replace the inner cell template to use cached cell values
# OLD: Two x-if branches (select vs non-select) with formatCell/formatCellWithColor calls
# NEW: Single getCachedCell call

old_cell_display = """                                        <template x-if="!isEditing(item.id, col.key)">
                                            <div>
                                                <template x-if="col.type === 'single-select' || col.type === 'multi-select'">
                                                    <div class="select-tag-cell"
                                                         @click.stop="openSelectDropdown($event, item, col)"
                                                         style="cursor: pointer; min-height: 24px;">
                                                        <span x-html="formatCellWithColor(item[col.key], col)"></span>
                                                    </div>
                                                </template>
                                                <template x-if="col.type !== 'single-select' && col.type !== 'multi-select'">
                                                    <span x-html="formatCell(item[col.key], col, item)"></span>
                                                </template>
                                            </div>
                                        </template>"""

new_cell_display = """                                        <template x-if="!isEditing(item.id, col.key)">
                                            <div :class="{'select-tag-cell': col.type === 'single-select' || col.type === 'multi-select'}"
                                                 :style="(col.type === 'single-select' || col.type === 'multi-select') ? 'cursor:pointer;min-height:24px' : ''"
                                                 @click.stop="(col.type === 'single-select' || col.type === 'multi-select') ? openSelectDropdown($event, item, col) : startInlineEdit(item, col)">
                                                <span x-html="_getCachedCell(item.id, col.key)"></span>
                                            </div>
                                        </template>"""

if old_cell_display in html:
    html = html.replace(old_cell_display, new_cell_display, 1)
    print("Step 2d: Replaced cell display with _getCachedCell (2 x-if -> 1)")
else:
    print("Step 2d: WARN - cell display pattern not found, trying alternative")
    # Try a more flexible match
    if 'formatCellWithColor(item[col.key], col)' in html and 'formatCell(item[col.key], col, item)' in html:
        html = html.replace(
            'x-html="formatCellWithColor(item[col.key], col)"',
            'x-html="_getCachedCell(item.id, col.key)"'
        )
        html = html.replace(
            'x-html="formatCell(item[col.key], col, item)"',
            'x-html="_getCachedCell(item.id, col.key)"'
        )
        print("Step 2d: Replaced formatCell/formatCellWithColor calls individually")

# STEP 3: Simplify :class binding on cells
old_class = """:class="{
                                            'cell-number': col.type === 'number',
                                            'cell-formula': col.formula,
                                            'cell-url': col.type === 'url',
                                            'cell-select': col.type === 'single-select' || col.type === 'multi-select',
                                            'cell-editing': isEditing(item.id, col.key),
                                            'cell-editable': !col.readOnly && !col.formula && col.type !== 'formula' && col.type !== 'system_generated_value' && col.key !== 'id'
                                        }"""

new_class = """:class="col._cellClass + (isEditing(item.id, col.key) ? ' cell-editing' : '')\""""

if old_class in html:
    html = html.replace(old_class, new_class, 1)
    print("Step 3: Simplified :class binding (6 conditions -> 1 string + 1 check)")
else:
    print("Step 3: WARN - :class pattern not found")

# Bump cache versions
import time
ts = str(int(time.time()))
html = re.sub(r'database_list\.js\?v=\d+', f'database_list.js?v={ts}', html)
html = re.sub(r'database_list\.css\?v=\d+', f'database_list.css?v={ts}', html)
print(f"Bumped versions to {ts}")

with open(HTML_PATH, 'w') as f:
    f.write(html)

print("\nAll steps complete! Restart: sudo systemctl restart property-manager propsheet")
