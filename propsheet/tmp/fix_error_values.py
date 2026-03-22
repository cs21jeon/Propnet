#!/usr/bin/env python3
"""Fix: handle Airtable #ERROR! and Infinity values in numeric fields, then re-import failed records"""
import os, sys, re, time, secrets, string, json, requests, psycopg2, psycopg2.extras

sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')

BASE_ID = 'appGSg5QfDNKgFf73'
TABLE_ID = 'tblnR438TK52Gr0HB'
TABLE_NAME = 'sales_building'
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

def convert(v):
    if v is None: return None
    if isinstance(v, dict):
        # Airtable error values like {"specialValue": "Infinity"} or {"error": "#ERROR!"}
        if 'error' in v: return None
        sv = v.get('specialValue')
        if sv == 'Infinity' or sv == '-Infinity' or sv == 'NaN': return None
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

# Fetch all records
print('Fetching...', flush=True)
url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'
headers = {'Authorization': f'Bearer {API_KEY}'}
records, offset = [], None
while True:
    params = {'pageSize': 100}
    if offset: params['offset'] = offset
    data = requests.get(url, headers=headers, params=params).json()
    records.extend(data.get('records', []))
    offset = data.get('offset')
    if not offset: break
    time.sleep(0.2)
print(f'{len(records)} records', flush=True)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get database_id
cur.execute("SELECT id FROM databases WHERE table_name = %s", (TABLE_NAME,))
db_id = cur.fetchone()['id']

# Get existing airtable_ids in DB
cur.execute(f'SELECT airtable_id FROM "{TABLE_NAME}"')
existing_ids = {r['airtable_id'] for r in cur.fetchall()}

# Find missing records
missing = [r for r in records if r['id'] not in existing_ids]
print(f'{len(missing)} missing records to insert', flush=True)

inserted, errors = 0, 0
for rec in missing:
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
        if errors <= 5: print(f'  ERR [{rec["id"]}]: {e}', flush=True)

conn.commit()
cur.close()
conn.close()

# Final count
conn2 = psycopg2.connect(**DB_CONFIG)
cur2 = conn2.cursor()
cur2.execute(f'SELECT count(*) FROM "{TABLE_NAME}"')
total = cur2.fetchone()[0]
conn2.close()

print(f'Inserted: {inserted}, Errors: {errors}', flush=True)
print(f'Total records now: {total}', flush=True)
