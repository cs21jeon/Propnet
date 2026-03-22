#!/usr/bin/env python3
"""Fix: when field type changes, also ALTER TABLE column type"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    content = f.read()

# Add ALTER TABLE after field_definitions UPDATE when type changes
old_commit = """                conn.commit()

        return jsonify({'success': True, 'message': '필드 정의가 저장되었습니다'})"""

new_commit = """                # If type changed, also alter the actual DB column type
                if fd_database_id:
                    from services.workspace_service import get_database as _get_db_fd
                    db_info_fd = _get_db_fd(fd_database_id)
                    if db_info_fd:
                        pg_type_map = {
                            'text': 'TEXT', 'long-text': 'TEXT', 'url': 'TEXT',
                            'number': 'NUMERIC', 'date': 'TIMESTAMP',
                            'single-select': 'TEXT', 'multi-select': 'TEXT',
                            'formula': None, 'attachment': 'TEXT',
                            'system_generated_value': None, 'system': None
                        }
                        new_pg_type = pg_type_map.get(field_type)
                        if new_pg_type:
                            try:
                                from psycopg2 import sql as psql_fd
                                cursor.execute(psql_fd.SQL(
                                    'ALTER TABLE {} ALTER COLUMN {} TYPE {} USING {}::{}'
                                ).format(
                                    psql_fd.Identifier(db_info_fd['table_name']),
                                    psql_fd.Identifier(field_name),
                                    psql_fd.SQL(new_pg_type),
                                    psql_fd.Identifier(field_name),
                                    psql_fd.SQL(new_pg_type)
                                ))
                            except Exception as alter_err:
                                logger.warning(f"Column type alter skipped: {alter_err}")

                conn.commit()

        return jsonify({'success': True, 'message': '필드 정의가 저장되었습니다'})"""

if 'If type changed, also alter' not in content:
    content = content.replace(old_commit, new_commit, 1)
    with open(path, 'w') as f:
        f.write(content)
    print("OK - Added ALTER TABLE on type change")
else:
    print("Already has")
