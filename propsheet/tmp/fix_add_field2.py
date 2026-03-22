#!/usr/bin/env python3
"""Fix add field: auto-show + position selector"""

js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

# 1. Add position to newField state
old_state = """                newField: {
                    name: '',
                    type: 'text'
                },"""
new_state = """                newField: {
                    name: '',
                    type: 'text',
                    position: ''
                },"""
if "'position'" not in js.split('newField:')[1].split('},')[0]:
    js = js.replace(old_state, new_state, 1)
    print("1. Added position to newField state")

# 2. Update saveNewField: auto-show + position
old_success = """                        if (result.success) {
                            this.showToast('필드가 추가되었습니다', 'success');
                            this.closeAddField();
                            await this.loadColumns(); // Reload columns
                            this.applyColumnOrder();
                            this.loadData();"""

new_success = """                        if (result.success) {
                            const newColKey = this.newField.name;
                            const insertBefore = this.newField.position;
                            this.showToast('필드가 추가되었습니다', 'success');
                            this.closeAddField();
                            await this.loadColumns();
                            this.applyColumnOrder();
                            // Auto-show new field at specified position
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

if 'Auto-show new field' not in js:
    js = js.replace(old_success, new_success, 1)
    print("2. Updated saveNewField with auto-show + position")

with open(js_path, 'w') as f:
    f.write(js)

# 3. HTML: Add position dropdown
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

# Find the add field modal's actions section
# Use unique context: it's after "새 필드 추가" heading
add_field_idx = html.index('새 필드 추가')
# Find the modal-actions after this point
actions_search = html[add_field_idx:]
actions_idx = actions_search.index('<div class="modal-actions">')
absolute_idx = add_field_idx + actions_idx

position_html = """            <div class="form-group">
                <label>추가 위치</label>
                <select x-model="newField.position">
                    <option value="">맨 뒤</option>
                    <template x-for="col in visibleColumnObjects" :key="col.key">
                        <option :value="col.key" x-text="col.label + ' 앞'"></option>
                    </template>
                </select>
            </div>

            """

if '추가 위치' not in html:
    html = html[:absolute_idx] + position_html + html[absolute_idx:]
    print("3. Added position dropdown to modal")

with open(html_path, 'w') as f:
    f.write(html)

print("Done!")
