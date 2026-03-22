#!/usr/bin/env python3
"""Fix add field: auto-show new field + position selector"""

# === 1. JS: Add position to newField + auto-show after add ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

# Update newField init to include position
old_init = "this.newField = { name: '', type: 'text' };\n                    this.showAddField = true;"
new_init = "this.newField = { name: '', type: 'text', position: '' };\n                    this.showAddField = true;"
js = js.replace(old_init, new_init, 1)

# Update close to reset position too
old_close = "this.newField = { name: '', type: 'text' };"
new_close = "this.newField = { name: '', type: 'text', position: '' };"
# Replace only the second occurrence (in closeAddField)
first_idx = js.index(old_close)
second_idx = js.index(old_close, first_idx + 1)
js = js[:second_idx] + new_close + js[second_idx + len(old_close):]

# Update saveNewField: auto-add to visibleColumns at position + save column order
old_save_success = """                        if (result.success) {
                            this.showToast('필드가 추가되었습니다', 'success');
                            this.closeAddField();
                            await this.loadColumns(); // Reload columns
                            this.applyColumnOrder();
                            this.loadData();"""

new_save_success = """                        if (result.success) {
                            const newColKey = this.newField.name;
                            const insertBefore = this.newField.position;
                            this.showToast('필드가 추가되었습니다', 'success');
                            this.closeAddField();
                            await this.loadColumns();
                            this.applyColumnOrder();

                            // Auto-show the new field
                            if (!this.visibleColumns.includes(newColKey)) {
                                if (insertBefore && this.visibleColumns.includes(insertBefore)) {
                                    const idx = this.visibleColumns.indexOf(insertBefore);
                                    this.visibleColumns.splice(idx, 0, newColKey);
                                } else {
                                    this.visibleColumns.push(newColKey);
                                }
                            }
                            this.saveColumnOrder();
                            this.loadData();"""

if 'Auto-show the new field' not in js:
    js = js.replace(old_save_success, new_save_success, 1)
    print("1. Updated saveNewField with auto-show + position")

with open(js_path, 'w') as f:
    f.write(js)

# === 2. HTML: Add position dropdown to add field modal ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

old_modal = """            <div class="modal-actions">
                <button class="btn-cancel" @click="closeAddField()">취소</button>
                <button class="btn-save" @click="saveNewField()">추가</button>
            </div>
        </div>
    </div>"""

# Check this is in the add field modal context
if old_modal in html:
    new_modal = """            <div class="form-group">
                <label>추가 위치</label>
                <select x-model="newField.position">
                    <option value="">맨 뒤</option>
                    <template x-for="col in visibleColumnObjects" :key="col.key">
                        <option :value="col.key" x-text="col.label + ' 앞'"></option>
                    </template>
                </select>
            </div>

            <div class="modal-actions">
                <button class="btn-cancel" @click="closeAddField()">취소</button>
                <button class="btn-save" @click="saveNewField()">추가</button>
            </div>
        </div>
    </div>"""

    # Only replace the one in add field modal (find by context)
    add_field_start = html.index('새 필드 추가')
    add_field_section = html[add_field_start:]
    modal_idx = add_field_section.index(old_modal)
    absolute_idx = add_field_start + modal_idx

    html = html[:absolute_idx] + new_modal + html[absolute_idx + len(old_modal):]
    print("2. Added position dropdown to add field modal")

with open(html_path, 'w') as f:
    f.write(html)

print("Done!")
