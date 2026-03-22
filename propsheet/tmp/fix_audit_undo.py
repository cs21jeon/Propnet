#!/usr/bin/env python3
"""Fix audit logging in update_single_field + force flag for undo"""

route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(route_path, 'r') as f:
    content = f.read()

# === 1. Add force flag to skip optimistic locking ===
old_lock = """        expected_updated_at = data.get('updated_at')

        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                # Optimistic locking: check updated_at before saving
                if expected_updated_at:"""

new_lock = """        expected_updated_at = data.get('updated_at')
        force = data.get('force', False)

        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                # Optimistic locking: check updated_at before saving (skip if force=True for undo)
                if expected_updated_at and not force:"""

if 'force = data.get' not in content:
    content = content.replace(old_lock, new_lock, 1)
    print("1. Added force flag for optimistic locking skip")

# === 2. Add old value fetch + audit logging before UPDATE ===
old_update = """                escaped_field = escape_column_name(field)
                query = f'UPDATE "{db_info["table_name"]}" SET {escaped_field} = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING updated_at'
                cursor.execute(query, (value, property_id))
                result = cursor.fetchone()
                conn.commit()"""

new_update = """                # Fetch old value for audit log
                from psycopg2 import sql as psql_audit
                cursor.execute(psql_audit.SQL('SELECT {} FROM {} WHERE id = %s').format(
                    psql_audit.Identifier(field), psql_audit.Identifier(db_info['table_name'])
                ), (property_id,))
                old_row = cursor.fetchone()
                old_value = old_row[field] if old_row else None

                escaped_field = escape_column_name(field)
                query = f'UPDATE "{db_info["table_name"]}" SET {escaped_field} = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING updated_at'
                cursor.execute(query, (value, property_id))
                result = cursor.fetchone()

                # Audit log (same transaction)
                _log_audit(cursor, database_id, property_id, field, old_value, value,
                          user_id=session.get('user_id'), user_email=session.get('user_email'))

                conn.commit()"""

if 'Fetch old value for audit' not in content:
    content = content.replace(old_update, new_update, 1)
    print("2. Added audit logging to update_single_field")

with open(route_path, 'w') as f:
    f.write(content)

# === 3. JS: Add force=true to undoLast ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

# Add force:true to undo request
old_undo_body = """                            body: JSON.stringify({
                                field: entry.field,
                                value: entry.oldValue,
                                db: this.databaseId,
                                updated_at: item ? item.updated_at : null
                            })"""

new_undo_body = """                            body: JSON.stringify({
                                field: entry.field,
                                value: entry.oldValue,
                                db: this.databaseId,
                                updated_at: item ? item.updated_at : null,
                                force: true
                            })"""

if 'force: true' not in js.split('undoLast')[1].split('undoLast')[0] if js.count('undoLast') > 1 else '':
    js = js.replace(old_undo_body, new_undo_body, 1)
    print("3. Added force=true to undoLast")

with open(js_path, 'w') as f:
    f.write(js)

print("Done!")
