#!/usr/bin/env python3
"""Test building info: 동작구(11590) 사당동(10700) 1131-0"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.building_unified_service import BuildingUnifiedService

svc = BuildingUnifiedService()

# 동작구: 11590, 사당동: 10700, 본번: 1131, 부번: 0
print("=== search_building (전유부+표제부+총괄표제부) ===")
result = svc.search_building('11590', '10700', '1131', '0')

if result and result.get('has_data'):
    print(f"Type: {result['type']}")
    bi = result.get('building_info')
    if bi:
        print('\n--- 표제부 ---')
        for k, v in bi.items():
            print(f'  {k}: {v}')
    ri = result.get('recap_title_info')
    if ri:
        print('\n--- 총괄표제부 ---')
        for k, v in ri.items():
            print(f'  {k}: {v}')
    dh = result.get('dong_ho_dict', {})
    if dh:
        print(f'\n동/호: {len(dh)} 동')
        for dong, hos in list(dh.items())[:3]:
            print(f'  {dong}: {hos[:5]}...' if len(hos) > 5 else f'  {dong}: {hos}')
else:
    print("No data")
