#!/usr/bin/env python3
import re, json

# === 1. schema_service.py ===
schema_path = "/home/webapp/goldenrabbit/backend/property-manager/services/schema_service.py"
with open(schema_path, "r") as f:
    content = f.read()

if 'select_colors' not in content:
    content = content.replace(
        "SELECT field_name, field_type, formula, is_editable, select_options, system_value_key",
        "SELECT field_name, field_type, formula, is_editable, select_options, system_value_key, select_colors", 1)

    content = content.replace(
        "select_options = field_def.get('select_options') if field_def else None",
        "select_options = field_def.get('select_options') if field_def else None\n                select_colors = field_def.get('select_colors') if field_def else None", 1)

    content = content.replace(
        "'selectOptions': select_options,\n                    'systemValueKey': system_value_key",
        "'selectOptions': select_options,\n                    'selectColors': select_colors,\n                    'systemValueKey': system_value_key", 1)

    with open(schema_path, "w") as f:
        f.write(content)
    print("1. schema_service: select_colors added")
else:
    print("1. schema_service: already has select_colors")

# === 2. routes/database.py: save select_colors ===
db_path = "/home/webapp/goldenrabbit/backend/property-manager/routes/database.py"
with open(db_path, "r") as f:
    content = f.read()

if 'select_colors' not in content:
    # Find the select_options save block and add after it
    marker = "if data.get('select_options'):"
    if marker in content:
        idx = content.index(marker)
        # Find the next blank line after this block
        next_blank = content.index('\n\n', idx)
        insert_point = next_blank
        insert_code = """

                if data.get('select_colors') is not None:
                    import json as json_mod
                    cursor.execute(
                        'UPDATE field_definitions SET select_colors = %s WHERE field_name = %s',
                        (json_mod.dumps(data['select_colors']), field_name)
                    )"""
        content = content[:insert_point] + insert_code + content[insert_point:]
        with open(db_path, "w") as f:
            f.write(content)
        print("2. routes: select_colors save added")
    else:
        print("2. WARN: select_options marker not found")
else:
    print("2. routes: already has select_colors")

# === 3. JS updates ===
js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

js_changes = 0

# 3a. Update getOptionColor to accept colObj and check saved colors
old_fn = "getOptionColor(option, options) {"
new_fn = "getOptionColor(option, options, colObj) {"
if old_fn in js:
    js = js.replace(old_fn, new_fn, 1)
    js_changes += 1

# Add color lookup before default
old_lookup = "if (!options || !Array.isArray(options)) return colors[0];"
new_lookup = """// Check saved colors
                    if (colObj && colObj.selectColors && colObj.selectColors[option]) {
                        const saved = colObj.selectColors[option];
                        return { bg: saved.bg, text: saved.text };
                    }
                    if (!options || !Array.isArray(options)) return defaultColors[0];"""
if 'colObj.selectColors' not in js:
    js = js.replace(old_lookup, new_lookup, 1)
    # Also rename colors array to defaultColors
    js = js.replace("const colors = [\n                        { bg: '#e8eaf6'", "const defaultColors = [\n                        { bg: '#e8eaf6'", 1)
    js = js.replace("return colors[idx % colors.length];", "return defaultColors[idx % defaultColors.length];", 1)
    js = js.replace("if (idx < 0) return colors[0];", "if (idx < 0) return defaultColors[0];", 1)
    js_changes += 1

# 3b. Add selectColors and management fields to editingField
old_edit = """                        isSystem: col.type === 'system' || col.key === 'id',"""
new_edit = """                        isSystem: col.type === 'system' || col.key === 'id',
                        selectColors: col.selectColors ? {...col.selectColors} : {},
                        selectOptionsList: (col.selectOptions || []).map(opt => ({
                            name: opt,
                            bg: (col.selectColors && col.selectColors[opt]) ? col.selectColors[opt].bg : null,
                            text: (col.selectColors && col.selectColors[opt]) ? col.selectColors[opt].text : null,
                        })),
                        newOptionName: '',
                        newOptionColorIdx: (col.selectOptions || []).length,"""
if 'selectOptionsList' not in js:
    js = js.replace(old_edit, new_edit, 1)
    js_changes += 1

# 3c. Add option management methods
add_methods = '''                addSelectOption() {
                    if (!this.editingField || !this.editingField.newOptionName.trim()) return;
                    const name = this.editingField.newOptionName.trim();
                    if (this.editingField.selectOptionsList.some(o => o.name === name)) {
                        alert('\\uc774\\ubbf8 \\uc874\\uc7ac\\ud558\\ub294 \\uc635\\uc158\\uc785\\ub2c8\\ub2e4');
                        return;
                    }
                    const palette = [
                        { bg: '#e8eaf6', text: '#3f51b5' }, { bg: '#e3f2fd', text: '#1976d2' },
                        { bg: '#e8f5e9', text: '#388e3c' }, { bg: '#fff3e0', text: '#f57c00' },
                        { bg: '#fce4ec', text: '#c62828' }, { bg: '#f3e5f5', text: '#7b1fa2' },
                        { bg: '#e0f2f1', text: '#00796b' }, { bg: '#fff8e1', text: '#f9a825' },
                        { bg: '#efebe9', text: '#5d4037' }, { bg: '#eceff1', text: '#546e7a' },
                    ];
                    const ci = this.editingField.newOptionColorIdx % palette.length;
                    const c = palette[ci];
                    this.editingField.selectOptionsList.push({ name, bg: c.bg, text: c.text });
                    this.editingField.newOptionName = '';
                    this.editingField.newOptionColorIdx = ci + 1;
                },

                removeSelectOption(idx) {
                    this.editingField.selectOptionsList.splice(idx, 1);
                },

                cycleOptionColor(idx) {
                    const palette = [
                        { bg: '#e8eaf6', text: '#3f51b5' }, { bg: '#e3f2fd', text: '#1976d2' },
                        { bg: '#e8f5e9', text: '#388e3c' }, { bg: '#fff3e0', text: '#f57c00' },
                        { bg: '#fce4ec', text: '#c62828' }, { bg: '#f3e5f5', text: '#7b1fa2' },
                        { bg: '#e0f2f1', text: '#00796b' }, { bg: '#fff8e1', text: '#f9a825' },
                        { bg: '#efebe9', text: '#5d4037' }, { bg: '#eceff1', text: '#546e7a' },
                    ];
                    const opt = this.editingField.selectOptionsList[idx];
                    const curIdx = palette.findIndex(c => c.bg === opt.bg);
                    const nextIdx = (curIdx + 1) % palette.length;
                    opt.bg = palette[nextIdx].bg;
                    opt.text = palette[nextIdx].text;
                },

'''

if 'addSelectOption()' not in js:
    # Insert before openSelectDropdown
    marker = "                openSelectDropdown(event, item, col) {"
    if marker in js:
        js = js.replace(marker, add_methods + marker, 1)
        js_changes += 1

# 3d. Update saveFieldSettings to use selectOptionsList
old_save = """if (this.editingField.type === 'single-select' || this.editingField.type === 'multi-select') {
                        if (this.editingField.selectOptionsText) {
                            payload.select_options = this.editingField.selectOptionsText"""
# Need to find the actual full block
save_marker = "if (this.editingField.type === 'single-select' || this.editingField.type === 'multi-select')"
save_idx = js.find(save_marker)
if save_idx > 0 and 'selectOptionsList' not in js[save_idx:save_idx+500]:
    # Find the closing brace of this if block
    brace_start = js.index('{', save_idx)
    depth = 0
    end_idx = brace_start
    for i in range(brace_start, min(brace_start + 500, len(js))):
        if js[i] == '{': depth += 1
        elif js[i] == '}':
            depth -= 1
            if depth == 0:
                end_idx = i + 1
                break

    new_save_block = """if (this.editingField.type === 'single-select' || this.editingField.type === 'multi-select') {
                        const opts = this.editingField.selectOptionsList || [];
                        payload.select_options = opts.map(o => o.name).join(', ');
                        const colors = {};
                        opts.forEach(o => { if (o.bg && o.text) colors[o.name] = { bg: o.bg, text: o.text }; });
                        payload.select_colors = colors;
                    }"""
    js = js[:save_idx] + new_save_block + js[end_idx:]
    js_changes += 1

with open(js_path, "w") as f:
    f.write(js)
print(f"3. JS: {js_changes} changes")

# === 4. HTML: Replace select option editor ===
html_path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(html_path, "r") as f:
    html = f.read()

old_html = """                    <template x-if="editingField.type === 'single-select'">
                        <div class="form-group">
                            <label>선택 옵션 (콤마로 구분)</label>
                            <input type="text" x-model="editingField.selectOptionsText" placeholder="옵션1, 옵션2, 옵션3">
                            <div class="hint">예: 매매, 전세, 월세</div>
                        </div>
                    </template>

                    <template x-if="editingField.type === 'multi-select'">
                        <div class="form-group">
                            <label>선택 옵션 (콤마로 구분)</label>
                            <input type="text" x-model="editingField.selectOptionsText" placeholder="옵션1, 옵션2, 옵션3">
                            <div class="hint">예: 입주가능, 공실, 임차인있음, 리모델링필요</div>
                        </div>
                    </template>"""

new_html = """                    <template x-if="editingField.type === 'single-select' || editingField.type === 'multi-select'">
                        <div class="form-group">
                            <label>선택 옵션</label>
                            <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;min-height:36px;padding:8px;border:1px solid var(--gray-200);border-radius:6px;background:var(--gray-50);">
                                <template x-for="(opt, idx) in editingField.selectOptionsList" :key="idx">
                                    <span :style="`background:${opt.bg||'#eceff1'};color:${opt.text||'#546e7a'};padding:4px 8px;border-radius:12px;font-size:13px;display:inline-flex;align-items:center;gap:4px;`">
                                        <span x-text="opt.name"></span>
                                        <button @click="cycleOptionColor(idx)" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:11px;opacity:0.7;" title="색상 변경">&#127912;</button>
                                        <button @click="removeSelectOption(idx)" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:14px;line-height:1;opacity:0.6;" title="삭제">&times;</button>
                                    </span>
                                </template>
                                <template x-if="!editingField.selectOptionsList || editingField.selectOptionsList.length === 0">
                                    <span style="color:var(--gray-400);font-size:13px;">옵션을 추가하세요</span>
                                </template>
                            </div>
                            <div style="display:flex;gap:6px;align-items:center;">
                                <input type="text" x-model="editingField.newOptionName" placeholder="새 옵션 이름" @keydown.enter.prevent="addSelectOption()" style="flex:1;padding:6px 10px;border:1px solid var(--gray-300);border-radius:4px;font-size:13px;">
                                <button @click="addSelectOption()" style="padding:6px 14px;background:var(--brand-blue,#667eea);color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;white-space:nowrap;">+ 추가</button>
                            </div>
                            <div class="hint" style="margin-top:4px;">Enter로 추가, &#127912;로 색상 변경, &times;로 삭제</div>
                        </div>
                    </template>"""

if old_html in html:
    html = html.replace(old_html, new_html, 1)
    print("4. HTML: Replaced with tag-based option editor")
else:
    print("4. WARN: old HTML pattern not found")

html = re.sub(r'database_list\.js\?v=\w+', 'database_list.js?v=20260317e', html)

with open(html_path, "w") as f:
    f.write(html)

print("\nDone!")
