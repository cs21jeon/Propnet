#!/usr/bin/env python3
"""
1. Add unique_id to workspaces and databases tables
2. Fix clone to generate new record_ids
3. Regenerate record_ids for existing cloned data
"""
import sys, os, secrets, string
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
import psycopg2.extras

def gen_uid(prefix, length=17):
    """Generate Airtable-style ID: prefix + alphanumeric"""
    chars = string.ascii_letters + string.digits
    return prefix + ''.join(secrets.choice(chars) for _ in range(length))

print('=== Step 1: Add unique_id columns ===', flush=True)
with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Workspaces
        cur.execute("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS unique_id VARCHAR(20) UNIQUE")
        # Databases
        cur.execute("ALTER TABLE databases ADD COLUMN IF NOT EXISTS unique_id VARCHAR(20) UNIQUE")
        conn.commit()
        print('  Added unique_id columns', flush=True)

        # Populate existing workspaces
        cur.execute("SELECT id FROM workspaces WHERE unique_id IS NULL")
        ws_rows = cur.fetchall()
        for row in ws_rows:
            uid = gen_uid('wsp')
            cur.execute("UPDATE workspaces SET unique_id = %s WHERE id = %s", (uid, row[0]))
        conn.commit()
        print(f'  Assigned {len(ws_rows)} workspace unique_ids', flush=True)

        # Populate existing databases
        cur.execute("SELECT id FROM databases WHERE unique_id IS NULL")
        db_rows = cur.fetchall()
        for row in db_rows:
            uid = gen_uid('db')
            cur.execute("UPDATE databases SET unique_id = %s WHERE id = %s", (uid, row[0]))
        conn.commit()
        print(f'  Assigned {len(db_rows)} database unique_ids', flush=True)

print('\n=== Step 2: Regenerate record_ids for cloned data ===', flush=True)
with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Find cloned databases (workspace_id != 1, i.e. not the original)
        cur.execute("""
            SELECT d.id, d.name, d.table_name, d.workspace_id
            FROM databases d
            WHERE d.workspace_id != 1
        """)
        cloned_dbs = cur.fetchall()
        print(f'  Found {len(cloned_dbs)} cloned databases', flush=True)

        for db in cloned_dbs:
            table = db['table_name']
            try:
                # Check if table has record_id column
                cur.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = %s AND column_name = 'record_id'
                """, (table,))
                if not cur.fetchone():
                    continue

                # Get all records
                from psycopg2 import sql as psql
                cur.execute(psql.SQL('SELECT id FROM {}').format(psql.Identifier(table)))
                records = cur.fetchall()
                updated = 0
                for rec in records:
                    new_rid = gen_uid('rec', 15)
                    cur.execute(psql.SQL('UPDATE {} SET record_id = %s WHERE id = %s').format(
                        psql.Identifier(table)
                    ), (new_rid, rec['id']))
                    updated += 1
                print(f'  {db["name"]} ({table}): {updated} record_ids regenerated', flush=True)
            except Exception as e:
                print(f'  {db["name"]}: error - {e}', flush=True)
                conn.rollback()

        conn.commit()

print('\n=== Step 3: Fix clone to generate new record_ids ===', flush=True)
# Update workspace_service.py clone_database_table_impl
ws_path = 'services/workspace_service.py'
with open(ws_path, 'r') as f:
    content = f.read()

# The clone copies record_id from source. We need to generate new ones after copy.
# Add record_id regeneration after the INSERT SELECT in clone_database_table_impl
old_clone_log = '    logger.info(f"Cloned table \'{source_table}\' -> \'{target_table}\' ({row_count} rows)")'
new_clone_log = """    # Regenerate record_ids for cloned records
    import secrets as _s, string as _str
    cursor.execute(psql.SQL('SELECT id FROM {}').format(psql.Identifier(target_table)))
    for row in cursor.fetchall():
        rid = row['id'] if isinstance(row, dict) else row[0]
        new_rid = 'rec' + ''.join(_s.choice(_str.ascii_letters + _str.digits) for _ in range(15))
        cursor.execute(psql.SQL('UPDATE {} SET record_id = %s WHERE id = %s').format(
            psql.Identifier(target_table)
        ), (new_rid, rid))

    logger.info(f"Cloned table '{source_table}' -> '{target_table}' ({row_count} rows, record_ids regenerated)")"""

if 'record_ids regenerated' not in content:
    content = content.replace(old_clone_log, new_clone_log, 1)
    print('  Updated clone to regenerate record_ids', flush=True)

# Also add unique_id generation for workspace/database creation
# For create_workspace: add unique_id
old_ws_insert = "INSERT INTO workspaces (name, slug, description, icon)"
new_ws_insert = "INSERT INTO workspaces (name, slug, description, icon, unique_id)"
old_ws_values = "VALUES (%s, %s, %s, %s)"
new_ws_values = "VALUES (%s, %s, %s, %s, %s)"
old_ws_params = "(name, slug, description, icon))"
new_ws_params = "(name, slug, description, icon, 'wsp' + ''.join(__import__('secrets').choice(__import__('string').ascii_letters + __import__('string').digits) for _ in range(17))))"

# Simpler approach: add unique_id generation in the function
if 'unique_id' not in content.split('def create_workspace')[1].split('def ')[0]:
    # Find the INSERT INTO workspaces
    old_insert_ws = """            cursor.execute('''
                INSERT INTO workspaces (name, slug, description, icon)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            ''', (name, slug, description, icon))"""
    new_insert_ws = """            import secrets as _ws_s, string as _ws_str
            ws_uid = 'wsp' + ''.join(_ws_s.choice(_ws_str.ascii_letters + _ws_str.digits) for _ in range(17))
            cursor.execute('''
                INSERT INTO workspaces (name, slug, description, icon, unique_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (name, slug, description, icon, ws_uid))"""
    if old_insert_ws in content:
        content = content.replace(old_insert_ws, new_insert_ws, 1)
        print('  Updated create_workspace with unique_id', flush=True)

# For create_database: add unique_id
old_insert_db = """                INSERT INTO databases (workspace_id, name, slug, table_name, description, icon, color)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id"""
new_insert_db = """                INSERT INTO databases (workspace_id, name, slug, table_name, description, icon, color, unique_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id"""
if old_insert_db in content:
    content = content.replace(old_insert_db, new_insert_db, 1)
    # Also update params
    old_db_params = "''', (workspace_id, name, slug, table_name, description, icon, color))"
    new_db_params = """            db_uid = 'db' + ''.join(__import__('secrets').choice(__import__('string').ascii_letters + __import__('string').digits) for _ in range(17))
            ''', (workspace_id, name, slug, table_name, description, icon, color, db_uid))"""
    # Simpler: add the uid generation before the execute
    content = content.replace(old_db_params, new_db_params, 1)
    print('  Updated create_database with unique_id', flush=True)

with open(ws_path, 'w') as f:
    f.write(content)

print('\n=== Step 4: Verify ===', flush=True)
with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, name, unique_id FROM workspaces ORDER BY id")
        for r in cur.fetchall():
            print(f'  WS: id={r["id"]}, name={r["name"]}, uid={r["unique_id"]}', flush=True)
        cur.execute("SELECT id, name, unique_id FROM databases ORDER BY id LIMIT 5")
        for r in cur.fetchall():
            print(f'  DB: id={r["id"]}, name={r["name"]}, uid={r["unique_id"]}', flush=True)

print('\nDone!', flush=True)
