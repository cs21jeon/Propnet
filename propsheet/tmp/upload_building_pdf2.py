#!/usr/bin/env python3
"""
Step 1 (local): Find PDFs, SCP to server
Step 2 (server): Match to records, update DB
"""
import os, re, subprocess, json

DRIVE_BASE = r'G:\내 드라이브\금토끼부동산중개\임대차 매물 (상가 포함)'
SERVER = 'cafe24-server'
UPLOAD_BASE = '/home/webapp/goldenrabbit/uploads/propsheet/43'

# Step 1: Find all 건축물대장 PDFs and extract jibun
pdf_map = {}  # jibun -> local_path
for root, dirs, files in os.walk(DRIVE_BASE):
    for f in files:
        if f.lower().endswith('.pdf') and ('건축' in f or '건물대장' in f):
            full_path = os.path.join(root, f)
            folder = os.path.basename(root)
            # Extract jibun from folder
            m = re.match(r'([가-힣]+동)\s+(\d+(?:-\d+)?)', folder)
            if m:
                jibun = f"{m.group(1)} {m.group(2)}"
                if jibun not in pdf_map:
                    pdf_map[jibun] = full_path

print(f"Found {len(pdf_map)} unique jibun PDFs")

# Step 2: Get records from server (현황=등록)
result = subprocess.run(
    ['ssh', SERVER, 'cd /home/webapp/goldenrabbit/backend/property-manager && python3 -c "'
     'from dotenv import load_dotenv; load_dotenv(\"/home/webapp/goldenrabbit/backend/.env\");'
     'from services.database_service import get_db_connection; import json;'
     'conn = get_db_connection(); cur = conn.cursor();'
     'cur.execute(\"UPDATE sales_building_copy SET \\\\\"건축물대장\\\\\" = NULL\"); conn.commit();'
     'print(f\"Cleared {cur.rowcount} rows\");'
     'cur.execute(\"SELECT id, \\\\\"지번 주소\\\\\", record_id FROM sales_building_copy WHERE \\\\\"현황\\\\\" = \\'등록\\'\");'
     'rows = [(r[0], r[1].strip() if r[1] else \"\", r[2] or \"\") for r in cur.fetchall()];'
     'print(json.dumps(rows, ensure_ascii=False));'
     'conn.close()"'],
    capture_output=True, text=True, encoding='utf-8'
)
print(result.stdout.split('\n')[0])  # Cleared message
records = json.loads(result.stdout.split('\n')[1])
print(f"Records with 현황=등록: {len(records)}")

# Step 3: Match and upload
uploaded = 0
no_match = []

for rec_id, addr, record_id in records:
    if not addr:
        continue

    # Extract dong+number from address
    m = re.search(r'([가-힣]+동)\s+(\d+(?:-\d+)?)', addr)
    if not m:
        no_match.append((rec_id, addr, 'parse failed'))
        continue

    jibun = f"{m.group(1)} {m.group(2)}"
    pdf_path = pdf_map.get(jibun)

    if not pdf_path:
        no_match.append((rec_id, addr, 'no PDF'))
        continue

    # Sanitize filename
    filename = os.path.basename(pdf_path)
    safe_filename = re.sub(r'[^\w가-힣\s\-_\.]', '', filename)
    if not safe_filename.endswith('.pdf'):
        safe_filename += '.pdf'

    if not record_id:
        record_id = f"rec_{rec_id}"

    remote_dir = f"{UPLOAD_BASE}/{record_id}"
    remote_path = f"{remote_dir}/{safe_filename}"

    # Create dir on server
    subprocess.run(['ssh', SERVER, f'mkdir -p "{remote_dir}"'],
                   capture_output=True)

    # SCP upload
    r = subprocess.run(['scp', pdf_path, f'{SERVER}:{remote_path}'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        no_match.append((rec_id, addr, f'scp failed: {r.stderr[:50]}'))
        continue

    # Update DB
    relative_path = f"/uploads/propsheet/43/{record_id}/{safe_filename}"
    cell_value = f"{safe_filename} ({relative_path})"

    subprocess.run(
        ['ssh', SERVER,
         f'cd /home/webapp/goldenrabbit/backend/property-manager && python3 -c "'
         f'from dotenv import load_dotenv; load_dotenv(\"/home/webapp/goldenrabbit/backend/.env\");'
         f'from services.database_service import get_db_connection;'
         f'conn = get_db_connection(); cur = conn.cursor();'
         f'cur.execute(\"UPDATE sales_building_copy SET \\\\\"건축물대장\\\\\" = %s WHERE id = %s\", (\"{cell_value}\", {rec_id}));'
         f'conn.commit(); conn.close(); print(\"OK\")"'],
        capture_output=True, text=True
    )

    uploaded += 1
    if uploaded % 10 == 0:
        print(f"  ... {uploaded} uploaded")

print(f"\n=== Results ===")
print(f"Uploaded: {uploaded}")
print(f"No match: {len(no_match)}")

if no_match:
    print(f"\n--- No match ---")
    for r in no_match:
        print(f"  id={r[0]}: [{r[1]}] ({r[2]})")
