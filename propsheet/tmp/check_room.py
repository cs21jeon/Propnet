#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # 임대차매물 종류
        cur.execute('SELECT "종류", COUNT(*) FROM lease_properties GROUP BY "종류" ORDER BY COUNT(*) DESC')
        print("=== 임대차매물 종류 ===")
        for r in cur.fetchall():
            print(f"  [{r[0]}] -> {r[1]}건")

        # 부분부동산 룸형태 컬럼 존재 확인
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'sales_building_copy'
        """)
        all_cols = [r[0] for r in cur.fetchall()]
        room_cols = [c for c in all_cols if '룸' in c or '방형태' in c]
        print(f"\n룸 관련 컬럼: {room_cols}")
        if not room_cols:
            print("룸형태 컬럼 없음")

        # 부분부동산 현재 상태
        cur.execute('SELECT "종류", "물건종류", "방", COUNT(*) FROM sales_building_copy GROUP BY "종류", "물건종류", "방" ORDER BY COUNT(*) DESC')
        print("\n=== 부분부동산 종류/물건종류/방 ===")
        for r in cur.fetchall():
            print(f"  종류={r[0]}, 물건종류={r[1]}, 방={r[2]} -> {r[3]}건")
