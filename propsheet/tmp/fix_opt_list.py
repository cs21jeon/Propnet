#!/usr/bin/env python3
"""Replace opt-tag inline layout with vertical list + row drag"""
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

old_block = '''                            <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;min-height:36px;padding:8px;border:1px solid var(--gray-200);border-radius:6px;background:var(--gray-50);">
                                <template x-for="(opt, idx) in editingField.selectOptionsList" :key="opt.name">
                                    <span class="opt-tag" :class="{'opt-tag-dragging': editingField.dragIdx === idx, 'opt-tag-dragover': editingField.dragOverIdx === idx && editingField.dragIdx !== idx}" draggable="true" @dragstart.stop="optDragStart($event, idx)" @dragover.prevent.stop="optDragOver($event, idx)" @dragleave="optDragLeave(idx)" @drop.prevent.stop="optDrop(idx)" @dragend="optDragEnd($event)">
                                        <span :style="`background:${opt.bg||'#eceff1'};color:${opt.text||'#546e7a'};padding:4px 8px;border-radius:12px;font-size:13px;display:inline-flex;align-items:center;gap:4px;pointer-events:none;`" draggable="false">
                                            <span x-text="opt.name"></span>
                                            <button @click.stop="toggleColorPicker(idx)" draggable="false" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:11px;opacity:0.7;pointer-events:auto;" title="색상 변경">&#127912;</button>
                                            <button @click.stop="removeSelectOption(idx)" draggable="false" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:14px;line-height:1;opacity:0.6;pointer-events:auto;" title="삭제">&times;</button>
                                        </span>
                                        <div x-show="editingField.colorPickerIdx === idx" @click.stop
                                             style="position:absolute;bottom:100%;left:0;z-index:100;background:white;border:1px solid #ddd;border-radius:8px;padding:6px;margin-bottom:4px;display:flex;gap:4px;flex-wrap:wrap;width:160px;box-shadow:0 4px 12px rgba(0,0,0,0.15);">
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
                                    </span>
                                </template>
                                <template x-if="!editingField.selectOptionsList || editingField.selectOptionsList.length === 0">
                                    <span style="color:var(--gray-400);font-size:13px;">옵션을 추가하세요</span>
                                </template>
                            </div>'''

new_block = '''                            <div class="opt-list" style="display:flex;flex-direction:column;gap:2px;margin-bottom:10px;padding:4px;border:1px solid var(--gray-200);border-radius:6px;background:var(--gray-50);max-height:200px;overflow-y:auto;">
                                <template x-for="(opt, idx) in editingField.selectOptionsList" :key="opt.name">
                                    <div class="opt-row"
                                         :class="{'opt-row-dragging': editingField.dragIdx === idx, 'opt-row-dragover': editingField.dragOverIdx === idx && editingField.dragIdx !== idx}"
                                         draggable="true"
                                         @dragstart="optDragStart($event, idx)"
                                         @dragover.prevent="optDragOver($event, idx)"
                                         @dragleave="optDragLeave(idx)"
                                         @drop.prevent="optDrop(idx)"
                                         @dragend="optDragEnd($event)"
                                         style="display:flex;align-items:center;gap:6px;padding:4px 8px;border-radius:6px;cursor:grab;user-select:none;position:relative;">
                                        <span style="color:var(--gray-400);font-size:11px;cursor:grab;">&#9776;</span>
                                        <span :style="`background:${opt.bg||'#eceff1'};color:${opt.text||'#546e7a'};padding:3px 10px;border-radius:12px;font-size:13px;flex:1;`" x-text="opt.name"></span>
                                        <button @click.stop="toggleColorPicker(idx)" style="background:none;border:none;cursor:pointer;font-size:11px;opacity:0.7;padding:2px 4px;" title="색상 변경">&#127912;</button>
                                        <button @click.stop="removeSelectOption(idx)" style="background:none;border:none;cursor:pointer;font-size:14px;line-height:1;opacity:0.6;padding:2px 4px;" title="삭제">&times;</button>
                                        <div x-show="editingField.colorPickerIdx === idx" @click.stop
                                             style="position:absolute;right:0;top:100%;z-index:100;background:white;border:1px solid #ddd;border-radius:8px;padding:6px;margin-top:2px;display:flex;gap:4px;flex-wrap:wrap;width:160px;box-shadow:0 4px 12px rgba(0,0,0,0.15);">
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
                                    </div>
                                </template>
                                <template x-if="!editingField.selectOptionsList || editingField.selectOptionsList.length === 0">
                                    <span style="color:var(--gray-400);font-size:13px;padding:8px;">옵션을 추가하세요</span>
                                </template>
                            </div>'''

if old_block in html:
    html = html.replace(old_block, new_block, 1)
    print("1. Replaced opt-tag with opt-row list layout")
else:
    print("1. WARN: pattern not found")

# Bump version
html = html.replace("database_list.js') }}?v=1774004200", "database_list.js') }}?v=1774004300")
with open(path, 'w') as f:
    f.write(html)

# Add CSS for opt-row
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(css_path, 'r') as f:
    css = f.read()

opt_row_css = """
/* Option list row drag */
.opt-row:hover { background: var(--gray-100); }
.opt-row:active { cursor: grabbing; }
.opt-row-dragging { opacity: 0.3; background: var(--gray-200); }
.opt-row-dragover { border-top: 2px solid var(--brand-blue, #667eea); }
"""

if 'opt-row' not in css:
    css += opt_row_css
    with open(css_path, 'w') as f:
        f.write(css)
    print("2. Added opt-row CSS")

print("Done!")
