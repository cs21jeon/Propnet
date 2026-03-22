#!/usr/bin/env python3
"""Step 4: Floating editor - remove per-cell isEditing x-if"""

HTML_PATH = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
JS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'

# ============ HTML changes ============
with open(HTML_PATH, 'r') as f:
    html = f.read()

# 4a. Remove per-cell editing templates
old_cell = (
    '                                        <!-- Inline editing input -->\n'
    '                                        <template x-if="isEditing(item.id, col.key)">\n'
    '                                            <input class="cell-edit-input"\n'
    '                                                   :type="getEditInputType(col)"\n'
    '                                                   x-model="editingCell.value"\n'
    '                                                   @blur="saveInlineEdit()"\n'
    '                                                   @keydown="handleEditKeydown($event, item, col)"\n'
    '                                                   @click.stop>\n'
    '                                        </template>\n'
    '                                        <!-- Normal display -->\n'
    '                                        <template x-if="!isEditing(item.id, col.key)">\n'
    '                                            <div :class="{\'select-tag-cell\': col.type === \'single-select\' || col.type === \'multi-select\'}"\n'
    '                                                 :style="(col.type === \'single-select\' || col.type === \'multi-select\') ? \'cursor:pointer;min-height:24px\' : \'\'"\n'
    '                                                 @click.stop="(col.type === \'single-select\' || col.type === \'multi-select\') ? openSelectDropdown($event, item, col) : startInlineEdit(item, col)">\n'
    '                                                <span x-html="_getCachedCell(item.id, col.key)"></span>\n'
    '                                            </div>\n'
    '                                        </template>'
)

new_cell = (
    '                                        <!-- Cell content (floating editor overlays on edit) -->\n'
    '                                            <div :class="{\'select-tag-cell\': col.type === \'single-select\' || col.type === \'multi-select\'}"\n'
    '                                                 :style="(col.type === \'single-select\' || col.type === \'multi-select\') ? \'cursor:pointer;min-height:24px\' : \'\'"\n'
    '                                                 @click.stop="(col.type === \'single-select\' || col.type === \'multi-select\') ? openSelectDropdown($event, item, col) : startInlineEdit(item, col)">\n'
    '                                                <span x-html="_getCachedCell(item.id, col.key)"></span>\n'
    '                                            </div>'
)

if old_cell in html:
    html = html.replace(old_cell, new_cell, 1)
    print('4a. Removed per-cell isEditing x-if templates')
else:
    print('4a. WARN: cell template pattern not found')

# 4b. Remove isEditing from :class
old_cls = ':class="col._cellClass + (isEditing(item.id, col.key) ? \' cell-editing\' : \'\')"'
new_cls = ':class="col._cellClass"'
if old_cls in html:
    html = html.replace(old_cls, new_cls, 1)
    print('4b. Removed isEditing from td :class')

# 4c. Add floating editor before pagination
floating = '''
            <!-- Floating inline editor (single instance, positioned over active cell) -->
            <div x-show="editingCell.itemId !== null"
                 x-cloak
                 class="floating-edit-container"
                 :style="editingCell._style || 'display:none'"
                 @click.stop>
                <input class="cell-edit-input floating-edit-input"
                       :type="editingCell._inputType || 'text'"
                       x-model="editingCell.value"
                       @blur="saveInlineEdit()"
                       @keydown="handleEditKeydown($event, editingCell._item, editingCell._col)"
                       x-ref="floatingEditInput">
            </div>
'''
if 'floating-edit-container' not in html:
    html = html.replace('<div class="pagination">', floating + '            <div class="pagination">', 1)
    print('4c. Added floating editor element')

with open(HTML_PATH, 'w') as f:
    f.write(html)

# ============ JS changes ============
with open(JS_PATH, 'r') as f:
    js = f.read()

# 4d. Modify startInlineEdit to position floating editor
# Find the startInlineEdit function and add positioning logic
old_start = "                    // Save current editing cell first"
new_start = """                    // Position floating editor over the clicked cell
                    const td = event ? (event.target.closest ? event.target.closest('td') : null) : null;

                    // Save current editing cell first"""

if old_start in js:
    js = js.replace(old_start, new_start, 1)
    print('4d. Added td detection in startInlineEdit')

# Add style computation after editingCell assignment
old_editing_set = """                    this.editingCell = {
                        itemId: item.id,
                        colKey: col.key,
                        value: editValue,
                        originalValue: editValue
                    };"""

new_editing_set = """                    this.editingCell = {
                        itemId: item.id,
                        colKey: col.key,
                        value: editValue,
                        originalValue: editValue,
                        _inputType: this.getEditInputType(col),
                        _item: item,
                        _col: col,
                        _style: ''
                    };

                    // Position floating editor over the cell
                    if (td) {
                        const rect = td.getBoundingClientRect();
                        this.editingCell._style = `position:fixed;left:${rect.left}px;top:${rect.top}px;width:${rect.width}px;height:${rect.height}px;z-index:100;`;
                    }"""

if old_editing_set in js:
    js = js.replace(old_editing_set, new_editing_set, 1)
    print('4e. Added floating editor positioning in startInlineEdit')

# Update focus logic to use floatingEditInput ref
old_focus = "// Focus the input after Alpine renders it"
new_focus = "// Focus the floating input after Alpine renders it"
if old_focus in js:
    js = js.replace(old_focus, new_focus, 1)

# Find the $nextTick focus and update ref
old_nexttick = "this.$nextTick(() => {"
# This might match multiple places, so let's be more specific
import re
# Find the focus logic near startInlineEdit
focus_pattern = re.search(r'(\$nextTick\(\(\) => \{[^}]*?\.focus\(\))', js)
if focus_pattern:
    old_focus_block = focus_pattern.group(0)
    if 'floatingEditInput' not in old_focus_block:
        new_focus_block = old_focus_block.replace('.focus()', '.focus()')
        # Actually we need to change the selector to use $refs.floatingEditInput
        if 'cell-edit-input' in old_focus_block:
            new_focus_block = "$nextTick(() => { if(this.$refs.floatingEditInput) this.$refs.floatingEditInput.focus()"
            js = js.replace(old_focus_block, new_focus_block, 1)
            print('4f. Updated focus to use floatingEditInput ref')

with open(JS_PATH, 'w') as f:
    f.write(js)

# ============ CSS changes ============
CSS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(CSS_PATH, 'r') as f:
    css = f.read()

if 'floating-edit-container' not in css:
    css += """
/* Floating inline editor */
.floating-edit-container {
    position: fixed;
    z-index: 100;
    background: #fff;
    box-shadow: 0 0 0 2px var(--brand-blue, #667eea);
    border-radius: 2px;
}
.floating-edit-input {
    width: 100% !important;
    height: 100% !important;
    border: none !important;
    outline: none !important;
    padding: 4px 8px !important;
    font-size: 13px !important;
    box-sizing: border-box;
}
"""
    with open(CSS_PATH, 'w') as f:
        f.write(css)
    print('4g. Added floating editor CSS')

print('\nStep 4 complete!')
