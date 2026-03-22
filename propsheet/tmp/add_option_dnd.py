#!/usr/bin/env python3

# === 1. JS: Add drag handlers for option reorder ===
js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

# Add drag methods before addSelectOption
drag_methods = '''                optDragStart(idx) {
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
                },

'''

if 'optDragStart' not in js:
    marker = "                addSelectOption() {"
    js = js.replace(marker, drag_methods + marker, 1)
    with open(js_path, "w") as f:
        f.write(js)
    print("1. JS: Added drag methods")
else:
    print("1. JS: Already has drag methods")

# === 2. HTML: Add drag attributes to option tags ===
html_path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(html_path, "r") as f:
    html = f.read()

old_span = '<span style="position:relative;display:inline-flex;align-items:center;">'
new_span = '<span style="position:relative;display:inline-flex;align-items:center;cursor:grab;" draggable="true" @dragstart="optDragStart(idx)" @dragover="optDragOver($event, idx)" @drop.prevent="optDrop(idx)" @dragend="editingField._dragIdx = undefined">'

if '@dragstart="optDragStart' not in html:
    html = html.replace(old_span, new_span, 1)
    print("2. HTML: Added drag attributes")
else:
    print("2. HTML: Already has drag attributes")

# Bump version
html = html.replace('database_list.js?v=20260317h', 'database_list.js?v=20260317i')

with open(html_path, "w") as f:
    f.write(html)

print("Done")
