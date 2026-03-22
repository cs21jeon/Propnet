#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/services/workspace_service.py'
with open(path, 'r') as f:
    content = f.read()

# Fix: escape % in column names for psycopg2
old = """            column_names = [col['column_name'] for col in columns]
            columns_str = ', '.join([f'"{col}"' for col in column_names])"""

new = """            column_names = [col['column_name'] for col in columns]
            # Escape % in column names for psycopg2 (e.g. "건폐율(%)")
            columns_str = ', '.join([f'"{col.replace(chr(37), chr(37)+chr(37))}"' for col in column_names])"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print("OK - Fixed % escape in clone column names")
else:
    print("WARN: pattern not found")
