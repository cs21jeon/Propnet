path = '/home/webapp/goldenrabbit/backend/property-manager/services/airtable_service.py'
with open(path, 'r') as f:
    content = f.read()

# In save_building_info: if jibun_address is just a number (no district info),
# fallback to building_info.plat_plc
old = """            # 지번 주소 생성
            jibun_address = self._format_jibun_address(address_data)"""

new = """            # 지번 주소 생성
            jibun_address = self._format_jibun_address(address_data)

            # 주소가 번지만 있고 시군구/동이 없으면 건물대장 plat_plc를 fallback으로 사용
            if jibun_address and not address_data.get('sigungu_name') and building_data and building_data.get('building_info'):
                plat_plc = building_data['building_info'].get('plat_plc', '')
                if plat_plc:
                    jibun_address = plat_plc
                    logger.info(f"지번 주소 fallback (plat_plc): {jibun_address}")"""

count = content.count(old)
if count > 0:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print(f'SUCCESS: plat_plc fallback added ({count} occurrences)')
else:
    print('ERROR: pattern not found')
