#!/usr/bin/env python3
import re

js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

changes = 0

# 1. Fix select_options to send as array, not string
old = "payload.select_options = opts.map(o => o.name).join(', ');"
new = "payload.select_options = opts.map(o => o.name);"
if old in js:
    js = js.replace(old, new, 1)
    changes += 1
    print("1. Fixed select_options to send as array")

# 2. Replace cycleOptionColor with palette picker approach
old_cycle = """                cycleOptionColor(idx) {
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
                },"""

new_cycle = """                toggleColorPicker(idx) {
                    this.editingField.colorPickerIdx = (this.editingField.colorPickerIdx === idx) ? -1 : idx;
                },

                applyOptionColor(idx, colorIdx) {
                    const palette = [
                        { bg: '#e8eaf6', text: '#3f51b5' }, { bg: '#e3f2fd', text: '#1976d2' },
                        { bg: '#e8f5e9', text: '#388e3c' }, { bg: '#fff3e0', text: '#f57c00' },
                        { bg: '#fce4ec', text: '#c62828' }, { bg: '#f3e5f5', text: '#7b1fa2' },
                        { bg: '#e0f2f1', text: '#00796b' }, { bg: '#fff8e1', text: '#f9a825' },
                        { bg: '#efebe9', text: '#5d4037' }, { bg: '#eceff1', text: '#546e7a' },
                    ];
                    const opt = this.editingField.selectOptionsList[idx];
                    opt.bg = palette[colorIdx].bg;
                    opt.text = palette[colorIdx].text;
                    this.editingField.colorPickerIdx = -1;
                },"""

if old_cycle in js:
    js = js.replace(old_cycle, new_cycle, 1)
    changes += 1
    print("2. Replaced cycleOptionColor with palette picker")

# 3. Add colorPickerIdx to editingField init
old_init = "newOptionColorIdx: (col.selectOptions || []).length,"
new_init = "newOptionColorIdx: (col.selectOptions || []).length,\n                        colorPickerIdx: -1,"
if 'colorPickerIdx' not in js:
    js = js.replace(old_init, new_init, 1)
    changes += 1
    print("3. Added colorPickerIdx to editingField")

with open(js_path, "w") as f:
    f.write(js)

# 4. Update HTML template - color palette UI
html_path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(html_path, "r") as f:
    html = f.read()

# Replace the color button from cycle to toggle picker
old_tag = """<span :style="`background:${opt.bg||'#eceff1'};color:${opt.text||'#546e7a'};padding:4px 8px;border-radius:12px;font-size:13px;display:inline-flex;align-items:center;gap:4px;`">
                                        <span x-text="opt.name"></span>
                                        <button @click="cycleOptionColor(idx)" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:11px;opacity:0.7;" title="색상 변경">&#127912;</button>
                                        <button @click="removeSelectOption(idx)" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:14px;line-height:1;opacity:0.6;" title="삭제">&times;</button>
                                    </span>"""

new_tag = """<span style="position:relative;display:inline-flex;align-items:center;">
                                        <span :style="`background:${opt.bg||'#eceff1'};color:${opt.text||'#546e7a'};padding:4px 8px;border-radius:12px;font-size:13px;display:inline-flex;align-items:center;gap:4px;`">
                                            <span x-text="opt.name"></span>
                                            <button @click.stop="toggleColorPicker(idx)" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:11px;opacity:0.7;" title="색상 변경">&#127912;</button>
                                            <button @click="removeSelectOption(idx)" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:14px;line-height:1;opacity:0.6;" title="삭제">&times;</button>
                                        </span>
                                        <div x-show="editingField.colorPickerIdx === idx" @click.stop
                                             style="position:absolute;top:100%;left:0;z-index:100;background:white;border:1px solid #ddd;border-radius:8px;padding:6px;margin-top:4px;display:flex;gap:4px;flex-wrap:wrap;width:160px;box-shadow:0 4px 12px rgba(0,0,0,0.15);">
                                            <template x-for="(pc, ci) in [
                                                {bg:'#e8eaf6',text:'#3f51b5'},{bg:'#e3f2fd',text:'#1976d2'},
                                                {bg:'#e8f5e9',text:'#388e3c'},{bg:'#fff3e0',text:'#f57c00'},
                                                {bg:'#fce4ec',text:'#c62828'},{bg:'#f3e5f5',text:'#7b1fa2'},
                                                {bg:'#e0f2f1',text:'#00796b'},{bg:'#fff8e1',text:'#f9a825'},
                                                {bg:'#efebe9',text:'#5d4037'},{bg:'#eceff1',text:'#546e7a'}
                                            ]" :key="ci">
                                                <button @click="applyOptionColor(idx, ci)"
                                                        :style="`width:24px;height:24px;border-radius:50%;border:2px solid ${opt.bg===pc.bg?pc.text:'transparent'};background:${pc.bg};cursor:pointer;`"
                                                        :title="'색상 ' + (ci+1)"></button>
                                            </template>
                                        </div>
                                    </span>"""

if old_tag in html:
    html = html.replace(old_tag, new_tag, 1)
    changes += 1
    print("4. HTML: Replaced with color palette picker")
else:
    print("4. WARN: old tag pattern not found")

html = re.sub(r'database_list\.js\?v=\w+', 'database_list.js?v=20260317f', html)

with open(html_path, "w") as f:
    f.write(html)

print(f"\nTotal changes: {changes}")
