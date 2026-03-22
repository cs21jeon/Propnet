#!/usr/bin/env python3
"""
Efficient approach:
1. Local: Find PDFs, build mapping JSON
2. Local: SCP all PDFs to temp dir on server
3. Server: Move files to correct dirs + update DB
"""
import os, re, subprocess, json, shutil, tempfile

DRIVE_BASE = r'G:\내 드라이브\금토끼부동산중개\임대차 매물 (상가 포함)'
SERVER = 'cafe24-server'

# Step 1: Find PDFs and build map
pdf_map = {}
for root, dirs, files in os.walk(DRIVE_BASE):
    for f in files:
        if f.lower().endswith('.pdf') and ('건축' in f or '건물대장' in f):
            full_path = os.path.join(root, f)
            folder = os.path.basename(root)
            m = re.match(r'([가-힣]+동)\s+(\d+(?:-\d+)?)', folder)
            if m:
                jibun = f"{m.group(1)} {m.group(2)}"
                if jibun not in pdf_map:
                    # Sanitize filename
                    safe = re.sub(r'[^\w가-힣\s\-_\.]', '', f)
                    if not safe.endswith('.pdf'):
                        safe += '.pdf'
                    # Use jibun as key for flat copy
                    flat_name = jibun.replace(' ', '_') + '__' + safe
                    pdf_map[jibun] = {
                        'local_path': full_path,
                        'flat_name': flat_name,
                        'safe_filename': safe
                    }

print(f"Found {len(pdf_map)} unique PDFs")

# Step 2: Copy all PDFs to a local temp dir with flat names
temp_dir = os.path.join(tempfile.gettempdir(), 'propsheet_pdfs')
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

for jibun, info in pdf_map.items():
    shutil.copy2(info['local_path'], os.path.join(temp_dir, info['flat_name']))

print(f"Copied {len(pdf_map)} PDFs to temp dir")

# Step 3: SCP entire temp dir to server
print("Uploading to server...")
r = subprocess.run(
    ['scp', '-r', temp_dir, f'{SERVER}:/tmp/propsheet_pdfs'],
    capture_output=True, text=True
)
if r.returncode != 0:
    print(f"SCP failed: {r.stderr}")
    exit(1)
print("Upload complete")

# Step 4: Save mapping JSON
mapping = {}
for jibun, info in pdf_map.items():
    mapping[jibun] = {
        'flat_name': info['flat_name'],
        'safe_filename': info['safe_filename']
    }

mapping_path = os.path.join(temp_dir, 'mapping.json')
with open(mapping_path, 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False)

subprocess.run(['scp', mapping_path, f'{SERVER}:/tmp/propsheet_pdfs/mapping.json'],
               capture_output=True)
print("Mapping uploaded")

# Cleanup local temp
shutil.rmtree(temp_dir)
print("\nNow run server script: ssh cafe24-server 'python3 /tmp/apply_pdfs.py'")
