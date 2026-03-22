#!/usr/bin/env python3
"""Restore select_options from actual data for all select fields with NULL options"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
import psycopg2.extras
from psycopg2 import sql

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT fd.id, fd.database_id, fd.field_name, fd.field_type, d.table_name
            FROM field_definitions fd
            JOIN databases d ON fd.database_id = d.id
            WHERE fd.field_type IN ('single-select', 'multi-select')
            AND (fd.select_options IS NULL OR array_length(fd.select_options, 1) IS NULL)
        """)
        missing = cur.fetchall()
        print(f'Select fields with NULL options: {len(missing)}', flush=True)

        fixed = 0
        for fd in missing:
            table = fd['table_name']
            fname = fd['field_name']
            try:
                query = sql.SQL("SELECT DISTINCT {} FROM {} WHERE {} IS NOT NULL AND {} != ''").format(
                    sql.Identifier(fname),
                    sql.Identifier(table),
                    sql.Identifier(fname),
                    sql.Identifier(fname)
                )
                cur.execute(query)
                raw_vals = [r[fname] for r in cur.fetchall()]
                all_opts = set()
                for v in raw_vals:
                    if v:
                        parts = [p.strip() for p in str(v).split(',')]
                        all_opts.update(p for p in parts if p)
                if all_opts:
                    opts = sorted(all_opts)
                    cur.execute('UPDATE field_definitions SET select_options = %s WHERE id = %s', (opts, fd['id']))
                    fixed += 1
                    print(f'  Fixed: {fname} (db={fd["database_id"]}): {opts}', flush=True)
                else:
                    print(f'  Empty: {fname} (db={fd["database_id"]})', flush=True)
            except Exception as e:
                print(f'  Skip: {fname} (db={fd["database_id"]}): {e}', flush=True)
                conn.rollback()

        conn.commit()
        print(f'Fixed {fixed} fields', flush=True)
