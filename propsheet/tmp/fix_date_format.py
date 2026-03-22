#!/usr/bin/env python3
"""Fix: getDetailDisplayValue should use col.dateFormat like formatCell does"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

old = """                getDetailDisplayValue(fieldKey) {
                    const val = this.detailPanel.item[fieldKey];
                    if (val === null || val === undefined) return '-';
                    const col = this.allColumns.find(c => c.key === fieldKey);
                    if (col && col.type === 'number' && !isNaN(val)) return Number(val).toLocaleString();
                    if (col && col.type === 'date' && val) {
                        try { return new Date(val).toLocaleDateString('ko-KR'); } catch { return val; }"""

new = """                getDetailDisplayValue(fieldKey) {
                    const val = this.detailPanel.item[fieldKey];
                    if (val === null || val === undefined) return '-';
                    const col = this.allColumns.find(c => c.key === fieldKey);
                    if (col && col.type === 'number' && !isNaN(val)) return Number(val).toLocaleString();
                    if (col && col.type === 'date' && val) {
                        try {
                            const d = new Date(val);
                            if (isNaN(d.getTime())) return String(val);
                            const df = col.dateFormat || {};
                            const style = df.style || 'long';
                            const y = d.getFullYear();
                            const m = String(d.getMonth() + 1).padStart(2, '0');
                            const dd = String(d.getDate()).padStart(2, '0');
                            switch (style) {
                                case 'long': return y + '년 ' + parseInt(m) + '월 ' + parseInt(dd) + '일';
                                case 'dot': return y + '.' + m + '.' + dd;
                                case 'dash': return y + '-' + m + '-' + dd;
                                case 'slash': return y + '/' + m + '/' + dd;
                                case 'compact8': return '' + y + m + dd;
                                case 'compact6': return String(y).slice(2) + m + dd;
                                case 'year': return '' + y;
                                default: return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
                            }
                        } catch { return String(val); }"""

if old in js:
    js = js.replace(old, new, 1)
    print("Fixed getDetailDisplayValue date formatting")
else:
    print("WARN: pattern not found")

# Bump version
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()
html = html.replace("database_list.js') }}?v=1774004300", "database_list.js') }}?v=1774004400")
with open(html_path, 'w') as f:
    f.write(html)

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')
