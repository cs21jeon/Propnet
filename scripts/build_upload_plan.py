#!/usr/bin/env python3
"""매칭 계획 생성 + SCP 업로드 + 서버 DB 업데이트"""
import os, re, json, subprocess, uuid, sys

GDRIVE_BASE = "G:/내 드라이브/금토끼부동산중개/빌라매물"
SERVER = "root@175.119.224.71"
UPLOAD_BASE = "/home/webapp/goldenrabbit/uploads/propsheet"
DB_ID = 38
TABLE = "goldenrabbit01_sales_multi_unit"

# 1. DB 레코드 가져오기
print("DB 레코드 조회 중...")
result = subprocess.run(
    f'''ssh {SERVER} "cd /home/webapp/goldenrabbit/backend && source venv/bin/activate && python3 -c \\"
import psycopg2, json
from dotenv import load_dotenv
import os
load_dotenv('.env')
conn = psycopg2.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
cur = conn.cursor()
cur.execute('SELECT id, record_id, \\\\\\\\\\"지번 주소\\\\\\\\\\", \\\\\\\\\\"동\\\\\\\\\\", \\\\\\\\\\"호수\\\\\\\\\\" FROM \\\\\\\\\\"goldenrabbit01_sales_multi_unit\\\\\\\\\\" WHERE database_id = 38 ORDER BY id')
print(json.dumps(cur.fetchall(), ensure_ascii=False))
conn.close()
\\""''',
    shell=True, capture_output=True, text=True
)
db_records = json.loads(result.stdout.strip())
print(f"  {len(db_records)}건")

# 2. 구글드라이브 스캔
print("구글드라이브 스캔 중...")
addr_pat = re.compile(r'([가-힣]+동\d*)\s+(\d+(?:-\d+)?)')
folder_files = {}

for folder in os.listdir(GDRIVE_BASE):
    fp = os.path.join(GDRIVE_BASE, folder)
    if not os.path.isdir(fp): continue
    m = addr_pat.search(folder)
    if not m: continue
    key = (m.group(1), m.group(2))
    pdfs = []
    for root, _, files in os.walk(fp):
        for f in files:
            if '건축물' in f and f.lower().endswith('.pdf'):
                pdfs.append(os.path.join(root, f))
    if pdfs:
        folder_files.setdefault(key, []).extend(pdfs)

print(f"  건축물대장 있는 주소: {len(folder_files)}건")

# 3. 매칭
plan = []
for rec in db_records:
    rid, record_id, addr, dong, ho = rec
    m = re.search(r'([가-힣]+동\d*)\s+(\d+(?:-\d+)?)', addr)
    if not m: continue
    key = (m.group(1), m.group(2))
    if key in folder_files:
        plan.append({'id': rid, 'record_id': record_id, 'addr': addr, 'files': folder_files[key]})

print(f"  매칭: {len(plan)}건, 총 파일: {sum(len(p['files']) for p in plan)}개")

# 4. SCP 업로드 + JSON 생성
print("\n파일 업로드 시작...")
upload_data = []
for i, item in enumerate(plan):
    rid = item['id']
    remote_dir = f"{UPLOAD_BASE}/{DB_ID}/{rid}"
    subprocess.run(f'ssh {SERVER} "mkdir -p {remote_dir}"', shell=True, capture_output=True)

    files_info = []
    for filepath in item['files']:
        orig = os.path.basename(filepath)
        ext = orig.rsplit('.', 1)[-1].lower()
        safe = f"{uuid.uuid4().hex[:12]}.{ext}"
        remote = f"{remote_dir}/{safe}"
        rel = f"/uploads/propsheet/{DB_ID}/{rid}/{safe}"

        r = subprocess.run(f'scp "{filepath}" {SERVER}:"{remote}"', shell=True, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ERROR: {orig}")
            continue

        fsize = os.path.getsize(filepath)
        files_info.append({
            'original_name': orig,
            'safe_name': safe,
            'relative_path': rel,
            'file_size': fsize
        })

    if files_info:
        upload_data.append({'record_id': rid, 'files': files_info})
        print(f"  [{i+1}/{len(plan)}] id={rid} {item['addr']}: {len(files_info)}개 업로드")

# 5. JSON을 서버에 전송
print(f"\nDB 업데이트 중 ({len(upload_data)}건)...")
json_str = json.dumps(upload_data, ensure_ascii=False)
subprocess.run(f"ssh {SERVER} 'cat > /tmp/propsheet_upload.json'", shell=True, input=json_str, capture_output=True, text=True)

# 6. 서버에서 DB 업데이트
db_script = '''
import psycopg2, json
from dotenv import load_dotenv
import os
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
conn = psycopg2.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
cur = conn.cursor()
with open('/tmp/propsheet_upload.json', 'r') as f:
    data = json.load(f)
for item in data:
    rid = item['record_id']
    for f in item['files']:
        cur.execute(
            "INSERT INTO file_attachments (database_id, record_id, field_name, filename, original_filename, file_size, mime_type, file_path) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (38, rid, '건축물대장', f['safe_name'], f['original_name'], f['file_size'], 'application/pdf', f['relative_path'])
        )
    cell_parts = [ff['original_name'] + ' (' + ff['relative_path'] + ')' for ff in item['files']]
    cell_value = ', '.join(cell_parts)
    cur.execute('UPDATE "goldenrabbit01_sales_multi_unit" SET "건축물대장" = %s WHERE id = %s', (cell_value, rid))
conn.commit()
print(f'{len(data)}건 레코드 업데이트 완료')
conn.close()
'''

subprocess.run(f"ssh {SERVER} 'cat > /tmp/propsheet_db_update.py'", shell=True, input=db_script, capture_output=True, text=True)
r = subprocess.run(
    f'ssh {SERVER} "cd /home/webapp/goldenrabbit/backend && source venv/bin/activate && python3 /tmp/propsheet_db_update.py"',
    shell=True, capture_output=True, text=True
)
print(r.stdout.strip())
if r.stderr:
    print(f"STDERR: {r.stderr.strip()}")

print("\n완료!")
