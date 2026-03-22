#!/usr/bin/env python3
"""Sync 용도지역 field_definition from DB39 to all other DBs that have the column"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2.extras import RealDictCursor, Json

SOURCE_DB = 39

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get source field_definition
        cur.execute("SELECT * FROM field_definitions WHERE database_id = %s AND field_name = '용도지역'", (SOURCE_DB,))
        src = cur.fetchone()
        if not src:
            print("Source not found!")
            exit(1)

        # Find all databases that have 용도지역 column
        cur.execute("""
            SELECT DISTINCT d.id, d.name, d.table_name
            FROM databases d
            JOIN information_schema.columns c ON c.table_name = d.table_name AND c.column_name = '용도지역'
            WHERE d.id != %s
            ORDER BY d.id
        """, (SOURCE_DB,))
        targets = cur.fetchall()

        for tgt in targets:
            db_id = tgt['id']
            cur.execute("""
                INSERT INTO field_definitions
                (database_id, field_name, display_name, field_type, formula, is_editable,
                 select_options, system_value_key, select_colors, number_format, date_format, api_key)
                VALUES (%s, '용도지역', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (database_id, field_name) DO UPDATE
                SET field_type = EXCLUDED.field_type,
                    select_options = EXCLUDED.select_options,
                    select_colors = EXCLUDED.select_colors,
                    display_name = EXCLUDED.display_name
            """, (
                db_id,
                src['display_name'] or '용도지역',
                src['field_type'],
                src['formula'],
                src['is_editable'],
                src['select_options'],
                src['system_value_key'],
                Json(src['select_colors']) if isinstance(src['select_colors'], dict) else src['select_colors'],
                Json(src['number_format']) if isinstance(src['number_format'], dict) else src['number_format'],
                Json(src['date_format']) if isinstance(src['date_format'], dict) else src['date_format'],
                src['api_key']
            ))
            print(f"  DB {db_id} ({tgt['name']}): synced")

        conn.commit()

print("\nDone!")
