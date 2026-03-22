#!/usr/bin/env python3

# === 1. HTML: Fix multi-select dropdown - add confirm button, change X behavior ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

# Replace dropdown header: X button clears for single, closes for multi
old_header = """            <div class="select-dropdown-header">
                <span x-text="selectDropdown.colType === 'single-select' ? '옵션 선택' : '옵션 선택 (복수)'"></span>
                <button class="select-dropdown-clear" @click="clearSelectValue()" title="선택 해제">✕</button>
            </div>"""

new_header = """            <div class="select-dropdown-header">
                <span x-text="selectDropdown.colType === 'single-select' ? '옵션 선택' : '옵션 선택 (복수)'"></span>
                <div style="display:flex;gap:6px;align-items:center;">
                    <template x-if="selectDropdown.colType === 'multi-select'">
                        <button class="select-dropdown-clear" @click="clearSelectValue()" title="선택 해제" style="font-size:11px;padding:2px 6px;">초기화</button>
                    </template>
                    <button class="select-dropdown-clear" @click="closeSelectDropdown()" title="닫기">✕</button>
                </div>
            </div>"""

if old_header in html:
    html = html.replace(old_header, new_header, 1)
    print("1. Fixed dropdown header - X now closes, added 초기화 for multi")

with open(html_path, 'w') as f:
    f.write(html)

# === 2. JS: Fix openSelectDropdown position to stay within viewport ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

# Fix dropdown positioning
old_pos = """                    this.selectDropdown = {
                        show: true,
                        itemId: item.id,
                        colKey: col.key,
                        colType: col.type,
                        options: options,
                        selected: selected,
                        col: col,
                        x: rect.left,
                        y: rect.bottom + 2
                    };"""

new_pos = """                    // Ensure dropdown stays within viewport
                    let ddX = rect.left;
                    let ddY = rect.bottom + 2;
                    const ddWidth = 220;
                    const ddHeight = Math.min(options.length * 36 + 50, 300);
                    if (ddX + ddWidth > window.innerWidth) ddX = window.innerWidth - ddWidth - 10;
                    if (ddY + ddHeight > window.innerHeight) ddY = rect.top - ddHeight - 2;
                    if (ddX < 0) ddX = 10;
                    if (ddY < 0) ddY = 10;

                    this.selectDropdown = {
                        show: true,
                        itemId: item.id,
                        colKey: col.key,
                        colType: col.type,
                        options: options,
                        selected: selected,
                        col: col,
                        x: ddX,
                        y: ddY
                    };"""

if old_pos in js:
    js = js.replace(old_pos, new_pos, 1)
    print("2. Fixed dropdown positioning")

# Fix multi-select: don't save on every click, save on close
old_multi = """                    } else {
                        // Multi-select: toggle option
                        const idx = dd.selected.indexOf(option);
                        if (idx > -1) {
                            dd.selected.splice(idx, 1);
                        } else {
                            dd.selected.push(option);
                        }
                        const newValue = dd.selected.join(', ');
                        await this.saveSelectValue(dd.itemId, dd.colKey, newValue);
                    }"""

new_multi = """                    } else {
                        // Multi-select: toggle option (save deferred to close)
                        const idx = dd.selected.indexOf(option);
                        if (idx > -1) {
                            dd.selected.splice(idx, 1);
                        } else {
                            dd.selected.push(option);
                        }
                        // Update cell display immediately but don't save yet
                        const item = this.items.find(i => i.id === dd.itemId);
                        if (item) item[dd.colKey] = dd.selected.join(', ') || null;
                        dd._dirty = true;
                    }"""

if old_multi in js:
    js = js.replace(old_multi, new_multi, 1)
    print("3. Multi-select: deferred save")

# Fix closeSelectDropdown: save multi-select on close
old_close = """                closeSelectDropdown() {
                    if (this.selectDropdown.show) {
                        this.selectDropdown.show = false;
                    }
                },"""

new_close = """                async closeSelectDropdown() {
                    const dd = this.selectDropdown;
                    if (dd.show) {
                        // Save multi-select on close if changed
                        if (dd.colType === 'multi-select' && dd._dirty) {
                            const newValue = dd.selected.join(', ');
                            await this.saveSelectValue(dd.itemId, dd.colKey, newValue);
                        }
                        this.selectDropdown.show = false;
                    }
                },"""

if old_close in js:
    js = js.replace(old_close, new_close, 1)
    print("4. Save multi-select on close")

with open(js_path, 'w') as f:
    f.write(js)

print("Done!")
