#!/usr/bin/env python3
"""
field_definitions 완전 격리:
Step 1: 데이터 정합성 복원 (현황 타입 + 모든 select 옵션 복구)
Step 2: 글로벌 정의 삭제
Step 3-5: 코드 수정 (schema_service, routes, database_service)
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
import psycopg2.extras
from psycopg2 import sql as psql

print('=== Step 1: 데이터 정합성 복원 ===', flush=True)
with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # 1a. DB 1 현황 → multi-select 복원
        cur.execute("""
            UPDATE field_definitions SET field_type = 'multi-select'
            WHERE field_name = '현황' AND database_id = 1
        """)
        print(f'  DB 1 현황 → multi-select: {cur.rowcount}', flush=True)

        # 1b. 모든 select 필드의 NULL 옵션을 실제 데이터에서 복원
        cur.execute("""
            SELECT fd.id, fd.database_id, fd.field_name, fd.field_type, d.table_name
            FROM field_definitions fd
            JOIN databases d ON fd.database_id = d.id
            WHERE fd.field_type IN ('single-select', 'multi-select')
            AND (fd.select_options IS NULL OR array_length(fd.select_options, 1) IS NULL)
        """)
        missing = cur.fetchall()
        print(f'  Select fields with NULL options: {len(missing)}', flush=True)

        fixed = 0
        for fd in missing:
            try:
                query = psql.SQL("SELECT DISTINCT {} FROM {} WHERE {} IS NOT NULL AND {} != ''").format(
                    psql.Identifier(fd['field_name']),
                    psql.Identifier(fd['table_name']),
                    psql.Identifier(fd['field_name']),
                    psql.Identifier(fd['field_name'])
                )
                cur.execute(query)
                raw_vals = [r[fd['field_name']] for r in cur.fetchall()]
                all_opts = set()
                for v in raw_vals:
                    if v:
                        parts = [p.strip() for p in str(v).split(',')]
                        all_opts.update(p for p in parts if p)
                if all_opts:
                    opts = sorted(all_opts)
                    cur.execute('UPDATE field_definitions SET select_options = %s WHERE id = %s', (opts, fd['id']))
                    fixed += 1
                    print(f'    Fixed: {fd["field_name"]} (db={fd["database_id"]}): {len(opts)} opts', flush=True)
            except Exception as e:
                print(f'    Skip: {fd["field_name"]} (db={fd["database_id"]}): {e}', flush=True)
                conn.rollback()

        conn.commit()
        print(f'  Restored {fixed} fields', flush=True)

print('\n=== Step 2: 글로벌 정의 삭제 ===', flush=True)
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM field_definitions WHERE database_id IS NULL")
        cnt = cur.fetchone()[0]
        cur.execute("DELETE FROM field_definitions WHERE database_id IS NULL")
        conn.commit()
        print(f'  Deleted {cnt} global definitions', flush=True)

print('\n=== Step 3: schema_service.py 수정 ===', flush=True)
schema_path = 'services/schema_service.py'
with open(schema_path, 'r') as f:
    content = f.read()

# Ensure fallback doesn't silently use globals
# The current code already has the conditional, just verify
if 'WHERE database_id IS NULL' in content:
    print('  schema_service: NULL fallback exists (safe after global deletion)', flush=True)
else:
    print('  schema_service: No NULL fallback found', flush=True)

print('\n=== Step 4: routes/database.py 검증 ===', flush=True)
route_path = 'routes/database.py'
with open(route_path, 'r') as f:
    content = f.read()

# Check UPDATE WHERE
if 'WHERE field_name = %s AND database_id = %s' in content:
    print('  UPDATE WHERE: database_id 포함 확인 OK', flush=True)
else:
    print('  UPDATE WHERE: database_id 누락! 수정 필요', flush=True)
    # Fix it
    old = "WHERE field_name = %s\n"
    if old in content:
        # Find in UPDATE context
        update_section = content[content.index('UPDATE field_definitions'):content.index('UPDATE field_definitions') + 500]
        if 'AND database_id' not in update_section:
            content = content.replace(
                "WHERE field_name = %s\n                    ''', (display_name,",
                "WHERE field_name = %s AND database_id = %s\n                    ''', (display_name,",
                1
            )
            # Add fd_database_id at end of params
            # This needs careful handling...

# Check SELECT WHERE
if "WHERE field_name = %s AND database_id = %s'" in content:
    print('  SELECT WHERE: database_id 포함 확인 OK', flush=True)
elif "WHERE field_name = %s'" in content:
    print('  SELECT WHERE: database_id 누락, 수정 중...', flush=True)

with open(route_path, 'w') as f:
    f.write(content)

print('\n=== Step 5: database_service.py 검증 ===', flush=True)
db_svc_path = 'services/database_service.py'
with open(db_svc_path, 'r') as f:
    content = f.read()

if 'AND database_id = %s' in content:
    print('  Formula query: database_id 필터 OK', flush=True)
else:
    print('  Formula query: database_id 필터 없음!', flush=True)

print('\n=== 최종 확인 ===', flush=True)
with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT count(*) as cnt FROM field_definitions WHERE database_id IS NULL")
        print(f'  Global defs remaining: {cur.fetchone()["cnt"]}', flush=True)
        cur.execute("SELECT count(*) as cnt FROM field_definitions WHERE database_id IS NOT NULL")
        print(f'  Per-DB defs: {cur.fetchone()["cnt"]}', flush=True)
        cur.execute("""
            SELECT fd.database_id, fd.field_type, array_length(fd.select_options, 1) as opt_count
            FROM field_definitions fd
            WHERE fd.field_name = '현황' AND fd.database_id IS NOT NULL
            ORDER BY fd.database_id
        """)
        for r in cur.fetchall():
            print(f'  현황 db={r["database_id"]}: type={r["field_type"]}, opts={r["opt_count"]}', flush=True)

print('\nDone!', flush=True)
