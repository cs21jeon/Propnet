#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/services/workspace_service.py'
with open(path, 'r') as f:
    content = f.read()

# Fix clone_database_table: use RealDictCursor
old = """def clone_database_table(source_table: str, target_table: str, source_db_id: int, target_db_id: int):
    \"\"\"Clone an existing database table structure and data\"\"\"
    with get_db_connection() as conn:
        with get_db_cursor(conn) as cursor:"""

new = """def clone_database_table(source_table: str, target_table: str, source_db_id: int, target_db_id: int):
    \"\"\"Clone an existing database table structure and data\"\"\"
    from psycopg2.extras import RealDictCursor
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print("OK - Fixed clone_database_table cursor")
else:
    print("WARN: pattern not found")
