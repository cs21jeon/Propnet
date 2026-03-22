#!/usr/bin/env python3
"""
Migrate 건물매물(DB1, sales_building) → 단일부동산(DB39, goldenrabbit01_sales_building)
- Copy data (don't move — keep original)
- Add missing columns to target
- Delete existing 1 row in target
- Copy field_definitions for new columns
- Re-generate record_ids
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from services.record_id_service import ensure_unique_record_id
from psycopg2 import sql as psql
import psycopg2.extras

SOURCE_TABLE = 'sales_building'
TARGET_TABLE = 'goldenrabbit01_sales_building'
SOURCE_DB_ID = 1
TARGET_DB_ID = 39

# System columns to skip
SKIP_COLS = {'id', 'created_at', 'updated_at', 'fields_hash', 'synced_at', 'database_id', 'record_id'}

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Step 1: Get source columns
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at')
            ORDER BY ordinal_position
        """, (SOURCE_TABLE,))
        source_cols = {r['column_name']: r for r in cur.fetchall()}
        print(f"Source: {len(source_cols)} columns")

        # Step 2: Get target columns
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at')
            ORDER BY ordinal_position
        """, (TARGET_TABLE,))
        target_cols = {r['column_name'] for r in cur.fetchall()}
        print(f"Target: {len(target_cols)} columns")

        # Step 3: Add missing columns to target
        type_map = {
            'character varying': 'VARCHAR',
            'text': 'TEXT',
            'numeric': 'NUMERIC',
            'integer': 'INTEGER',
            'bigint': 'BIGINT',
            'date': 'DATE',
            'timestamp without time zone': 'TIMESTAMP',
        }
        added_cols = []
        for col_name, col_info in source_cols.items():
            if col_name in SKIP_COLS:
                continue
            if col_name not in target_cols:
                pg_type = type_map.get(col_info['data_type'], 'TEXT')
                cur.execute(psql.SQL('ALTER TABLE {} ADD COLUMN {} {}').format(
                    psql.Identifier(TARGET_TABLE),
                    psql.Identifier(col_name),
                    psql.SQL(pg_type)
                ))
                added_cols.append(col_name)
        conn.commit()
        print(f"Step 3: Added {len(added_cols)} columns: {added_cols}")

        # Step 4: Delete existing rows in target
        cur.execute(psql.SQL('DELETE FROM {}').format(psql.Identifier(TARGET_TABLE)))
        print(f"Step 4: Deleted {cur.rowcount} existing rows from target")

        # Step 5: Get data columns to copy (intersection of source cols and target cols after additions)
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at')
            ORDER BY ordinal_position
        """, (TARGET_TABLE,))
        target_cols_final = [r['column_name'] for r in cur.fetchall()]

        # Columns that exist in both source and target (excluding database_id, record_id)
        copy_cols = [c for c in target_cols_final if c in source_cols and c not in ('database_id', 'record_id')]
        print(f"Step 5: {len(copy_cols)} columns to copy")

        # Step 6: Copy data with new database_id and record_id
        col_ids = [psql.Identifier(c) for c in copy_cols]
        cols_sql = psql.SQL(', ').join(col_ids)

        # Build SELECT: copy columns from source, replace database_id with target
        select_parts = []
        insert_cols = [psql.Identifier('database_id')]
        for c in copy_cols:
            insert_cols.append(psql.Identifier(c))
            select_parts.append(psql.Identifier(c))

        insert_sql = psql.SQL(', ').join(insert_cols)
        select_sql = psql.SQL(', ').join([psql.Literal(TARGET_DB_ID)] + select_parts)

        query = psql.SQL('INSERT INTO {} ({}) SELECT {} FROM {} RETURNING id').format(
            psql.Identifier(TARGET_TABLE),
            insert_sql,
            select_sql,
            psql.Identifier(SOURCE_TABLE)
        )
        cur.execute(query)
        new_ids = [r['id'] for r in cur.fetchall()]
        print(f"Step 6: Copied {len(new_ids)} rows")

        # Step 7: Generate unique record_ids for all copied rows
        for row_id in new_ids:
            rec_id = ensure_unique_record_id(TARGET_TABLE)
            cur.execute(psql.SQL('UPDATE {} SET record_id = %s WHERE id = %s').format(
                psql.Identifier(TARGET_TABLE)), (rec_id, row_id))
        print(f"Step 7: Generated {len(new_ids)} record_ids")

        # Step 8: Copy field_definitions for added columns (from DB1 to DB39)
        for col_name in added_cols:
            cur.execute("""
                SELECT field_name, display_name, field_type, formula, is_editable,
                       select_options, system_value_key, select_colors, number_format, date_format, api_key
                FROM field_definitions
                WHERE database_id = %s AND field_name = %s
            """, (SOURCE_DB_ID, col_name))
            fd = cur.fetchone()
            if fd:
                cur.execute("""
                    INSERT INTO field_definitions
                    (database_id, field_name, display_name, field_type, formula, is_editable,
                     select_options, system_value_key, select_colors, number_format, date_format, api_key)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (database_id, field_name) DO UPDATE
                    SET display_name = EXCLUDED.display_name, field_type = EXCLUDED.field_type,
                        formula = EXCLUDED.formula, is_editable = EXCLUDED.is_editable
                """, (TARGET_DB_ID, fd['field_name'], fd['display_name'], fd['field_type'],
                      fd['formula'], fd['is_editable'], fd['select_options'],
                      fd['system_value_key'], fd['select_colors'], fd['number_format'],
                      fd['date_format'], fd['api_key']))
        print(f"Step 8: Copied field_definitions for {len(added_cols)} new columns")

        # Step 9: Trigger 광고(자동완성) regeneration
        cur.execute(psql.SQL(
            'UPDATE {} SET "광고(자동완성)" = "광고(자동완성)"'
        ).format(psql.Identifier(TARGET_TABLE)))
        print(f"Step 9: Triggered 광고(자동완성) regeneration for {cur.rowcount} rows")

        conn.commit()

# Verify
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(f'SELECT COUNT(*) FROM "{SOURCE_TABLE}"')
        print(f"\nSource (건물매물): {cur.fetchone()[0]} rows (unchanged)")
        cur.execute(f'SELECT COUNT(*) FROM "{TARGET_TABLE}"')
        print(f"Target (단일부동산): {cur.fetchone()[0]} rows")

print("\nDone!")
