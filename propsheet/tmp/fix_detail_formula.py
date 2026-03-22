#!/usr/bin/env python3
"""
Fix detail panel formula display:
1. openDetailPanel: use list_properties API (includes formula)
2. refreshRecord: use direct property assignment for Alpine reactivity
"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Fix 1: openDetailPanel — use list_properties API instead of get_property
old_open = """                async openDetailPanel(id) {
                    this.detailPanel.show = true;
                    this.detailPanel.loading = true;
                    this.detailPanel.itemId = id;
                    this.detailPanel.editingField = null;

                    try {
                        const res = await fetch(`${basePath}/api/database/property/${id}?db=${this.databaseId}`);
                        const data = await res.json();
                        if (data.success) {
                            this.detailPanel.item = data.data;
                        } else {
                            this.showToast(data.error || '데이터 로드 실패', 'error');
                            this.detailPanel.show = false;
                        }
                    } catch (err) {
                        this.showToast('데이터 로드 실패: ' + err.message, 'error');
                        this.detailPanel.show = false;
                    } finally {
                        this.detailPanel.loading = false;
                    }
                },"""

new_open = """                async openDetailPanel(id) {
                    this.detailPanel.show = true;
                    this.detailPanel.loading = true;
                    this.detailPanel.itemId = id;
                    this.detailPanel.editingField = null;

                    try {
                        // Use list_properties API to include formula-computed values
                        const params = new URLSearchParams({
                            db: this.databaseId,
                            page: 1, per_page: 1,
                            sort_by: 'id', sort_order: 'desc',
                            filter_id_op: 'equals', filter_id_val: id
                        });
                        const res = await fetch(`${basePath}/api/database/properties?${params}`);
                        const data = await res.json();
                        if (data.success && data.items && data.items.length > 0) {
                            this.detailPanel.item = data.items[0];
                        } else {
                            this.showToast('데이터 로드 실패', 'error');
                            this.detailPanel.show = false;
                        }
                    } catch (err) {
                        this.showToast('데이터 로드 실패: ' + err.message, 'error');
                        this.detailPanel.show = false;
                    } finally {
                        this.detailPanel.loading = false;
                    }
                },"""

if old_open in js:
    js = js.replace(old_open, new_open, 1)
    print("1. Fixed openDetailPanel to use list_properties API")
else:
    print("1. WARN: openDetailPanel pattern not found")

# Fix 2: refreshRecord — use direct property assignment for Alpine reactivity
old_refresh = """                        if (data.success && data.items && data.items.length > 0) {
                            const updated = data.items[0];
                            const idx = this.items.findIndex(i => i.id === itemId);
                            if (idx >= 0) {
                                this.items[idx] = { ...this.items[idx], ...updated };
                            }
                            // Update detail panel if open
                            if (this.detailPanel.show && this.detailPanel.itemId === itemId) {
                                this.detailPanel.item = { ...this.detailPanel.item, ...updated };
                            }
                        }"""

new_refresh = """                        if (data.success && data.items && data.items.length > 0) {
                            const updated = data.items[0];
                            const idx = this.items.findIndex(i => i.id === itemId);
                            if (idx >= 0) {
                                // Direct property assignment for Alpine reactivity
                                Object.keys(updated).forEach(k => { this.items[idx][k] = updated[k]; });
                            }
                            // Update detail panel if open — direct property assignment
                            if (this.detailPanel.show && this.detailPanel.itemId === itemId) {
                                Object.keys(updated).forEach(k => { this.detailPanel.item[k] = updated[k]; });
                            }
                        }"""

if old_refresh in js:
    js = js.replace(old_refresh, new_refresh, 1)
    print("2. Fixed refreshRecord to use direct property assignment")
else:
    print("2. WARN: refreshRecord pattern not found")

# Bump version
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()
html = html.replace("database_list.js') }}?v=1774003200", "database_list.js') }}?v=1774004000")
with open(html_path, 'w') as f:
    f.write(html)
print("3. Bumped to v=1774004000")

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')
