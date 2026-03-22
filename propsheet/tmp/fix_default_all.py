#!/usr/bin/env python3
"""When view has no column_config, always show all columns (ignore localStorage)"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

old = """                    } else {
                        // Fallback to localStorage or defaults
                        const savedColumns = localStorage.getItem(`visibleColumns_${this.databaseId}`);
                        if (savedColumns) {
                            const saved = JSON.parse(savedColumns);
                            this.visibleColumns = saved.filter(key => this.allColumns.some(col => col.key === key));
                            if (this.visibleColumns.length === 0) {
                                this.visibleColumns = this.allColumns.map(col => col.key);
                            }
                        } else {
                            this.visibleColumns = this.allColumns.map(col => col.key);
                        }
                    }"""

new = """                    } else {
                        // No view column config: show all columns
                        this.visibleColumns = this.allColumns.map(col => col.key);
                    }"""

if old in js:
    js = js.replace(old, new, 1)
    print("Removed localStorage fallback, always show all columns when view has no config")
else:
    print("WARN: pattern not found")

with open(path, 'w') as f:
    f.write(js)
