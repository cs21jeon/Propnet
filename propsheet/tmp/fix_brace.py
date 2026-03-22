#!/usr/bin/env python3
"""Fix missing closing brace for startInlineEdit"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    content = f.read()

# The sed command may have added }, after every }); - let's undo that first
# and fix properly
# Undo sed: remove all instances of the pattern },\n                }, that sed added
content = content.replace('});\n                },\n', '});\n')

# Now add the closing }, only before saveInlineEdit
old = '                    });\n\n                async saveInlineEdit()'
new = '                    });\n                },\n\n                async saveInlineEdit()'

if old in content:
    content = content.replace(old, new, 1)
    print('Fixed: added closing }, for startInlineEdit')
else:
    print('WARN: pattern not found')

with open(path, 'w') as f:
    f.write(content)
