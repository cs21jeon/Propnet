#!/usr/bin/env python3
"""
Migrate field_definitions from global to per-database:
1. Add database_id column
2. For each DB, copy matching field_definitions (by column existence)
3. Update schema_service to filter by database_id
4. Update routes to include database_id in save
5. Update clone to copy field_definitions
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
import psycopg2.extras

# === STEP 1: DB Migration ===
print('=== Step 1: DB Migration ===', flush=True)
with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Add database_id column if not exists
        cur.execute("ALTER TABLE field_definitions ADD COLUMN IF NOT EXISTS database_id INTEGER REFERENCES databases(id) ON DELETE CASCADE")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_field_defs_db ON field_definitions(database_id)")
        conn.commit()
        print('  Added database_id column + index', flush=True)

        # Get all databases with their columns
        cur.execute("SELECT id, name, table_name FROM databases ORDER BY id")
        databases = cur.fetchall()

        # Get current global field definitions
        cur.execute("SELECT * FROM field_definitions WHERE database_id IS NULL")
        global_defs = cur.fetchall()
        print(f'  {len(global_defs)} global field definitions to distribute', flush=True)

        # For each database, check which columns exist and create per-DB definitions
        for db in databases:
            db_id = db['id']
            table_name = db['table_name']

            # Check if already migrated
            cur.execute("SELECT count(*) as cnt FROM field_definitions WHERE database_id = %s", (db_id,))
            if cur.fetchone()['cnt'] > 0:
                print(f'  DB {db_id} ({db["name"]}): already has per-DB defs, skipping', flush=True)
                continue

            # Get columns in this table
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
            """, (table_name,))
            table_cols = {r['column_name'] for r in cur.fetchall()}

            # Copy matching global defs for this DB
            copied = 0
            for fd in global_defs:
                if fd['field_name'] in table_cols:
                    cur.execute("""
                        INSERT INTO field_definitions
                        (database_id, field_name, display_name, field_type, formula, select_options,
                         is_required, display_order, is_visible, is_editable, column_width,
                         system_value_key, select_colors, number_format, date_format, api_key)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        db_id, fd['field_name'], fd.get('display_name'), fd['field_type'],
                        fd.get('formula'), fd.get('select_options'), fd.get('is_required'),
                        fd.get('display_order'), fd.get('is_visible'), fd.get('is_editable'),
                        fd.get('column_width'), fd.get('system_value_key'),
                        psycopg2.extras.Json(fd['select_colors']) if fd.get('select_colors') else None,
                        psycopg2.extras.Json(fd['number_format']) if fd.get('number_format') else None,
                        psycopg2.extras.Json(fd['date_format']) if fd.get('date_format') else None,
                        fd.get('api_key')
                    ))
                    copied += 1
            print(f'  DB {db_id} ({db["name"]}): {copied} field defs copied (of {len(table_cols)} columns)', flush=True)

        conn.commit()

        # Count new per-DB defs
        cur.execute("SELECT count(*) as cnt FROM field_definitions WHERE database_id IS NOT NULL")
        print(f'  Total per-DB definitions: {cur.fetchone()["cnt"]}', flush=True)

print('\n=== Step 2: Update schema_service.py ===', flush=True)

# === STEP 2: schema_service.py - filter by database_id ===
schema_path = 'services/schema_service.py'
with open(schema_path, 'r') as f:
    content = f.read()

# The get_table_columns function needs database_id parameter
# Find the function signature
old_sig = "def get_table_columns(table_name: str) -> list:"
new_sig = "def get_table_columns(table_name: str, database_id: int = None) -> list:"
if 'database_id: int' not in content:
    content = content.replace(old_sig, new_sig, 1)
    print('  Updated function signature', flush=True)

# Update the field_definitions query to filter by database_id
old_query = """            cursor.execute(\"\"\"
                SELECT field_name, field_type, formula, is_editable, select_options, system_value_key, select_colors, number_format, date_format, api_key
                FROM field_definitions
            \"\"\")"""

new_query = """            if database_id:
                cursor.execute(\"\"\"
                    SELECT field_name, field_type, formula, is_editable, select_options, system_value_key, select_colors, number_format, date_format, api_key
                    FROM field_definitions
                    WHERE database_id = %s
                \"\"\", (database_id,))
            else:
                cursor.execute(\"\"\"
                    SELECT field_name, field_type, formula, is_editable, select_options, system_value_key, select_colors, number_format, date_format, api_key
                    FROM field_definitions
                    WHERE database_id IS NULL
                \"\"\")"""

if 'WHERE database_id' not in content:
    content = content.replace(old_query, new_query, 1)
    print('  Updated field_definitions query with database_id filter', flush=True)

with open(schema_path, 'w') as f:
    f.write(content)

print('\n=== Step 3: Update routes ===', flush=True)

# === STEP 3: routes/database.py - pass database_id to get_table_columns + field save ===
route_path = 'routes/database.py'
with open(route_path, 'r') as f:
    content = f.read()

# 3a. get_database_columns endpoint: pass database_id
old_cols = "columns = get_table_columns(db_info['table_name'])"
new_cols = "columns = get_table_columns(db_info['table_name'], database_id=database_id)"
count = content.count(old_cols)
if count > 0:
    content = content.replace(old_cols, new_cols)
    print(f'  Updated get_table_columns calls ({count})', flush=True)

# 3b. field-definition save: include database_id
old_fd_save = "field_name = data.get('field_name')\n        display_name = data.get('display_name')\n        field_type = data.get('field_type')"
new_fd_save = "field_name = data.get('field_name')\n        display_name = data.get('display_name')\n        field_type = data.get('field_type')\n        fd_database_id = data.get('database_id')"
if 'fd_database_id' not in content:
    content = content.replace(old_fd_save, new_fd_save, 1)
    print('  Added fd_database_id extraction', flush=True)

# Update the SELECT to check by database_id + field_name
old_check = "cursor.execute(\n                    'SELECT id FROM field_definitions WHERE field_name = %s',\n                    (field_name,)\n                )"
new_check = """cursor.execute(
                    'SELECT id FROM field_definitions WHERE field_name = %s AND (database_id = %s OR (database_id IS NULL AND %s IS NULL))',
                    (field_name, fd_database_id, fd_database_id)
                )"""
if 'database_id = %s OR' not in content:
    content = content.replace(old_check, new_check, 1)
    print('  Updated field_definitions lookup', flush=True)

# Update the UPDATE to scope by database_id
old_where = "WHERE field_name = %s\n                    ''', (display_name, field_type,"
new_where = "WHERE field_name = %s AND (database_id = %s OR (database_id IS NULL AND %s IS NULL))\n                    ''', (display_name, field_type,"
if 'database_id = %s OR (database_id IS NULL' not in content:
    content = content.replace(old_where, new_where, 1)
    # Add database_id params at the end of the UPDATE tuple
    old_end_update = "system_value_key, field_name))"
    new_end_update = "system_value_key, field_name, fd_database_id, fd_database_id))"
    # Only replace the first occurrence (UPDATE, not INSERT)
    idx = content.find(new_end_update)
    if idx < 0:
        content = content.replace(old_end_update, new_end_update, 1)
    print('  Updated UPDATE WHERE clause', flush=True)

# Update INSERT to include database_id
old_insert_cols = "(field_name, display_name, field_type, column_width, formula, select_options, select_colors, number_format,"
new_insert_cols = "(database_id, field_name, display_name, field_type, column_width, formula, select_options, select_colors, number_format,"
if 'database_id, field_name, display_name' not in content:
    content = content.replace(old_insert_cols, new_insert_cols, 1)
    # Add placeholder
    old_insert_vals = "''', (field_name, field_name, field_type,"
    new_insert_vals = "''', (fd_database_id, field_name, field_name, field_type,"
    content = content.replace(old_insert_vals, new_insert_vals, 1)
    # Add VALUES placeholder count
    content = content.replace(
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    print('  Updated INSERT with database_id', flush=True)

# 3c. delete_column: scope by database_id
old_delete_fd = """        system_columns = ['id', 'database_id', 'created_at', 'updated_at']
        if column_name in system_columns:
            return jsonify({'success': False, 'error': '시스템 필드는 삭제할 수 없습니다'}), 400"""
# Check if there's a field_definitions cleanup in delete
if 'DELETE FROM field_definitions' not in content.split('delete_column')[1].split('def ')[0] if 'delete_column' in content else '':
    pass  # Field definitions cleanup is handled by the column itself

with open(route_path, 'w') as f:
    f.write(content)

print('\n=== Step 4: Update JS ===', flush=True)

# === STEP 4: JS - send database_id with field save ===
js_path = 'static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

# Add database_id to field save payload
old_payload = "field_name: this.editingField.key,\n                        display_name: this.editingField.label,"
new_payload = "field_name: this.editingField.key,\n                        display_name: this.editingField.label,\n                        database_id: this.databaseId,"
if 'database_id: this.databaseId' not in js.split('saveFieldSettings')[1].split('}')[0] if 'saveFieldSettings' in js else '':
    js = js.replace(old_payload, new_payload, 1)
    print('  Added database_id to save payload', flush=True)

with open(js_path, 'w') as f:
    f.write(js)

print('\n=== Step 5: Update clone to copy field_definitions ===', flush=True)

# === STEP 5: Update clone_database_full to copy field_definitions ===
ws_path = 'services/workspace_service.py'
with open(ws_path, 'r') as f:
    content = f.read()

# Add field_definitions copy to clone_database_views_impl (or as separate step)
old_views_end = "    logger.info(f\"Cloned {cloned} views from db {source_db_id} -> {target_db_id}\")\n    return cloned"
new_views_end = """    logger.info(f"Cloned {cloned} views from db {source_db_id} -> {target_db_id}")
    return cloned


def clone_field_definitions_impl(cursor, source_db_id, target_db_id):
    \"\"\"Clone field_definitions for a database\"\"\"
    from psycopg2.extras import Json
    cursor.execute(\"\"\"
        SELECT field_name, display_name, field_type, formula, select_options,
               is_required, display_order, is_visible, is_editable, column_width,
               system_value_key, select_colors, number_format, date_format, api_key
        FROM field_definitions
        WHERE database_id = %s
    \"\"\", (source_db_id,))
    defs = cursor.fetchall()

    for fd in defs:
        if isinstance(fd, tuple):
            vals = list(fd)
        else:
            vals = [fd['field_name'], fd.get('display_name'), fd['field_type'],
                    fd.get('formula'), fd.get('select_options'), fd.get('is_required'),
                    fd.get('display_order'), fd.get('is_visible'), fd.get('is_editable'),
                    fd.get('column_width'), fd.get('system_value_key'),
                    fd.get('select_colors'), fd.get('number_format'),
                    fd.get('date_format'), fd.get('api_key')]

        # Handle JSONB fields
        sc = vals[11]  # select_colors
        nf = vals[12]  # number_format
        df = vals[13]  # date_format

        cursor.execute(\"\"\"
            INSERT INTO field_definitions
            (database_id, field_name, display_name, field_type, formula, select_options,
             is_required, display_order, is_visible, is_editable, column_width,
             system_value_key, select_colors, number_format, date_format, api_key)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        \"\"\", (target_db_id, vals[0], vals[1], vals[2], vals[3], vals[4],
               vals[5], vals[6], vals[7], vals[8], vals[9], vals[10],
               Json(sc) if sc else None,
               Json(nf) if nf else None,
               Json(df) if df else None,
               vals[14]))

    logger.info(f"Cloned {len(defs)} field definitions from db {source_db_id} -> {target_db_id}")
    return len(defs)"""

if 'clone_field_definitions_impl' not in content:
    content = content.replace(old_views_end, new_views_end, 1)
    print('  Added clone_field_definitions_impl', flush=True)

# Add call in clone_database_full
old_full = "                clone_database_views_impl(cursor, source_db_id, target_db_id)"
new_full = "                clone_database_views_impl(cursor, source_db_id, target_db_id)\n                clone_field_definitions_impl(cursor, source_db_id, target_db_id)"
if 'clone_field_definitions_impl(cursor' not in content:
    content = content.replace(old_full, new_full, 1)
    print('  Added clone_field_definitions to clone_database_full', flush=True)

with open(ws_path, 'w') as f:
    f.write(content)

# === STEP 6: Update list_properties to pass database_id ===
print('\n=== Step 6: Update list_properties ===', flush=True)

db_svc_path = 'services/database_service.py'
with open(db_svc_path, 'r') as f:
    content = f.read()

# Add database_id param to list_properties
old_list_sig = "def list_properties(\n    page: int = 1,"
new_list_sig = "def list_properties(\n    database_id: int = None,\n    page: int = 1,"
if 'database_id: int = None' not in content:
    content = content.replace(old_list_sig, new_list_sig, 1)
    print('  Added database_id to list_properties', flush=True)

# Update formula query to filter by database_id
old_formula_q = """            cursor.execute(\"\"\"
                SELECT field_name, formula
                FROM field_definitions
                WHERE formula IS NOT NULL AND formula != ''
            \"\"\")"""

new_formula_q = """            if database_id:
                cursor.execute(\"\"\"
                    SELECT field_name, formula
                    FROM field_definitions
                    WHERE formula IS NOT NULL AND formula != '' AND database_id = %s
                \"\"\", (database_id,))
            else:
                cursor.execute(\"\"\"
                    SELECT field_name, formula
                    FROM field_definitions
                    WHERE formula IS NOT NULL AND formula != '' AND database_id IS NULL
                \"\"\")"""

if "AND database_id = %s" not in content.split('formula')[1].split('system_value_key')[0] if 'formula' in content else '':
    content = content.replace(old_formula_q, new_formula_q, 1)
    print('  Updated formula query', flush=True)

# Similarly update system_generated fields query
old_sys_q = """            cursor.execute(\"\"\"
                SELECT field_name, system_value_key
                FROM field_definitions
                WHERE field_type = 'system_generated_value'
                AND system_value_key IS NOT NULL AND system_value_key != ''
            \"\"\")"""

new_sys_q = """            if database_id:
                cursor.execute(\"\"\"
                    SELECT field_name, system_value_key
                    FROM field_definitions
                    WHERE field_type = 'system_generated_value'
                    AND system_value_key IS NOT NULL AND system_value_key != ''
                    AND database_id = %s
                \"\"\", (database_id,))
            else:
                cursor.execute(\"\"\"
                    SELECT field_name, system_value_key
                    FROM field_definitions
                    WHERE field_type = 'system_generated_value'
                    AND system_value_key IS NOT NULL AND system_value_key != ''
                    AND database_id IS NULL
                \"\"\")"""

if "system_value_key IS NOT NULL AND system_value_key != '' AND database_id" not in content:
    content = content.replace(old_sys_q, new_sys_q, 1)
    print('  Updated system fields query', flush=True)

with open(db_svc_path, 'w') as f:
    f.write(content)

# === STEP 7: Update route caller to pass database_id ===
print('\n=== Step 7: Update route callers ===', flush=True)
with open(route_path, 'r') as f:
    content = f.read()

# list_all_properties: pass database_id
old_call = "result = list_properties(\n            page=page,"
new_call = "result = list_properties(\n            database_id=database_id,\n            page=page,"
if 'database_id=database_id,\n            page=page' not in content:
    content = content.replace(old_call, new_call, 1)
    print('  Updated list_properties call', flush=True)

with open(route_path, 'w') as f:
    f.write(content)

print('\nDone!', flush=True)
