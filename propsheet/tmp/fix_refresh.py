#!/usr/bin/env python3
"""Fix _refreshRecord to use correct API response key, and add to saveSelectValue"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# 1. Fix _refreshRecord: API returns data.data, not data.item
old_refresh = """                        if (data.success && data.item) {
                            const idx = this.items.findIndex(i => i.id === itemId);
                            if (idx >= 0) {
                                this.items[idx] = { ...this.items[idx], ...data.item };
                            }
                            // Update detail panel if open
                            if (this.detailPanel.show && this.detailPanel.itemId === itemId) {
                                this.detailPanel.item = { ...this.detailPanel.item, ...data.item };
                            }"""

new_refresh = """                        if (data.success && data.data) {
                            const updated = data.data;
                            const idx = this.items.findIndex(i => i.id === itemId);
                            if (idx >= 0) {
                                this.items[idx] = { ...this.items[idx], ...updated };
                            }
                            // Update detail panel if open
                            if (this.detailPanel.show && this.detailPanel.itemId === itemId) {
                                this.detailPanel.item = { ...this.detailPanel.item, ...updated };
                            }"""

if old_refresh in js:
    js = js.replace(old_refresh, new_refresh, 1)
    print("1. Fixed _refreshRecord response key (item -> data)")

# 2. Add _refreshRecord to saveSelectValue
# Find the success block in saveSelectValue
old_sv = """                                this.pushUndo(itemId, colKey, prevValue, value);
                            }
                        } else if (res.status === 409) {
                            this.handleConflict(itemId);
                        } else {
                            this.showToast(data.error || '저장 실패', 'error');
                        }
                    } catch (err) {
                        this.showToast('저장 실패: ' + err.message, 'error');
                    }
                },


                async uploadFile"""

new_sv = """                                this.pushUndo(itemId, colKey, prevValue, value);
                            }
                            // Refresh record to get formula results
                            await this._refreshRecord(itemId);
                        } else if (res.status === 409) {
                            this.handleConflict(itemId);
                        } else {
                            this.showToast(data.error || '저장 실패', 'error');
                        }
                    } catch (err) {
                        this.showToast('저장 실패: ' + err.message, 'error');
                    }
                },


                async uploadFile"""

if old_sv in js:
    js = js.replace(old_sv, new_sv, 1)
    print("2. Added _refreshRecord to saveSelectValue")
else:
    print("2. WARN: saveSelectValue pattern not found")

# 3. Also add to saveDetailField if it exists
if 'saveDetailField' in js:
    # Find saveDetailField success
    import re
    detail_match = re.search(r'async saveDetailField.*?this\.showToast\(.저장 실패.*?\}', js, re.DOTALL)
    if detail_match and '_refreshRecord' not in detail_match.group(0):
        # Find the success block inside saveDetailField
        old_detail = detail_match.group(0)
        # Add refresh after pushUndo in detail save
        if 'pushUndo' in old_detail:
            new_detail = old_detail.replace(
                'this.pushUndo(',
                'await this._refreshRecord(this.detailPanel.itemId);\n                        this.pushUndo(',
                1
            )
            js = js.replace(old_detail, new_detail, 1)
            print("3. Added _refreshRecord to saveDetailField")

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')
