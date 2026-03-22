#!/usr/bin/env python3

# === 1. CSS: Add drag visual feedback ===
css_path = "/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css"
with open(css_path, "r") as f:
    css = f.read()

if '.opt-tag-dragging' not in css:
    css += """
/* Select option drag-and-drop */
.opt-tag {
    position: relative;
    display: inline-flex;
    align-items: center;
    cursor: grab;
    transition: transform 0.15s, box-shadow 0.15s;
    user-select: none;
}
.opt-tag:hover {
    transform: translateY(-2px);
    box-shadow: 0 3px 8px rgba(0,0,0,0.12);
}
.opt-tag:active {
    cursor: grabbing;
}
.opt-tag-dragging {
    opacity: 0.4;
    transform: scale(0.95);
}
.opt-tag-dragover {
    margin-left: 28px;
    transition: margin 0.2s;
}
"""
    with open(css_path, "w") as f:
        f.write(css)
    print("1. CSS: Added drag visual styles")

# === 2. JS: Update drag handlers with visual feedback ===
js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

old_drag = """                optDragStart(idx) {
                    this.editingField._dragIdx = idx;
                },

                optDragOver(event, idx) {
                    event.preventDefault();
                    event.dataTransfer.dropEffect = 'move';
                },

                optDrop(idx) {
                    const from = this.editingField._dragIdx;
                    if (from === undefined || from === idx) return;
                    const list = this.editingField.selectOptionsList;
                    const item = list.splice(from, 1)[0];
                    list.splice(idx, 0, item);
                    this.editingField._dragIdx = undefined;
                },"""

new_drag = """                optDragStart(event, idx) {
                    this.editingField._dragIdx = idx;
                    this.editingField._dragOverIdx = -1;
                    event.dataTransfer.effectAllowed = 'move';
                    // Delay to let browser capture drag image first
                    requestAnimationFrame(() => {
                        event.target.closest('.opt-tag').classList.add('opt-tag-dragging');
                    });
                },

                optDragOver(event, idx) {
                    event.preventDefault();
                    event.dataTransfer.dropEffect = 'move';
                    this.editingField._dragOverIdx = idx;
                },

                optDragLeave(idx) {
                    if (this.editingField._dragOverIdx === idx) {
                        this.editingField._dragOverIdx = -1;
                    }
                },

                optDrop(idx) {
                    const from = this.editingField._dragIdx;
                    this.editingField._dragOverIdx = -1;
                    if (from === undefined || from === idx) return;
                    const list = this.editingField.selectOptionsList;
                    const item = list.splice(from, 1)[0];
                    list.splice(idx, 0, item);
                    this.editingField._dragIdx = undefined;
                },

                optDragEnd(event) {
                    this.editingField._dragIdx = undefined;
                    this.editingField._dragOverIdx = -1;
                    // Remove class from all tags
                    document.querySelectorAll('.opt-tag-dragging').forEach(el => el.classList.remove('opt-tag-dragging'));
                },"""

if old_drag in js:
    js = js.replace(old_drag, new_drag, 1)
    with open(js_path, "w") as f:
        f.write(js)
    print("2. JS: Updated drag handlers with visual feedback")
else:
    print("2. WARN: old drag pattern not found")

# === 3. HTML: Update tag with CSS classes and drag events ===
html_path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(html_path, "r") as f:
    html = f.read()

old_tag = '<span style="position:relative;display:inline-flex;align-items:center;cursor:grab;" draggable="true" @dragstart="optDragStart(idx)" @dragover="optDragOver($event, idx)" @drop.prevent="optDrop(idx)" @dragend="editingField._dragIdx = undefined">'

new_tag = '<span class="opt-tag" :class="{\'opt-tag-dragging\': editingField._dragIdx === idx, \'opt-tag-dragover\': editingField._dragOverIdx === idx && editingField._dragIdx !== idx}" draggable="true" @dragstart="optDragStart($event, idx)" @dragover.prevent="optDragOver($event, idx)" @dragleave="optDragLeave(idx)" @drop.prevent="optDrop(idx)" @dragend="optDragEnd($event)">'

if old_tag in html:
    html = html.replace(old_tag, new_tag, 1)
    print("3. HTML: Updated tag with CSS classes")
else:
    print("3. WARN: old tag pattern not found")

# Also add _dragOverIdx init
old_init = "colorPickerIdx: -1,"
new_init = "colorPickerIdx: -1,\n                        _dragIdx: undefined,\n                        _dragOverIdx: -1,"
if '_dragOverIdx' not in html and '_dragOverIdx' not in open(js_path).read().split('editingField = {')[0]:
    pass  # init is in JS

# Check JS editingField init
with open(js_path, "r") as f:
    js2 = f.read()

if '_dragOverIdx' not in js2.split('openFieldSettings')[1].split('this.showFieldSettings')[0]:
    old_init_js = "colorPickerIdx: -1,"
    new_init_js = "colorPickerIdx: -1,\n                        _dragIdx: undefined,\n                        _dragOverIdx: -1,"
    if '_dragOverIdx: -1' not in js2:
        js2 = js2.replace(old_init_js, new_init_js, 1)
        with open(js_path, "w") as f:
            f.write(js2)
        print("4. JS: Added _dragOverIdx init")

# Bump version
html = html.replace('?v=20260317i', '?v=20260317j')
html = html.replace('?v=20260317h', '?v=20260317j')

with open(html_path, "w") as f:
    f.write(html)

print("Done")
