#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/services/database_service.py'
with open(path, 'r') as f:
    c = f.read()

old = '''            # Always include raw airtable_id for image rendering
            select_parts.append(f'"{table_name}".airtable_id AS _raw_airtable_id')'''

new = '''            # Include raw airtable_id for image rendering (only if column exists)
            if 'airtable_id' in table_columns:
                select_parts.append(f'"{table_name}".airtable_id AS _raw_airtable_id')'''

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(c)
    print("OK - Fixed airtable_id column check")
else:
    print("WARN: pattern not found")
