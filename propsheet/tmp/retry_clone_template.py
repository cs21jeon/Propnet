#!/usr/bin/env python3
"""Retry cloning databases into template workspace"""
import sys, os, secrets, string
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from services.workspace_service import clone_database_full
import psycopg2.extras
import traceback

TEMPLATE_WS_ID = 12

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Check if template DBs already exist
        cur.execute("SELECT id, name, table_name FROM databases WHERE workspace_id = %s", (TEMPLATE_WS_ID,))
        existing = cur.fetchall()
        if existing:
            print(f"Template already has {len(existing)} databases, cleaning up...")
            for db in existing:
                try:
                    cur.execute(f'DROP TABLE IF EXISTS "{db["table_name"]}" CASCADE')
                except:
                    pass
                cur.execute("DELETE FROM field_definitions WHERE database_id = %s", (db['id'],))
                cur.execute("DELETE FROM views WHERE database_id = %s", (db['id'],))
                cur.execute("DELETE FROM databases WHERE id = %s", (db['id'],))
            conn.commit()
            print("Cleaned up existing template databases")

        # Source databases from 금토끼부동산 (ws_id=11)
        cur.execute("SELECT id, name, slug, table_name, icon, color FROM databases WHERE workspace_id = 11 ORDER BY id")
        source_dbs = cur.fetchall()

        for sdb in source_dbs:
            target_table = 'template_' + sdb['slug'].replace('-', '_')
            db_uid = 'db' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(17))

            cur.execute("""
                INSERT INTO databases (workspace_id, name, slug, table_name, icon, color, unique_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (TEMPLATE_WS_ID, sdb['name'], sdb['slug'], target_table,
                  sdb['icon'], sdb['color'], db_uid))
            new_db_id = cur.fetchone()['id']
            conn.commit()  # Commit so FK constraint is satisfied

            try:
                clone_database_full(sdb['table_name'], target_table, sdb['id'], new_db_id)
                # Clear data (template should be empty)
                with get_db_connection() as conn2:
                    with conn2.cursor() as cur2:
                        cur2.execute(f'DELETE FROM "{target_table}"')
                        conn2.commit()
                print(f"OK: {sdb['name']} → {target_table} (db_id={new_db_id}), data cleared")
            except Exception as e:
                print(f"ERROR: {sdb['name']}: {e}")
                traceback.print_exc()
                # Clean up
                cur.execute("DELETE FROM databases WHERE id = %s", (new_db_id,))
                conn.commit()
                try:
                    cur.execute(f'DROP TABLE IF EXISTS "{target_table}" CASCADE')
                    conn.commit()
                except:
                    pass

print("\nDone!")
