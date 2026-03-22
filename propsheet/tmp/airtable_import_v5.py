#!/usr/bin/env python3
"""Airtable → Propsheet import (v5 - % escape fix)"""
import os, sys, re, time, secrets, string, requests, psycopg2, psycopg2.extras

sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')

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

def gen_id():
    return 'rec' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(15))

def esc(name):
    """Escape column name for psycopg2 query string (double % signs)"""
    return '"' + name.replace('%', '%%') + '"'

def fetch_all():
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    records, offset = [], None
    while True:
        params = {'pageSize': 100}
        if offset: params['offset'] = offset
        data = requests.get(url, headers=headers, params=params).json()
        records.extend(data.get('records', []))
        print(f'  {len(records)} records...', flush=True)
        offset = data.get('offset')
        if not offset: break
        time.sleep(0.2)
    return records

def convert(v):
    if v is None: return None
    if isinstance(v, list):
        if not v: return None
        if isinstance(v[0], dict):
            return ', '.join(f'{a.get("filename","")} ({a.get("url","")})' for a in v)
        return ', '.join(str(x) for x in v)
    if isinstance(v, bool): return 'O' if v else 'X'
    return v

def detect_type(records, key):
    for rec in records:
        v = rec.get('fields', {}).get(key)
        if v is None: continue
        if isinstance(v, bool): return 'TEXT'
        if isinstance(v, (int, float)): return 'NUMERIC'
        if isinstance(v, str) and re.match(r'^\d{4}-\d{2}-\d{2}', v): return 'TIMESTAMP'
        return 'TEXT'
    return 'TEXT'

def main():
    print('=== Airtable Import v5 ===', flush=True)
    records = fetch_all()
    print(f'Total: {len(records)}', flush=True)
    if not records: return

    all_fields = {}
    for rec in records:
        for k in rec.get('fields', {}):
            if k not in all_fields:
                all_fields[k] = detect_type(records, k)
    print(f'{len(all_fields)} fields', flush=True)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Ensure columns
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (TABLE_NAME,))
    existing = {r['column_name'] for r in cur.fetchall()}
    for col, ctype in [('airtable_id','VARCHAR(20)'),('record_id','VARCHAR(64)'),('database_id','INTEGER')]:
        if col not in existing:
            cur.execute(f'ALTER TABLE "{TABLE_NAME}" ADD COLUMN IF NOT EXISTS "{col}" {ctype}')
    for fname, ftype in all_fields.items():
        if fname not in existing:
            cur.execute(f'ALTER TABLE "{TABLE_NAME}" ADD COLUMN IF NOT EXISTS "{fname}" {ftype}')
    conn.commit()

    # Database entry
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
    conn.commit()
    print(f'Database id={db_id}', flush=True)

    # Clear
    cur.execute(f'DELETE FROM "{TABLE_NAME}"')
    conn.commit()

    # Insert
    print(f'Inserting {len(records)} records...', flush=True)
    inserted, errors = 0, 0
    for rec in records:
        try:
            col_names = ['airtable_id', 'record_id', 'database_id']
            vals = [rec['id'], gen_id(), db_id]
            for k, v in rec.get('fields', {}).items():
                col_names.append(k)
                vals.append(convert(v))
            # Use esc() to handle % in column names
            col_sql = ', '.join(esc(c) for c in col_names)
            placeholders = ', '.join(['%s'] * len(vals))
            query = f'INSERT INTO "{TABLE_NAME}" ({col_sql}) VALUES ({placeholders})'
            cur.execute(query, vals)
            inserted += 1
        except Exception as e:
            conn.rollback()
            errors += 1
            if errors <= 3: print(f'  ERR [{rec["id"]}]: {e}', flush=True)

    conn.commit()
    print(f'Done: {inserted} inserted, {errors} errors', flush=True)

    # Field definitions
    for fname in all_fields:
        pg_type = all_fields[fname]
        ps_type = 'number' if pg_type == 'NUMERIC' else 'date' if pg_type == 'TIMESTAMP' else 'text'
        for rec in records:
            v = rec.get('fields', {}).get(fname)
            if isinstance(v, list) and v:
                ps_type = 'attachment' if isinstance(v[0], dict) else 'multi-select'
                break
        select_opts = None
        if ps_type == 'multi-select':
            opts = set()
            for rec in records:
                v = rec.get('fields', {}).get(fname)
                if isinstance(v, list): opts.update(str(x) for x in v if not isinstance(x, dict))
            select_opts = sorted(opts) if opts else None
        cur.execute("SELECT id FROM field_definitions WHERE field_name = %s", (fname,))
        if not cur.fetchone():
            cur.execute("INSERT INTO field_definitions (field_name, display_name, field_type, is_editable, select_options) VALUES (%s,%s,%s,%s,%s)",
                       (fname, fname, ps_type, True, select_opts))
    conn.commit()

    # Default view
    cur.execute("SELECT id FROM views WHERE database_id = %s AND is_default = true", (db_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO views (database_id, name, slug, is_default, display_order) VALUES (%s,%s,%s,true,0)", (db_id, '전체 보기', 'all'))
        conn.commit()

    cur.close()
    conn.close()
    print(f'\n=== Complete! {inserted} records ===', flush=True)
    print(f'/propsheet/workspace/{WORKSPACE_SLUG}/database/{DB_SLUG}', flush=True)

if __name__ == '__main__':
    main()
