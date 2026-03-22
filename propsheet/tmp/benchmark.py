#!/usr/bin/env python3
import time, sys, os, json
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import list_properties, get_db_connection, get_db_cursor
import psycopg2.extras

print('=== Backend Benchmark ===', flush=True)

# 1. Raw SELECT * (no formulas)
start = time.time()
with get_db_connection() as conn:
    with get_db_cursor(conn, cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute('SELECT * FROM sales_building')
        rows = cur.fetchall()
t = time.time() - start
print(f'1. Raw SELECT *: {t:.3f}s ({len(rows)} rows)', flush=True)

# 2. list_properties with 50 rows
start = time.time()
r = list_properties(page=1, per_page=50, table_name='sales_building')
t = time.time() - start
print(f'2. list_properties(50): {t:.3f}s', flush=True)

# 3. list_properties with all rows
start = time.time()
r = list_properties(page=1, per_page=9999, table_name='sales_building')
t = time.time() - start
items = r['items']
print(f'3. list_properties(ALL): {t:.3f}s ({len(items)} rows)', flush=True)

# 4. JSON serialization
start = time.time()
j = json.dumps({'items': items}, default=str, ensure_ascii=False)
t = time.time() - start
print(f'4. JSON serialize: {t:.3f}s ({len(j)//1024}KB)', flush=True)

# 5. Check how many formula fields are computed
with get_db_connection() as conn:
    with get_db_cursor(conn, cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT field_name, formula FROM field_definitions WHERE formula IS NOT NULL AND formula != ''")
        formulas = cur.fetchall()
        print(f'\n5. Formula fields: {len(formulas)}', flush=True)
        for f in formulas:
            print(f'   {f["field_name"]}: {f["formula"][:60]}', flush=True)

# 6. Test query with EXPLAIN ANALYZE
print(f'\n6. EXPLAIN ANALYZE (all rows):', flush=True)
with get_db_connection() as conn:
    with get_db_cursor(conn, cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Build the same query list_properties would use
        cur.execute("SELECT field_name, formula FROM field_definitions WHERE formula IS NOT NULL AND formula != ''")
        formula_fields = {r['field_name']: r['formula'] for r in cur.fetchall()}

        cur.execute("EXPLAIN ANALYZE SELECT * FROM sales_building ORDER BY created_at DESC")
        for row in cur.fetchall():
            vals = list(row.values())
            print(f'   {vals[0]}', flush=True)
