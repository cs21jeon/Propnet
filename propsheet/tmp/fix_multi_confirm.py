#!/usr/bin/env python3

# === 1. HTML: Add confirm button for multi-select, outside click saves ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

old_dropdown = """    <template x-if="selectDropdown.show">
        <div class="select-dropdown"
             :style="`left: ${selectDropdown.x}px; top: ${selectDropdown.y}px;`"
             @click.stop>
            <div class="select-dropdown-header">
                <span x-text="selectDropdown.colType === 'single-select' ? '옵션 선택' : '옵션 선택 (복수)'"></span>
                <div style="display:flex;gap:6px;align-items:center;">
                    <template x-if="selectDropdown.colType === 'multi-select'">
                        <button class="select-dropdown-clear" @click="clearSelectValue()" title="선택 해제" style="font-size:11px;padding:2px 6px;">초기화</button>
                    </template>
                    <button class="select-dropdown-clear" @click="closeSelectDropdown()" title="닫기">✕</button>
                </div>
            </div>"""

new_dropdown = """    <template x-if="selectDropdown.show">
        <div class="select-dropdown-backdrop" @click="closeSelectDropdown()"></div>
    </template>
    <template x-if="selectDropdown.show">
        <div class="select-dropdown"
             :style="`left: ${selectDropdown.x}px; top: ${selectDropdown.y}px;`"
             @click.stop>
            <div class="select-dropdown-header">
                <span x-text="selectDropdown.colType === 'single-select' ? '옵션 선택' : '옵션 선택 (복수)'"></span>
                <div style="display:flex;gap:6px;align-items:center;">
                    <template x-if="selectDropdown.colType === 'multi-select'">
                        <button class="select-dropdown-clear" @click="clearSelectValue()" title="선택 해제" style="font-size:11px;padding:2px 6px;">초기화</button>
                    </template>
                    <button class="select-dropdown-clear" @click="closeSelectDropdown()" title="닫기">✕</button>
                </div>
            </div>"""

if old_dropdown in html:
    html = html.replace(old_dropdown, new_dropdown, 1)
    print("1. Added backdrop for outside click")

# Add confirm button after options list (before closing </div>)
old_options_end = """                <template x-if="selectDropdown.options.length === 0">
                    <div class="select-dropdown-empty">옵션이 없습니다. 필드 설정에서 추가하세요.</div>
                </template>
            </div>
        </div>"""

new_options_end = """                <template x-if="selectDropdown.options.length === 0">
                    <div class="select-dropdown-empty">옵션이 없습니다. 필드 설정에서 추가하세요.</div>
                </template>
            </div>
            <template x-if="selectDropdown.colType === 'multi-select'">
                <div class="select-dropdown-footer">
                    <button class="select-confirm-btn" @click="closeSelectDropdown()">확인</button>
                </div>
            </template>
        </div>"""

if old_options_end in html:
    html = html.replace(old_options_end, new_options_end, 1)
    print("2. Added confirm button for multi-select")

with open(html_path, 'w') as f:
    f.write(html)

# === 2. CSS: backdrop + confirm button styles ===
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(css_path, 'r') as f:
    css = f.read()

if '.select-dropdown-backdrop' not in css:
    css += """
/* Select dropdown backdrop (click outside to close) */
.select-dropdown-backdrop {
    position: fixed;
    inset: 0;
    z-index: 999;
}

/* Multi-select confirm button */
.select-dropdown-footer {
    padding: 8px 12px;
    border-top: 1px solid var(--border);
    text-align: right;
}
.select-confirm-btn {
    padding: 5px 20px;
    background: var(--brand-blue, #667eea);
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    cursor: pointer;
}
.select-confirm-btn:hover {
    opacity: 0.9;
}
"""
    with open(css_path, 'w') as f:
        f.write(css)
    print("3. Added CSS for backdrop + confirm button")

# Bump
import re
with open(html_path, 'rb') as f:
    raw = f.read()
raw = re.sub(rb'database_list\.js\?v=\w+', b'database_list.js?v=20260318b', raw)
raw = re.sub(rb'database_list\.css\?v=\w+', b'database_list.css?v=20260318b', raw)
with open(html_path, 'wb') as f:
    f.write(raw)
print("4. Bumped versions")

print("Done!")
