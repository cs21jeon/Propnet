#!/usr/bin/env python3
import sys, os, json
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2.extras import RealDictCursor

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        for db_id, label in [(39, '원본 단일'), (53, '샘플 단일')]:
            cur.execute('SELECT COUNT(*) as cnt FROM field_definitions WHERE database_id = %s', (db_id,))
            print(f'\n=== {label} (DB {db_id}) ===')
            print(f'field_definitions: {cur.fetchone()["cnt"]}')

            # Check specific fields
            cur.execute("""
                SELECT field_name, field_type, select_options, display_order
                FROM field_definitions
                WHERE database_id = %s AND field_name IN ('현황','광고','종류')
                ORDER BY field_name
            """, (db_id,))
            for f in cur.fetchall():
                opts = f['select_options'][:3] if f['select_options'] else None
                print(f'  {f["field_name"]}: type={f["field_type"]}, opts={opts}, order={f["display_order"]}')

            # Views
            cur.execute('SELECT name, is_default, column_config FROM views WHERE database_id = %s', (db_id,))
            views = cur.fetchall()
            print(f'views: {len(views)}')
            for v in views:
                cc = v['column_config']
                cols = []
                if isinstance(cc, dict) and 'columns' in cc:
                    cols = cc['columns'][:5]
                elif isinstance(cc, list):
                    cols = cc[:5]
                print(f'  {v["name"]} (default={v["is_default"]}): first_cols={cols}')
