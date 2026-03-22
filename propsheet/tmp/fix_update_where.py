#!/usr/bin/env python3
"""Fix UPDATE WHERE clause to scope by database_id"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    content = f.read()

# Fix UPDATE: add database_id to WHERE
old = """                        WHERE field_name = %s
                    ''', (display_name, field_type, column_width, formula, select_options, json_mod.dumps(select_colors) if select_colors else None, json_mod.dumps(number_format) if number_format else None, json_mod.dumps(date_format) if date_format else None, is_editable, system_value_key, field_name))"""

new = """                        WHERE field_name = %s AND database_id = %s
                    ''', (display_name, field_type, column_width, formula, select_options, json_mod.dumps(select_colors) if select_colors else None, json_mod.dumps(number_format) if number_format else None, json_mod.dumps(date_format) if date_format else None, is_editable, system_value_key, field_name, fd_database_id))"""

if 'WHERE field_name = %s AND database_id' not in content:
    content = content.replace(old, new, 1)
    print("1. Fixed UPDATE WHERE with database_id")
else:
    print("1. Already fixed")

# Also fix the SELECT check
old_check = """cursor.execute(
                    'SELECT id FROM field_definitions WHERE field_name = %s',
                    (field_name,)
                )"""
new_check = """cursor.execute(
                    'SELECT id FROM field_definitions WHERE field_name = %s AND database_id = %s',
                    (field_name, fd_database_id)
                )"""

if "WHERE field_name = %s'," in content and "AND database_id = %s'," not in content:
    content = content.replace(old_check, new_check, 1)
    print("2. Fixed SELECT check with database_id")

with open(path, 'w') as f:
    f.write(content)
print("Done")
