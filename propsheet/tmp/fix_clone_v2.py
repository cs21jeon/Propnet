#!/usr/bin/env python3
"""Rewrite clone_database_table to use CREATE TABLE ... (LIKE ...) + INSERT ... SELECT"""
path = '/home/webapp/goldenrabbit/backend/property-manager/services/workspace_service.py'
with open(path, 'r') as f:
    content = f.read()

# Replace entire clone_database_table function
import re
old_fn = re.search(
    r'def clone_database_table\(.*?\n(?=\ndef |\nclass |\Z)',
    content, re.DOTALL
).group()

new_fn = '''def clone_database_table(source_table: str, target_table: str, source_db_id: int, target_db_id: int):
    """Clone an existing database table structure and data using CREATE TABLE LIKE"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Create table with identical structure (copies columns, types, defaults)
            cursor.execute(f"""
                CREATE TABLE "{target_table}" (LIKE "{source_table}" INCLUDING DEFAULTS)
            """)

            # Remove any inherited constraints that reference other tables
            cursor.execute(f"""
                SELECT conname FROM pg_constraint
                WHERE conrelid = '"{target_table}"'::regclass
                AND contype = 'f'
            """)
            for row in cursor.fetchall():
                cursor.execute(f'ALTER TABLE "{target_table}" DROP CONSTRAINT IF EXISTS "{row[0]}"')

            # Add serial primary key if not exists
            cursor.execute(f"""
                SELECT column_default FROM information_schema.columns
                WHERE table_name = '{target_table}' AND column_name = 'id'
            """)
            col_default = cursor.fetchone()
            if col_default and col_default[0] and 'nextval' in str(col_default[0]):
                # id column has a sequence from source, create new one
                cursor.execute(f"""
                    CREATE SEQUENCE IF NOT EXISTS "{target_table}_id_seq";
                    ALTER TABLE "{target_table}" ALTER COLUMN id SET DEFAULT nextval('"{target_table}_id_seq"');
                    ALTER SEQUENCE "{target_table}_id_seq" OWNED BY "{target_table}".id;
                """)

            # Get all column names except id
            cursor.execute(f"""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND column_name != 'id'
                ORDER BY ordinal_position
            """, (source_table,))
            all_cols = [r[0] for r in cursor.fetchall()]

            # Build column list with % escaping for psycopg2
            def esc(name):
                return '"' + name.replace('%', '%%') + '"'

            cols_escaped = ', '.join(esc(c) for c in all_cols)

            # Build SELECT with database_id replacement
            select_parts = []
            for c in all_cols:
                if c == 'database_id':
                    select_parts.append('%%s')
                else:
                    select_parts.append(esc(c))
            select_escaped = ', '.join(select_parts)

            copy_sql = f"""
                INSERT INTO "{target_table}" ({cols_escaped})
                SELECT {select_escaped}
                FROM "{source_table}"
            """
            cursor.execute(copy_sql, (target_db_id,))

            row_count = cursor.rowcount
            conn.commit()
            logger.info(f"Cloned table '{source_table}' to '{target_table}' with {row_count} records")
            return row_count


'''

content = content[:content.index('def clone_database_table(')] + new_fn + content[content.index('def clone_database_table(') + len(old_fn):]

with open(path, 'w') as f:
    f.write(content)
print("OK - Rewrote clone_database_table with CREATE TABLE LIKE")
