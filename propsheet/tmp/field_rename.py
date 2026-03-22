#!/usr/bin/env python3
"""
1. Add api_key column to field_definitions (copy from field_name)
2. Add display_name support to schema_service (return display_name as label)
3. Allow field name editing (updates display_name only, not column/api_key)
4. Show api_key in field settings modal (read-only, copy button)
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')

# === 1. DB: Add api_key column, populate from field_name ===
from services.database_service import get_db_connection
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE field_definitions ADD COLUMN IF NOT EXISTS api_key VARCHAR(255)")
        # Populate api_key from field_name where NULL
        cur.execute("UPDATE field_definitions SET api_key = field_name WHERE api_key IS NULL OR api_key = ''")
        conn.commit()
        print(f"1. DB: api_key column added and populated ({cur.rowcount} rows)")

# === 2. schema_service.py: Return display_name as label, add apiKey ===
schema_path = 'services/schema_service.py'
with open(schema_path, 'r') as f:
    content = f.read()

# Add api_key to SELECT query
if 'api_key' not in content.split('SELECT field_name')[1].split('FROM')[0]:
    content = content.replace(
        'select_colors, number_format, date_format',
        'select_colors, number_format, date_format, api_key'
    )
    print("2a. Added api_key to SELECT")

# Add api_key extraction
if "field_def.get('api_key')" not in content:
    content = content.replace(
        "date_format = field_def.get('date_format') if field_def else None",
        "date_format = field_def.get('date_format') if field_def else None\n                api_key = field_def.get('api_key') if field_def else col_name"
    )
    print("2b. Added api_key extraction")

# Use display_name as label if available
if "'apiKey'" not in content:
    content = content.replace(
        "'dateFormat': date_format,",
        "'dateFormat': date_format,\n                    'apiKey': api_key or col_name,"
    )
    print("2c. Added apiKey to column output")

# Change label to use display_name
if 'display_name' not in content.split("'label':")[0].split("'key':")[1] if "'label':" in content else '':
    old_label = "'label': col_name,"
    new_label = "'label': (field_def.get('display_name') or col_name) if field_def else col_name,"
    if old_label in content:
        content = content.replace(old_label, new_label, 1)
        print("2d. Label now uses display_name")

with open(schema_path, 'w') as f:
    f.write(content)

# === 3. routes/database.py: Update field-definition save to handle display_name rename ===
db_route_path = 'routes/database.py'
with open(db_route_path, 'r') as f:
    content = f.read()

if 'display_name' not in content.split('field-definition')[1].split('def ')[0] if 'field-definition' in content else '':
    # Add display_name to the save logic
    old_save = "field_name = data.get('field_name')\n        field_type = data.get('field_type')"
    new_save = "field_name = data.get('field_name')\n        display_name = data.get('display_name')\n        field_type = data.get('field_type')"
    if old_save in content:
        content = content.replace(old_save, new_save, 1)

    # Add display_name to UPDATE query
    old_update = "SET field_type = %s,"
    new_update = "SET display_name = COALESCE(%s, display_name),\n                            field_type = %s,"
    if old_update in content and 'COALESCE(%s, display_name)' not in content:
        content = content.replace(old_update, new_update, 1)
        # Add display_name to UPDATE params
        old_params = "''', (field_type, column_width, formula, select_options,"
        new_params = "''', (display_name, field_type, column_width, formula, select_options,"
        if old_params in content:
            content = content.replace(old_params, new_params, 1)

    with open(db_route_path, 'w') as f:
        f.write(content)
    print("3. routes: Added display_name save")

# === 4. JS: Enable field name editing + show api_key ===
js_path = 'static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

# Add apiKey to editingField
if 'apiKey: col.apiKey' not in js:
    js = js.replace(
        "isSystem: col.type === 'system' || col.key === 'id',",
        "isSystem: col.type === 'system' || col.key === 'id',\n                        apiKey: col.apiKey || col.key,"
    )
    print("4a. Added apiKey to editingField")

# Add display_name to save payload
if 'payload.display_name' not in js:
    old_payload = "field_name: this.editingField.key,"
    new_payload = "field_name: this.editingField.key,\n                        display_name: this.editingField.label,"
    if old_payload in js:
        js = js.replace(old_payload, new_payload, 1)
        print("4b. Added display_name to save payload")

with open(js_path, 'w') as f:
    f.write(js)

# === 5. HTML: Enable field name input + add api_key display ===
html_path = 'templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

# Replace readonly field name input with editable + api_key display
old_field_name = """                    <div class="form-group">
                        <label>필드 이름</label>
                        <input type="text" x-model="editingField.label" readonly disabled>
                        <div class="hint">필드 이름은 변경할 수 없습니다</div>
                    </div>"""

new_field_name = """                    <div class="form-group">
                        <label>필드 이름</label>
                        <template x-if="!editingField.isSystem">
                            <input type="text" x-model="editingField.label">
                        </template>
                        <template x-if="editingField.isSystem">
                            <input type="text" x-model="editingField.label" readonly disabled>
                        </template>
                    </div>
                    <div class="form-group" x-show="editingField.apiKey">
                        <label>API Key</label>
                        <div style="display:flex;align-items:center;gap:6px;">
                            <input type="text" :value="editingField.apiKey" readonly disabled style="flex:1;background:var(--gray-50);color:var(--gray-600);font-family:monospace;font-size:12px;">
                            <button type="button" @click="navigator.clipboard.writeText(editingField.apiKey); $el.textContent='복사됨!'; setTimeout(()=>$el.textContent='복사', 1500)" style="padding:4px 10px;border:1px solid var(--gray-300);border-radius:4px;background:white;cursor:pointer;font-size:12px;white-space:nowrap;">복사</button>
                        </div>
                        <div class="hint">외부 연동 시 사용되는 고정 식별자 (변경 불가)</div>
                    </div>"""

if old_field_name in html:
    html = html.replace(old_field_name, new_field_name, 1)
    print("5. HTML: Enabled field name editing + api_key display")

import re
html = re.sub(r'database_list\.js\?v=\w+', 'database_list.js?v=20260318f', html)

with open(html_path, 'w') as f:
    f.write(html)

print("\nDone!")
