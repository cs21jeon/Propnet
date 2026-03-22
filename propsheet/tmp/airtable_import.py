#!/usr/bin/env python3
"""
Airtable → Propsheet 임포트 스크립트
Usage: python3 airtable_import.py
"""
import os, sys, json, re, time, requests
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from services.record_id_service import ensure_unique_record_id
import psycopg2, psycopg2.extras

# ============ CONFIG ============
BASE_ID = 'appQkFdB8TdPVNWdz'
TABLE_ID = 'tblT28nHoneqlbgBh'
WORKSPACE_SLUG = 'goldenrabbit'
DB_NAME = '공동주택 매물'
DB_SLUG = 'sales-multi-unit'
TABLE_NAME = 'sales_multi_unit'
API_KEY = os.getenv('AIRTABLE_API_KEY')
# ================================

def fetch_all_records():
    """Fetch all records from Airtable with pagination"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    all_records = []
    offset = None

    while True:
        params = {'pageSize': 100}
        if offset:
            params['offset'] = offset

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        records = data.get('records', [])
        all_records.extend(records)
        print(f'  Fetched {len(all_records)} records...')

        offset = data.get('offset')
        if not offset:
            break
        time.sleep(0.2)  # Rate limit

    return all_records

def analyze_fields(records):
    """Analyze field types from actual data"""
    field_info = {}

    for rec in records:
        for key, value in rec.get('fields', {}).items():
            if key not in field_info:
                field_info[key] = {'types': set(), 'sample': value}

            if isinstance(value, bool):
                field_info[key]['types'].add('bool')
            elif isinstance(value, int):
                field_info[key]['types'].add('number')
            elif isinstance(value, float):
                field_info[key]['types'].add('number')
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    field_info[key]['types'].add('attachment')
                else:
                    field_info[key]['types'].add('multi-select')
            elif isinstance(value, str):
                # Try to detect type
                if re.match(r'^\d{4}-\d{2}-\d{2}', value):
                    field_info[key]['types'].add('date')
                else:
                    field_info[key]['types'].add('text')

    return field_info

def get_pg_type(field_types):
    """Map detected types to PostgreSQL column type"""
    if 'number' in field_types:
        return 'NUMERIC'
    elif 'date' in field_types:
        return 'TIMESTAMP'
    elif 'attachment' in field_types:
        return 'TEXT'
    else:
        return 'TEXT'

def get_propsheet_type(field_types):
    """Map detected types to Propsheet field type"""
    if 'number' in field_types:
        return 'number'
    elif 'date' in field_types:
        return 'date'
    elif 'multi-select' in field_types:
        return 'multi-select'
    elif 'attachment' in field_types:
        return 'attachment'
    else:
        return 'text'

def convert_value(value):
    """Convert Airtable value for PostgreSQL insertion"""
    if value is None:
        return None
    if isinstance(value, list):
        if value and isinstance(value[0], dict):
            # Attachment - store as "filename (url)" format
            parts = []
            for att in value:
                fname = att.get('filename', '')
                url = att.get('url', '')
                parts.append(f'{fname} ({url})')
            return ', '.join(parts)
        else:
            # Multi-select - store as comma-separated
            return ', '.join(str(v) for v in value)
    if isinstance(value, bool):
        return 'O' if value else 'X'
    return value

def escape_col(name):
    """Escape column name for SQL"""
    return f'"{name}"'

def main():
    print(f'=== Airtable Import ===')
    print(f'Base: {BASE_ID}, Table: {TABLE_ID}')
    print(f'Target: {WORKSPACE_SLUG}/{DB_SLUG} ({TABLE_NAME})')

    # 1. Fetch all records
    print(f'\n1. Fetching records from Airtable...')
    records = fetch_all_records()
    print(f'   Total: {len(records)} records')

    if not records:
        print('No records found!')
        return

    # 2. Analyze fields
    print(f'\n2. Analyzing fields...')
    field_info = analyze_fields(records)
    print(f'   Found {len(field_info)} fields:')
    for name, info in sorted(field_info.items()):
        pg_type = get_pg_type(info['types'])
        ps_type = get_propsheet_type(info['types'])
        print(f'   {name:35s} -> {pg_type:10s} ({ps_type})')

    # 3. Create/update table and insert data
    print(f'\n3. Creating table and importing data...')

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Check if table already exists
            cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)", (TABLE_NAME,))
            table_exists = cur.fetchone()['exists']

            if table_exists:
                cur.execute(f'SELECT count(*) as cnt FROM "{TABLE_NAME}"')
                existing_count = cur.fetchone()['cnt']
                print(f'   Table {TABLE_NAME} exists with {existing_count} records')

                # Get existing columns
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (TABLE_NAME,))
                existing_cols = {r['column_name'] for r in cur.fetchall()}

                # Add missing columns
                for fname, finfo in field_info.items():
                    if fname not in existing_cols:
                        pg_type = get_pg_type(finfo['types'])
                        cur.execute(f'ALTER TABLE "{TABLE_NAME}" ADD COLUMN {escape_col(fname)} {pg_type}')
                        print(f'   Added column: {fname} ({pg_type})')

                # Clear existing data and re-import
                cur.execute(f'DELETE FROM "{TABLE_NAME}"')
                print(f'   Cleared {existing_count} existing records')
            else:
                # Create new table
                col_defs = [
                    'id SERIAL PRIMARY KEY',
                    'airtable_id VARCHAR(20) UNIQUE',
                    'record_id VARCHAR(64) UNIQUE',
                    'database_id INTEGER',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                ]
                for fname, finfo in field_info.items():
                    pg_type = get_pg_type(finfo['types'])
                    col_defs.append(f'{escape_col(fname)} {pg_type}')

                create_sql = f'CREATE TABLE "{TABLE_NAME}" ({", ".join(col_defs)})'
                cur.execute(create_sql)
                print(f'   Created table: {TABLE_NAME}')

            # 4. Get or create database entry
            cur.execute("SELECT id FROM workspaces WHERE slug = %s", (WORKSPACE_SLUG,))
            ws = cur.fetchone()
            if not ws:
                print(f'   ERROR: Workspace {WORKSPACE_SLUG} not found!')
                return
            ws_id = ws['id']

            cur.execute("SELECT id FROM databases WHERE slug = %s AND workspace_id = %s", (DB_SLUG, ws_id))
            db_row = cur.fetchone()
            if db_row:
                db_id = db_row['id']
                print(f'   Using existing database entry (id={db_id})')
            else:
                cur.execute("""
                    INSERT INTO databases (workspace_id, name, slug, table_name, icon, color)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, (ws_id, DB_NAME, DB_SLUG, TABLE_NAME, '🏢', '#667eea'))
                db_id = cur.fetchone()['id']
                print(f'   Created database entry (id={db_id})')

            # 5. Insert records
            print(f'\n4. Inserting {len(records)} records...')
            inserted = 0
            errors = 0

            for rec in records:
                try:
                    fields = rec.get('fields', {})
                    airtable_id = rec['id']
                    record_id = ensure_unique_record_id(TABLE_NAME)

                    # Build insert
                    col_names = ['airtable_id', 'record_id', 'database_id']
                    values = [airtable_id, record_id, db_id]

                    for fname, fvalue in fields.items():
                        col_names.append(fname)
                        values.append(convert_value(fvalue))

                    placeholders = ', '.join(['%s'] * len(values))
                    col_sql = ', '.join(escape_col(c) for c in col_names)

                    cur.execute(f'INSERT INTO "{TABLE_NAME}" ({col_sql}) VALUES ({placeholders})', values)
                    inserted += 1
                except Exception as e:
                    errors += 1
                    if errors <= 3:
                        print(f'   Error inserting {rec["id"]}: {e}')

            conn.commit()
            print(f'   Inserted: {inserted}, Errors: {errors}')

            # 6. Create field_definitions
            print(f'\n5. Creating field definitions...')
            for fname, finfo in field_info.items():
                ps_type = get_propsheet_type(finfo['types'])
                is_editable = ps_type not in ('formula',)

                # Collect select options for multi-select fields
                select_options = None
                if ps_type == 'multi-select':
                    options = set()
                    for rec in records:
                        val = rec.get('fields', {}).get(fname)
                        if isinstance(val, list):
                            options.update(str(v) for v in val)
                    select_options = sorted(options) if options else None

                cur.execute("SELECT id FROM field_definitions WHERE field_name = %s", (fname,))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO field_definitions (field_name, display_name, field_type, is_editable, select_options)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (fname, fname, ps_type, is_editable, select_options))

            conn.commit()

            # 7. Create default view
            cur.execute("SELECT id FROM views WHERE database_id = %s AND is_default = true", (db_id,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO views (database_id, name, slug, is_default, display_order)
                    VALUES (%s, %s, %s, true, 0)
                """, (db_id, '전체 보기', 'all'))
                print(f'   Created default view')

            conn.commit()

    print(f'\n=== Import Complete ===')
    print(f'Table: {TABLE_NAME}')
    print(f'Records: {inserted}')
    print(f'Fields: {len(field_info)}')
    print(f'URL: /propsheet/workspace/{WORKSPACE_SLUG}/database/{DB_SLUG}')

if __name__ == '__main__':
    main()
