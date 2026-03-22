#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2.extras import RealDictCursor

CHECKS = [
    (39, 56, '단일부동산'),
    (43, 57, '부분부동산'),
    (38, 58, '집합부동산'),
]

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        all_ok = True
        for src, tgt, name in CHECKS:
            print(f"\n=== {name} (DB {src} → {tgt}) ===")

            # field_definitions count
            cur.execute("SELECT COUNT(*) as cnt FROM field_definitions WHERE database_id = %s", (src,))
            src_fd = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM field_definitions WHERE database_id = %s", (tgt,))
            tgt_fd = cur.fetchone()['cnt']
            ok = '✓' if src_fd == tgt_fd else '✗'
            if src_fd != tgt_fd: all_ok = False
            print(f"  {ok} field_definitions: {src_fd} → {tgt_fd}")

            # Check specific field types
            for field in ['현황', '광고', '종류']:
                cur.execute("SELECT field_type, select_options FROM field_definitions WHERE database_id = %s AND field_name = %s", (src, field))
                s = cur.fetchone()
                cur.execute("SELECT field_type, select_options FROM field_definitions WHERE database_id = %s AND field_name = %s", (tgt, field))
                t = cur.fetchone()
                if s and t:
                    ok = '✓' if s['field_type'] == t['field_type'] else '✗'
                    if s['field_type'] != t['field_type']: all_ok = False
                    print(f"  {ok} {field}: {s['field_type']} → {t['field_type']}, opts={t['select_options'] is not None}")
                elif s and not t:
                    print(f"  ✗ {field}: source has, target MISSING")
                    all_ok = False

            # Views
            cur.execute("SELECT COUNT(*) as cnt FROM views WHERE database_id = %s", (src,))
            src_v = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM views WHERE database_id = %s", (tgt,))
            tgt_v = cur.fetchone()['cnt']
            ok = '✓' if src_v == tgt_v else '✗'
            if src_v != tgt_v: all_ok = False
            print(f"  {ok} views: {src_v} → {tgt_v}")

            # View column order
            cur.execute("SELECT column_config FROM views WHERE database_id = %s AND is_default = true", (tgt,))
            v = cur.fetchone()
            if v and v['column_config']:
                cc = v['column_config']
                cols = cc.get('columns', [])[:5] if isinstance(cc, dict) else cc[:5]
                print(f"  기본뷰 첫 5컬럼: {cols}")

            # Row count
            cur.execute("SELECT table_name FROM databases WHERE id = %s", (tgt,))
            tbl = cur.fetchone()['table_name']
            cur.execute(f'SELECT COUNT(*) as cnt FROM "{tbl}"')
            rows = cur.fetchone()['cnt']
            ok = '✓' if rows == 1 else '✗'
            if rows != 1: all_ok = False
            print(f"  {ok} rows: {rows}")

        print(f"\n{'=== ALL OK ===' if all_ok else '=== ISSUES FOUND ==='}")
