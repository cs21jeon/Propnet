#!/usr/bin/env python3
"""Server-side: Move PDFs to correct dirs + update DB"""
import sys, os, re, json, shutil
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

TABLE = 'sales_building_copy'
DB_ID = 43
UPLOAD_BASE = '/home/webapp/goldenrabbit/uploads/propsheet/43'
TEMP_DIR = '/tmp/propsheet_pdfs'

# Load mapping
with open(os.path.join(TEMP_DIR, 'mapping.json'), 'r', encoding='utf-8') as f:
    mapping = json.load(f)
print(f"Loaded {len(mapping)} PDF mappings")

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Clear all 건축물대장
        cur.execute(f'UPDATE "{TABLE}" SET "건축물대장" = NULL')
        print(f"Cleared {cur.rowcount} rows")
        conn.commit()

        # Get 등록 records
        cur.execute(f"""
            SELECT id, "지번 주소", record_id FROM "{TABLE}" WHERE "현황" = '등록'
        """)
        records = cur.fetchall()
        print(f"Records with 현황=등록: {len(records)}")

        uploaded = 0
        no_match = []

        for rec_id, addr, record_id in records:
            if not addr:
                continue
            addr = addr.strip()

            # Extract dong+number
            m = re.search(r'([가-힣]+동)\s+(\d+(?:-\d+)?)', addr)
            if not m:
                no_match.append((rec_id, addr, 'parse'))
                continue

            jibun = f"{m.group(1)} {m.group(2)}"
            info = mapping.get(jibun)
            if not info:
                no_match.append((rec_id, addr, 'no PDF'))
                continue

            if not record_id:
                record_id = f"rec_{rec_id}"

            # Move file
            src = os.path.join(TEMP_DIR, info['flat_name'])
            if not os.path.exists(src):
                no_match.append((rec_id, addr, 'file missing'))
                continue

            dest_dir = os.path.join(UPLOAD_BASE, record_id)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, info['safe_filename'])
            shutil.copy2(src, dest)

            # Update DB
            relative_path = f"/uploads/propsheet/43/{record_id}/{info['safe_filename']}"
            cell_value = f"{info['safe_filename']} ({relative_path})"
            cur.execute(f'UPDATE "{TABLE}" SET "건축물대장" = %s WHERE id = %s',
                        (cell_value, rec_id))
            uploaded += 1

        conn.commit()

print(f"\n=== Results ===")
print(f"Uploaded: {uploaded}")
print(f"No match: {len(no_match)}")
if no_match:
    print("\n--- No match ---")
    for r in no_match:
        print(f"  id={r[0]}: [{r[1]}] ({r[2]})")

# Cleanup
shutil.rmtree(TEMP_DIR, ignore_errors=True)
print("\nDone!")
