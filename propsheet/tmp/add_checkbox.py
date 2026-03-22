#!/usr/bin/env python3
"""Add checkbox field type to Propsheet"""

HTML_PATH = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
JS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
SCHEMA_PATH = '/home/webapp/goldenrabbit/backend/property-manager/services/schema_service.py'

# ============================================================
# 1. HTML: Add checkbox option to both field type dropdowns
# ============================================================
with open(HTML_PATH, 'r') as f:
    html = f.read()

# Add after attachment option in field add modal
html = html.replace(
    '                    <option value="attachment">File (파일/이미지)</option>\n                </select>',
    '                    <option value="attachment">File (파일/이미지)</option>\n                    <option value="checkbox">Checkbox (체크박스)</option>\n                </select>',
    1
)

# Add after attachment option in field settings modal
html = html.replace(
    '                            <option value="attachment">File (파일/이미지)</option>\n                        </select>',
    '                            <option value="attachment">File (파일/이미지)</option>\n                            <option value="checkbox">Checkbox (체크박스)</option>\n                        </select>',
    1
)

# Add checkbox rendering in detail panel (before the normal field template)
# In the detail panel, checkbox should show as a toggle
old_detail_normal = """                                <template x-if="col.type !== 'single-select' && col.type !== 'multi-select' && col.type !== 'attachment'">"""
new_detail_normal = """                                <!-- Checkbox field -->
                                <template x-if="col.type === 'checkbox'">
                                    <div style="padding:4px 0;">
                                        <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
                                            <input type="checkbox"
                                                   :checked="detailPanel.item[col.key] === true || detailPanel.item[col.key] === 'true' || detailPanel.item[col.key] === 1 || detailPanel.item[col.key] === '1'"
                                                   @change="detailPanel.item[col.key] = $event.target.checked; saveCheckboxField(col.key, $event.target.checked)"
                                                   style="width:18px;height:18px;cursor:pointer;">
                                            <span x-text="(detailPanel.item[col.key] === true || detailPanel.item[col.key] === 'true' || detailPanel.item[col.key] === 1 || detailPanel.item[col.key] === '1') ? '예' : '아니오'" style="font-size:13px;color:var(--text-secondary);"></span>
                                        </label>
                                    </div>
                                </template>
                                <template x-if="col.type !== 'single-select' && col.type !== 'multi-select' && col.type !== 'attachment' && col.type !== 'checkbox'">"""

if old_detail_normal in html:
    html = html.replace(old_detail_normal, new_detail_normal, 1)
    print("1a. Added checkbox to detail panel")
else:
    print("1a. WARN: detail panel pattern not found")

# Bump version
html = html.replace("database_list.js') }}?v=1774004400", "database_list.js') }}?v=1774004500")
html = html.replace("database_list.css') }}?v=", "database_list.css') }}?v=1774004500____").replace("?v=1774004500____", "?v=1774004500")

with open(HTML_PATH, 'w') as f:
    f.write(html)
print("1b. Updated HTML")

# ============================================================
# 2. JS: Add checkbox rendering in formatCell + saveCheckboxField
# ============================================================
with open(JS_PATH, 'r') as f:
    js = f.read()

# Add checkbox case in formatCell switch
old_switch = "                        case 'single-select':\n                        case 'multi-select':"
new_switch = """                        case 'checkbox': {
                            const checked = value === true || value === 'true' || value === 1 || value === '1';
                            return checked
                                ? '<span style="color:#388e3c;font-size:16px;">&#9745;</span>'
                                : '<span style="color:#999;font-size:16px;">&#9744;</span>';
                        }
                        case 'single-select':
                        case 'multi-select':"""

if old_switch in js:
    js = js.replace(old_switch, new_switch, 1)
    print("2a. Added checkbox to formatCell")

# Add saveCheckboxField method
checkbox_method = """
                async saveCheckboxField(fieldKey, checked) {
                    const itemId = this.detailPanel.itemId;
                    const value = checked ? 'true' : 'false';
                    try {
                        const res = await fetch(`${basePath}/api/database/property/${itemId}/field`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                field: fieldKey,
                                value: value,
                                db: this.databaseId,
                                updated_at: this.detailPanel.item.updated_at || null
                            })
                        });
                        const data = await res.json();
                        if (data.success) {
                            const item = this.items.find(i => i.id === itemId);
                            if (item) item[fieldKey] = value;
                            await this.refreshRecord(itemId);
                        }
                    } catch (e) {}
                },

"""

if 'saveCheckboxField' not in js:
    js = js.replace(
        '                getDetailDisplayValue(fieldKey) {',
        checkbox_method + '                getDetailDisplayValue(fieldKey) {',
        1
    )
    print("2b. Added saveCheckboxField method")

# Add checkbox click handler for inline cells (toggle on click)
# In startInlineEdit, skip checkbox type (handle directly)
old_start = "                    if (col.type === 'single-select' || col.type === 'multi-select') return;"
new_start = """                    if (col.type === 'single-select' || col.type === 'multi-select') return;
                    // Checkbox: toggle directly without edit mode
                    if (col.type === 'checkbox') {
                        const current = item[col.key];
                        const newVal = (current === true || current === 'true' || current === 1 || current === '1') ? 'false' : 'true';
                        item[col.key] = newVal;
                        this.saveInlineCheckbox(item.id, col.key, newVal);
                        return;
                    }"""

if old_start in js:
    js = js.replace(old_start, new_start, 1)
    print("2c. Added checkbox toggle in startInlineEdit")

# Add saveInlineCheckbox
inline_checkbox = """
                async saveInlineCheckbox(itemId, colKey, value) {
                    try {
                        await fetch(`${basePath}/api/database/property/${itemId}/field`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ field: colKey, value: value, db: this.databaseId })
                        });
                        await this.refreshRecord(itemId);
                    } catch (e) {}
                },

"""

if 'saveInlineCheckbox' not in js:
    js = js.replace(
        '                async saveCheckboxField',
        inline_checkbox + '                async saveCheckboxField',
        1
    )
    print("2d. Added saveInlineCheckbox method")

with open(JS_PATH, 'w') as f:
    f.write(js)

# ============================================================
# 3. Schema: Add checkbox type recognition
# ============================================================
with open(SCHEMA_PATH, 'r') as f:
    schema = f.read()

if "'checkbox'" not in schema:
    schema = schema.replace(
        "                    elif explicit_type == 'attachment':\n                        field_type = 'attachment'",
        "                    elif explicit_type == 'attachment':\n                        field_type = 'attachment'\n                    elif explicit_type == 'checkbox':\n                        field_type = 'checkbox'",
        1
    )
    with open(SCHEMA_PATH, 'w') as f:
        f.write(schema)
    print("3. Added checkbox to schema_service")

# Verify JS
import subprocess
result = subprocess.run(['node', '-c', JS_PATH], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')

print("\nDone!")
