#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

# Remove the entire x-for block for items (replace with empty - renderTable handles it)
old_xfor = """                        <template x-for="item in items" :key="item.id">
                            <tr>
                                <td class="cell-expand" @click.stop="openDetailPanel(item.id)" title="상세 보기" style="width:30px;min-width:30px;max-width:30px;text-align:center;cursor:pointer;color:var(--gray-400);">
                                    <span style="font-size:14px">▶</span>
                                </td>
                                <template x-for="col in visibleColumnObjects" :key="col.key">
                                    <td :data-col-key="col.key"
                                        :style="(w => `width: ${w}px; min-width: ${w}px; max-width: ${w}px;`)(columnWidths[col.key] || col.defaultWidth || 150)"
                                        :class="{
                                            'cell-number': col.type === 'number',
                                            'cell-formula': col.formula,
                                            'cell-url': col.type === 'url',
                                            'cell-select': col.type === 'single-select' || col.type === 'multi-select',
                                            'cell-editing': isEditing(item.id, col.key),
                                            'cell-editable': !col.readOnly && !col.formula && col.type !== 'formula' && col.type !== 'system_generated_value' && col.key !== 'id'
                                        }"
                                        @click.stop="startInlineEdit(item, col)">
                                        <!-- Inline editing input -->
                                        <template x-if="isEditing(item.id, col.key)">
                                            <input class="cell-edit-input"
                                                   :type="getEditInputType(col)"
                                                   x-model="editingCell.value"
                                                   @blur="saveInlineEdit()"
                                                   @keydown="handleEditKeydown($event, item, col)"
                                                   @click.stop>
                                        </template>
                                        <!-- Normal display -->
                                        <template x-if="!isEditing(item.id, col.key)">
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
                                        </template>
                                    </td>
                                </template>
                            </tr>
                        </template>"""

new_xfor = """                        <!-- Rendered by renderTable() in JS -->"""

if old_xfor in html:
    html = html.replace(old_xfor, new_xfor, 1)
    print("Removed Alpine x-for tbody template")
else:
    print("WARN: x-for pattern not found")

# Bump version
html = html.replace('v=20260317v', 'v=20260317w')

with open(path, 'w') as f:
    f.write(html)
print("Done")
