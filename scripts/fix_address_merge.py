#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/register.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old = "        address = request.form.get('address', '').strip()\n        license_no"
new = """        address = request.form.get('address', '').strip()
        address_detail = request.form.get('address_detail', '').strip()
        if address_detail:
            address = address + ' ' + address_detail
        license_no"""

c = c.replace(old, new)
with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
