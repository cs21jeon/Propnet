#!/usr/bin/env python3
import re, sys, os

sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')

# === 1. DB: Add date_format column ===
from services.database_service import get_db_connection
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE field_definitions ADD COLUMN IF NOT EXISTS date_format JSONB DEFAULT '{}'")
        conn.commit()
print("1. DB: Added date_format column")

# === 2. schema_service.py ===
schema_path = "services/schema_service.py"
with open(schema_path, "r") as f:
    c = f.read()

if 'date_format' not in c:
    c = c.replace(
        "number_format = field_def.get('number_format') if field_def else None",
        "number_format = field_def.get('number_format') if field_def else None\n                date_format = field_def.get('date_format') if field_def else None"
    )
    c = c.replace(
        "'numberFormat': number_format,",
        "'numberFormat': number_format,\n                    'dateFormat': date_format,"
    )
    # Add to SELECT query - find the line with number_format
    c = c.replace(
        "select_colors, number_format",
        "select_colors, number_format, date_format"
    )
    with open(schema_path, "w") as f:
        f.write(c)
    print("2. schema_service: Added date_format")
else:
    print("2. Already has date_format")

# === 3. routes/database.py ===
db_path = "routes/database.py"
with open(db_path, "r") as f:
    c = f.read()

if 'date_format' not in c:
    c = c.replace(
        "number_format = data.get('number_format')",
        "number_format = data.get('number_format')\n        date_format = data.get('date_format')"
    )
    # UPDATE query
    c = c.replace(
        "number_format = %s,\n                            is_editable",
        "number_format = %s,\n                            date_format = %s,\n                            is_editable"
    )
    c = c.replace(
        "json_mod.dumps(number_format) if number_format else None, is_editable, system_value_key, field_name))",
        "json_mod.dumps(number_format) if number_format else None, json_mod.dumps(date_format) if date_format else None, is_editable, system_value_key, field_name))"
    )
    # INSERT columns
    c = c.replace(
        "select_colors, number_format, is_editable, system_value_key)",
        "select_colors, number_format, date_format, is_editable, system_value_key)"
    )
    c = c.replace(
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    c = c.replace(
        "json_mod.dumps(number_format) if number_format else None, is_editable, system_value_key))",
        "json_mod.dumps(number_format) if number_format else None, json_mod.dumps(date_format) if date_format else None, is_editable, system_value_key))"
    )
    with open(db_path, "w") as f:
        f.write(c)
    print("3. routes: Added date_format save")
else:
    print("3. Already has date_format")

# === 4. JS: Update date rendering + editingField + save ===
js_path = "static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

js_changes = 0

# 4a. Replace date case in formatCell
old_date = """case 'date':
                            if (!value) return '-';
                            try {
                                const d = new Date(value);
                                if (!isNaN(d.getTime())) {
                                    return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
                                }
                            } catch {}
                            return String(value);"""

new_date = """case 'date': {
                            if (!value) return '-';
                            try {
                                const d = new Date(value);
                                if (isNaN(d.getTime())) return String(value);
                                const df = col.dateFormat || {};
                                const style = df.style || 'long';
                                const y = d.getFullYear();
                                const m = String(d.getMonth() + 1).padStart(2, '0');
                                const dd = String(d.getDate()).padStart(2, '0');
                                switch (style) {
                                    case 'long': return `${y}년 ${parseInt(m)}월 ${parseInt(dd)}일`;
                                    case 'dot': return `${y}.${m}.${dd}`;
                                    case 'dash': return `${y}-${m}-${dd}`;
                                    case 'slash': return `${y}/${m}/${dd}`;
                                    case 'year': return `${y}`;
                                    case 'yearMonth': return `${y}년 ${parseInt(m)}월`;
                                    case 'yearMonthDot': return `${y}.${m}`;
                                    default: return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
                                }
                            } catch {}
                            return String(value);
                        }"""

if old_date in js:
    js = js.replace(old_date, new_date, 1)
    js_changes += 1

# 4b. Add dateFormat to editingField
old_nf = "numberFormat: col.numberFormat ? {...col.numberFormat} : { thousands: true, decimals: -1, allowNegative: true },"
new_nf = """numberFormat: col.numberFormat ? {...col.numberFormat} : { thousands: true, decimals: -1, allowNegative: true },
                        dateFormat: col.dateFormat ? {...col.dateFormat} : { style: 'long' },"""
if 'dateFormat: col.dateFormat' not in js:
    js = js.replace(old_nf, new_nf, 1)
    js_changes += 1

# 4c. Add dateFormat to save payload
old_nf_save = """if (this.editingField.numberFormat && (this.editingField.type === 'number' || this.editingField.type === 'formula')) {
                        payload.number_format = this.editingField.numberFormat;
                    }"""
new_nf_save = """if (this.editingField.numberFormat && (this.editingField.type === 'number' || this.editingField.type === 'formula')) {
                        payload.number_format = this.editingField.numberFormat;
                    }
                    if (this.editingField.dateFormat && this.editingField.type === 'date') {
                        payload.date_format = this.editingField.dateFormat;
                    }"""
if 'payload.date_format' not in js:
    js = js.replace(old_nf_save, new_nf_save, 1)
    js_changes += 1

with open(js_path, "w") as f:
    f.write(js)
print(f"4. JS: {js_changes} changes")

# === 5. HTML: Add date format options UI ===
html_path = "templates/propsheet/database_list.html"
with open(html_path, "r") as f:
    html = f.read()

date_format_html = """                    <template x-if="editingField.type === 'date'">
                        <div class="form-group">
                            <label>날짜 형식</label>
                            <select x-model="editingField.dateFormat.style" style="padding:6px 10px;border:1px solid var(--gray-300);border-radius:4px;font-size:13px;">
                                <option value="long">1991년 10월 16일</option>
                                <option value="dot">1991.10.16</option>
                                <option value="dash">1991-10-16</option>
                                <option value="slash">1991/10/16</option>
                                <option value="yearMonth">1991년 10월</option>
                                <option value="yearMonthDot">1991.10</option>
                                <option value="year">1991 (년도만)</option>
                            </select>
                            <div class="hint" style="margin-top:4px;">
                                <span x-text="(() => {
                                    const d = new Date('1991-10-16');
                                    const s = editingField.dateFormat.style || 'long';
                                    const y=d.getFullYear(), m=String(d.getMonth()+1).padStart(2,'0'), dd=String(d.getDate()).padStart(2,'0');
                                    if(s==='long') return y+'년 '+parseInt(m)+'월 '+parseInt(dd)+'일';
                                    if(s==='dot') return y+'.'+m+'.'+dd;
                                    if(s==='dash') return y+'-'+m+'-'+dd;
                                    if(s==='slash') return y+'/'+m+'/'+dd;
                                    if(s==='year') return y+'';
                                    if(s==='yearMonth') return y+'년 '+parseInt(m)+'월';
                                    if(s==='yearMonthDot') return y+'.'+m;
                                    return '';
                                })()"></span>
                            </div>
                        </div>
                    </template>

"""

# Insert before the formula section
formula_marker = '                    <template x-if="editingField.type === \'number\' || (editingField.type === \'formula\')">'
if "editingField.type === 'date'" not in html or "날짜 형식" not in html:
    html = html.replace(formula_marker, date_format_html + formula_marker, 1)
    print("5. HTML: Added date format options UI")
else:
    print("5. HTML: Already has date format UI")

# Bump versions
html = re.sub(r'database_list\.js\?v=\w+', 'database_list.js?v=20260317n', html)
html = re.sub(r'database_list\.css\?v=\w+', 'database_list.css?v=20260317n', html)

with open(html_path, "w") as f:
    f.write(html)

print("\nDone!")
