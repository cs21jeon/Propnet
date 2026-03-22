#!/usr/bin/env python3
"""
Migrate 임대차매물(DB9, lease_properties) → 부분부동산(DB43, sales_building_copy)
- Field name mapping applied (부분부동산 기준)
- All 임대차 data copied
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

SOURCE_TABLE = 'lease_properties'
TARGET_TABLE = 'sales_building_copy'
SOURCE_DB_ID = 9
TARGET_DB_ID = 43

# Field name mapping: source → target
FIELD_MAP = {
    '지번': '지번 주소',
    '호': '호수',
    '층수': '층',
    '전용면적(㎡)': '전용면적',
    '관리비(만원)': '관리비',
    # These are the same name, copied directly:
    # 주용도, 현황, 보증금(만원), 월세(만원), 소유주연락처, 비공개메모, 지도,
    # 종류, 융자(만원), 사용승인일, 사진링크, 건축물대장, 방향
}

# Source columns to skip (system/auto-generated)
SKIP_SOURCE = {'id', 'created_at', 'updated_at', 'fields_hash', 'synced_at',
               'database_id', 'record_id', 'airtable_id', 'Created',
               '광고(자동완성)', '지도'}

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
            WHERE table_name = %s ORDER BY ordinal_position
        """, (SOURCE_TABLE,))
        source_cols = {r['column_name']: r['data_type'] for r in cur.fetchall()}

        # Step 2: Get target columns
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s ORDER BY ordinal_position
        """, (TARGET_TABLE,))
        target_cols = {r['column_name'] for r in cur.fetchall()}

        # Step 3: Determine which source columns need to be added to target
        # Build the mapping: for each source col, what's the target col name?
        add_cols = []
        for src_col, src_type in source_cols.items():
            if src_col in SKIP_SOURCE:
                continue
            tgt_col = FIELD_MAP.get(src_col, src_col)  # mapped name or same name
            if tgt_col not in target_cols:
                pg_type = type_map.get(src_type, 'TEXT')
                cur.execute(psql.SQL('ALTER TABLE {} ADD COLUMN {} {}').format(
                    psql.Identifier(TARGET_TABLE),
                    psql.Identifier(tgt_col),
                    psql.SQL(pg_type)))
                add_cols.append(f'{src_col} → {tgt_col}')
        conn.commit()
        print(f"1. Added {len(add_cols)} columns: {add_cols}")

        # Step 4: Delete existing rows
        cur.execute(psql.SQL('DELETE FROM {}').format(psql.Identifier(TARGET_TABLE)))
        print(f"2. Deleted {cur.rowcount} existing rows")
        conn.commit()

        # Step 5: Build INSERT query with field mapping
        # For each source column (not skipped), map to target column name
        insert_pairs = []  # (target_col_name, source_col_name)
        for src_col in source_cols:
            if src_col in SKIP_SOURCE:
                continue
            tgt_col = FIELD_MAP.get(src_col, src_col)
            # Verify target has this column now
            cur.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, (TARGET_TABLE, tgt_col))
            if cur.fetchone():
                insert_pairs.append((tgt_col, src_col))

        print(f"3. {len(insert_pairs)} columns to copy")

        # Build SQL
        tgt_col_ids = [psql.Identifier('database_id')] + [psql.Identifier(t) for t, s in insert_pairs]
        src_col_ids = [psql.Literal(TARGET_DB_ID)] + [psql.Identifier(s) for t, s in insert_pairs]

        query = psql.SQL('INSERT INTO {} ({}) SELECT {} FROM {}').format(
            psql.Identifier(TARGET_TABLE),
            psql.SQL(', ').join(tgt_col_ids),
            psql.SQL(', ').join(src_col_ids),
            psql.Identifier(SOURCE_TABLE))
        cur.execute(query)
        print(f"4. Inserted {cur.rowcount} rows")
        conn.commit()

    # Step 6: Generate record_ids
    with conn.cursor() as cur:
        cur.execute(f'SELECT id FROM "{TARGET_TABLE}" WHERE record_id IS NULL ORDER BY id')
        ids = [r[0] for r in cur.fetchall()]
        for row_id in ids:
            rec_id = ensure_unique_record_id(TARGET_TABLE)
            cur.execute(f'UPDATE "{TARGET_TABLE}" SET record_id = %s WHERE id = %s', (rec_id, row_id))
        conn.commit()
        print(f"5. Generated {len(ids)} record_ids")

    # Step 7: Copy Created → created_at
    with conn.cursor() as cur:
        # airtable_id was skipped, but Created needs to go to created_at
        # Match by 지번 주소 (mapped from 지번)
        cur.execute(f'''
            UPDATE "{TARGET_TABLE}" t
            SET created_at = s."Created"
            FROM "{SOURCE_TABLE}" s
            WHERE t."지번 주소" = s."지번"
            AND COALESCE(t."호수", '') = COALESCE(s."호", '')
            AND s."Created" IS NOT NULL
        ''')
        print(f"6. Copied Created → created_at for {cur.rowcount} rows")
        conn.commit()

    # Step 8: Copy field_definitions for new columns
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        copied = 0
        for src_col, src_type in source_cols.items():
            if src_col in SKIP_SOURCE:
                continue
            tgt_col = FIELD_MAP.get(src_col, src_col)
            # Only copy for newly added columns
            if f'{src_col} → {tgt_col}' in str(add_cols) or (src_col != tgt_col):
                cur.execute("""
                    SELECT * FROM field_definitions WHERE database_id = %s AND field_name = %s
                """, (SOURCE_DB_ID, src_col))
                fd = cur.fetchone()
                if fd:
                    cur.execute("""
                        INSERT INTO field_definitions
                        (database_id, field_name, display_name, field_type, formula, is_editable,
                         select_options, system_value_key, select_colors, number_format, date_format, api_key)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (database_id, field_name) DO NOTHING
                    """, (TARGET_DB_ID, tgt_col, fd.get('display_name') or tgt_col, fd['field_type'],
                          fd['formula'], fd['is_editable'], fd['select_options'], fd['system_value_key'],
                          Json(fd['select_colors']) if isinstance(fd.get('select_colors'), dict) else fd.get('select_colors'),
                          Json(fd['number_format']) if isinstance(fd.get('number_format'), dict) else fd.get('number_format'),
                          Json(fd['date_format']) if isinstance(fd.get('date_format'), dict) else fd.get('date_format'),
                          fd.get('api_key')))
                    copied += 1
        conn.commit()
        print(f"7. Copied {copied} field_definitions")

    # Step 9: Trigger regeneration
    with conn.cursor() as cur:
        cur.execute(f'UPDATE "{TARGET_TABLE}" SET "방향" = "방향"')
        print(f"8. Triggered update on {cur.rowcount} rows")
        conn.commit()

    # Verify
    with conn.cursor() as cur:
        cur.execute(f'SELECT COUNT(*) FROM "{SOURCE_TABLE}"')
        print(f"\nSource (임대차매물): {cur.fetchone()[0]} rows (unchanged)")
        cur.execute(f'SELECT COUNT(*) FROM "{TARGET_TABLE}"')
        print(f"Target (부분부동산): {cur.fetchone()[0]} rows")

print("Done!")
