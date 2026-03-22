#!/usr/bin/env python3
"""Fix: When view has column_config, reorder allColumns to match view's column order"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# After setting visibleColumns from view config, also reorder allColumns
old = """                    if (hasViewColumns) {
                        if (Array.isArray(viewConfig)) {
                            this.visibleColumns = viewConfig.filter(k => this.allColumns.some(c => c.key === k));
                        } else {
                            this.visibleColumns = viewConfig.columns.filter(k => this.allColumns.some(c => c.key === k));
                            if (viewConfig.widths) {
                                this.columnWidths = { ...this.columnWidths, ...viewConfig.widths };
                            }
                        }
                    } else {
                        // No view column config: show all columns
                        this.visibleColumns = this.allColumns.map(col => col.key);
                    }"""

new = """                    if (hasViewColumns) {
                        const viewCols = Array.isArray(viewConfig) ? viewConfig : (viewConfig.columns || []);
                        this.visibleColumns = viewCols.filter(k => this.allColumns.some(c => c.key === k));
                        if (!Array.isArray(viewConfig) && viewConfig.widths) {
                            this.columnWidths = { ...this.columnWidths, ...viewConfig.widths };
                        }
                        // Reorder allColumns to match view's column order
                        const orderMap = {};
                        viewCols.forEach((key, idx) => { orderMap[key] = idx; });
                        const maxIdx = viewCols.length;
                        this.allColumns.sort((a, b) => {
                            const ia = orderMap[a.key] !== undefined ? orderMap[a.key] : maxIdx;
                            const ib = orderMap[b.key] !== undefined ? orderMap[b.key] : maxIdx;
                            return ia - ib;
                        });
                    } else {
                        // No view column config: show all columns
                        this.visibleColumns = this.allColumns.map(col => col.key);
                    }"""

if old in js:
    js = js.replace(old, new, 1)
    print("Fixed: allColumns reordered by view's column_config")
else:
    print("WARN: pattern not found")

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR: {result.stderr}')
