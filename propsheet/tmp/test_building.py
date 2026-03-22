#!/usr/bin/env python3
"""Test building info lookup for 동작구 사당동 1131"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.building_unified_service import BuildingUnifiedService
import json

svc = BuildingUnifiedService()

# 동작구: 11590, 사당동: 10600, 본번: 1131, 부번: 0
result = svc.search_building('11590', '10600', '1131', '0')

if result and result.get('has_data'):
    print(f"Type: {result['type']}")

    # Building info (표제부)
    bi = result.get('building_info')
    if bi:
        print('\n=== 표제부 (building_info) ===')
        for k, v in bi.items():
            print(f'  {k}: {v}')

    # Recap title info (총괄표제부)
    ri = result.get('recap_title_info')
    if ri:
        print('\n=== 총괄표제부 (recap_title_info) ===')
        for k, v in ri.items():
            print(f'  {k}: {v}')

    # Dong/Ho
    dh = result.get('dong_ho_dict', {})
    print(f'\n동/호: {len(dh)} 동')
    for dong, hos in list(dh.items())[:2]:
        print(f'  {dong}: {len(hos)}개 호실')
else:
    print("No data found")

    # Try as single building (표제부 only)
    title_data = svc._get_title_info('11590', '10600', '1131', '0')
    if title_data and int(title_data.get('totalCount', 0)) > 0:
        bi = svc._extract_title_info(title_data)
        print('\n=== 단독건물 표제부 ===')
        for k, v in bi.items():
            print(f'  {k}: {v}')
    else:
        print("표제부도 없음")
