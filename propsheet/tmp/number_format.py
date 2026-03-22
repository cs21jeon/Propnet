#!/usr/bin/env python3
import re

# === 1. DB: Add number_format column ===
print("=== 1. DB Migration ===")
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE field_definitions ADD COLUMN IF NOT EXISTS number_format JSONB DEFAULT '{}'")
        conn.commit()
print("1. DB: Added number_format column")

# === 2. schema_service.py: Pass number_format to frontend ===
schema_path = "/home/webapp/goldenrabbit/backend/property-manager/services/schema_service.py"
with open(schema_path, "r") as f:
    content = f.read()

if 'number_format' not in content:
    content = content.replace(
        "select_colors = field_def.get('select_colors') if field_def else None",
        "select_colors = field_def.get('select_colors') if field_def else None\n                number_format = field_def.get('number_format') if field_def else None"
    )
    content = content.replace(
        "'selectColors': select_colors,",
        "'selectColors': select_colors,\n                    'numberFormat': number_format,"
    )
    # Add to query
    content = content.replace(
        "select_colors",
        "select_colors, number_format",
        1  # only the SELECT query
    )
    # Fix: the above replaced too many. Let's be precise
    with open(schema_path, "w") as f:
        f.write(content)
    print("2. schema_service: Added number_format")
else:
    print("2. schema_service: Already has number_format")

# Verify the SELECT query
with open(schema_path, "r") as f:
    content = f.read()
if 'number_format' in content and content.count('number_format') >= 3:
    print("   Verified: number_format in query, extraction, and output")

# === 3. routes/database.py: Save number_format ===
db_path = "/home/webapp/goldenrabbit/backend/property-manager/routes/database.py"
with open(db_path, "r") as f:
    content = f.read()

if 'number_format' not in content:
    # Add to data extraction
    content = content.replace(
        "select_colors = data.get('select_colors')  # color map {option: {bg, text}}",
        "select_colors = data.get('select_colors')  # color map {option: {bg, text}}\n        number_format = data.get('number_format')  # {thousands: bool, decimals: int, allowNegative: bool}"
    )

    # Add to UPDATE query
    content = content.replace(
        "select_colors = %s,\n                            is_editable",
        "select_colors = %s,\n                            number_format = %s,\n                            is_editable"
    )
    # Add to UPDATE params
    content = content.replace(
        "json_mod.dumps(select_colors) if select_colors else None, is_editable, system_value_key, field_name))",
        "json_mod.dumps(select_colors) if select_colors else None, json_mod.dumps(number_format) if number_format else None, is_editable, system_value_key, field_name))"
    )

    # Add to INSERT columns
    content = content.replace(
        "(field_name, display_name, field_type, column_width, formula, select_options, select_colors, is_editable, system_value_key)",
        "(field_name, display_name, field_type, column_width, formula, select_options, select_colors, number_format, is_editable, system_value_key)"
    )
    # Add to INSERT values
    content = content.replace(
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    content = content.replace(
        "json_mod.dumps(select_colors) if select_colors else None, is_editable, system_value_key))",
        "json_mod.dumps(select_colors) if select_colors else None, json_mod.dumps(number_format) if number_format else None, is_editable, system_value_key))"
    )

    with open(db_path, "w") as f:
        f.write(content)
    print("3. routes: Added number_format save")
else:
    print("3. routes: Already has number_format")

# === 4. JS: Format numbers using col.numberFormat ===
js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

# Replace simple number formatting
old_num = "case 'number':\n                            return Number(value).toLocaleString();"
new_num = """case 'number': {
                            const num = Number(value);
                            if (isNaN(num)) return String(value);
                            const fmt = col.numberFormat || {};
                            const decimals = (fmt.decimals !== undefined && fmt.decimals !== null) ? fmt.decimals : -1;
                            const thousands = fmt.thousands !== false; // default true
                            const allowNeg = fmt.allowNegative !== false; // default true
                            let val = (!allowNeg && num < 0) ? 0 : num;
                            if (decimals >= 0) {
                                val = val.toFixed(decimals);
                                if (thousands) {
                                    const parts = val.split('.');
                                    parts[0] = parts[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
                                    return parts.join('.');
                                }
                                return val;
                            }
                            return thousands ? val.toLocaleString() : String(val);
                        }"""

if old_num in js:
    js = js.replace(old_num, new_num, 1)
    print("4. JS: Updated number formatting with col.numberFormat")
else:
    print("4. WARN: number format pattern not found")

# Add numberFormat to editingField
old_edit = "selectColors: col.selectColors ? {...col.selectColors} : {},"
new_edit = """selectColors: col.selectColors ? {...col.selectColors} : {},
                        numberFormat: col.numberFormat ? {...col.numberFormat} : { thousands: true, decimals: -1, allowNegative: true },"""

if 'numberFormat: col.numberFormat' not in js:
    js = js.replace(old_edit, new_edit, 1)
    print("5. JS: Added numberFormat to editingField")

# Add numberFormat to save payload
old_save_end = "payload.select_colors = colors;"
new_save_end = """payload.select_colors = colors;
                    }
                    if (this.editingField.type === 'number' || this.editingField.type === 'formula') {
                        payload.number_format = this.editingField.numberFormat;"""
# This is tricky - need to add after the select block closes. Let's find a better approach.
# Actually, add it as a separate block after the select block
old_payload_end = """payload.select_colors = colors;
                    }"""
new_payload_end = """payload.select_colors = colors;
                    }
                    if (this.editingField.numberFormat && (this.editingField.type === 'number' || this.editingField.type === 'formula')) {
                        payload.number_format = this.editingField.numberFormat;
                    }"""

if 'payload.number_format' not in js:
    # Find the last occurrence of the select_colors block closing
    if old_payload_end in js:
        js = js.replace(old_payload_end, new_payload_end, 1)
        print("6. JS: Added numberFormat to save payload")
    else:
        print("6. WARN: payload end pattern not found")

with open(js_path, "w") as f:
    f.write(js)

# === 5. HTML: Add number format options in field settings ===
html_path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(html_path, "r") as f:
    html = f.read()

# Add number format section after the type select, before formula section
num_format_html = """                    <template x-if="editingField.type === 'number' || (editingField.type === 'formula')">
                        <div class="form-group" style="display:flex;flex-direction:column;gap:10px;">
                            <label>숫자 형식</label>
                            <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;">
                                <label style="display:flex;align-items:center;gap:4px;font-size:13px;cursor:pointer;">
                                    <input type="checkbox" x-model="editingField.numberFormat.thousands"> 1,000 단위 쉼표
                                </label>
                                <label style="display:flex;align-items:center;gap:4px;font-size:13px;cursor:pointer;">
                                    <input type="checkbox" x-model="editingField.numberFormat.allowNegative"> 음수 허용
                                </label>
                            </div>
                            <div style="display:flex;align-items:center;gap:8px;">
                                <label style="font-size:13px;white-space:nowrap;">소수점 자릿수</label>
                                <select x-model.number="editingField.numberFormat.decimals" style="padding:4px 8px;border:1px solid var(--gray-300);border-radius:4px;font-size:13px;">
                                    <option :value="-1">자동</option>
                                    <option :value="0">0 (정수)</option>
                                    <option :value="1">1</option>
                                    <option :value="2">2</option>
                                    <option :value="3">3</option>
                                    <option :value="4">4</option>
                                </select>
                                <span style="color:var(--gray-500);font-size:12px;" x-text="editingField.numberFormat.decimals >= 0 ? '예: ' + (1234.5678).toFixed(editingField.numberFormat.decimals) : '예: 1234.5678'"></span>
                            </div>
                        </div>
                    </template>

"""

# Insert before the formula section
formula_marker = '                    <template x-if="editingField.type === \'formula\'">'
if '숫자 형식' not in html:
    html = html.replace(formula_marker, num_format_html + formula_marker, 1)
    print("7. HTML: Added number format options UI")

# Bump versions
html = re.sub(r'database_list\.js\?v=\w+', 'database_list.js?v=20260317k', html)
html = re.sub(r'database_list\.css\?v=\w+', 'database_list.css?v=20260317k', html)

with open(html_path, "w") as f:
    f.write(html)

print("\nDone!")
