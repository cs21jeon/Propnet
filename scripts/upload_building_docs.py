#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
건축물대장 PDF 파일을 구글드라이브에서 찾아 PropSheet 집합부동산 DB에 업로드
"""

import os
import re
import json
import subprocess
import uuid
from collections import defaultdict

# === 설정 ===
GDRIVE_BASE = "G:/내 드라이브/금토끼부동산중개/빌라매물"
SERVER = "root@175.119.224.71"
UPLOAD_BASE = "/home/webapp/goldenrabbit/uploads/propsheet"
DB_ID = 38  # 집합부동산
TABLE_NAME = "goldenrabbit01_sales_multi_unit"

# === DB 레코드 조회 ===
def get_db_records():
    """서버에서 집합부동산 레코드 조회"""
    cmd = f'''ssh {SERVER} "cd /home/webapp/goldenrabbit/backend && source venv/bin/activate && python3 -c \\"
import psycopg2, json
from dotenv import load_dotenv
import os
load_dotenv('.env')
conn = psycopg2.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
cur = conn.cursor()
cur.execute('SELECT id, record_id, \\\\\\\\\\"지번 주소\\\\\\\\\\", \\\\\\\\\\"동\\\\\\\\\\", \\\\\\\\\\"호수\\\\\\\\\\" FROM \\\\\\\\\\"{TABLE_NAME}\\\\\\\\\\" WHERE database_id = {DB_ID} ORDER BY id')
rows = cur.fetchall()
print(json.dumps(rows, ensure_ascii=False))
conn.close()
\\""'''
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def extract_dong_bunji(addr):
    """주소에서 동+번지 추출"""
    m = re.search(r'([가-힣]+동\d*)\s+(\d+(?:-\d+)?)', addr)
    if m:
        return m.group(1), m.group(2)
    return None, None


def find_building_docs():
    """구글드라이브 폴더에서 건축물대장 PDF 파일 검색"""
    addr_pattern = re.compile(r'([가-힣]+동\d*)\s+(\d+(?:-\d+)?)')
    folder_files = {}  # (dong, bunji) -> [file_paths]

    for folder in os.listdir(GDRIVE_BASE):
        folder_path = os.path.join(GDRIVE_BASE, folder)
        if not os.path.isdir(folder_path):
            continue

        m = addr_pattern.search(folder)
        if not m:
            continue

        dong, bunji = m.group(1), m.group(2)
        key = (dong, bunji)

        bldg_files = []
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                if '건축물' in f and f.lower().endswith('.pdf'):
                    bldg_files.append(os.path.join(root, f))

        if bldg_files:
            if key not in folder_files:
                folder_files[key] = []
            folder_files[key].extend(bldg_files)

    return folder_files


def build_upload_plan(db_records, folder_files):
    """DB 레코드와 폴더 파일 매칭"""
    plan = []

    for rec_id_num, record_id, addr, dong, ho in db_records:
        d_dong, d_bunji = extract_dong_bunji(addr)
        if not d_dong:
            continue

        key = (d_dong, d_bunji)
        if key in folder_files:
            plan.append({
                'id': rec_id_num,
                'record_id': record_id,
                'addr': addr,
                'dong': dong,
                'ho': ho,
                'files': folder_files[key]
            })

    return plan


def upload_files(plan):
    """파일 업로드 및 DB 업데이트"""
    total = len(plan)
    for i, item in enumerate(plan):
        rec_id = item['id']
        record_id = item['record_id']
        addr = item['addr']
        files = item['files']

        print(f"\n[{i+1}/{total}] id={rec_id} {addr} ({len(files)}개 파일)")

        # 서버에 디렉토리 생성
        remote_dir = f"{UPLOAD_BASE}/{DB_ID}/{rec_id}"
        subprocess.run(
            f'ssh {SERVER} "mkdir -p {remote_dir}"',
            shell=True, capture_output=True
        )

        uploaded = []
        for filepath in files:
            original_name = os.path.basename(filepath)
            ext = original_name.rsplit('.', 1)[-1].lower()
            safe_name = f"{uuid.uuid4().hex[:12]}.{ext}"
            remote_path = f"{remote_dir}/{safe_name}"
            relative_path = f"/uploads/propsheet/{DB_ID}/{rec_id}/{safe_name}"

            # SCP 업로드
            scp_cmd = f'scp "{filepath}" {SERVER}:"{remote_path}"'
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  ERROR uploading {original_name}: {result.stderr}")
                continue

            file_size = os.path.getsize(filepath)
            uploaded.append({
                'original_name': original_name,
                'safe_name': safe_name,
                'relative_path': relative_path,
                'file_size': file_size,
            })
            print(f"  -> {original_name}")

        if not uploaded:
            continue

        # DB 업데이트: file_attachments 삽입 + 건축물대장 셀 값 갱신
        inserts = []
        cell_parts = []
        for f in uploaded:
            inserts.append(
                f"INSERT INTO file_attachments (database_id, record_id, field_name, filename, original_filename, file_size, mime_type, file_path) "
                f"VALUES ({DB_ID}, {rec_id}, '건축물대장', '{f['safe_name']}', '{f['original_name'].replace(chr(39), chr(39)+chr(39))}', {f['file_size']}, 'application/pdf', '{f['relative_path']}');"
            )
            escaped_name = f['original_name'].replace("'", "''")
            cell_parts.append(f"{escaped_name} ({f['relative_path']})")

        cell_value = ", ".join(cell_parts).replace("'", "''")

        sql = " ".join(inserts) + f' UPDATE "{TABLE_NAME}" SET "건축물대장" = \'{cell_value}\' WHERE id = {rec_id};'

        sql_cmd = f'''ssh {SERVER} "cd /home/webapp/goldenrabbit/backend && source venv/bin/activate && python3 -c \\"
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv('.env')
conn = psycopg2.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
cur = conn.cursor()
cur.execute(\\\\\\"\\"\\"\\"DELETE FROM file_attachments WHERE database_id = {DB_ID} AND record_id = {rec_id} AND field_name = '건축물대장'\\\\\\"\\"\\"\\"\\")
cur.execute(\\\\\\"\\"\\"\\"UPDATE \\\\\\\\\\\\\\\"{TABLE_NAME}\\\\\\\\\\\\\\\\" SET \\\\\\\\\\\\\\\\"건축물대장\\\\\\\\\\\\\\\\" = NULL WHERE id = {rec_id}\\\\\\"\\"\\"\\"\\")
conn.commit()
conn.close()
print('cleared')
\\""'''

        # This is getting too complex with escaping. Use a different approach.
        print(f"  DB 업데이트 중...")


def clear_and_upload(plan):
    """더 안전한 방법: 서버에 Python 스크립트를 만들어 실행"""
    # 업로드 계획을 JSON으로 서버에 전송
    upload_data = []

    for item in plan:
        rec_id = item['id']
        files_info = []

        remote_dir = f"{UPLOAD_BASE}/{DB_ID}/{rec_id}"
        subprocess.run(f'ssh {SERVER} "mkdir -p {remote_dir}"', shell=True, capture_output=True)

        for filepath in item['files']:
            original_name = os.path.basename(filepath)
            ext = original_name.rsplit('.', 1)[-1].lower()
            safe_name = f"{uuid.uuid4().hex[:12]}.{ext}"
            remote_path = f"{remote_dir}/{safe_name}"
            relative_path = f"/uploads/propsheet/{DB_ID}/{rec_id}/{safe_name}"

            # SCP
            scp_cmd = f'scp "{filepath}" {SERVER}:"{remote_path}"'
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  ERROR: {original_name}: {result.stderr.strip()}")
                continue

            file_size = os.path.getsize(filepath)
            files_info.append({
                'original_name': original_name,
                'safe_name': safe_name,
                'relative_path': relative_path,
                'file_size': file_size,
            })
            print(f"  [{item['addr']}] {original_name}")

        if files_info:
            upload_data.append({
                'record_id': rec_id,
                'files': files_info
            })

    # JSON을 서버에 전송
    json_str = json.dumps(upload_data, ensure_ascii=False)
    json_path = "/tmp/propsheet_upload.json"

    # Write JSON to server
    proc = subprocess.run(
        f"ssh {SERVER} 'cat > {json_path}'",
        shell=True, input=json_str, capture_output=True, text=True
    )

    # Run DB update script on server
    server_script = f'''
import psycopg2, json
from dotenv import load_dotenv
import os
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
conn = psycopg2.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
cur = conn.cursor()

with open('{json_path}', 'r') as f:
    data = json.load(f)

DB_ID = {DB_ID}
TABLE = '{TABLE_NAME}'

# 1. 기존 건축물대장 필드 전체 클리어
cur.execute(f'UPDATE "{{TABLE}}" SET "건축물대장" = NULL WHERE database_id = %s', (DB_ID,))
cur.execute('DELETE FROM file_attachments WHERE database_id = %s AND field_name = %s', (DB_ID, '건축물대장'))
print(f"기존 데이터 클리어 완료")

# 2. 새 파일 메타데이터 삽입 + 셀 값 갱신
for item in data:
    rec_id = item['record_id']
    files = item['files']

    for f in files:
        cur.execute(
            "INSERT INTO file_attachments (database_id, record_id, field_name, filename, original_filename, file_size, mime_type, file_path) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (DB_ID, rec_id, '건축물대장', f['safe_name'], f['original_name'], f['file_size'], 'application/pdf', f['relative_path'])
        )

    cell_parts = [f"{{f['original_name']}} ({{f['relative_path']}})" for f in files]
    cell_value = ', '.join(cell_parts)
    cur.execute(f'UPDATE "{{TABLE}}" SET "건축물대장" = %s WHERE id = %s', (cell_value, rec_id))
    print(f"  id={{rec_id}}: {{len(files)}}개 파일 등록")

conn.commit()
print(f"완료: {{len(data)}}건 레코드 업데이트")
conn.close()
'''

    # Write and execute server script
    script_path = "/tmp/propsheet_db_update.py"
    proc = subprocess.run(
        f"ssh {SERVER} 'cat > {script_path}'",
        shell=True, input=server_script, capture_output=True, text=True
    )

    result = subprocess.run(
        f'ssh {SERVER} "cd /home/webapp/goldenrabbit/backend && source venv/bin/activate && python3 {script_path}"',
        shell=True, capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr}")


if __name__ == '__main__':
    print("=== 1. DB 레코드 조회 ===")
    records = get_db_records()
    print(f"집합부동산 레코드: {len(records)}건")

    print("\n=== 2. 구글드라이브 건축물대장 파일 검색 ===")
    folder_files = find_building_docs()
    print(f"건축물대장 파일이 있는 주소: {len(folder_files)}건")

    print("\n=== 3. 매칭 ===")
    plan = build_upload_plan(records, folder_files)
    print(f"매칭된 레코드: {len(plan)}건")
    total_files = sum(len(p['files']) for p in plan)
    print(f"총 업로드 파일: {total_files}건")

    print("\n=== 4. 업로드 미리보기 ===")
    for p in plan:
        print(f"  id={p['id']} | {p['addr']} | 동={p['dong']} | 호={p['ho']} | 파일 {len(p['files'])}개")

    confirm = input(f"\n{len(plan)}건 레코드에 {total_files}개 파일을 업로드하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("취소됨")
        exit()

    print("\n=== 5. 파일 업로드 + DB 업데이트 ===")
    clear_and_upload(plan)
    print("\n완료!")
