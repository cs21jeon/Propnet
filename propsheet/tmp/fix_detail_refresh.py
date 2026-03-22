#!/usr/bin/env python3
"""Add _refreshRecord to saveDetailField"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

old = """                        if (data.success) {
                            this.detailPanel.item[fieldKey] = newValue || null;
                            if (data.updated_at) this.detailPanel.item.updated_at = data.updated_at;
                            const item = this.items.find(i => i.id === this.detailPanel.itemId);
                            if (item) {
                                item[fieldKey] = newValue || null;
                                if (data.updated_at) item.updated_at = data.updated_at;
                            }
                        } else if (res.status === 409) {
                            this.handleConflict(this.detailPanel.itemId);
                        } else {
                            this.showToast(data.error || '저장 실패', 'error');
                        }
                    } catch (err) {
                        this.showToast('저장 실패: ' + err.message, 'error');
                    }
                },

                handleDetailKeydown"""

new = """                        if (data.success) {
                            this.detailPanel.item[fieldKey] = newValue || null;
                            if (data.updated_at) this.detailPanel.item.updated_at = data.updated_at;
                            const item = this.items.find(i => i.id === this.detailPanel.itemId);
                            if (item) {
                                item[fieldKey] = newValue || null;
                                if (data.updated_at) item.updated_at = data.updated_at;
                            }
                            // Refresh record to get formula results
                            await this._refreshRecord(this.detailPanel.itemId);
                        } else if (res.status === 409) {
                            this.handleConflict(this.detailPanel.itemId);
                        } else {
                            this.showToast(data.error || '저장 실패', 'error');
                        }
                    } catch (err) {
                        this.showToast('저장 실패: ' + err.message, 'error');
                    }
                },

                handleDetailKeydown"""

if old in js:
    js = js.replace(old, new, 1)
    print("Added _refreshRecord to saveDetailField")
else:
    print("WARN: pattern not found")

# Bump version
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()
html = html.replace("database_list.js') }}?v=1774003000", "database_list.js') }}?v=1774003100")
with open(html_path, 'w') as f:
    f.write(html)
print("Bumped to v=1774003100")

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')
