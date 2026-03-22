#!/usr/bin/env python3
"""Fix record duplication: use psql.Literal for params instead of %s in psql.SQL"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    content = f.read()

old = """                if source_id:
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
                    ), (database_id, record_id, source_id))"""

new = """                if source_id:
                    # Duplicate: copy all columns from source record
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s AND column_name NOT IN ('id', 'created_at', 'updated_at')", (table_name,))
                    cols = [r['column_name'] for r in cursor.fetchall()]
                    from psycopg2 import sql as psql
                    col_ids = [psql.Identifier(c) for c in cols if c not in ('record_id', 'database_id')]
                    cols_sql = psql.SQL(', ').join(col_ids)
                    # Use psql.Literal for values to avoid % conflict with column names like 건폐율(%)
                    query = psql.SQL('INSERT INTO {} ({}, {}) SELECT {}, {}, {} FROM {} WHERE id = {} RETURNING id').format(
                        psql.Identifier(table_name),
                        psql.Identifier('database_id'), cols_sql,
                        psql.Literal(database_id), psql.Literal(record_id), cols_sql,
                        psql.Identifier(table_name),
                        psql.Literal(source_id)
                    )
                    cursor.execute(query)"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print("OK - Fixed record duplication % escaping")
else:
    print("WARN: pattern not found")
