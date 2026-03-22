#!/usr/bin/env python3
"""Refresh sales_building from Airtable - preserving field_definitions settings"""
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

def fetch_all():
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    records, offset = [], None
    while True:
        params = {'pageSize': 100}
        if offset: params['offset'] = offset
        data = requests.get(url, headers=headers, params=params).json()
        if 'error' in data:
            print(f'API Error: {data["error"]["message"]}', flush=True)
            return []
        records.extend(data.get('records', []))
        print(f'  {len(records)} records...', flush=True)
        offset = data.get('offset')
        if not offset: break
        time.sleep(0.2)
    return records

def convert(v):
    if v is None: return None
    if isinstance(v, dict):
        sv = v.get('specialValue')
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
    return v

def detect_pg_type(records, key):
    for rec in records:
        v = rec.get('fields', {}).get(key)
        if v is None: continue
        if isinstance(v, bool): return 'TEXT'
        if isinstance(v, (int, float)): return 'NUMERIC'
        if isinstance(v, str) and re.match(r'^\d{4}-\d{2}-\d{2}', v): return 'TIMESTAMP'
        return 'TEXT'
    return 'TEXT'

def detect_ps_type(records, key, pg_type):
    for rec in records:
        v = rec.get('fields', {}).get(key)
        if isinstance(v, list) and v:
            if isinstance(v[0], dict): return 'attachment'
            return 'multi-select'
    if pg_type == 'NUMERIC': return 'number'
    if pg_type == 'TIMESTAMP': return 'date'
    return 'text'

def main():
    print('=== Refresh sales_building ===', flush=True)

    records = fetch_all()
    print(f'Total: {len(records)} records', flush=True)
    if not records: return

    # Detect all fields
    all_fields = {}
    for rec in records:
        for k in rec.get('fields', {}):
            if k not in all_fields:
                all_fields[k] = detect_pg_type(records, k)
    print(f'{len(all_fields)} fields from Airtable', flush=True)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get existing columns
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (TABLE_NAME,))
    existing_cols = {r['column_name'] for r in cur.fetchall()}
    print(f'{len(existing_cols)} existing columns in DB', flush=True)

    # Add missing columns
    added = []
    for fname, ftype in all_fields.items():
        if fname not in existing_cols:
            cur.execute(f'ALTER TABLE "{TABLE_NAME}" ADD COLUMN IF NOT EXISTS "{fname}" {ftype}')
            added.append(fname)
    if added:
        print(f'Added {len(added)} new columns: {added}', flush=True)
    conn.commit()

    # Get database_id
    cur.execute("SELECT id FROM databases WHERE table_name = %s", (TABLE_NAME,))
    row = cur.fetchone()
    db_id = row['id'] if row else 1

    # Backup count before
    cur.execute(f'SELECT count(*) as cnt FROM "{TABLE_NAME}"')
    before_count = cur.fetchone()['cnt']
    print(f'Before: {before_count} records', flush=True)

    # Clear and re-insert
    cur.execute(f'DELETE FROM "{TABLE_NAME}"')
    conn.commit()

    print(f'Inserting {len(records)} records...', flush=True)
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
            if errors <= 5: print(f'  ERR [{rec["id"]}]: {e}', flush=True)
    conn.commit()
    print(f'Inserted: {inserted}, Errors: {errors}', flush=True)

    # Update field_definitions - add new ones, merge select options (preserve existing settings)
    print('Updating field_definitions...', flush=True)
    for fname in all_fields:
        pg_type = all_fields[fname]
        ps_type = detect_ps_type(records, fname, pg_type)

        # Collect select options from data
        new_opts = set()
        if ps_type == 'multi-select':
            for rec in records:
                v = rec.get('fields', {}).get(fname)
                if isinstance(v, list):
                    new_opts.update(str(x) for x in v if not isinstance(x, dict))

        cur.execute("SELECT id, select_options FROM field_definitions WHERE field_name = %s", (fname,))
        existing = cur.fetchone()

        if existing:
            # Merge select options (add new ones, keep existing)
            if ps_type == 'multi-select' and new_opts:
                old_opts = set(existing['select_options'] or [])
                merged = list(old_opts | new_opts)
                if merged != list(old_opts):
                    cur.execute("UPDATE field_definitions SET select_options = %s WHERE field_name = %s",
                               (sorted(merged), fname))
                    print(f'  Merged options for {fname}: +{len(new_opts - old_opts)} new', flush=True)
        else:
            # New field - create definition
            select_opts = sorted(new_opts) if new_opts else None
            cur.execute("INSERT INTO field_definitions (field_name, display_name, field_type, is_editable, select_options) VALUES (%s,%s,%s,%s,%s)",
                       (fname, fname, ps_type, True, select_opts))
            print(f'  New field_definition: {fname} ({ps_type})', flush=True)

    conn.commit()
    cur.close()
    conn.close()

    print(f'\n=== Done! {before_count} → {inserted} records ===', flush=True)

if __name__ == '__main__':
    main()
