#!/usr/bin/env python3
import json

path = "/home/webapp/goldenrabbit/backend/property-manager/routes/database.py"
with open(path, "r") as f:
    content = f.read()

if 'select_colors' in content:
    print("Already has select_colors")
else:
    # Add select_colors to data extraction
    content = content.replace(
        "select_options = data.get('select_options')\n        system_value_key = data.get('system_value_key') # New",
        "select_options = data.get('select_options')\n        select_colors = data.get('select_colors')  # color map {option: {bg, text}}\n        system_value_key = data.get('system_value_key') # New"
    )

    # Update UPDATE query
    content = content.replace(
        """                    cursor.execute('''
                        UPDATE field_definitions
                        SET field_type = %s,
                            column_width = %s,
                            formula = %s,
                            select_options = %s,
                            is_editable = %s,
                            system_value_key = %s
                        WHERE field_name = %s
                    ''', (field_type, column_width, formula, select_options, is_editable, system_value_key, field_name))""",
        """                    import json as json_mod
                    cursor.execute('''
                        UPDATE field_definitions
                        SET field_type = %s,
                            column_width = %s,
                            formula = %s,
                            select_options = %s,
                            select_colors = %s,
                            is_editable = %s,
                            system_value_key = %s
                        WHERE field_name = %s
                    ''', (field_type, column_width, formula, select_options, json_mod.dumps(select_colors) if select_colors else None, is_editable, system_value_key, field_name))"""
    )

    # Update INSERT query
    content = content.replace(
        """                    cursor.execute('''
                        INSERT INTO field_definitions
                        (field_name, display_name, field_type, column_width, formula, select_options, is_editable, system_value_key)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (field_name, field_name, field_type, column_width, formula, select_options, is_editable, system_value_key))""",
        """                    cursor.execute('''
                        INSERT INTO field_definitions
                        (field_name, display_name, field_type, column_width, formula, select_options, select_colors, is_editable, system_value_key)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (field_name, field_name, field_type, column_width, formula, select_options, json_mod.dumps(select_colors) if select_colors else None, is_editable, system_value_key))"""
    )

    with open(path, "w") as f:
        f.write(content)
    print("OK - Added select_colors to field-definition save")
