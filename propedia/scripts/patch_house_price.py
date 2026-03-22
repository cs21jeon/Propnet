path = '/home/webapp/goldenrabbit/backend/property-manager/services/airtable_service.py'
with open(path, 'r') as f:
    content = f.read()

changes = 0

# 1. save_building_info: 주택공시가(만원) 필드 추가
# 승강기수 저장 뒤에 추가
old_building = """            # 승강기수 (건물이 있을 때만 저장)
            if has_building_data:
                record['승강기수'] = elevator_total

            # 사용승인일 (ISO 포맷)
            if use_approval_date_iso:
                record['사용승인일'] = use_approval_date_iso"""

new_building = """            # 승강기수 (건물이 있을 때만 저장)
            if has_building_data:
                record['승강기수'] = elevator_total

            # 주택공시가(만원) - building_info의 house_price
            house_price = self._safe_int(bldg_info.get('house_price'))
            if house_price and house_price > 0:
                # API에서 원 단위로 오므로 만원 단위로 변환
                record['주택공시가(만원)'] = house_price // 10000

            # 사용승인일 (ISO 포맷)
            if use_approval_date_iso:
                record['사용승인일'] = use_approval_date_iso"""

if old_building in content:
    content = content.replace(old_building, new_building)
    changes += 1
    print('1. save_building_info: 주택공시가(만원) 추가')

# 2. save_multi_unit: 주택가격(만원) 필드 추가
# area_data에서 house_price를 가져옴
old_multi = """            if zone_classification:
                record['용도지역'] = zone_classification

            # 저장
            result = table.create(record)"""

new_multi = """            if zone_classification:
                record['용도지역'] = zone_classification

            # 주택가격(만원) - area_data의 house_price (전유부 공동주택공시가격)
            house_price = self._safe_int(area_data.get('house_price'))
            if house_price and house_price > 0:
                # API에서 원 단위로 오므로 만원 단위로 변환
                record['주택가격(만원)'] = house_price // 10000

            # 저장
            result = table.create(record)"""

if old_multi in content:
    content = content.replace(old_multi, new_multi)
    changes += 1
    print('2. save_multi_unit: 주택가격(만원) 추가')

with open(path, 'w') as f:
    f.write(content)
print(f'DONE: {changes} changes')
