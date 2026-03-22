#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
신규 행정구역 주소 보정 패치
- _inject_new_district_name() 함수 추가
- search_by_jibun(), search_by_bdmgtsn() 응답에 적용
"""

# 파일 읽기
with open('/home/webapp/goldenrabbit/backend/property-manager/routes/app_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. _inject_new_district_name 함수 추가 (bp = Blueprint 바로 위에)
old_blueprint = '''bp = Blueprint('app_api', __name__)'''

new_blueprint = '''def _inject_new_district_name(address, bjdong_code):
    """
    주소에 신규 행정구역 구 이름 삽입
    "경기도 화성시 오산동 988" → "경기도 화성시 동탄구 오산동 988"

    Args:
        address: 원본 주소 문자열
        bjdong_code: 법정동 코드 (10자리)

    Returns:
        str: 구 이름이 삽입된 주소 (신규 행정구역이 아니면 원본 반환)
    """
    if not address or not bjdong_code or len(bjdong_code) < 5:
        return address

    NEW_ADMIN_HWASEONG = {
        '41591': '만세구',
        '41593': '효행구',
        '41595': '병점구',
        '41597': '동탄구'
    }

    sigungu_cd = bjdong_code[:5]
    if sigungu_cd not in NEW_ADMIN_HWASEONG:
        return address

    new_district = NEW_ADMIN_HWASEONG[sigungu_cd]

    # 이미 구 이름이 있으면 그대로 반환
    if new_district in address:
        return address

    # "화성시 " 뒤에 구 이름 삽입
    pattern = r'(화성시)\s+'
    replacement = f'\\1 {new_district} '
    return re.sub(pattern, replacement, address)


bp = Blueprint('app_api', __name__)'''

content = content.replace(old_blueprint, new_blueprint)
print("1. _inject_new_district_name 함수 추가 완료")

# 2. search_by_jibun() 응답에서 주소 보정 적용
# building_info와 recap_title_info의 plat_plc, new_plat_plc 주소 보정
old_jibun_return = '''        return jsonify({
            'success': True,
            'codes': codes,
            'address': {
                'bjdong_code': bjdong_code,
                'full_address': address_info.get('full_address', '') if address_info else '',
                'sido_name': address_info.get('sido_name', '') if address_info else '',
                'sigungu_name': address_info.get('sigungu_name', '') if address_info else '',
                'eupmyeondong_name': address_info.get('eupmyeondong_name', '') if address_info else ''
            },
            'building': {
                'has_data': building_result.get('has_data', False),
                'type': building_result.get('type'),
                'building_info': building_result.get('building_info'),
                'recap_title_info': building_result.get('recap_title_info'),
                'dong_ho_dict': building_result.get('dong_ho_dict'),
                'floor_info': floor_info
            },
            'land': land_info
        })'''

new_jibun_return = '''        # 신규 행정구역 주소 보정
        building_info = building_result.get('building_info')
        recap_title_info = building_result.get('recap_title_info')

        if building_info:
            if building_info.get('plat_plc'):
                building_info['plat_plc'] = _inject_new_district_name(building_info['plat_plc'], bjdong_code)
            if building_info.get('new_plat_plc'):
                building_info['new_plat_plc'] = _inject_new_district_name(building_info['new_plat_plc'], bjdong_code)

        if recap_title_info:
            if recap_title_info.get('plat_plc'):
                recap_title_info['plat_plc'] = _inject_new_district_name(recap_title_info['plat_plc'], bjdong_code)
            if recap_title_info.get('new_plat_plc'):
                recap_title_info['new_plat_plc'] = _inject_new_district_name(recap_title_info['new_plat_plc'], bjdong_code)

        # 정규화된 시군구명 사용 (화성시동탄구 → 화성시 동탄구)
        sigungu_name_display = address_info.get('sigungu_name_normalized', '') if address_info else ''
        if not sigungu_name_display:
            sigungu_name_display = address_info.get('sigungu_name', '') if address_info else ''

        full_address_display = address_info.get('full_address_normalized', '') if address_info else ''
        if not full_address_display:
            full_address_display = address_info.get('full_address', '') if address_info else ''

        return jsonify({
            'success': True,
            'codes': codes,
            'address': {
                'bjdong_code': bjdong_code,
                'full_address': full_address_display,
                'sido_name': address_info.get('sido_name', '') if address_info else '',
                'sigungu_name': sigungu_name_display,
                'eupmyeondong_name': address_info.get('eupmyeondong_name', '') if address_info else '',
                'new_district_name': address_info.get('new_district_name', '') if address_info else ''
            },
            'building': {
                'has_data': building_result.get('has_data', False),
                'type': building_result.get('type'),
                'building_info': building_info,
                'recap_title_info': recap_title_info,
                'dong_ho_dict': building_result.get('dong_ho_dict'),
                'floor_info': floor_info
            },
            'land': land_info
        })'''

content = content.replace(old_jibun_return, new_jibun_return)
print("2. search_by_jibun() 응답에 주소 보정 적용 완료")

# 3. search_by_bdmgtsn() 응답에서 주소 보정 적용
old_bdmgtsn_return = '''        return jsonify({
            'success': True,
            'codes': codes,
            'address': {
                'bjdong_code': display_bjdong_code,
                'full_address': address_info.get('full_address', '') if address_info else '',
                'sido_name': address_info.get('sido_name', '') if address_info else '',
                'sigungu_name': address_info.get('sigungu_name', '') if address_info else '',
                'eupmyeondong_name': address_info.get('eupmyeondong_name', '') if address_info else ''
            },
            'building': {
                'has_data': building_result.get('has_data', False),
                'type': building_result.get('type'),
                'building_info': building_result.get('building_info'),
                'recap_title_info': building_result.get('recap_title_info'),
                'dong_ho_dict': building_result.get('dong_ho_dict'),
                'floor_info': floor_info
            },
            'land': land_info
        })'''

new_bdmgtsn_return = '''        # 신규 행정구역 주소 보정
        building_info = building_result.get('building_info')
        recap_title_info = building_result.get('recap_title_info')

        if building_info:
            if building_info.get('plat_plc'):
                building_info['plat_plc'] = _inject_new_district_name(building_info['plat_plc'], display_bjdong_code)
            if building_info.get('new_plat_plc'):
                building_info['new_plat_plc'] = _inject_new_district_name(building_info['new_plat_plc'], display_bjdong_code)

        if recap_title_info:
            if recap_title_info.get('plat_plc'):
                recap_title_info['plat_plc'] = _inject_new_district_name(recap_title_info['plat_plc'], display_bjdong_code)
            if recap_title_info.get('new_plat_plc'):
                recap_title_info['new_plat_plc'] = _inject_new_district_name(recap_title_info['new_plat_plc'], display_bjdong_code)

        # 정규화된 시군구명 사용 (화성시동탄구 → 화성시 동탄구)
        sigungu_name_display = address_info.get('sigungu_name_normalized', '') if address_info else ''
        if not sigungu_name_display:
            sigungu_name_display = address_info.get('sigungu_name', '') if address_info else ''

        full_address_display = address_info.get('full_address_normalized', '') if address_info else ''
        if not full_address_display:
            full_address_display = address_info.get('full_address', '') if address_info else ''

        return jsonify({
            'success': True,
            'codes': codes,
            'address': {
                'bjdong_code': display_bjdong_code,
                'full_address': full_address_display,
                'sido_name': address_info.get('sido_name', '') if address_info else '',
                'sigungu_name': sigungu_name_display,
                'eupmyeondong_name': address_info.get('eupmyeondong_name', '') if address_info else '',
                'new_district_name': address_info.get('new_district_name', '') if address_info else ''
            },
            'building': {
                'has_data': building_result.get('has_data', False),
                'type': building_result.get('type'),
                'building_info': building_info,
                'recap_title_info': recap_title_info,
                'dong_ho_dict': building_result.get('dong_ho_dict'),
                'floor_info': floor_info
            },
            'land': land_info
        })'''

content = content.replace(old_bdmgtsn_return, new_bdmgtsn_return)
print("3. search_by_bdmgtsn() 응답에 주소 보정 적용 완료")

# 파일 저장
with open('/home/webapp/goldenrabbit/backend/property-manager/routes/app_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n패치 완료!")
print("- _inject_new_district_name() 함수 추가")
print("- 화성시 신규 구(동탄구/만세구/효행구/병점구) 주소에 구 이름 삽입")
print("- search_by_jibun() 응답의 building_info, recap_title_info 주소 보정")
print("- search_by_bdmgtsn() 응답의 building_info, recap_title_info 주소 보정")
print("- address 응답에 new_district_name 필드 추가")
