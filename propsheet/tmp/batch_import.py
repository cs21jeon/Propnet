#!/usr/bin/env python3
"""Batch Airtable → Propsheet import"""
import os, sys, re, time, secrets, string, requests, psycopg2, psycopg2.extras

sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')

API_KEY = os.getenv('AIRTABLE_API_KEY')
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'goldenrabbit_db'),
    'user': os.getenv('DB_USER', 'goldenrabbit_user'),
    'password': os.getenv('DB_PASSWORD', '')
}
WORKSPACE_SLUG = 'goldenrabbit'

IMPORTS = [
    {
        'base_id': 'appzooFXYu5oRBcwF', 'table_id': 'tblC6RP3eY6ZhZwUn',
        'db_name': '임대차 매물', 'db_slug': 'lease-properties', 'table_name': 'lease_properties',
    },
    {
        'base_id': 'appAVGngyG0RSSfxp', 'table_id': 'tblcwfx1CTq0qm83L',
        'db_name': '토지건물 매물', 'db_slug': 'land-building', 'table_name': 'land_building',
    },
    {
        'base_id': 'appBm845MhVkkaBD1', 'table_id': 'tblgik4xDNNPb8WUE',
        'db_name': '상담 문의', 'db_slug': 'inquiry', 'table_name': 'inquiry',
    },
    {
        'base_id': 'appK4DRJtSOubnMa6', 'table_id': 'tblgik4xDNNPb8WUE',
        'db_name': '상담 내역', 'db_slug': 'consultation', 'table_name': 'consultation',
    },
    {
        'base_id': 'appGB69dISTr3ohBO', 'table_id': 'tbls3C6WWtYHgNSUA',
        'db_name': '순번 관리', 'db_slug': 'numbering', 'table_name': 'numbering',
    },
    {
        'base_id': 'apphQM0YbpFBG4dlb', 'table_id': 'tbl3rFrS0FneNVLhz',
        'db_name': '아파트 정보', 'db_slug': 'apartment-info', 'table_name': 'apartment_info',
    },
]

def gen_id():
    return 'rec' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(15))

def esc(name):
    return '"' + name.replace('%', '%%') + '"'

def fetch_all(base_id, table_id):
    url = f'https://api.airtable.com/v0/{base_id}/{table_id}'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    records, offset = [], None
    while True:
        params = {'pageSize': 100}
        if offset: params['offset'] = offset
        data = requests.get(url, headers=headers, params=params).json()
        if 'error' in data:
            print(f'  API Error: {data["error"]["message"]}', flush=True)
            return []
        records.extend(data.get('records', []))
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

def import_one(cfg):
    base_id = cfg['base_id']
    table_id = cfg['table_id']
    db_name = cfg['db_name']
    db_slug = cfg['db_slug']
    table_name = cfg['table_name']

    print(f'\n{"="*50}', flush=True)
    print(f'Importing: {db_name} ({base_id}/{table_id})', flush=True)
    print(f'{"="*50}', flush=True)

    # Fetch
    records = fetch_all(base_id, table_id)
    if not records:
        print(f'  No records found, skipping.', flush=True)
        return 0
    print(f'  Fetched {len(records)} records, analyzing...', flush=True)

    # Detect fields
    all_fields = {}
    for rec in records:
        for k in rec.get('fields', {}):
            if k not in all_fields:
                all_fields[k] = detect_type(records, k)
    print(f'  {len(all_fields)} fields', flush=True)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Check if table exists
        cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)", (table_name,))
        table_exists = cur.fetchone()['exists']

        if table_exists:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
            existing = {r['column_name'] for r in cur.fetchall()}
            for fname, ftype in all_fields.items():
                if fname not in existing:
                    cur.execute(f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "{fname}" {ftype}')
            for col, ctype in [('airtable_id','VARCHAR(20)'),('record_id','VARCHAR(64)'),('database_id','INTEGER')]:
                if col not in existing:
                    cur.execute(f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "{col}" {ctype}')
        else:
            col_defs = ['id SERIAL PRIMARY KEY', 'airtable_id VARCHAR(20)', 'record_id VARCHAR(64)',
                        'database_id INTEGER', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                        'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP']
            for fname, ftype in all_fields.items():
                col_defs.append(f'"{fname}" {ftype}')
            cur.execute(f'CREATE TABLE "{table_name}" ({", ".join(col_defs)})')
            print(f'  Created table: {table_name}', flush=True)
        conn.commit()

        # Database entry
        cur.execute("SELECT id FROM workspaces WHERE slug = %s", (WORKSPACE_SLUG,))
        ws_id = cur.fetchone()['id']
        cur.execute("SELECT id FROM databases WHERE slug = %s AND workspace_id = %s", (db_slug, ws_id))
        db_row = cur.fetchone()
        if db_row:
            db_id = db_row['id']
        else:
            cur.execute("INSERT INTO databases (workspace_id, name, slug, table_name, icon, color) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                       (ws_id, db_name, db_slug, table_name, '📋', '#667eea'))
            db_id = cur.fetchone()['id']
        conn.commit()

        # Clear existing data
        cur.execute(f'DELETE FROM "{table_name}"')
        conn.commit()

        # Insert records
        inserted, errors = 0, 0
        for rec in records:
            try:
                col_names = ['airtable_id', 'record_id', 'database_id']
                vals = [rec['id'], gen_id(), db_id]
                for k, v in rec.get('fields', {}).items():
                    col_names.append(k)
                    vals.append(convert(v))
                col_sql = ', '.join(esc(c) for c in col_names)
                placeholders = ', '.join(['%s'] * len(vals))
                cur.execute(f'INSERT INTO "{table_name}" ({col_sql}) VALUES ({placeholders})', vals)
                inserted += 1
            except Exception as e:
                conn.rollback()
                errors += 1
                if errors <= 2: print(f'  ERR: {e}', flush=True)
        conn.commit()

        # Field definitions (only new ones)
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
            cur.execute("INSERT INTO views (database_id, name, slug, is_default, display_order) VALUES (%s,%s,%s,true,0)",
                       (db_id, '전체 보기', 'all'))
            conn.commit()

        print(f'  Result: {inserted} inserted, {errors} errors', flush=True)
        return inserted

    except Exception as e:
        conn.rollback()
        print(f'  FATAL: {e}', flush=True)
        import traceback
        traceback.print_exc()
        return 0
    finally:
        cur.close()
        conn.close()

def main():
    print('=== Batch Airtable Import ===', flush=True)
    total = 0
    for i, cfg in enumerate(IMPORTS, 1):
        print(f'\n[{i}/{len(IMPORTS)}]', flush=True)
        count = import_one(cfg)
        total += count
        time.sleep(0.5)

    print(f'\n{"="*50}', flush=True)
    print(f'All done! Total {total} records imported from {len(IMPORTS)} bases.', flush=True)

if __name__ == '__main__':
    main()
