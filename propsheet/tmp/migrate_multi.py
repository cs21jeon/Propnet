#!/usr/bin/env python3
"""
Migrate 공동주택 매물(DB16, sales_multi_unit) → 집합부동산(DB38, goldenrabbit01_sales_multi_unit)
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from services.record_id_service import ensure_unique_record_id
from psycopg2 import sql as psql
from psycopg2.extras import RealDictCursor, Json

SOURCE_TABLE = 'sales_multi_unit'
TARGET_TABLE = 'goldenrabbit01_sales_multi_unit'
SOURCE_DB_ID = 16
TARGET_DB_ID = 38

SKIP_COLS = {'id', 'created_at', 'updated_at', 'fields_hash', 'synced_at', 'database_id', 'record_id'}

type_map = {
    'character varying': 'VARCHAR',
    'text': 'TEXT',
    'numeric': 'NUMERIC',
    'integer': 'INTEGER',
    'bigint': 'BIGINT',
    'date': 'DATE',
    'timestamp without time zone': 'TIMESTAMP',
}

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Step 1: Get source columns
        cur.execute("""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at')
            ORDER BY ordinal_position
        """, (SOURCE_TABLE,))
        source_cols = {r['column_name']: r['data_type'] for r in cur.fetchall()}

        # Step 2: Get target columns
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at')
            ORDER BY ordinal_position
        """, (TARGET_TABLE,))
        target_cols = {r['column_name'] for r in cur.fetchall()}

        # Step 3: Add missing columns
        added_cols = []
        for col_name, data_type in source_cols.items():
            if col_name in SKIP_COLS:
                continue
            if col_name not in target_cols:
                pg_type = type_map.get(data_type, 'TEXT')
                cur.execute(psql.SQL('ALTER TABLE {} ADD COLUMN {} {}').format(
                    psql.Identifier(TARGET_TABLE),
                    psql.Identifier(col_name),
                    psql.SQL(pg_type)))
                added_cols.append(col_name)
        conn.commit()
        print(f"1. Added {len(added_cols)} columns: {added_cols}")

        # Step 4: Delete existing rows
        cur.execute(psql.SQL('DELETE FROM {}').format(psql.Identifier(TARGET_TABLE)))
        print(f"2. Deleted {cur.rowcount} existing rows")

        # Step 5: Get copyable columns
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at','database_id','record_id')
            ORDER BY ordinal_position
        """, (TARGET_TABLE,))
        target_cols_final = {r['column_name'] for r in cur.fetchall()}
        copy_cols = [c for c in source_cols if c not in SKIP_COLS and c in target_cols_final]
        print(f"3. {len(copy_cols)} columns to copy")

        # Step 6: Copy data
        insert_cols = [psql.Identifier('database_id')] + [psql.Identifier(c) for c in copy_cols]
        select_parts = [psql.Literal(TARGET_DB_ID)] + [psql.Identifier(c) for c in copy_cols]

        query = psql.SQL('INSERT INTO {} ({}) SELECT {} FROM {}').format(
            psql.Identifier(TARGET_TABLE),
            psql.SQL(', ').join(insert_cols),
            psql.SQL(', ').join(select_parts),
            psql.Identifier(SOURCE_TABLE))
        cur.execute(query)
        print(f"4. Inserted {cur.rowcount} rows")
        conn.commit()

    # Step 7: Generate record_ids
    with conn.cursor() as cur:
        cur.execute(f'SELECT id FROM "{TARGET_TABLE}" WHERE record_id IS NULL ORDER BY id')
        ids = [r[0] for r in cur.fetchall()]
        for row_id in ids:
            rec_id = ensure_unique_record_id(TARGET_TABLE)
            cur.execute(f'UPDATE "{TARGET_TABLE}" SET record_id = %s WHERE id = %s', (rec_id, row_id))
        conn.commit()
        print(f"5. Generated {len(ids)} record_ids")

    # Step 8: Copy field_definitions
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        copied = 0
        for col_name in added_cols:
            cur.execute("""
                SELECT field_name, display_name, field_type, formula, is_editable,
                       select_options, system_value_key, select_colors, number_format, date_format, api_key
                FROM field_definitions WHERE database_id = %s AND field_name = %s
            """, (SOURCE_DB_ID, col_name))
            fd = cur.fetchone()
            if fd:
                cur.execute("""
                    INSERT INTO field_definitions
                    (database_id, field_name, display_name, field_type, formula, is_editable,
                     select_options, system_value_key, select_colors, number_format, date_format, api_key)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (database_id, field_name) DO UPDATE
                    SET display_name = EXCLUDED.display_name, field_type = EXCLUDED.field_type
                """, (TARGET_DB_ID, fd['field_name'], fd['display_name'], fd['field_type'],
                      fd['formula'], fd['is_editable'], fd['select_options'], fd['system_value_key'],
                      Json(fd['select_colors']) if isinstance(fd['select_colors'], dict) else fd['select_colors'],
                      Json(fd['number_format']) if isinstance(fd['number_format'], dict) else fd['number_format'],
                      Json(fd['date_format']) if isinstance(fd['date_format'], dict) else fd['date_format'],
                      fd['api_key']))
                copied += 1
        conn.commit()
        print(f"6. Copied {copied} field_definitions")

    # Step 9: Trigger regeneration
    with conn.cursor() as cur:
        cur.execute(f'UPDATE "{TARGET_TABLE}" SET "위반건축물" = "위반건축물"')
        print(f"7. Triggered update on {cur.rowcount} rows")
        conn.commit()

    # Verify
    with conn.cursor() as cur:
        cur.execute(f'SELECT COUNT(*) FROM "{SOURCE_TABLE}"')
        print(f"\nSource (공동주택): {cur.fetchone()[0]} rows (unchanged)")
        cur.execute(f'SELECT COUNT(*) FROM "{TARGET_TABLE}"')
        print(f"Target (집합부동산): {cur.fetchone()[0]} rows")

print("Done!")
