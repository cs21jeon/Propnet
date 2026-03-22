#!/usr/bin/env python3
"""Add audit logging, history API, trash/restore"""

route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(route_path, 'r') as f:
    content = f.read()

# === 1. Add audit logging to update_single_field ===
# Find where the field is updated successfully
old_success = """                        if data.success:
                            if (item) {
                                item[colKey] = value || null;"""
# Actually this is JS. We need to find the Python route.

# Find the actual update in the Python route
old_update_success = """                    cursor.execute(f'''
                        UPDATE "{db_info['table_name']}" SET "{field}" = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', (value, property_id))"""

# Let's find the exact pattern
import re

# Find update_single_field function and add audit logging
if 'audit_log' not in content:
    # Add audit insert after successful field update
    # Find the pattern: after UPDATE SET field = value, before conn.commit()
    # The update_single_field function updates a single field

    # Add a helper function for audit logging at the top of the file (after imports)
    audit_helper = '''

def _log_audit(cursor, database_id, record_id, field_name, old_value, new_value, user_id=None, user_email=None):
    """Log a field change to audit_log"""
    try:
        cursor.execute("""
            INSERT INTO audit_log (database_id, record_id, field_name, old_value, new_value, user_id, user_email)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (database_id, record_id, field_name,
              str(old_value) if old_value is not None else None,
              str(new_value) if new_value is not None else None,
              user_id, user_email))
    except Exception as e:
        logger.warning(f"Audit log failed: {e}")

'''
    # Insert after the imports section
    marker = "bp = Blueprint('database', __name__)"
    if marker in content:
        content = content.replace(marker, marker + audit_helper, 1)
        print("1a. Added _log_audit helper")

    # Add audit logging to update_single_field
    # Find where it reads the old value and updates
    old_field_update = """                # Update the field
                cursor.execute(
                    f'UPDATE "{db_info["table_name"]}" SET "{field}" = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s',
                    (value, property_id)
                )"""

    if old_field_update not in content:
        # Try alternative pattern
        old_field_update = """                cursor.execute(f\'\'\'
                    UPDATE "{db_info["table_name"]}" SET "{field}" = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                \'\'\', (value, property_id))"""

    # Search for any UPDATE pattern in update_single_field
    # Let's find it by context
    update_section = content[content.index('def update_single_field'):]
    update_func_end = update_section.index('\ndef ', 10)
    update_func = update_section[:update_func_end]

    # Find the UPDATE ... SET "{field}" pattern
    update_match = re.search(r'cursor\.execute\([^)]*UPDATE[^)]*SET[^)]*\{field\}[^)]*\)', update_func)
    if update_match:
        old_stmt = update_match.group()
        # Add old value fetch + audit before the update
        new_stmt = f"""# Fetch old value for audit
                from psycopg2 import sql as psql
                cursor.execute(psql.SQL('SELECT {{}} FROM {{}} WHERE id = %s').format(
                    psql.Identifier(field), psql.Identifier(db_info['table_name'])
                ), (property_id,))
                old_row = cursor.fetchone()
                old_value = old_row[field] if old_row and isinstance(old_row, dict) else (old_row[0] if old_row else None)

                {old_stmt}

                # Audit log
                _log_audit(cursor, database_id, property_id, field, old_value, value,
                          user_id=session.get('user_id'), user_email=session.get('user_email'))"""

        content = content[:content.index('def update_single_field') + update_match.start()] + new_stmt + content[content.index('def update_single_field') + update_match.end():]
        print("1b. Added audit logging to update_single_field")

# === 2. Add history API ===
history_routes = '''

@bp.route('/database/<int:db_id>/history/<int:record_id>/<field_name>', methods=['GET'])
@login_required
@require_database_role("viewer")
def get_field_history(db_id, record_id, field_name):
    """Get change history for a specific field"""
    try:
        limit = request.args.get('limit', 20, type=int)
        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, old_value, new_value, user_email, created_at
                    FROM audit_log
                    WHERE database_id = %s AND record_id = %s AND field_name = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (db_id, record_id, field_name, limit))
                history = cursor.fetchall()
                for h in history:
                    if h.get('created_at'):
                        h['created_at'] = h['created_at'].isoformat()
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/database/<int:db_id>/history/<int:record_id>/<field_name>/revert/<int:audit_id>', methods=['POST'])
@login_required
@require_database_role("editor")
def revert_field(db_id, record_id, field_name, audit_id):
    """Revert a field to a previous value"""
    try:
        from services.workspace_service import get_database as _get_db
        db_info = _get_db(db_id)
        if not db_info:
            return jsonify({'success': False, 'error': 'DB not found'}), 404

        from psycopg2 import sql as psql
        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                # Get the audit entry
                cursor.execute('SELECT old_value FROM audit_log WHERE id = %s AND database_id = %s', (audit_id, db_id))
                audit = cursor.fetchone()
                if not audit:
                    return jsonify({'success': False, 'error': '이력을 찾을 수 없습니다'}), 404

                # Get current value for new audit entry
                cursor.execute(psql.SQL('SELECT {} FROM {} WHERE id = %s').format(
                    psql.Identifier(field_name), psql.Identifier(db_info['table_name'])
                ), (record_id,))
                current = cursor.fetchone()
                current_value = current[field_name] if current else None

                # Revert
                cursor.execute(psql.SQL('UPDATE {} SET {} = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s').format(
                    psql.Identifier(db_info['table_name']), psql.Identifier(field_name)
                ), (audit['old_value'], record_id))

                # Log the revert as a new audit entry
                _log_audit(cursor, db_id, record_id, field_name, current_value, audit['old_value'],
                          user_id=session.get('user_id'), user_email=session.get('user_email'))

                conn.commit()

        return jsonify({'success': True, 'message': '되돌리기 완료'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/database/<int:db_id>/trash', methods=['GET'])
@login_required
@require_database_role("viewer")
def get_trash(db_id):
    """Get deleted records (trash)"""
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, original_id, record_data, deleted_at, expires_at
                    FROM deleted_records
                    WHERE database_id = %s AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY deleted_at DESC
                """, (db_id,))
                items = cursor.fetchall()
                for item in items:
                    if item.get('deleted_at'):
                        item['deleted_at'] = item['deleted_at'].isoformat()
                    if item.get('expires_at'):
                        item['expires_at'] = item['expires_at'].isoformat()
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/database/<int:db_id>/trash/<int:trash_id>/restore', methods=['POST'])
@login_required
@require_database_role("editor")
def restore_from_trash(db_id, trash_id):
    """Restore a deleted record from trash"""
    try:
        from services.workspace_service import get_database as _get_db3
        from psycopg2 import sql as psql
        import json

        db_info = _get_db3(db_id)
        if not db_info:
            return jsonify({'success': False, 'error': 'DB not found'}), 404

        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT * FROM deleted_records WHERE id = %s AND database_id = %s', (trash_id, db_id))
                trash = cursor.fetchone()
                if not trash:
                    return jsonify({'success': False, 'error': '삭제된 레코드를 찾을 수 없습니다'}), 404

                data = trash['record_data']
                if isinstance(data, str):
                    data = json.loads(data)

                # Remove system columns
                for key in ['id', 'created_at', 'updated_at']:
                    data.pop(key, None)

                cols = list(data.keys())
                vals = list(data.values())
                cols_sql = psql.SQL(', ').join(psql.Identifier(c) for c in cols)
                placeholders = psql.SQL(', ').join([psql.Placeholder()] * len(vals))

                cursor.execute(psql.SQL('INSERT INTO {} ({}) VALUES ({}) RETURNING id').format(
                    psql.Identifier(db_info['table_name']), cols_sql, placeholders
                ), vals)
                new_id = cursor.fetchone()['id']

                # Remove from trash
                cursor.execute('DELETE FROM deleted_records WHERE id = %s', (trash_id,))
                conn.commit()

        return jsonify({'success': True, 'new_id': new_id, 'message': '레코드가 복원되었습니다'})
    except Exception as e:
        logger.error(f"Restore error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

'''

if 'get_field_history' not in content:
    # Add before the file upload section
    upload_marker = '# ===== File Upload ====='
    if upload_marker in content:
        content = content.replace(upload_marker, history_routes + '\n' + upload_marker, 1)
    else:
        content += history_routes
    print("2. Added history/revert/trash/restore API routes")

# === 3. Modify delete_property to move to trash instead of permanent delete ===
old_delete = """def delete_property_route(property_id):"""
if old_delete in content:
    # Find the delete function
    del_start = content.index(old_delete)
    del_section = content[del_start:]
    del_end = del_section.index('\ndef ', 10)

    old_func = del_section[:del_end]

    new_func = """def delete_property_route(property_id):
    \"\"\"Move property to trash (soft delete)\"\"\"
    try:
        database_id = request.args.get('db', 1, type=int)
        from services.workspace_service import get_database
        db_info = get_database(database_id)
        if not db_info:
            return jsonify({'success': False, 'error': 'DB not found'}), 404

        import json
        from psycopg2 import sql as psql

        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                # Fetch full record for trash
                cursor.execute(psql.SQL('SELECT * FROM {} WHERE id = %s').format(
                    psql.Identifier(db_info['table_name'])
                ), (property_id,))
                record = cursor.fetchone()
                if not record:
                    return jsonify({'success': False, 'error': '레코드를 찾을 수 없습니다'}), 404

                # Convert to serializable dict
                record_data = {}
                for k, v in record.items():
                    if hasattr(v, 'isoformat'):
                        record_data[k] = v.isoformat()
                    else:
                        record_data[k] = v

                # Move to trash
                from psycopg2.extras import Json
                cursor.execute(\"\"\"
                    INSERT INTO deleted_records (database_id, table_name, original_id, record_data, deleted_by)
                    VALUES (%s, %s, %s, %s, %s)
                \"\"\", (database_id, db_info['table_name'], property_id,
                       Json(record_data), session.get('user_id')))

                # Delete from main table
                cursor.execute(psql.SQL('DELETE FROM {} WHERE id = %s').format(
                    psql.Identifier(db_info['table_name'])
                ), (property_id,))

                conn.commit()

        return jsonify({'success': True, 'message': '레코드가 휴지통으로 이동되었습니다 (30일 후 영구 삭제)'})
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

"""
    content = content[:del_start] + new_func + content[del_start + del_end:]
    print("3. Modified delete to use trash")

with open(route_path, 'w') as f:
    f.write(content)

print("Done - Backend!")
