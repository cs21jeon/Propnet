#!/usr/bin/env python3
"""Re-import land_building with dict value fix"""
import os, sys, re, time, secrets, string, requests, psycopg2, psycopg2.extras, json

sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')

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
        sv = v.get('specialValue')
        if sv: return sv  # "Infinity", "NaN" etc as string
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        if not v: return None
        if isinstance(v[0], dict):
            if 'url' in v[0]:
                return ', '.join(f'{a.get("filename","")} ({a.get("url","")})' for a in v)
            return json.dumps(v, ensure_ascii=False)
        return ', '.join(str(x) for x in v)
    if isinstance(v, bool): return 'O' if v else 'X'
    return v

# Fetch all records
url = 'https://api.airtable.com/v0/appAVGngyG0RSSfxp/tblcwfx1CTq0qm83L'
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
print(f'Fetched {len(records)}', flush=True)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("SELECT id FROM databases WHERE slug = 'land-building'")
db_id = cur.fetchone()['id']
cur.execute('DELETE FROM "land_building"')
conn.commit()

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
        cur.execute(f'INSERT INTO "land_building" ({col_sql}) VALUES ({ph})', vals)
        inserted += 1
    except Exception as e:
        conn.rollback()
        errors += 1
        if errors <= 3: print(f'ERR: {e}', flush=True)

conn.commit()
cur.close()
conn.close()
print(f'Done: {inserted} inserted, {errors} errors', flush=True)
