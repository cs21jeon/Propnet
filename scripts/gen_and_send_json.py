#!/usr/bin/env python3
"""서버 업로드 디렉토리의 파일과 원본 파일명을 매칭하여 JSON 생성 후 서버에 전송"""
import os, re, json, subprocess, hashlib

GDRIVE_BASE = "G:/내 드라이브/금토끼부동산중개/빌라매물"
SERVER = "root@175.119.224.71"
DB_ID = 38

# DB 레코드
with open(os.path.expanduser('~/AppData/Local/Temp/jibhap_records.json'), 'r', encoding='utf-8') as f:
    db_records = json.load(f)

# 구글드라이브 파일 -> 크기로 매핑 (크기+확장자로 원본 파일명 역추적)
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
                full = os.path.join(root, f)
                fsize = os.path.getsize(full)
                pdfs.append({'path': full, 'name': f, 'size': fsize})
    if pdfs:
        folder_files.setdefault(key, []).extend(pdfs)

# 매칭
plan = []
for rec in db_records:
    rid, record_id, addr, dong, ho = rec
    m = re.search(r'([가-힣]+동\d*)\s+(\d+(?:-\d+)?)', addr or '')
    if not m: continue
    key = (m.group(1), m.group(2))
    if key in folder_files:
        plan.append({'id': rid, 'files': folder_files[key]})

# 서버 파일 목록 조회
result = subprocess.run(
    f'ssh {SERVER} "find /home/webapp/goldenrabbit/uploads/propsheet/38/ -name \'*.pdf\' -printf \'%p %s\\n\'"',
    shell=True, capture_output=True, text=True
)

# 파싱: /uploads/propsheet/38/{record_id}/{safe_name}.pdf size
server_files = {}  # (record_id, size) -> safe_name
for line in result.stdout.strip().split('\n'):
    if not line.strip(): continue
    parts = line.rsplit(' ', 1)
    if len(parts) != 2: continue
    path, size = parts[0], int(parts[1])
    # path: /home/webapp/goldenrabbit/uploads/propsheet/38/87/abc123def456.pdf
    segs = path.split('/')
    rid_str = segs[-2]
    safe_name = segs[-1]
    server_files.setdefault(int(rid_str), []).append({'safe': safe_name, 'size': size})

# 매칭: record_id + file_size로 원본 파일명 연결
upload_data = []
for item in plan:
    rid = item['id']
    if rid not in server_files:
        continue

    srv_files = server_files[rid]
    local_files = item['files']

    matched = []
    used_srv = set()
    for lf in local_files:
        for j, sf in enumerate(srv_files):
            if j in used_srv: continue
            if lf['size'] == sf['size']:
                rel = f"/uploads/propsheet/{DB_ID}/{rid}/{sf['safe']}"
                matched.append({
                    'original_name': lf['name'],
                    'safe_name': sf['safe'],
                    'relative_path': rel,
                    'file_size': lf['size']
                })
                used_srv.add(j)
                break

    if matched:
        upload_data.append({'record_id': rid, 'files': matched})
        print(f"id={rid}: {len(matched)}개 매칭")

# JSON 저장 및 전송
json_path = os.path.expanduser('~/AppData/Local/Temp/propsheet_upload.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(upload_data, f, ensure_ascii=False, indent=2)

print(f"\nJSON 생성: {len(upload_data)}건, 총 {sum(len(x['files']) for x in upload_data)}개 파일")

# SCP로 서버에 전송
r = subprocess.run(f'scp "{json_path}" {SERVER}:/tmp/propsheet_upload.json', shell=True, capture_output=True, text=True)
if r.returncode == 0:
    print("JSON 서버 전송 완료")
else:
    print(f"전송 실패: {r.stderr}")
