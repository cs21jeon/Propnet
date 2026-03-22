#!/usr/bin/env python3
"""Add pollChanges method to database_list.js"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

poll_method = """
                // ===== Real-time Sync Polling =====
                async pollChanges() {
                    if (!this.databaseId || this.loading) return;
                    try {
                        const res = await fetch(
                            `${basePath}/api/database/changes?db=${this.databaseId}&since=${encodeURIComponent(this.syncTimestamp)}`
                        );
                        if (!res.ok) return;
                        const data = await res.json();
                        if (data.server_time) this.syncTimestamp = data.server_time;
                        if (!data.success || !data.changes || !data.changes.length) return;

                        const myEmail = document.querySelector('meta[name="user-email"]')?.content || '';
                        let needReloadData = false;
                        let needReloadColumns = false;

                        for (const change of data.changes) {
                            if (change.user_email === myEmail) continue;

                            switch (change.event_type) {
                                case 'cell_update': {
                                    const item = this.items.find(i => i.id === change.record_id);
                                    if (item && change.field_name) {
                                        item[change.field_name] = change.new_value;
                                    }
                                    break;
                                }
                                case 'record_add':
                                case 'record_delete':
                                    needReloadData = true;
                                    break;
                                case 'field_add':
                                case 'field_delete':
                                    needReloadColumns = true;
                                    needReloadData = true;
                                    break;
                            }
                        }

                        if (needReloadColumns) await this.loadColumns();
                        if (needReloadData) await this.loadData();
                    } catch (e) {
                        // Silent retry on next poll
                    }
                },

"""

if 'async pollChanges' not in js:
    js = js.replace(
        '                formatCell(value, col, row) {',
        poll_method + '                formatCell(value, col, row) {',
        1
    )
    print('Added pollChanges method')
else:
    print('pollChanges already exists')

with open(path, 'w') as f:
    f.write(js)

# Verify
import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'JS ERROR:\n{result.stderr}')
