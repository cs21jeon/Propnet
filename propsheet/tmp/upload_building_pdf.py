#!/usr/bin/env python3
"""
Upload 건축물대장 PDFs from Google Drive to server,
match to 부분부동산 records where 현황='등록'
"""
import sys, os, re, subprocess, shutil
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

TABLE = 'sales_building_copy'
DB_ID = 43
UPLOAD_BASE = '/home/webapp/goldenrabbit/uploads/propsheet'
DRIVE_BASE = '/g/내 드라이브/금토끼부동산중개/임대차 매물 (상가 포함)'

# Step 1: Clear existing 건축물대장 for all records
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(f'UPDATE "{TABLE}" SET "건축물대장" = NULL')
        print(f"1. Cleared 건축물대장 for {cur.rowcount} rows")
        conn.commit()

# Step 2: Get records where 현황='등록'
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT id, "지번 주소", record_id FROM "{TABLE}"
            WHERE "현황" = '등록'
        """)
        records = cur.fetchall()
        print(f"2. Found {len(records)} records with 현황=등록")

# Step 3: Find all 건축물대장 PDFs
pdf_files = []
for root, dirs, files in os.walk(DRIVE_BASE):
    for f in files:
        if f.endswith('.pdf') and ('건축' in f or '건물대장' in f):
            pdf_files.append(os.path.join(root, f))
print(f"3. Found {len(pdf_files)} PDF files")

# Step 4: Extract 지번 from folder name
def extract_jibun_from_path(path):
    """Extract 지번 like '사당동 278-22' from folder path"""
    # Get parent folder name
    folder = os.path.basename(os.path.dirname(path))
    # Extract pattern: XXX동 NNN-NNN or XXX동 NNN
    m = re.match(r'([가-힣]+동)\s+(\d+(?:-\d+)?)', folder)
    if m:
        return f"동작구 {m.group(1)} {m.group(2)}"
    # Try other districts
    m = re.match(r'([가-힣]+구\s+[가-힣]+동)\s+(\d+(?:-\d+)?)', folder)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return None

# Build PDF lookup by jibun
pdf_by_jibun = {}
for pdf_path in pdf_files:
    jibun = extract_jibun_from_path(pdf_path)
    if jibun:
        # If multiple PDFs for same jibun, keep the first (or latest)
        if jibun not in pdf_by_jibun:
            pdf_by_jibun[jibun] = pdf_path
print(f"4. Mapped {len(pdf_by_jibun)} unique jibun addresses to PDFs")

# Step 5: Match and upload
uploaded = 0
no_match = []
errors = []

for rec_id, addr, record_id in records:
    if not addr:
        continue
    addr_clean = addr.strip()

    # Try exact match
    pdf_path = pdf_by_jibun.get(addr_clean)

    # Try without trailing spaces
    if not pdf_path:
        for jibun, path in pdf_by_jibun.items():
            if jibun.strip() == addr_clean.strip():
                pdf_path = path
                break

    # Try matching just dong+number part
    if not pdf_path:
        m = re.search(r'([가-힣]+동)\s+(\d+(?:-\d+)?)', addr_clean)
        if m:
            short_key = f"동작구 {m.group(1)} {m.group(2)}"
            pdf_path = pdf_by_jibun.get(short_key)
            # Also try 관악구, 서초구 variants
            if not pdf_path:
                for prefix in ['관악구', '서초구']:
                    pdf_path = pdf_by_jibun.get(f"{prefix} {m.group(1)} {m.group(2)}")
                    if pdf_path:
                        break

    if not pdf_path:
        no_match.append((rec_id, addr_clean))
        continue

    try:
        # Create upload directory
        if not record_id:
            record_id = f"rec_{rec_id}"
        upload_dir = f"{UPLOAD_BASE}/{DB_ID}/{record_id}"
        os.makedirs(upload_dir, exist_ok=True)

        # Copy PDF to server
        filename = os.path.basename(pdf_path)
        # Sanitize filename
        safe_filename = re.sub(r'[^\w가-힣\s\-_\.]', '', filename)
        if not safe_filename.endswith('.pdf'):
            safe_filename += '.pdf'
        dest_path = os.path.join(upload_dir, safe_filename)
        shutil.copy2(pdf_path, dest_path)

        # Update DB
        relative_path = f"/uploads/propsheet/{DB_ID}/{record_id}/{safe_filename}"
        cell_value = f"{safe_filename} ({relative_path})"

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f'UPDATE "{TABLE}" SET "건축물대장" = %s WHERE id = %s',
                            (cell_value, rec_id))
                conn.commit()

        uploaded += 1

    except Exception as e:
        errors.append((rec_id, addr_clean, str(e)))

print(f"\n=== Results ===")
print(f"Uploaded: {uploaded}")
print(f"No PDF match: {len(no_match)}")
print(f"Errors: {len(errors)}")

if no_match:
    print(f"\n--- No PDF match (현황=등록) ---")
    for r in no_match:
        print(f"  id={r[0]}: [{r[1]}]")

if errors:
    print(f"\n--- Errors ---")
    for r in errors:
        print(f"  id={r[0]}: [{r[1]}] -> {r[2]}")
