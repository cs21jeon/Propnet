#!/usr/bin/env python3
"""Re-migrate: columns already added, just need to copy data"""
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
TARGET_DB_ID = 39

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Step 1: Delete existing rows
        cur.execute(f'DELETE FROM "{TARGET_TABLE}"')
        print(f"1. Deleted {cur.rowcount} existing rows")

        # Step 2: Get common columns (exist in both tables, excluding system cols)
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at','database_id','record_id')
            ORDER BY ordinal_position
        """, (SOURCE_TABLE,))
        source_cols = {r[0] for r in cur.fetchall()}

        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND column_name NOT IN ('id','created_at','updated_at','fields_hash','synced_at','database_id','record_id')
            ORDER BY ordinal_position
        """, (TARGET_TABLE,))
        target_cols = {r[0] for r in cur.fetchall()}

        copy_cols = sorted(source_cols & target_cols)
        print(f"2. {len(copy_cols)} columns to copy")

        # Step 3: INSERT with database_id
        col_ids = [psql.Identifier(c) for c in copy_cols]
        insert_cols = [psql.Identifier('database_id')] + col_ids
        select_parts = [psql.Literal(TARGET_DB_ID)] + col_ids

        query = psql.SQL('INSERT INTO {} ({}) SELECT {} FROM {}').format(
            psql.Identifier(TARGET_TABLE),
            psql.SQL(', ').join(insert_cols),
            psql.SQL(', ').join(select_parts),
            psql.Identifier(SOURCE_TABLE)
        )
        cur.execute(query)
        print(f"3. Inserted {cur.rowcount} rows")
        conn.commit()

    # Step 4: Generate record_ids (separate transaction)
    with conn.cursor() as cur:
        cur.execute(f'SELECT id FROM "{TARGET_TABLE}" WHERE record_id IS NULL ORDER BY id')
        ids = [r[0] for r in cur.fetchall()]
        for row_id in ids:
            rec_id = ensure_unique_record_id(TARGET_TABLE)
            cur.execute(f'UPDATE "{TARGET_TABLE}" SET record_id = %s WHERE id = %s', (rec_id, row_id))
        conn.commit()
        print(f"4. Generated {len(ids)} record_ids")

    # Step 5: Trigger 광고 + 지도 regeneration
    with conn.cursor() as cur:
        cur.execute(f'UPDATE "{TARGET_TABLE}" SET "위반건축물" = "위반건축물"')
        print(f"5. Triggered update on {cur.rowcount} rows")
        conn.commit()

    # Verify
    with conn.cursor() as cur:
        cur.execute(f'SELECT COUNT(*) FROM "{TARGET_TABLE}"')
        print(f"\nTarget (단일부동산): {cur.fetchone()[0]} rows")
        cur.execute(f'SELECT COUNT(*) FROM "{SOURCE_TABLE}"')
        print(f"Source (건물매물): {cur.fetchone()[0]} rows (unchanged)")

print("Done!")
