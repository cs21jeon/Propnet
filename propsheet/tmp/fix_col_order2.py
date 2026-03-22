#!/usr/bin/env python3
"""Fix: After loadColumns(), re-apply view column order"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Add view column order re-apply at the end of loadColumns()
old = """                            // Populate search field select
                            const select = document.getElementById('searchFieldSelect');
                            if (select) {
                                // Clear existing options except the first one
                                while (select.options.length > 1) {
                                    select.remove(1);
                                }
                                // Add options for all columns
                                this.allColumns.forEach(col => {
                                    const option = document.createElement('option');
                                    option.value = col.key;
                                    option.textContent = col.label;
                                    select.appendChild(option);
                                });
                            }
                        }
                    } catch (error) {
                        console.error('Error loading columns:', error);
                    }
                },"""

new = """                            // Populate search field select
                            const select = document.getElementById('searchFieldSelect');
                            if (select) {
                                while (select.options.length > 1) {
                                    select.remove(1);
                                }
                                this.allColumns.forEach(col => {
                                    const option = document.createElement('option');
                                    option.value = col.key;
                                    option.textContent = col.label;
                                    select.appendChild(option);
                                });
                            }

                            // Re-apply view column order after reload
                            this._applyViewColumnOrder();
                        }
                    } catch (error) {
                        console.error('Error loading columns:', error);
                    }
                },"""

if old in js:
    js = js.replace(old, new, 1)
    print("1. Added _applyViewColumnOrder() call in loadColumns")
else:
    print("1. WARN: pattern not found")

# Add _applyViewColumnOrder helper method
helper = """
                _applyViewColumnOrder() {
                    const view = this.views.find(v => v.id === this.currentViewId);
                    if (!view || !view.column_config) return;
                    const viewCols = Array.isArray(view.column_config) ? view.column_config : (view.column_config.columns || []);
                    if (viewCols.length === 0) return;

                    // Reorder allColumns to match view order
                    const orderMap = {};
                    viewCols.forEach((key, idx) => { orderMap[key] = idx; });
                    const maxIdx = viewCols.length;
                    this.allColumns.sort((a, b) => {
                        const ia = orderMap[a.key] !== undefined ? orderMap[a.key] : maxIdx;
                        const ib = orderMap[b.key] !== undefined ? orderMap[b.key] : maxIdx;
                        return ia - ib;
                    });

                    // Also update visibleColumns
                    this.visibleColumns = viewCols.filter(k => this.allColumns.some(c => c.key === k));
                },

"""

if '_applyViewColumnOrder' not in js or js.count('_applyViewColumnOrder') <= 2:
    # Insert before applyColumnOrder
    js = js.replace(
        '                applyColumnOrder() {',
        helper + '                applyColumnOrder() {',
        1
    )
    print("2. Added _applyViewColumnOrder helper method")
else:
    print("2. Helper already exists")

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR: {result.stderr}')
