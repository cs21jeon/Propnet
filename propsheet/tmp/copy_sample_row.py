#!/usr/bin/env python3
"""Copy first row from 금토끼부동산 DBs to 샘플워크스페이스 DBs"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from services.record_id_service import ensure_unique_record_id
from psycopg2 import sql as psql
import re

SKIP_COLS = {'id', 'created_at', 'updated_at', 'fields_hash', 'synced_at', 'database_id', 'record_id'}

# Source (금토끼부동산 ws=11) → Target (샘플 ws=12)
PAIRS = [
    ('goldenrabbit01_sales_building', 39, 'template_sales_building', 51),    # 단일
    ('sales_building_copy', 43, 'template_sales_building_copy', 52),          # 부분
    ('goldenrabbit01_sales_multi_unit', 38, 'template_sales_multi_unit', 50), # 집합
]

with get_db_connection() as conn:
    with conn.cursor() as cur:
        for src_table, src_db_id, tgt_table, tgt_db_id in PAIRS:
            print(f"\n=== {src_table} → {tgt_table} ===")

            # 1. Get source columns
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at')
                ORDER BY ordinal_position
            """, (src_table,))
            src_cols = [r[0] for r in cur.fetchall()]

            # 2. Get target columns
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at')
                ORDER BY ordinal_position
            """, (tgt_table,))
            tgt_cols = set(r[0] for r in cur.fetchall())

            # 3. Add missing columns to target
            added = []
            for col in src_cols:
                if col in SKIP_COLS:
                    continue
                if col not in tgt_cols:
                    # Get type from source
                    cur.execute("""
                        SELECT data_type FROM information_schema.columns
                        WHERE table_name = %s AND column_name = %s
                    """, (src_table, col))
                    dtype = cur.fetchone()
                    if dtype:
                        type_map = {
                            'character varying': 'VARCHAR',
                            'text': 'TEXT',
                            'numeric': 'NUMERIC',
                            'integer': 'INTEGER',
                            'bigint': 'BIGINT',
                            'date': 'DATE',
                            'timestamp without time zone': 'TIMESTAMP',
                        }
                        pg_type = type_map.get(dtype[0], 'TEXT')
                        cur.execute(psql.SQL('ALTER TABLE {} ADD COLUMN {} {}').format(
                            psql.Identifier(tgt_table),
                            psql.Identifier(col),
                            psql.SQL(pg_type)))
                        added.append(col)
            if added:
                conn.commit()
                print(f"  Added {len(added)} columns: {added[:5]}...")

            # 4. Clear target table
            cur.execute(psql.SQL('DELETE FROM {}').format(psql.Identifier(tgt_table)))
            print(f"  Cleared {cur.rowcount} rows")

            # 5. Get first row from source (by id ASC)
            cur.execute(psql.SQL('SELECT id FROM {} ORDER BY id LIMIT 1').format(
                psql.Identifier(src_table)))
            first = cur.fetchone()
            if not first:
                print("  No source data!")
                conn.commit()
                continue
            first_id = first[0]

            # 6. Get common columns (in source order)
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at')
                ORDER BY ordinal_position
            """, (tgt_table,))
            tgt_cols_now = set(r[0] for r in cur.fetchall())

            copy_cols = [c for c in src_cols if c not in SKIP_COLS and c in tgt_cols_now]

            # 7. Copy first row
            insert_cols = [psql.Identifier('database_id')] + [psql.Identifier(c) for c in copy_cols]
            select_parts = [psql.Literal(tgt_db_id)] + [psql.Identifier(c) for c in copy_cols]

            query = psql.SQL('INSERT INTO {} ({}) SELECT {} FROM {} WHERE id = {}').format(
                psql.Identifier(tgt_table),
                psql.SQL(', ').join(insert_cols),
                psql.SQL(', ').join(select_parts),
                psql.Identifier(src_table),
                psql.Literal(first_id))
            cur.execute(query)
            print(f"  Copied 1 row (source id={first_id})")

            # 8. Generate record_id
            cur.execute(psql.SQL('SELECT id FROM {} WHERE record_id IS NULL').format(
                psql.Identifier(tgt_table)))
            for row in cur.fetchall():
                rec_id = ensure_unique_record_id(tgt_table)
                cur.execute(psql.SQL('UPDATE {} SET record_id = %s WHERE id = %s').format(
                    psql.Identifier(tgt_table)), (rec_id, row[0]))

            conn.commit()
            print(f"  Done!")

        # 9. Copy field_definitions order (column_order from views)
        # Also sync field_definitions from source to target for any new columns
        for src_db_id, tgt_db_id in [(39, 51), (43, 52), (38, 50)]:
            cur.execute("""
                SELECT field_name, display_name, field_type, formula, is_editable,
                       select_options, system_value_key, select_colors, number_format, date_format, api_key, display_order
                FROM field_definitions WHERE database_id = %s
            """, (src_db_id,))
            from psycopg2.extras import RealDictCursor, Json
            # Re-query with dict cursor
            pass

        conn.commit()

print("\nAll done!")
