#!/usr/bin/env python3
"""Fix select option drag-and-drop:
1. Change x-for key from idx to opt.name
2. Add draggable="false" to inner buttons
3. Use @dragover.prevent.stop
"""
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

# Find the opt-tag template line
old = '''                                <template x-for="(opt, idx) in editingField.selectOptionsList" :key="idx">
                                    <span class="opt-tag" :class="{'opt-tag-dragging': editingField.dragIdx === idx, 'opt-tag-dragover': editingField.dragOverIdx === idx && editingField.dragIdx !== idx}" draggable="true" @dragstart="optDragStart($event, idx)" @dragover.prevent="optDragOver($event, idx)" @dragleave="optDragLeave(idx)" @drop.prevent="optDrop(idx)" @dragend="optDragEnd($event)">
                                        <span :style="`background:${opt.bg||'#eceff1'};color:${opt.text||'#546e7a'};padding:4px 8px;border-radius:12px;font-size:13px;display:inline-flex;align-items:center;gap:4px;`">
                                            <span x-text="opt.name"></span>
                                            <button @click.stop="toggleColorPicker(idx)" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:11px;opacity:0.7;" title="색상 변경">&#127912;</button>
                                            <button @click="removeSelectOption(idx)" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:14px;line-height:1;opacity:0.6;" title="삭제">&times;</button>
                                        </span>'''

new = '''                                <template x-for="(opt, idx) in editingField.selectOptionsList" :key="opt.name">
                                    <span class="opt-tag" :class="{'opt-tag-dragging': editingField.dragIdx === idx, 'opt-tag-dragover': editingField.dragOverIdx === idx && editingField.dragIdx !== idx}" draggable="true" @dragstart.stop="optDragStart($event, idx)" @dragover.prevent.stop="optDragOver($event, idx)" @dragleave="optDragLeave(idx)" @drop.prevent.stop="optDrop(idx)" @dragend="optDragEnd($event)">
                                        <span :style="`background:${opt.bg||'#eceff1'};color:${opt.text||'#546e7a'};padding:4px 8px;border-radius:12px;font-size:13px;display:inline-flex;align-items:center;gap:4px;pointer-events:none;`" draggable="false">
                                            <span x-text="opt.name"></span>
                                            <button @click.stop="toggleColorPicker(idx)" draggable="false" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:11px;opacity:0.7;pointer-events:auto;" title="색상 변경">&#127912;</button>
                                            <button @click.stop="removeSelectOption(idx)" draggable="false" style="background:none;border:none;cursor:pointer;padding:0 2px;font-size:14px;line-height:1;opacity:0.6;pointer-events:auto;" title="삭제">&times;</button>
                                        </span>'''

if old in html:
    html = html.replace(old, new, 1)
    print("Fixed opt-tag drag template")
else:
    print("WARN: pattern not found")

# Bump version
html = html.replace("database_list.js') }}?v=1774004100", "database_list.js') }}?v=1774004200")

with open(path, 'w') as f:
    f.write(html)
print("Done!")
