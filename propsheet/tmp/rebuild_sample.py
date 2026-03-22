#!/usr/bin/env python3
"""
Rebuild sample workspace:
1. Delete existing sample DBs (tables + metadata)
2. Clone 금토끼부동산 3 DBs to sample workspace
3. Keep only first row in each
"""
import sys, os, secrets, string
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from services.workspace_service import clone_database_full
from psycopg2 import sql as psql
from psycopg2.extras import RealDictCursor

SAMPLE_WS_ID = 12

# Source DBs from 금토끼부동산 (ws=11)
SOURCES = [
    (39, 'goldenrabbit01_sales_building', '단일부동산', 'single'),
    (43, 'sales_building_copy', '부분부동산', 'part'),
    (38, 'goldenrabbit01_sales_multi_unit', '집합부동산', 'multi-unit'),
]

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Step 1: Delete existing sample DBs
        cur.execute("SELECT id, table_name FROM databases WHERE workspace_id = %s", (SAMPLE_WS_ID,))
        existing = cur.fetchall()
        for db in existing:
            try:
                cur.execute(psql.SQL('DROP TABLE IF EXISTS {} CASCADE').format(
                    psql.Identifier(db['table_name'])))
            except:
                pass
            cur.execute("DELETE FROM field_definitions WHERE database_id = %s", (db['id'],))
            cur.execute("DELETE FROM views WHERE database_id = %s", (db['id'],))
            cur.execute("DELETE FROM databases WHERE id = %s", (db['id'],))
        conn.commit()
        print(f"1. Deleted {len(existing)} existing sample DBs")

        # Step 2: Clone each DB
        for src_db_id, src_table, name, slug in SOURCES:
            target_table = 'template_' + slug.replace('-', '_')
            db_uid = 'db' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(17))

            # Get source icon/color
            cur.execute("SELECT icon, color FROM databases WHERE id = %s", (src_db_id,))
            src_info = cur.fetchone()

            cur.execute("""
                INSERT INTO databases (workspace_id, name, slug, table_name, icon, color, unique_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (SAMPLE_WS_ID, name, slug, target_table,
                  src_info['icon'] if src_info else None,
                  src_info['color'] if src_info else None,
                  db_uid))
            new_db_id = cur.fetchone()['id']
            conn.commit()

            try:
                clone_database_full(src_table, target_table, src_db_id, new_db_id)
                print(f"2. Cloned {name} → {target_table} (db_id={new_db_id})")
            except Exception as e:
                print(f"2. ERROR cloning {name}: {e}")
                cur.execute("DELETE FROM databases WHERE id = %s", (new_db_id,))
                conn.commit()
                continue

            # Step 3: Keep only first row
            with get_db_connection() as conn2:
                with conn2.cursor() as cur2:
                    cur2.execute(psql.SQL('SELECT MIN(id) FROM {}').format(
                        psql.Identifier(target_table)))
                    first_id = cur2.fetchone()[0]
                    if first_id:
                        cur2.execute(psql.SQL('DELETE FROM {} WHERE id != %s').format(
                            psql.Identifier(target_table)), (first_id,))
                        print(f"3. Kept first row (id={first_id}), deleted {cur2.rowcount} others")
                    conn2.commit()

print("\nDone!")
