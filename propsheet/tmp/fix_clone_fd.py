#!/usr/bin/env python3
"""Fix: Add clone_field_definitions_impl call to clone_database_full"""
path = '/home/webapp/goldenrabbit/backend/property-manager/services/workspace_service.py'
with open(path, 'r') as f:
    ws = f.read()

old = """                clone_database_table_impl(cursor, source_table, target_table, source_db_id, target_db_id)
                clone_database_views_impl(cursor, source_db_id, target_db_id)"""

new = """                clone_database_table_impl(cursor, source_table, target_table, source_db_id, target_db_id)
                clone_field_definitions_impl(cursor, source_db_id, target_db_id)
                clone_database_views_impl(cursor, source_db_id, target_db_id)"""

if old in ws:
    ws = ws.replace(old, new, 1)
    print("Added clone_field_definitions_impl to clone_database_full")
else:
    print("WARN: pattern not found")

with open(path, 'w') as f:
    f.write(ws)

# Now fix the existing sample DBs by copying field_definitions
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2.extras import RealDictCursor, Json

PAIRS = [(39, 53), (43, 54), (38, 55)]

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        for src, tgt in PAIRS:
            # Delete existing
            cur.execute("DELETE FROM field_definitions WHERE database_id = %s", (tgt,))

            # Copy
            cur.execute("""
                SELECT field_name, display_name, field_type, formula, select_options,
                       is_required, display_order, is_visible, is_editable, column_width,
                       system_value_key, select_colors, number_format, date_format, api_key
                FROM field_definitions WHERE database_id = %s
            """, (src,))
            defs = cur.fetchall()

            for fd in defs:
                sc = fd.get('select_colors')
                nf = fd.get('number_format')
                df = fd.get('date_format')
                cur.execute("""
                    INSERT INTO field_definitions
                    (database_id, field_name, display_name, field_type, formula, select_options,
                     is_required, display_order, is_visible, is_editable, column_width,
                     system_value_key, select_colors, number_format, date_format, api_key)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (tgt, fd['field_name'], fd['display_name'], fd['field_type'],
                      fd['formula'], fd['select_options'], fd['is_required'],
                      fd['display_order'], fd['is_visible'], fd['is_editable'],
                      fd['column_width'], fd['system_value_key'],
                      Json(sc) if isinstance(sc, dict) else sc,
                      Json(nf) if isinstance(nf, dict) else nf,
                      Json(df) if isinstance(df, dict) else df,
                      fd['api_key']))

            print(f"DB {src} -> {tgt}: copied {len(defs)} field_definitions")
        conn.commit()

print("Done!")
