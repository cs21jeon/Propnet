#!/usr/bin/env python3
"""
Implement virtual scrolling for Propsheet.
Only render visible rows (~30) instead of all rows (367+).
"""

JS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list_v2.js'
HTML_PATH = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
CSS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list_v2.css'

# ============================================================
# STEP A: JS — Add virtual scroll state and methods
# ============================================================

with open(JS_PATH, 'r') as f:
    js = f.read()

# A1. Add virtual scroll constants and state after _visibleColumnObjects
vs_state = """
                // ===== Virtual Scroll =====
                _ROW_HEIGHT: 36,
                _BUFFER_ROWS: 5,
                _scrollTop: 0,
                _containerHeight: 600,
                _useVirtualScroll: false,

"""

# Insert after _visibleColumnObjects: [],
js = js.replace(
    "                _visibleColumnObjects: [],\n",
    "                _visibleColumnObjects: [],\n" + vs_state,
    1
)
print("A1. Added virtual scroll state")

# A2. Add _visibleItems getter after the visibleColumnObjects getter
vs_getter = """
                get _visibleItems() {
                    if (!this._useVirtualScroll || this.items.length <= 100) {
                        return this.items;
                    }
                    const startRow = Math.max(0, Math.floor(this._scrollTop / this._ROW_HEIGHT) - this._BUFFER_ROWS);
                    const visibleCount = Math.ceil(this._containerHeight / this._ROW_HEIGHT) + (this._BUFFER_ROWS * 2);
                    const endRow = Math.min(this.items.length, startRow + visibleCount);
                    return this.items.slice(startRow, endRow);
                },

                get _spacerTop() {
                    if (!this._useVirtualScroll || this.items.length <= 100) return 0;
                    const startRow = Math.max(0, Math.floor(this._scrollTop / this._ROW_HEIGHT) - this._BUFFER_ROWS);
                    return startRow * this._ROW_HEIGHT;
                },

                get _totalHeight() {
                    if (!this._useVirtualScroll || this.items.length <= 100) return 'auto';
                    return (this.items.length * this._ROW_HEIGHT) + 'px';
                },

"""

# Insert after the visibleColumnObjects getter closing
old_filterable = "                get filterableColumns() {"
js = js.replace(old_filterable, vs_getter + old_filterable, 1)
print("A2. Added _visibleItems, _spacerTop, _totalHeight getters")

# A3. Add onVirtualScroll handler and init code
vs_handler = """
                onVirtualScroll(event) {
                    this._scrollTop = event.target.scrollTop;
                    this._containerHeight = event.target.clientHeight;
                    // Close floating editor on scroll
                    if (this.editingCell.itemId !== null) {
                        this.saveInlineEdit();
                    }
                },

"""

# Insert before formatCell
js = js.replace(
    "                // ===== Cell Format Cache",
    vs_handler + "                // ===== Cell Format Cache",
    1
)
print("A3. Added onVirtualScroll handler")

# A4. Enable virtual scroll when perPage is large (전체)
# In loadData, after items are set, enable/disable virtual scroll
old_load = """                            this.items = allItems;
                                this._buildCellCache();
                            }
                        } else {
                                this.items = allItems;
                                this._buildCellCache();
                            }"""

# The batch rendering code has a complex structure, let's find it more carefully
# Find the loadData success block
import re

# Remove the batch rendering entirely and replace with simple + virtual scroll toggle
# Find the pattern with allItems
batch_pattern = re.search(
    r'const allItems = data\.items;.*?this\.pages = data\.pages;.*?(// Batch render.*?)\}',
    js, re.DOTALL
)

if batch_pattern:
    batch_block = batch_pattern.group(0)
    new_block = """const allItems = data.items;
                            this.total = data.total;
                            this.pages = data.pages;
                            this.items = allItems;
                            this._useVirtualScroll = allItems.length > 100;
                            this._scrollTop = 0;
                            this._buildCellCache();
                            // Init container height
                            this.$nextTick(() => {
                                const c = this.$refs.virtualContainer;
                                if (c) this._containerHeight = c.clientHeight;
                            });}"""
    js = js.replace(batch_block, new_block, 1)
    print("A4. Replaced batch rendering with virtual scroll toggle")
else:
    # Try simpler approach - find the success block
    old_success = """                        if (data.success) {
                            const allItems = data.items;
                            this.total = data.total;
                            this.pages = data.pages;

                            // Batch render: first 30 rows immediately, rest deferred
                            const BATCH = 30;
                            if (allItems.length > BATCH) {
                                this.items = allItems.slice(0, BATCH);
                                this._buildCellCache();
                                requestAnimationFrame(() => {
                                    this.items = allItems;
                                    this._buildCellCache();
                                });
                            } else {
                                this.items = allItems;
                                this._buildCellCache();
                            }
                        }"""
    new_success = """                        if (data.success) {
                            this.items = data.items;
                            this.total = data.total;
                            this.pages = data.pages;
                            this._useVirtualScroll = data.items.length > 100;
                            this._scrollTop = 0;
                            this._buildCellCache();
                            this.$nextTick(() => {
                                const c = this.$refs.virtualContainer;
                                if (c) this._containerHeight = c.clientHeight;
                            });
                        }"""
    if old_success in js:
        js = js.replace(old_success, new_success, 1)
        print("A4b. Replaced batch rendering with virtual scroll toggle (alt)")
    else:
        print("A4. WARN: could not find loadData success block to replace")

# A5. Remove old scroll listener for editing (now handled in onVirtualScroll)
old_scroll = """                    // Scroll closes floating editor (prevents position mismatch)
                    const _tableContainer = document.querySelector('.table-container');
                    if (_tableContainer) {
                        _tableContainer.addEventListener('scroll', () => {
                            if (this.editingCell.itemId !== null) {
                                this.saveInlineEdit();
                            }
                        });
                    }

"""
if old_scroll in js:
    js = js.replace(old_scroll, "", 1)
    print("A5. Removed old scroll listener (now in onVirtualScroll)")

with open(JS_PATH, 'w') as f:
    f.write(js)
print("JS saved")

# ============================================================
# STEP B: HTML — Wrap table in virtual scroll container
# ============================================================

with open(HTML_PATH, 'r') as f:
    html = f.read()

# B1. Replace spreadsheet-wrapper div with virtual scroll container
old_wrapper = """        <div class="spreadsheet-container">
            <div class="spreadsheet-wrapper">
                <table class="spreadsheet">"""

new_wrapper = """        <div class="spreadsheet-container">
            <div class="spreadsheet-wrapper"
                 x-ref="virtualContainer"
                 @scroll="onVirtualScroll($event)">
                <!-- Virtual scroll spacer -->
                <div :style="_useVirtualScroll ? 'min-height:' + _totalHeight : ''">
                <table class="spreadsheet" :style="_useVirtualScroll ? 'transform:translateY(' + _spacerTop + 'px)' : ''">"""

if old_wrapper in html:
    html = html.replace(old_wrapper, new_wrapper, 1)
    print("B1. Added virtual scroll container wrapper")
else:
    print("B1. WARN: wrapper pattern not found")

# B2. Change x-for from "items" to "_visibleItems"
old_xfor = 'x-for="item in items" :key="item.id"'
new_xfor = 'x-for="item in _visibleItems" :key="item.id"'
if old_xfor in html:
    html = html.replace(old_xfor, new_xfor, 1)
    print("B2. Changed x-for to use _visibleItems")
else:
    print("B2. WARN: x-for pattern not found")

# B3. Close the spacer div after </table>
old_table_close = """                </table>
            </div>"""
new_table_close = """                </table>
                </div><!-- virtual scroll spacer -->
            </div>"""
# Find the first occurrence (there might be multiple </table> - we want the main one)
if old_table_close in html:
    html = html.replace(old_table_close, new_table_close, 1)
    print("B3. Closed virtual scroll spacer div")

with open(HTML_PATH, 'w') as f:
    f.write(html)
print("HTML saved")

# ============================================================
# STEP C: CSS — Row height fixed + container styles
# ============================================================

with open(CSS_PATH, 'r') as f:
    css = f.read()

vs_css = """
/* Virtual Scroll */
.spreadsheet-wrapper {
    overflow-y: auto !important;
    max-height: calc(100vh - 280px);
}
.spreadsheet tbody tr {
    height: 36px;
    max-height: 36px;
}
.spreadsheet tbody td {
    max-height: 36px;
    line-height: 24px;
}
"""

if 'Virtual Scroll' not in css:
    css += vs_css
    print("C1. Added virtual scroll CSS")

with open(CSS_PATH, 'w') as f:
    f.write(css)

# ============================================================
# STEP D: Verify JS syntax
# ============================================================
import subprocess
result = subprocess.run(['node', '-c', JS_PATH], capture_output=True, text=True)
if result.returncode == 0:
    print("\nJS syntax: OK")
else:
    print(f"\nJS SYNTAX ERROR:\n{result.stderr}")

print("\nDone! Restart: sudo systemctl restart property-manager propsheet")
