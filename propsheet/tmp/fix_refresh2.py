#!/usr/bin/env python3
"""Fix: _refreshRecord should use list_properties API (includes formula) instead of get_property"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

old = """                async _refreshRecord(itemId) {
                    // Fetch updated record from server (includes formula results)
                    try {
                        const res = await fetch(`${basePath}/api/database/property/${itemId}?db=${this.databaseId}`);
                        if (!res.ok) return;
                        const data = await res.json();
                        if (data.success && data.data) {
                            const updated = data.data;
                            const idx = this.items.findIndex(i => i.id === itemId);
                            if (idx >= 0) {
                                this.items[idx] = { ...this.items[idx], ...updated };
                            }
                            // Update detail panel if open
                            if (this.detailPanel.show && this.detailPanel.itemId === itemId) {
                                this.detailPanel.item = { ...this.detailPanel.item, ...updated };
                            }
                        }
                    } catch (e) {
                        // Silent fail
                    }
                },"""

new = """                async _refreshRecord(itemId) {
                    // Fetch updated record from server (includes formula results)
                    // Use list_properties API with filter to get formula-computed values
                    try {
                        const params = new URLSearchParams({
                            db: this.databaseId,
                            page: 1,
                            per_page: 1,
                            sort_by: 'id',
                            sort_order: 'desc',
                            [`filter_id_op`]: 'equals',
                            [`filter_id_val`]: itemId
                        });
                        const res = await fetch(`${basePath}/api/database/properties?${params}`);
                        if (!res.ok) return;
                        const data = await res.json();
                        if (data.success && data.items && data.items.length > 0) {
                            const updated = data.items[0];
                            const idx = this.items.findIndex(i => i.id === itemId);
                            if (idx >= 0) {
                                this.items[idx] = { ...this.items[idx], ...updated };
                            }
                            // Update detail panel if open
                            if (this.detailPanel.show && this.detailPanel.itemId === itemId) {
                                this.detailPanel.item = { ...this.detailPanel.item, ...updated };
                            }
                        }
                    } catch (e) {
                        // Silent fail
                    }
                },"""

if old in js:
    js = js.replace(old, new, 1)
    print("Fixed _refreshRecord to use list_properties API (includes formula)")
else:
    print("WARN: pattern not found")

with open(path, 'w') as f:
    f.write(js)

# Bump version
import re
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()
html = html.replace("database_list.js') }}?v=1774002000", "database_list.js') }}?v=1774003000")
with open(html_path, 'w') as f:
    f.write(html)
print("Bumped JS version to 1774003000")

# Verify syntax
import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')
