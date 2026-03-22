#!/usr/bin/env python3
"""Fix: use two-step approach for INSERT SELECT - avoid % escaping issue with params"""
path = '/home/webapp/goldenrabbit/backend/property-manager/services/workspace_service.py'
with open(path, 'r') as f:
    content = f.read()

# Replace the problematic INSERT SELECT with a safe approach:
# Step 1: INSERT SELECT without database_id replacement
# Step 2: UPDATE database_id after insert

old = """    # Escape % in column names for psycopg2
    def esc(name):
        return '"' + name.replace('%', '%%') + '"'

    cols_escaped = ', '.join(esc(c) for c in all_cols)
    select_parts = []
    for c in all_cols:
        if c == 'database_id':
            select_parts.append('%%s')
        else:
            select_parts.append(esc(c))
    select_escaped = ', '.join(select_parts)

    copy_sql = f'INSERT INTO "{target_table}" ({cols_escaped}) SELECT {select_escaped} FROM "{source_table}"'
    cursor.execute(copy_sql, (target_db_id,))
    row_count = cursor.rowcount"""

new = """    # Copy data: use psycopg2.sql module to avoid % escaping issues
    from psycopg2 import sql

    col_ids = [sql.Identifier(c) for c in all_cols]
    cols_sql = sql.SQL(', ').join(col_ids)

    # Build SELECT: replace database_id with literal value
    select_parts = []
    for c in all_cols:
        if c == 'database_id':
            select_parts.append(sql.Literal(target_db_id))
        else:
            select_parts.append(sql.Identifier(c))
    select_sql = sql.SQL(', ').join(select_parts)

    copy_query = sql.SQL('INSERT INTO {} ({}) SELECT {} FROM {}').format(
        sql.Identifier(target_table),
        cols_sql,
        select_sql,
        sql.Identifier(source_table)
    )
    cursor.execute(copy_query)
    row_count = cursor.rowcount"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print("OK - Fixed INSERT SELECT to use psycopg2.sql module")
else:
    print("WARN: pattern not found")
