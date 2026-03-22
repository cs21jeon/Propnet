#!/usr/bin/env python3
import sys, os, traceback
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')

# Simulate the exact route flow
from services.workspace_service import get_database
from services.database_service import list_properties
import logging
logging.basicConfig(level=logging.WARNING)

db = get_database(39)
table_name = db['table_name']
print(f'DB 39: {db["name"]}, table={table_name}')

# This is exactly what the route does
database_id = 39
page = 1
per_page = 50
sort_by = '레코드생성일자'
sort_order = 'desc'

try:
    result = list_properties(
        database_id=database_id,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
        table_name=table_name
    )
    print(f'SUCCESS: {result["total"]} records')
except Exception as e:
    print(f'FAILED: {e}')
    traceback.print_exc()
