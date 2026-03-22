#!/usr/bin/env python3
"""Full clone integration test"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.workspace_service import (
    create_workspace, create_database, clone_database_full,
    get_workspace_by_slug, find_orphaned_databases
)
from services.database_service import get_db_connection, list_properties

print('=== Full Clone Test ===', flush=True)

ws_id = create_workspace(name='Test Clone', slug='test-clone-final', icon='🧪')
print(f'1. Workspace id={ws_id}', flush=True)

source = get_workspace_by_slug('goldenrabbit')
databases = source.get('databases', [])
print(f'2. Source: {len(databases)} databases', flush=True)

ok, fail = [], []
new_tables = []
for db in databases:
    slug = db['slug'] + '_tc'
    table = slug.replace('-', '_')
    new_tables.append(table)
    try:
        new_id = create_database(workspace_id=ws_id, name=db['name'], slug=slug,
                                  table_name=table, icon=db.get('icon', '📊'))
        clone_database_full(db['table_name'], table, db['id'], new_id)
        r = list_properties(page=1, per_page=1, table_name=table)
        print(f'   OK: {db["name"]} ({r["total"]} rows)', flush=True)
        ok.append(db['name'])
    except Exception as e:
        print(f'   FAIL: {db["name"]}: {e}', flush=True)
        fail.append(db['name'])

print(f'\n3. Results: {len(ok)} ok, {len(fail)} fail', flush=True)
if fail:
    print(f'   Failed: {fail}', flush=True)

# Cleanup
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('DELETE FROM views WHERE database_id IN (SELECT id FROM databases WHERE workspace_id = %s)', (ws_id,))
        cur.execute('DELETE FROM database_shares WHERE database_id IN (SELECT id FROM databases WHERE workspace_id = %s)', (ws_id,))
        cur.execute('DELETE FROM databases WHERE workspace_id = %s', (ws_id,))
        cur.execute('DELETE FROM workspace_members WHERE workspace_id = %s', (ws_id,))
        cur.execute('DELETE FROM workspaces WHERE id = %s', (ws_id,))
        for t in new_tables:
            cur.execute(f'DROP TABLE IF EXISTS "{t}" CASCADE')
        conn.commit()
print('4. Cleanup done', flush=True)
