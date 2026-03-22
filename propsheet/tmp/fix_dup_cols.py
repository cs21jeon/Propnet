#!/usr/bin/env python3
"""Fix: INSERT column count must match SELECT count — add record_id to INSERT columns"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    content = f.read()

old = """                    # Use psql.Literal for values to avoid % conflict with column names like 건폐율(%)
                    query = psql.SQL('INSERT INTO {} ({}, {}) SELECT {}, {}, {} FROM {} WHERE id = {} RETURNING id').format(
                        psql.Identifier(table_name),
                        psql.Identifier('database_id'), cols_sql,
                        psql.Literal(database_id), psql.Literal(record_id), cols_sql,
                        psql.Identifier(table_name),
                        psql.Literal(source_id)
                    )"""

new = """                    # Use psql.Literal for values to avoid % conflict with column names like 건폐율(%)
                    query = psql.SQL('INSERT INTO {} ({}, {}, {}) SELECT {}, {}, {} FROM {} WHERE id = {} RETURNING id').format(
                        psql.Identifier(table_name),
                        psql.Identifier('database_id'), psql.Identifier('record_id'), cols_sql,
                        psql.Literal(database_id), psql.Literal(record_id), cols_sql,
                        psql.Identifier(table_name),
                        psql.Literal(source_id)
                    )"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print("OK")
else:
    print("WARN: not found")
