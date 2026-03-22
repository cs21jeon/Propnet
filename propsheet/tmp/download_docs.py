#!/usr/bin/env python3
"""Download 건축물대장 PDFs from Airtable API and map to propsheet DB"""
import sys, os, time, requests
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
import psycopg2.extras

API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = 'appGSg5QfDNKgFf73'
TABLE_ID = 'tblnR438TK52Gr0HB'
SAVE_DIR = '/home/webapp/goldenrabbit/backups/airtable/images'  # Same structure as photos

print('=== Download 건축물대장 from Airtable ===', flush=True)

# 1. Fetch all records with 건축물대장
url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'
headers = {'Authorization': f'Bearer {API_KEY}'}
records = []
offset = None
while True:
    params = {'pageSize': 100}
    if offset:
        params['offset'] = offset
    resp = requests.get(url, headers=headers, params=params)
    data = resp.json()
    records.extend(data.get('records', []))
    offset = data.get('offset')
    if not offset:
        break
    time.sleep(0.2)

print(f'Total records: {len(records)}', flush=True)

# 2. Download 건축물대장 attachments
downloaded = 0
skipped = 0
errors = 0

for rec in records:
    aid = rec['id']
    attachments = rec.get('fields', {}).get('건축물대장', [])
    if not attachments or not isinstance(attachments, list):
        continue

    for att in attachments:
        filename = att.get('filename', '')
        att_url = att.get('url', '')
        if not filename or not att_url:
            continue

        # Save to same folder as images
        save_dir = os.path.join(SAVE_DIR, aid)
        save_path = os.path.join(save_dir, filename)

        if os.path.exists(save_path):
            skipped += 1
            continue

        try:
            os.makedirs(save_dir, exist_ok=True)
            resp = requests.get(att_url, timeout=30)
            if resp.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(resp.content)
                downloaded += 1
                if downloaded % 20 == 0:
                    print(f'  Downloaded {downloaded}...', flush=True)
            else:
                errors += 1
                if errors <= 3:
                    print(f'  HTTP {resp.status_code}: {aid}/{filename}', flush=True)
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f'  Error: {aid}/{filename}: {e}', flush=True)
        time.sleep(0.1)  # Rate limit

print(f'\nDownloaded: {downloaded}, Skipped: {skipped}, Errors: {errors}', flush=True)

# 3. Update DB cell values — same as photo migration
print('\nUpdating DB cell values...', flush=True)
import re

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT id, airtable_id, "건축물대장"
            FROM sales_building
            WHERE "건축물대장" IS NOT NULL AND "건축물대장" != ''
            AND airtable_id IS NOT NULL AND airtable_id LIKE 'rec%'
        """)
        recs = cur.fetchall()
        print(f'Records with 건축물대장: {len(recs)}', flush=True)

        updated = 0
        for r in recs:
            aid = r['airtable_id']
            doc = r['건축물대장']

            # Extract filename
            match = re.match(r'^(.+?\.(pdf|jpg|jpeg|png))', doc, re.IGNORECASE)
            if not match:
                continue

            filename = match.group(1).strip()
            backup_path = os.path.join(SAVE_DIR, aid, filename)

            if os.path.exists(backup_path):
                local_url = f'/uploads/airtable/{aid}/{filename}'
                new_value = f'{filename} ({local_url})'
                cur.execute('UPDATE sales_building SET "건축물대장" = %s WHERE id = %s', (new_value, r['id']))
                updated += 1

        conn.commit()
        print(f'Updated cell values: {updated}', flush=True)

print('\nDone!', flush=True)
