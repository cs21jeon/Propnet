#!/usr/bin/env python3
"""Re-import 공동주택 매물 from Airtable (creates table fresh)"""
import os, sys, re, time, secrets, string, json, requests, psycopg2, psycopg2.extras

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
    'host': os.getenv('DB_HOST', 'localhost'), 'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'goldenrabbit_db'), 'user': os.getenv('DB_USER', 'goldenrabbit_user'),
    'password': os.getenv('DB_PASSWORD', '')
}

def gen_id():
    return 'rec' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(15))

def esc(name):
    return '"' + name.replace('%', '%%') + '"'

def fetch_all():
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    records, offset = [], None
    while True:
        params = {'pageSize': 100}
        if offset: params['offset'] = offset
        data = requests.get(url, headers=headers, params=params).json()
        if 'error' in data:
            print(f'API Error: {data}', flush=True)
            return []
        records.extend(data.get('records', []))
        offset = data.get('offset')
        if not offset: break
        time.sleep(0.2)
    return records

def convert(v):
    if v is None: return None
    if isinstance(v, dict):
        if 'error' in v: return None
        sv = v.get('specialValue')
        if sv in ('Infinity', '-Infinity', 'NaN'): return None
        if sv: return sv
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        if not v: return None
        if isinstance(v[0], dict):
            if 'url' in v[0]:
                return ', '.join(f'{a.get("filename","")} ({a.get("url","")})' for a in v)
            return json.dumps(v, ensure_ascii=False)
        return ', '.join(str(x) for x in v)
    if isinstance(v, bool): return 'O' if v else 'X'
    if isinstance(v, float):
        import math
        if math.isinf(v) or math.isnan(v): return None
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

print('=== Re-import 공동주택 매물 ===', flush=True)
records = fetch_all()
print(f'Fetched: {len(records)}', flush=True)
if not records:
    sys.exit(1)

all_fields = {}
for rec in records:
    for k in rec.get('fields', {}):
        if k not in all_fields:
            all_fields[k] = detect_type(records, k)
print(f'{len(all_fields)} fields', flush=True)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Drop if exists, create fresh
cur.execute(f'DROP TABLE IF EXISTS "{TABLE_NAME}" CASCADE')
col_defs = ['id SERIAL PRIMARY KEY', 'airtable_id VARCHAR(20)', 'record_id VARCHAR(64)',
            'database_id INTEGER', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP']
for fname, ftype in all_fields.items():
    col_defs.append(f'"{fname}" {ftype}')
cur.execute(f'CREATE TABLE "{TABLE_NAME}" ({", ".join(col_defs)})')
conn.commit()
print('Table created', flush=True)

# Get/create database entry
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

# Insert
inserted, errors = 0, 0
for rec in records:
    try:
        cols = ['airtable_id', 'record_id', 'database_id']
        vals = [rec['id'], gen_id(), db_id]
        for k, v in rec.get('fields', {}).items():
            cols.append(k)
            vals.append(convert(v))
        col_sql = ', '.join(esc(c) for c in cols)
        ph = ', '.join(['%s'] * len(vals))
        cur.execute(f'INSERT INTO "{TABLE_NAME}" ({col_sql}) VALUES ({ph})', vals)
        inserted += 1
    except Exception as e:
        conn.rollback()
        errors += 1
        if errors <= 3: print(f'  ERR: {e}', flush=True)

conn.commit()

# Default view
cur.execute("SELECT id FROM views WHERE database_id = %s AND is_default = true", (db_id,))
if not cur.fetchone():
    cur.execute("INSERT INTO views (database_id, name, slug, is_default, display_order) VALUES (%s,%s,%s,true,0)", (db_id, '전체 보기', 'all'))
    conn.commit()

cur.close()
conn.close()
print(f'\nDone! {inserted} records, {errors} errors', flush=True)
