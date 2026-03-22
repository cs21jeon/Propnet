#!/usr/bin/env python3
"""Swap select tag bg/text colors in dark mode"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Add isDark helper at top of formatCellWithColor
old_fcwc = """                formatCellWithColor(value, col) {
                    if (value === null || value === undefined) return '-';
                    const options = col.selectOptions || [];

                    if (col.type === 'single-select') {
                        if (!value || value === '-') return '-';
                        const c = this.getOptionColor(value, options, col);
                        return `<span class="select-tag" style="background:${c.bg};color:${c.text}">${value}</span>`;
                    }
                    if (col.type === 'multi-select') {
                        if (!value || value === '-') return '-';
                        let values = [];
                        if (Array.isArray(value)) values = value;
                        else if (typeof value === 'string') values = value.split(',').map(v => v.trim()).filter(v => v);
                        if (values.length === 0) return '-';
                        return values.map(v => {
                            const c = this.getOptionColor(v, options, col);
                            return `<span class="select-tag" style="background:${c.bg};color:${c.text}">${v}</span>`;
                        }).join(' ');
                    }"""

new_fcwc = """                formatCellWithColor(value, col) {
                    if (value === null || value === undefined) return '-';
                    const options = col.selectOptions || [];
                    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

                    if (col.type === 'single-select') {
                        if (!value || value === '-') return '-';
                        const c = this.getOptionColor(value, options, col);
                        const bg = isDark ? c.text : c.bg;
                        const text = isDark ? c.bg : c.text;
                        return `<span class="select-tag" style="background:${bg};color:${text}">${value}</span>`;
                    }
                    if (col.type === 'multi-select') {
                        if (!value || value === '-') return '-';
                        let values = [];
                        if (Array.isArray(value)) values = value;
                        else if (typeof value === 'string') values = value.split(',').map(v => v.trim()).filter(v => v);
                        if (values.length === 0) return '-';
                        return values.map(v => {
                            const c = this.getOptionColor(v, options, col);
                            const bg = isDark ? c.text : c.bg;
                            const text = isDark ? c.bg : c.text;
                            return `<span class="select-tag" style="background:${bg};color:${text}">${v}</span>`;
                        }).join(' ');
                    }"""

if old_fcwc in js:
    js = js.replace(old_fcwc, new_fcwc, 1)
    print("1. Swapped select tag colors in formatCellWithColor")
else:
    print("1. WARN: formatCellWithColor pattern not found")

# Also need to refresh cells when theme changes (toggle)
# In toggleTheme, trigger loadData to re-render cells with new colors
old_toggle = """                toggleTheme() {
                    this.darkMode = !this.darkMode;
                    if (this.darkMode) {
                        document.documentElement.setAttribute('data-theme', 'dark');
                        localStorage.setItem('propsheet-theme', 'dark');
                    } else {
                        document.documentElement.removeAttribute('data-theme');
                        localStorage.setItem('propsheet-theme', 'light');
                    }
                },"""

new_toggle = """                toggleTheme() {
                    this.darkMode = !this.darkMode;
                    if (this.darkMode) {
                        document.documentElement.setAttribute('data-theme', 'dark');
                        localStorage.setItem('propsheet-theme', 'dark');
                    } else {
                        document.documentElement.removeAttribute('data-theme');
                        localStorage.setItem('propsheet-theme', 'light');
                    }
                    // Re-render to apply color changes
                    this.loadData();
                },"""

if old_toggle in js:
    js = js.replace(old_toggle, new_toggle, 1)
    print("2. Added loadData to toggleTheme for color refresh")

# Bump version
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()
import re
html = re.sub(r"database_list\.js'\) \}\}\?v=\d+", "database_list.js') }}?v=1774005200", html)
with open(html_path, 'w') as f:
    f.write(html)
print("3. Bumped JS version")

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')
