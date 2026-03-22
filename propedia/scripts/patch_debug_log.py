path = '/home/webapp/goldenrabbit/backend/property-manager/services/airtable_service.py'
with open(path, 'r') as f:
    content = f.read()

old = """            # 지번 주소 생성
            jibun_address = self._format_jibun_address(address_data)

            # 주소가 번지만 있고 시군구/동이 없으면 건물대장 plat_plc를 fallback으로 사용
            if jibun_address and not address_data.get('sigungu_name') and building_data and building_data.get('building_info'):
                plat_plc = building_data['building_info'].get('plat_plc', '')
                if plat_plc:
                    jibun_address = plat_plc
                    logger.info(f"지번 주소 fallback (plat_plc): {jibun_address}")"""

new = """            # 지번 주소 생성
            logger.info(f"[DEBUG] address_data: sigungu={address_data.get('sigungu_name')!r}, emd={address_data.get('eupmyeondong_name')!r}, full={address_data.get('full_address')!r}")
            logger.info(f"[DEBUG] building_data keys: {list(building_data.keys()) if building_data else None}")
            if building_data and building_data.get('building_info'):
                bi = building_data['building_info']
                logger.info(f"[DEBUG] building_info.plat_plc={bi.get('plat_plc')!r}, new_plat_plc={bi.get('new_plat_plc')!r}")

            jibun_address = self._format_jibun_address(address_data)
            logger.info(f"[DEBUG] jibun_address after format: {jibun_address!r}")

            # 주소가 불완전하면 건물대장 plat_plc를 fallback으로 사용
            # sigungu_name이 없거나 빈 문자열이면 fallback
            sigungu = (address_data.get('sigungu_name') or '').strip()
            if not sigungu and building_data and building_data.get('building_info'):
                plat_plc = (building_data['building_info'].get('plat_plc') or '').strip()
                if plat_plc:
                    jibun_address = plat_plc
                    logger.info(f"지번 주소 fallback (plat_plc): {jibun_address}")
            logger.info(f"[DEBUG] final jibun_address: {jibun_address!r}")"""

# Replace both occurrences (save_building_info and save_multi_unit)
count = content.count(old)
if count > 0:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print(f'SUCCESS: debug logging added ({count} occurrences)')
else:
    print('ERROR: pattern not found')
    # Show what's actually there
    idx = content.find('# 지번 주소 생성')
    if idx >= 0:
        print('Found at index:', idx)
        print(repr(content[idx:idx+400]))
