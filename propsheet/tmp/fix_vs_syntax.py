#!/usr/bin/env python3
"""Fix virtual scroll syntax error in loadData"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list_v2.js'
with open(path, 'r') as f:
    js = f.read()

# The broken block
old = """                            this._scrollTop = 0;
                            this._buildCellCache();
                            // Init container height
                            this.$nextTick(() => {
                                const c = this.$refs.virtualContainer;
                                if (c) this._containerHeight = c.clientHeight;
                            });});
                            } else {
                                this.items = allItems;
                                this._buildCellCache();
                            }
                        }"""

new = """                            this._scrollTop = 0;
                            this._buildCellCache();
                            // Init container height
                            this.$nextTick(() => {
                                const c = this.$refs.virtualContainer;
                                if (c) this._containerHeight = c.clientHeight;
                            });
                        }"""

if old in js:
    js = js.replace(old, new, 1)
    print('Fixed loadData syntax')
else:
    print('WARN: pattern not found')

with open(path, 'w') as f:
    f.write(js)

# Verify
import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
if result.returncode == 0:
    print('JS syntax: OK')
else:
    print(f'JS ERROR:\n{result.stderr}')
