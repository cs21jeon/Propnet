#!/usr/bin/env python3
"""Fix 2: Close floating editor on scroll"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Add scroll listener after the "Click outside to deselect columns" block
old = "                    // Ctrl+Z undo listener"
new = """                    // Scroll closes floating editor (prevents position mismatch)
                    const _tableContainer = document.querySelector('.table-container');
                    if (_tableContainer) {
                        _tableContainer.addEventListener('scroll', () => {
                            if (this.editingCell.itemId !== null) {
                                this.saveInlineEdit();
                            }
                        });
                    }

                    // Ctrl+Z undo listener"""

if old in js:
    js = js.replace(old, new, 1)
    print('Added scroll listener to close floating editor')
else:
    print('WARN: pattern not found')

with open(path, 'w') as f:
    f.write(js)
print('Done')
