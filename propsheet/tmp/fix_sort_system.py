#!/usr/bin/env python3
"""Fix: when sorting by system_generated_value field, use the actual mapped column"""
path = '/home/webapp/goldenrabbit/backend/property-manager/services/database_service.py'
with open(path, 'r') as f:
    py = f.read()

old = """            # Check if the sort column exists in the table, fall back to created_at or id
            cursor.execute(f\"\"\"
                SELECT data_type FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            \"\"\", (table_name, sort_by))"""

new = """            # If sorting by a system_generated_value field, use the actual DB column
            if sort_by in system_fields:
                sort_by = system_fields[sort_by]  # e.g. '레코드생성일자' → 'created_at'

            # Check if the sort column exists in the table, fall back to created_at or id
            cursor.execute(f\"\"\"
                SELECT data_type FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            \"\"\", (table_name, sort_by))"""

if old in py:
    py = py.replace(old, new, 1)
    print("Added system_generated_value sort redirect")
else:
    print("WARN: pattern not found")

with open(path, 'w') as f:
    f.write(py)
