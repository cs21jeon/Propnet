#!/usr/bin/env python3
js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

# Fix: when no saved color, assign default palette color based on index
old = """                        selectOptionsList: (col.selectOptions || []).map(opt => ({
                            name: opt,
                            bg: (col.selectColors && col.selectColors[opt]) ? col.selectColors[opt].bg : null,
                            text: (col.selectColors && col.selectColors[opt]) ? col.selectColors[opt].text : null,
                        })),"""

new = """                        selectOptionsList: (col.selectOptions || []).map((opt, i) => {
                            const defPalette = [
                                {bg:'#e8eaf6',text:'#3f51b5'},{bg:'#e3f2fd',text:'#1976d2'},
                                {bg:'#e8f5e9',text:'#388e3c'},{bg:'#fff3e0',text:'#f57c00'},
                                {bg:'#fce4ec',text:'#c62828'},{bg:'#f3e5f5',text:'#7b1fa2'},
                                {bg:'#e0f2f1',text:'#00796b'},{bg:'#fff8e1',text:'#f9a825'},
                                {bg:'#efebe9',text:'#5d4037'},{bg:'#eceff1',text:'#546e7a'},
                            ];
                            const saved = (col.selectColors && col.selectColors[opt]);
                            const def = defPalette[i % defPalette.length];
                            return {
                                name: opt,
                                bg: saved ? saved.bg : def.bg,
                                text: saved ? saved.text : def.text,
                            };
                        }),"""

if old in js:
    js = js.replace(old, new, 1)
    with open(js_path, "w") as f:
        f.write(js)
    print("OK - Fixed selectOptionsList init with default colors")
else:
    print("WARN: pattern not found")
