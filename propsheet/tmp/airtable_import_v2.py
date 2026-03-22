#!/usr/bin/env python3
"""Airtable → Propsheet import (v2 - fast)"""
import os, sys, json, re, time, secrets, string, requests, psycopg2, psycopg2.extras

sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')

# Config
BASE_ID = 'appQkFdB8TdPVNWdz'
TABLE_ID = 'tblT28nHoneqlbgBh'
WORKSPACE_SLUG = 'goldenrabbit'
DB_NAME = '공동주택 매물'
DB_SLUG = 'sales-multi-unit'
TABLE_NAME = 'sales_multi_unit'
API_KEY = os.getenv('AIRTABLE_API_KEY')

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'goldenrabbit_db'),
    'user': os.getenv('DB_USER', 'goldenrabbit_user'),
    'password': os.getenv('DB_PASSWORD', '')
}

def gen_record_id():
    chars = string.ascii_letters + string.digits
    return 'rec' + ''.join(secrets.choice(chars) for _ in range(15))

def fetch_all():
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    records = []
    offset = None
    while True:
        params = {'pageSize': 100}
        if offset:
            params['offset'] = offset
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        records.extend(data.get('records', []))
        print(f'  Fetched {len(records)}...', flush=True)
        offset = data.get('offset')
        if not offset:
            break
        time.sleep(0.2)
    return records

def convert_value(v):
    if v is None: return None
    if isinstance(v, list):
        if v and isinstance(v[0], dict):
            return ', '.join(f'{a.get("filename","")} ({a.get("url","")})' for a in v)
        return ', '.join(str(x) for x in v)
    if isinstance(v, bool): return 'O' if v else 'X'
    return v

def get_pg_type(records, key):
    for rec in records:
        v = rec.get('fields', {}).get(key)
        if v is not None:
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return 'NUMERIC'
            if isinstance(v, str) and re.match(r'^\d{4}-\d{2}-\d{2}', v):
                return 'TIMESTAMP'
            break
    return 'TEXT'

def main():
    print('=== Airtable Import v2 ===', flush=True)

    # 1. Fetch
    print('1. Fetching...', flush=True)
    records = fetch_all()
    print(f'   {len(records)} records', flush=True)
    if not records: return

    # 2. Analyze fields
    all_fields = {}
    for rec in records:
        for k in rec.get('fields', {}):
            if k not in all_fields:
                all_fields[k] = get_pg_type(records, k)
    print(f'2. {len(all_fields)} fields detected', flush=True)

    # 3. DB operations
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Check existing columns
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (TABLE_NAME,))
        existing_cols = {r['column_name'] for r in cur.fetchall()}

        # Add missing columns
        added = 0
        for fname, ftype in all_fields.items():
            if fname not in existing_cols:
                cur.execute(f'ALTER TABLE "{TABLE_NAME}" ADD COLUMN "{fname}" {ftype}')
                added += 1
        if added:
            print(f'   Added {added} columns', flush=True)

        # Get workspace/database IDs
        cur.execute("SELECT id FROM workspaces WHERE slug = %s", (WORKSPACE_SLUG,))
        ws_id = cur.fetchone()['id']

        cur.execute("SELECT id FROM databases WHERE slug = %s AND workspace_id = %s", (DB_SLUG, ws_id))
        db_row = cur.fetchone()
        if db_row:
            db_id = db_row['id']
        else:
            cur.execute("INSERT INTO databases (workspace_id, name, slug, table_name, icon, color) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                       (ws_id, DB_NAME, DB_SLUG, TABLE_NAME, '🏢', '#667eea'))
            db_id = cur.fetchone()['id']
            print(f'   Created database (id={db_id})', flush=True)

        # Clear and re-insert
        cur.execute(f'DELETE FROM "{TABLE_NAME}"')
        print(f'3. Inserting {len(records)} records...', flush=True)

        inserted = 0
        errors = 0
        for rec in records:
            try:
                fields = rec.get('fields', {})
                cols = ['airtable_id', 'record_id', 'database_id']
                vals = [rec['id'], gen_record_id(), db_id]
                for k, v in fields.items():
                    cols.append(k)
                    vals.append(convert_value(v))
                placeholders = ','.join(['%s'] * len(vals))
                col_sql = ','.join(f'"{c}"' for c in cols)
                cur.execute(f'INSERT INTO "{TABLE_NAME}" ({col_sql}) VALUES ({placeholders})', vals)
                inserted += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f'   ERR: {rec["id"]}: {e}', flush=True)
                conn.rollback()
                # Retry without this record
                continue

        conn.commit()
        print(f'   Done: {inserted} inserted, {errors} errors', flush=True)

        # 4. Field definitions
        print('4. Field definitions...', flush=True)
        for fname, ftype in all_fields.items():
            ps_type = 'number' if ftype == 'NUMERIC' else 'date' if ftype == 'TIMESTAMP' else 'text'
            # Check for multi-select
            for rec in records:
                v = rec.get('fields', {}).get(fname)
                if isinstance(v, list) and v and not isinstance(v[0], dict):
                    ps_type = 'multi-select'
                    break
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    ps_type = 'attachment'
                    break

            select_opts = None
            if ps_type == 'multi-select':
                opts = set()
                for rec in records:
                    v = rec.get('fields', {}).get(fname)
                    if isinstance(v, list):
                        opts.update(str(x) for x in v)
                select_opts = sorted(opts) if opts else None

            cur.execute("SELECT id FROM field_definitions WHERE field_name = %s", (fname,))
            if not cur.fetchone():
                cur.execute("INSERT INTO field_definitions (field_name, display_name, field_type, is_editable, select_options) VALUES (%s,%s,%s,%s,%s)",
                           (fname, fname, ps_type, True, select_opts))

        # 5. Default view
        cur.execute("SELECT id FROM views WHERE database_id = %s AND is_default = true", (db_id,))
        if not cur.fetchone():
            cur.execute("INSERT INTO views (database_id, name, slug, is_default, display_order) VALUES (%s,%s,%s,true,0)", (db_id, '전체 보기', 'all'))

        conn.commit()
        print(f'\n=== Complete! ===', flush=True)
        print(f'Records: {inserted}', flush=True)
        print(f'Fields: {len(all_fields)}', flush=True)
        print(f'URL: /propsheet/workspace/{WORKSPACE_SLUG}/database/{DB_SLUG}', flush=True)

    except Exception as e:
        conn.rollback()
        print(f'FATAL ERROR: {e}', flush=True)
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
