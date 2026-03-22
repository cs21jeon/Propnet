#!/usr/bin/env python3
"""
Migrate 대표사진 cell values: replace airtable CDN URLs with local /uploads/airtable/ paths.
Only for records where the backup image actually exists on disk.
"""
import sys, os, re
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
import psycopg2.extras
from psycopg2 import sql

BACKUP_DIR = '/home/webapp/goldenrabbit/backups/airtable/images'

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Get all records with 대표사진 and airtable_id
        cur.execute("""
            SELECT id, airtable_id, "대표사진"
            FROM sales_building
            WHERE "대표사진" IS NOT NULL AND "대표사진" != ''
            AND airtable_id IS NOT NULL AND airtable_id LIKE 'rec%'
        """)
        records = cur.fetchall()
        print(f'Records with photos: {len(records)}', flush=True)

        updated = 0
        skipped = 0
        for rec in records:
            aid = rec['airtable_id']
            photo = rec['대표사진']

            # Extract filename from "filename (url)" format
            match = re.match(r'^(.+?\.(jpg|jpeg|png|gif|webp))\s*\(', photo, re.IGNORECASE)
            if not match:
                skipped += 1
                continue

            filename = match.group(1).strip()
            backup_path = os.path.join(BACKUP_DIR, aid, filename)

            if os.path.exists(backup_path):
                # Build local URL
                local_url = f'/uploads/airtable/{aid}/{filename}'
                new_value = f'{filename} ({local_url})'
                cur.execute('UPDATE sales_building SET "대표사진" = %s WHERE id = %s', (new_value, rec['id']))
                updated += 1
            else:
                skipped += 1

        conn.commit()
        print(f'Updated: {updated}, Skipped: {skipped} (no backup file)', flush=True)
