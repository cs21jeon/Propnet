#!/usr/bin/env python3
"""
Fix: After file upload, update the cell value so formatCell can render it.
Format: "original_filename (url)" — same as airtable format.
Also fix file extension in saved filename (missing dot).
"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    content = f.read()

# Fix 1: Add dot before extension in saved filename
old_fname = "safe_filename = f'{uuid.uuid4().hex[:12]}_{ext}' if ext else uuid.uuid4().hex[:12]"
new_fname = "safe_filename = f'{uuid.uuid4().hex[:12]}.{ext}' if ext else uuid.uuid4().hex[:12]"
if old_fname in content:
    content = content.replace(old_fname, new_fname, 1)
    print("1. Fixed filename extension (added dot)")

# Fix 2: After saving metadata, update the cell value in the record
old_log = "logger.info(f\"File uploaded: {file.filename} ({file_size} bytes) to db={db_id}, record={record_id}\")"
new_log = """# Update cell value to show the file
                from psycopg2 import sql as psql
                from services.workspace_service import get_database as get_db_info
                db_info = get_db_info(db_id)
                if db_info:
                    table_name = db_info['table_name']
                    # Build cell value: "filename (url)" format for existing formatCell rendering
                    cell_value = f'{file.filename} ({relative_path})'
                    # Get current cell value and append if exists
                    cursor.execute(psql.SQL('SELECT {} FROM {} WHERE id = %s').format(
                        psql.Identifier(field_name), psql.Identifier(table_name)
                    ), (record_id,))
                    current = cursor.fetchone()
                    if current:
                        current_val = current.get(field_name) or current[0] if isinstance(current, dict) else current[0]
                        if current_val and str(current_val).strip():
                            cell_value = str(current_val) + ', ' + cell_value
                    cursor.execute(psql.SQL('UPDATE {} SET {} = %s WHERE id = %s').format(
                        psql.Identifier(table_name), psql.Identifier(field_name)
                    ), (cell_value, record_id))
                    conn.commit()

                logger.info(f"File uploaded: {file.filename} ({file_size} bytes) to db={db_id}, record={record_id}")"""

if old_log in content:
    content = content.replace(old_log, new_log, 1)
    print("2. Added cell value update after upload")

# Fix 3: On delete, also update cell value
old_delete = """                # Delete metadata
                cursor.execute('DELETE FROM file_attachments WHERE id = %s', (file_id,))
                conn.commit()"""

new_delete = """                # Delete metadata
                cursor.execute('DELETE FROM file_attachments WHERE id = %s', (file_id,))

                # Rebuild cell value from remaining files
                from psycopg2 import sql as psql
                from services.workspace_service import get_database as get_db_info2
                db_info = get_db_info2(db_id)
                if db_info:
                    cursor.execute(
                        'SELECT original_filename, file_path FROM file_attachments WHERE database_id = %s AND record_id = %s AND field_name = %s ORDER BY created_at',
                        (db_id, file_rec['record_id'], file_rec['field_name'])
                    )
                    remaining = cursor.fetchall()
                    if remaining:
                        cell_value = ', '.join(f"{r['original_filename']} ({r['file_path']})" for r in remaining)
                    else:
                        cell_value = None
                    cursor.execute(psql.SQL('UPDATE {} SET {} = %s WHERE id = %s').format(
                        psql.Identifier(db_info['table_name']), psql.Identifier(file_rec['field_name'])
                    ), (cell_value, file_rec['record_id']))

                conn.commit()"""

if old_delete in content:
    content = content.replace(old_delete, new_delete, 1)
    print("3. Added cell value rebuild on delete")

with open(path, 'w') as f:
    f.write(content)

print("Done!")
