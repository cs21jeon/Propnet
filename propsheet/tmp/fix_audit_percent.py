#!/usr/bin/env python3
"""Fix % in column names for audit log SELECT and UPDATE in update_single_field"""
import re

path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    py = f.read()

# Fix 1: Audit log SELECT — use as_string + %% escape
old = """                # Fetch old value for audit log
                from psycopg2 import sql as psql_audit
                cursor.execute(psql_audit.SQL('SELECT {} FROM {} WHERE id = %s').format(
                    psql_audit.Identifier(field), psql_audit.Identifier(db_info['table_name'])
                ), (property_id,))"""

new = """                # Fetch old value for audit log
                from psycopg2 import sql as psql_audit
                audit_query = psql_audit.SQL('SELECT {} FROM {} WHERE id = %s').format(
                    psql_audit.Identifier(field), psql_audit.Identifier(db_info['table_name'])
                )
                # Escape % in column names (e.g. 건폐율(%)) to prevent psycopg2 param confusion
                import re as _re
                audit_query_str = audit_query.as_string(cursor)
                audit_query_str = _re.sub(r'"([^"]*?)%([^s])', r'"\\1%%\\2', audit_query_str)
                cursor.execute(audit_query_str, (property_id,))"""

if old in py:
    py = py.replace(old, new, 1)
    print("1. Fixed audit SELECT % escape")
else:
    print("1. WARN: audit SELECT pattern not found")

# Fix 2: UPDATE query — escape_column_name produces "건폐율(%)" which has % issue
old_update = """                escaped_field = escape_column_name(field)
                query = f'UPDATE "{db_info["table_name"]}" SET {escaped_field} = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING updated_at'
                cursor.execute(query, (value, property_id))"""

new_update = """                update_q = psql_audit.SQL('UPDATE {} SET {} = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING updated_at').format(
                    psql_audit.Identifier(db_info['table_name']),
                    psql_audit.Identifier(field)
                )
                update_q_str = update_q.as_string(cursor)
                update_q_str = _re.sub(r'"([^"]*?)%([^s])', r'"\\1%%\\2', update_q_str)
                cursor.execute(update_q_str, (value, property_id))"""

if old_update in py:
    py = py.replace(old_update, new_update, 1)
    print("2. Fixed UPDATE % escape")
else:
    print("2. WARN: UPDATE pattern not found")

with open(path, 'w') as f:
    f.write(py)
print("Done!")
