#!/usr/bin/env python3
"""Apply map formula + remove defaults to ALL databases"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
import psycopg2.extras
from psycopg2 import sql as psql

MAP_FORMULA = "'https://map.kakao.com/?q=' || REPLACE(\"지번 주소\", ' ', '')"

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT d.id, d.name, d.table_name, w.name as ws_name
            FROM databases d JOIN workspaces w ON d.workspace_id = w.id
            ORDER BY d.id
        """)
        databases = cur.fetchall()

        for db in databases:
            table = db['table_name']
            db_id = db['id']
            print(f'\n=== {db["ws_name"]} / {db["name"]} ({table}) ===', flush=True)

            # Check table exists
            cur.execute('SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)', (table,))
            if not cur.fetchone()['exists']:
                print('  SKIP: table not found', flush=True)
                continue

            # 1. Remove ALL column defaults
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND column_default IS NOT NULL
                AND column_name NOT IN ('id', 'created_at', 'updated_at')
            """, (table,))
            defaults = [r['column_name'] for r in cur.fetchall()]
            for col in defaults:
                try:
                    cur.execute(psql.SQL('ALTER TABLE {} ALTER COLUMN {} DROP DEFAULT').format(
                        psql.Identifier(table), psql.Identifier(col)))
                except:
                    conn.rollback()
            if defaults:
                print(f'  Dropped {len(defaults)} defaults', flush=True)

            # 2. Check 지도 + 지번 주소
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND column_name IN ('지도', '지번 주소')
            """, (table,))
            map_cols = {r['column_name'] for r in cur.fetchall()}

            if '지도' in map_cols and '지번 주소' in map_cols:
                # Update existing URLs
                cur.execute(psql.SQL(
                    "UPDATE {} SET {} = 'https://map.kakao.com/?q=' || REPLACE({}, ' ', '') WHERE {} IS NOT NULL"
                ).format(
                    psql.Identifier(table), psql.Identifier('지도'),
                    psql.Identifier('지번 주소'), psql.Identifier('지번 주소')
                ))
                print(f'  Updated {cur.rowcount} map URLs', flush=True)

                # Update formula in field_definitions
                cur.execute(
                    "UPDATE field_definitions SET formula = %s, field_type = 'formula' WHERE field_name = %s AND database_id = %s",
                    (MAP_FORMULA, '지도', db_id)
                )
                fd_updated = cur.rowcount
                if fd_updated == 0:
                    # Insert if not exists
                    cur.execute(
                        "INSERT INTO field_definitions (database_id, field_name, display_name, field_type, formula, is_editable) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                        (db_id, '지도', '지도', 'formula', MAP_FORMULA, False)
                    )
                print(f'  Formula updated', flush=True)

                # Apply trigger
                trigger_name = 'trigger_map_' + table[:30]
                cur.execute(psql.SQL('DROP TRIGGER IF EXISTS {} ON {}').format(
                    psql.Identifier(trigger_name), psql.Identifier(table)))
                try:
                    cur.execute(psql.SQL(
                        "CREATE TRIGGER {} BEFORE INSERT OR UPDATE ON {} FOR EACH ROW EXECUTE FUNCTION update_map_link()"
                    ).format(psql.Identifier(trigger_name), psql.Identifier(table)))
                    print(f'  Map trigger applied', flush=True)
                except Exception as e:
                    print(f'  Trigger error: {e}', flush=True)
                    conn.rollback()
            else:
                print(f'  No map columns', flush=True)

        conn.commit()

print('\nAll done!', flush=True)
