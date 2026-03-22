#!/usr/bin/env python3
"""Update 부분부동산 (sales_building_copy, DB 43):
- Remove: 실투자금, 실투자금(융자포함), 융자제외수익률(%), 융자포함수익률, 층 (복사본)
- Add: 호수, 물건종류, 호실, 전용면적, 관리비, 방, 화(화장실), 입주가능일
- 층 already exists as numeric - keep it
- Update field_definitions accordingly
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2 import sql as psql

TABLE = 'sales_building_copy'
DB_ID = 43

# Columns to drop
DROP_COLS = ['실투자금', '실투자금(융자포함)', '융자제외수익률(%)', '융자포함수익률', '층 (복사본)']

# Columns to add (name, type, display_name)
ADD_COLS = [
    ('호수', 'character varying', 'varchar', '호수'),
    ('물건종류', 'character varying', 'varchar', '물건종류'),
    ('호실', 'character varying', 'varchar', '호실'),
    ('전용면적', 'numeric', 'number', '전용면적'),
    ('관리비', 'numeric', 'number', '관리비'),
    ('방', 'integer', 'number', '방'),
    ('화', 'integer', 'number', '화'),
    ('입주가능일', 'character varying', 'varchar', '입주가능일'),
]

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # 1. Drop columns
        for col in DROP_COLS:
            # Check if column exists
            cur.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, (TABLE, col))
            if cur.fetchone():
                cur.execute(psql.SQL('ALTER TABLE {} DROP COLUMN {}').format(
                    psql.Identifier(TABLE), psql.Identifier(col)))
                print(f'  Dropped: {col}')
                # Remove from field_definitions
                cur.execute(
                    "DELETE FROM field_definitions WHERE database_id = %s AND field_name = %s",
                    (DB_ID, col))
            else:
                print(f'  SKIP drop (not found): {col}')

        # 2. Add new columns
        for col_name, pg_type, field_type, display_name in ADD_COLS:
            cur.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, (TABLE, col_name))
            if cur.fetchone():
                print(f'  Already exists: {col_name}')
            else:
                cur.execute(psql.SQL('ALTER TABLE {} ADD COLUMN {} {}').format(
                    psql.Identifier(TABLE), psql.Identifier(col_name), psql.SQL(pg_type)))
                print(f'  Added: {col_name} ({pg_type})')

            # Upsert field_definition
            cur.execute("""
                INSERT INTO field_definitions (database_id, field_name, display_name, field_type, is_editable)
                VALUES (%s, %s, %s, %s, true)
                ON CONFLICT (database_id, field_name) DO UPDATE
                SET display_name = EXCLUDED.display_name, field_type = EXCLUDED.field_type
            """, (DB_ID, col_name, display_name, field_type))

        # 3. Verify final columns
        cur.execute("""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name = %s ORDER BY ordinal_position
        """, (TABLE,))
        print(f'\n=== Final columns ({TABLE}) ===')
        for r in cur.fetchall():
            print(f'  {r[0]} ({r[1]})')

        conn.commit()

print('\nDone!')
