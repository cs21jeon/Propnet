#!/usr/bin/env python3
import json, os, sys

sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
import psycopg2.extras

# 1. Airtable backup
backup_path = '/home/webapp/goldenrabbit/backups/airtable/all_properties.json'
with open(backup_path) as f:
    backup = json.load(f)
print(f'=== Airtable Backup ===')
print(f'Total records: {len(backup)}')
if backup:
    fields = backup[0].get('fields', {})
    print(f'Fields per record: {len(fields)}')

# 2. Propsheet DB
with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute('SELECT count(*) as cnt FROM sales_building')
        print(f'\n=== Propsheet DB (sales_building) ===')
        print(f'Total records: {cur.fetchone()["cnt"]}')

        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'sales_building' ORDER BY ordinal_position")
        db_cols = [r['column_name'] for r in cur.fetchall()]
        print(f'DB columns: {len(db_cols)}')

# 3. Gap analysis
airtable_fields = set()
for rec in backup:
    airtable_fields.update(rec.get('fields', {}).keys())

print(f'\n=== Gap Analysis ===')
print(f'Airtable unique fields: {len(airtable_fields)}')
missing = [f for f in sorted(airtable_fields) if f not in db_cols]
if missing:
    print(f'Fields in Airtable but NOT in DB ({len(missing)}):')
    for m in missing:
        print(f'  - {m}')
else:
    print('All Airtable fields exist in DB!')

# 4. Record comparison
backup_ids = {r['id'] for r in backup}
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT airtable_id FROM sales_building WHERE airtable_id IS NOT NULL')
        db_ids = {r[0] for r in cur.fetchall()}

not_in_db = backup_ids - db_ids
not_in_backup = db_ids - backup_ids
print(f'\nRecords in backup but NOT in DB: {len(not_in_db)}')
if not_in_db:
    for rid in list(not_in_db)[:5]:
        rec = next(r for r in backup if r['id'] == rid)
        print(f'  {rid}: {rec.get("fields", {}).get("지번 주소", "?")}')
print(f'Records in DB but NOT in backup: {len(not_in_backup)}')

# 5. Other databases in Propsheet
with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute('SELECT id, name, table_name FROM databases ORDER BY id')
        print(f'\n=== Propsheet Databases ===')
        for r in cur.fetchall():
            cur2 = conn.cursor()
            try:
                cur2.execute(f'SELECT count(*) FROM "{r["table_name"]}"')
                cnt = cur2.fetchone()[0]
            except:
                cnt = 'ERROR'
                conn.rollback()
            print(f'  id={r["id"]}: {r["name"]} ({r["table_name"]}) -> {cnt} records')

# 6. Image backup
img_dir = '/home/webapp/goldenrabbit/backups/airtable/images/'
img_folders = [d for d in os.listdir(img_dir) if os.path.isdir(os.path.join(img_dir, d))]
total_imgs = sum(len(os.listdir(os.path.join(img_dir, d))) for d in img_folders)
print(f'\n=== Image Backup ===')
print(f'Folders: {len(img_folders)}, Total files: {total_imgs}')

# 7. Check Airtable views/tables
backup_dir = '/home/webapp/goldenrabbit/backups/airtable/'
json_files = sorted(f for f in os.listdir(backup_dir) if f.endswith('.json'))
print(f'\n=== Backup JSON files ===')
for jf in json_files:
    fpath = os.path.join(backup_dir, jf)
    size = os.path.getsize(fpath) / 1024
    try:
        with open(fpath) as f:
            data = json.load(f)
        count = len(data) if isinstance(data, list) else 'dict'
    except:
        count = '?'
    print(f'  {jf}: {size:.0f}KB ({count} items)')
