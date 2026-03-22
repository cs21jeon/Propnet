#!/usr/bin/env python3
"""Add source_id support to create_new_property for record duplication"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    content = f.read()

# Add source_id handling after record_id generation
old = """        # Generate unique record_id
        record_id = ensure_unique_record_id(table_name)

        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                # Insert empty record with record_id and 레코드생성일자
                cursor.execute(f\'\'\'
                    INSERT INTO "{table_name}" (database_id, record_id, "레코드생성일자")
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    RETURNING id, record_id, "레코드생성일자"
                \'\'\', (database_id, record_id))"""

new = """        # Generate unique record_id
        record_id = ensure_unique_record_id(table_name)
        source_id = data.get('source_id')

        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                if source_id:
                    # Duplicate: copy all columns from source record
                    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s AND column_name NOT IN ('id', 'created_at', 'updated_at')", (table_name,))
                    cols = [r['column_name'] for r in cursor.fetchall()]
                    from psycopg2 import sql as psql
                    col_ids = [psql.Identifier(c) for c in cols if c not in ('record_id', 'database_id')]
                    cols_sql = psql.SQL(', ').join(col_ids)
                    cursor.execute(psql.SQL(
                        'INSERT INTO {} (database_id, record_id, {}) SELECT %s, %s, {} FROM {} WHERE id = %s RETURNING id'
                    ).format(
                        psql.Identifier(table_name), cols_sql, cols_sql, psql.Identifier(table_name)
                    ), (database_id, record_id, source_id))
                else:
                    # Empty new record
                    try:
                        cursor.execute(f\'\'\'
                            INSERT INTO "{table_name}" (database_id, record_id, "레코드생성일자")
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            RETURNING id
                        \'\'\', (database_id, record_id))
                    except Exception:
                        # Table might not have 레코드생성일자
                        cursor.execute(f\'\'\'
                            INSERT INTO "{table_name}" (database_id, record_id)
                            VALUES (%s, %s)
                            RETURNING id
                        \'\'\', (database_id, record_id))"""

if 'source_id' not in content.split('create_new_property')[1].split('def ')[0]:
    content = content.replace(old, new, 1)

    # Fix the result handling
    old_result = """                result = cursor.fetchone()
                new_id = result[0]
                new_record_id = result[1]
                created_time = result[2]
                conn.commit()

                return jsonify({
                    'success': True,
                    'id': new_id,
                    'record_id': new_record_id,
                    'created_at': created_time.isoformat() if created_time else None,
                    'message': '새 레코드가 생성되었습니다'
                })"""

    new_result = """                result = cursor.fetchone()
                new_id = result['id'] if isinstance(result, dict) else result[0]
                conn.commit()

                msg = '레코드가 복제되었습니다' if source_id else '새 레코드가 생성되었습니다'
                return jsonify({
                    'success': True,
                    'id': new_id,
                    'record_id': record_id,
                    'message': msg
                })"""

    content = content.replace(old_result, new_result, 1)

    with open(path, 'w') as f:
        f.write(content)
    print("OK - Added source_id duplication support")
else:
    print("Already has source_id")
