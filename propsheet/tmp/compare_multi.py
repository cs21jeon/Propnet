#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

SKIP = ('id','created_at','updated_at','fields_hash','synced_at')

with get_db_connection() as conn:
    with conn.cursor() as cur:
        all_cols = {}
        for tbl, label in [('sales_multi_unit', '공동주택 매물(DB16)'), ('goldenrabbit01_sales_multi_unit', '집합부동산(DB38)')]:
            cur.execute("""
                SELECT column_name, data_type FROM information_schema.columns
                WHERE table_name = %s AND column_name NOT IN %s
                ORDER BY ordinal_position
            """, (tbl, SKIP))
            cols = cur.fetchall()
            all_cols[tbl] = {c[0]: c[1] for c in cols}
            print(f'\n=== {label} ({len(cols)} cols) ===')
            for c in cols:
                print(f'  {c[0]} ({c[1]})')
            cur.execute(f'SELECT COUNT(*) FROM "{tbl}"')
            print(f'  → {cur.fetchone()[0]}행')

        # Compare
        src = all_cols['sales_multi_unit']
        tgt = all_cols['goldenrabbit01_sales_multi_unit']

        common = set(src.keys()) & set(tgt.keys())
        src_only = set(src.keys()) - set(tgt.keys())
        tgt_only = set(tgt.keys()) - set(src.keys())

        print(f'\n=== 비교 ===')
        print(f'공통: {len(common)}개')
        print(f'공동주택에만: {len(src_only)}개 → {sorted(src_only)}')
        print(f'집합부동산에만: {len(tgt_only)}개 → {sorted(tgt_only)}')
