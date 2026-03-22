#!/usr/bin/env python3
"""Test building info lookup for 동작구 사당동 321-69"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.building_unified_service import BuildingUnifiedService

svc = BuildingUnifiedService()

# 동작구: 11590, 사당동: 10700, 본번: 321, 부번: 69
result = svc.search_building('11590', '10700', '321', '69')

if result and result.get('has_data'):
    print(f"Type: {result['type']}")
    bi = result.get('building_info')
    if bi:
        print('\n=== 표제부 ===')
        for k, v in bi.items():
            print(f'  {k}: {v}')
    ri = result.get('recap_title_info')
    if ri:
        print('\n=== 총괄표제부 ===')
        for k, v in ri.items():
            print(f'  {k}: {v}')
else:
    print("multi_unit 데이터 없음, 단독건물 표제부 조회...")
    title_data = svc._get_title_info('11590', '10700', '321', '69')
    if title_data and int(title_data.get('totalCount', 0)) > 0:
        bi = svc._extract_title_info(title_data)
        print('\n=== 단독건물 표제부 ===')
        for k, v in bi.items():
            print(f'  {k}: {v}')
    else:
        print("표제부도 없음")
