#!/usr/bin/env python3
"""
1. Copy view column_config from 금토끼 → 샘플 (field order)
2. Fix default visible columns to show all
"""
import sys, os, json
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection
from psycopg2.extras import RealDictCursor, Json

# Source → Target DB mapping
PAIRS = [
    (39, 51),  # 단일
    (43, 52),  # 부분
    (38, 50),  # 집합
]

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        for src_db, tgt_db in PAIRS:
            # Get source views
            cur.execute("SELECT * FROM views WHERE database_id = %s ORDER BY id", (src_db,))
            src_views = cur.fetchall()
            print(f"\nDB {src_db} → {tgt_db}: {len(src_views)} source views")

            # Delete existing target views
            cur.execute("DELETE FROM views WHERE database_id = %s", (tgt_db,))

            # Copy views
            for sv in src_views:
                cur.execute("""
                    INSERT INTO views (database_id, name, slug, filter_config, sort_config,
                                       column_config, display_order, is_default)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    tgt_db,
                    sv['name'],
                    sv['slug'],
                    Json(sv['filter_config']) if sv['filter_config'] else None,
                    Json(sv['sort_config']) if sv['sort_config'] else None,
                    Json(sv['column_config']) if sv['column_config'] else None,
                    sv['display_order'],
                    sv['is_default']
                ))
                cc = sv['column_config']
                cols_count = 0
                if isinstance(cc, dict) and 'columns' in cc:
                    cols_count = len(cc['columns'])
                elif isinstance(cc, list):
                    cols_count = len(cc)
                print(f"  Copied view '{sv['name']}' (default={sv['is_default']}, columns={cols_count})")

        conn.commit()

# Also verify the JS fix for default all columns
JS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(JS_PATH, 'r') as f:
    js = f.read()

# Check if the fix was applied
if 'allColumns.slice(0, 12)' in js or 'slice(0, Math.min(12' in js:
    print("\nWARN: Still has 12-column limit! Fixing...")
    js = js.replace(
        'this.visibleColumns = this.allColumns.slice(0, 12).map(col => col.key);',
        'this.visibleColumns = this.allColumns.map(col => col.key);'
    )
    js = js.replace(
        'this.visibleColumns = this.allColumns.slice(0, Math.min(12, this.allColumns.length)).map(col => col.key);',
        'this.visibleColumns = this.allColumns.map(col => col.key);'
    )
    with open(JS_PATH, 'w') as f:
        f.write(js)
    print("Fixed!")
else:
    # Check what the fallback line looks like
    import re
    matches = re.findall(r'this\.visibleColumns = this\.allColumns.*?;', js)
    print("\nCurrent visibleColumns assignments:")
    for m in matches:
        print(f"  {m}")

print("\nDone!")
