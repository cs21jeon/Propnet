#!/usr/bin/env python3
"""Fix clone_column: also clone field_definitions"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    content = f.read()

# Add field_definitions clone after data copy
old = """                # Copy data from source column to new column
                cursor.execute(f'''
                    UPDATE "{db_info['table_name']}"
                    SET "{new_column_name}" = "{source_column}"
                ''')

                conn.commit()

        return jsonify({'success': True, 'message': '필드가 복제되었습니다'})"""

new = """                # Copy data from source column to new column
                cursor.execute(f'''
                    UPDATE "{db_info['table_name']}"
                    SET "{new_column_name}" = "{source_column}"
                ''')

                # Clone field_definition if exists
                from psycopg2.extras import RealDictCursor as RDC2
                cursor2 = conn.cursor(cursor_factory=RDC2)
                cursor2.execute(
                    "SELECT * FROM field_definitions WHERE field_name = %s AND database_id = %s",
                    (source_column, database_id)
                )
                src_fd = cursor2.fetchone()
                if src_fd:
                    import json as json_clone
                    from psycopg2.extras import Json
                    cursor.execute('''
                        INSERT INTO field_definitions
                        (database_id, field_name, display_name, field_type, formula, select_options,
                         select_colors, number_format, date_format, is_editable, system_value_key, api_key)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        database_id, new_column_name, new_column_name, src_fd['field_type'],
                        src_fd.get('formula'), src_fd.get('select_options'),
                        Json(src_fd['select_colors']) if src_fd.get('select_colors') else None,
                        Json(src_fd['number_format']) if src_fd.get('number_format') else None,
                        Json(src_fd['date_format']) if src_fd.get('date_format') else None,
                        src_fd.get('is_editable', True), src_fd.get('system_value_key'),
                        new_column_name
                    ))
                cursor2.close()

                conn.commit()

        return jsonify({'success': True, 'message': '필드가 복제되었습니다'})"""

if 'Clone field_definition' not in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print("OK - Added field_definitions clone to clone_column")
else:
    print("Already has")
