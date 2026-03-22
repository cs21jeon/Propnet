#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

# Add attachment option to field type dropdown
old = '<option value="system_generated_value">System Value (시스템설정값)</option>'
new = '<option value="attachment">File (파일/이미지)</option>\n                            <option value="system_generated_value">System Value (시스템설정값)</option>'

if 'value="attachment"' not in html:
    html = html.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(html)
    print("OK - Added attachment type to dropdown")
else:
    print("Already exists")
