#!/usr/bin/env python3
"""Fix: After saving a cell, refresh the record from server to get formula results"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# 1. Add _refreshRecord helper method
refresh_method = """
                async _refreshRecord(itemId) {
                    // Fetch updated record from server (includes formula results)
                    try {
                        const res = await fetch(`${basePath}/api/database/property/${itemId}?db=${this.databaseId}`);
                        if (!res.ok) return;
                        const data = await res.json();
                        if (data.success && data.item) {
                            const idx = this.items.findIndex(i => i.id === itemId);
                            if (idx >= 0) {
                                this.items[idx] = { ...this.items[idx], ...data.item };
                            }
                            // Update detail panel if open
                            if (this.detailPanel.show && this.detailPanel.itemId === itemId) {
                                this.detailPanel.item = { ...this.detailPanel.item, ...data.item };
                            }
                        }
                    } catch (e) {
                        // Silent fail
                    }
                },

"""

if '_refreshRecord' not in js:
    js = js.replace(
        '                async saveInlineEdit() {',
        refresh_method + '                async saveInlineEdit() {',
        1
    )
    print("1. Added _refreshRecord method")

# 2. Call _refreshRecord after successful saveInlineEdit
old_inline = """                            if (item) {
                                item[colKey] = value || null;
                                if (data.updated_at) item.updated_at = data.updated_at;
                                this.pushUndo(itemId, colKey, originalValue, value);
                                // Update cell cache for this cell
                                const col = this.visibleColumnObjects.find(c => c.key === colKey);
                                if (col) this._invalidateCellCache(itemId, colKey, value || null, col, item);
                            }"""

new_inline = """                            if (item) {
                                item[colKey] = value || null;
                                if (data.updated_at) item.updated_at = data.updated_at;
                                this.pushUndo(itemId, colKey, originalValue, value);
                            }
                            // Refresh record to get formula results
                            await this._refreshRecord(itemId);"""

if old_inline in js:
    js = js.replace(old_inline, new_inline, 1)
    print("2. Added _refreshRecord to saveInlineEdit")
else:
    # Try without cache invalidation line (might not exist)
    old_inline2 = """                            if (item) {
                                item[colKey] = value || null;
                                if (data.updated_at) item.updated_at = data.updated_at;
                                this.pushUndo(itemId, colKey, originalValue, value);
                            }"""
    new_inline2 = """                            if (item) {
                                item[colKey] = value || null;
                                if (data.updated_at) item.updated_at = data.updated_at;
                                this.pushUndo(itemId, colKey, originalValue, value);
                            }
                            // Refresh record to get formula results
                            await this._refreshRecord(itemId);"""
    if old_inline2 in js:
        js = js.replace(old_inline2, new_inline2, 1)
        print("2b. Added _refreshRecord to saveInlineEdit (alt)")

# 3. Call _refreshRecord after successful saveSelectValue
old_select = """                                this.pushUndo(itemId, colKey, prevValue, value);
                                // Update cell cache
                                const col = this.visibleColumnObjects.find(c => c.key === colKey);
                                if (col) this._invalidateCellCache(itemId, colKey, value || null, col, item);"""

new_select = """                                this.pushUndo(itemId, colKey, prevValue, value);
                            }
                            // Refresh record to get formula results
                            await this._refreshRecord(itemId);
                            if (false) {"""

if old_select in js:
    js = js.replace(old_select, new_select, 1)
    print("3. Added _refreshRecord to saveSelectValue")
else:
    # Try simpler pattern
    old_select2 = """                                this.pushUndo(itemId, colKey, prevValue, value);
                            }"""
    new_select2 = """                                this.pushUndo(itemId, colKey, prevValue, value);
                            }
                            // Refresh record to get formula results
                            await this._refreshRecord(itemId);"""
    # Only replace in saveSelectValue context - find the right one
    # Count occurrences
    count = js.count(old_select2)
    if count > 0:
        # Replace only the one in saveSelectValue (second occurrence after saveInlineEdit)
        # Actually let's be safe and just add it after the saveSelectValue function's success block
        pass
    print("3. SKIP - will handle manually if needed")

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')
