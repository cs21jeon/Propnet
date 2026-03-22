#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
building_unified_service.py 패치 - 신규 행정구역 old_bjdong_code 지원
VWorld API 호출 시 구 법정동코드 사용
"""

# 파일 읽기
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. import 추가 (BjdongService)
old_import = 'from services.vworld_service import VWorldService'
new_import = '''from services.vworld_service import VWorldService
from services.bjdong_service import BjdongService'''

content = content.replace(old_import, new_import)
print("1. BjdongService import 추가 완료")

# 2. __init__에 bjdong_service 초기화 추가
old_init = '''        self.vworld_service = VWorldService()

        # PostgreSQL 연결 정보'''

new_init = '''        self.vworld_service = VWorldService()
        self.bjdong_service = BjdongService()

        # PostgreSQL 연결 정보'''

content = content.replace(old_init, new_init)
print("2. bjdong_service 초기화 추가 완료")

# 3. _calculate_land_share_manually에서 구 코드 변환 추가
old_calc = '''            logger.info(f"대지지분 수동 계산 - 시군구: {sigungu_cd}, 법정동: {bjdong_cd}, 번지: {bun}-{ji}")

            # 1. 부속지번 정보 조회'''

new_calc = '''            logger.info(f"대지지분 수동 계산 - 시군구: {sigungu_cd}, 법정동: {bjdong_cd}, 번지: {bun}-{ji}")

            # 신규 행정구역 확인 - 구 법정동코드로 변환
            full_bjdong_code = sigungu_cd + bjdong_cd
            old_bjdong_code = self.bjdong_service.get_old_bjdong_code(full_bjdong_code)

            if old_bjdong_code:
                # 구 코드로 변환
                api_sigungu_cd = old_bjdong_code[:5]
                api_bjdong_cd = old_bjdong_code[5:]
                logger.info(f"신규 행정구역 감지 - 구 코드로 변환: {sigungu_cd}{bjdong_cd} → {old_bjdong_code}")
            else:
                # 기존 코드 그대로 사용
                api_sigungu_cd = sigungu_cd
                api_bjdong_cd = bjdong_cd

            # 1. 부속지번 정보 조회'''

content = content.replace(old_calc, new_calc)
print("3. 구 법정동코드 변환 로직 추가 완료")

# 4. 부속지번 조회에서 api 코드 사용
old_attached = '''            attached_jibuns = self._get_attached_jibun_info(sigungu_cd, bjdong_cd, '0', bun, ji)'''
new_attached = '''            attached_jibuns = self._get_attached_jibun_info(api_sigungu_cd, api_bjdong_cd, '0', bun, ji)'''

content = content.replace(old_attached, new_attached, 1)  # 첫 번째만 교체
print("4. 부속지번 조회 API 코드 변경 완료")

# 5. VWorld 토지면적 조회에서 api 코드 사용
old_vworld = '''            land_result = self.vworld_service.get_total_land_area(sigungu_cd, bjdong_cd, jibun_list)'''
new_vworld = '''            land_result = self.vworld_service.get_total_land_area(api_sigungu_cd, api_bjdong_cd, jibun_list)'''

content = content.replace(old_vworld, new_vworld)
print("5. VWorld 토지면적 조회 API 코드 변경 완료")

# 6. 전유공용면적 API 호출에서 api 코드 사용
old_area_api = '''                params = {
                    'serviceKey': self.api_key,
                    'sigunguCd': sigungu_cd,
                    'bjdongCd': bjdong_cd,'''

new_area_api = '''                params = {
                    'serviceKey': self.api_key,
                    'sigunguCd': api_sigungu_cd,
                    'bjdongCd': api_bjdong_cd,'''

content = content.replace(old_area_api, new_area_api)
print("6. 전유공용면적 API 호출 코드 변경 완료")

# 7. DB 조회에서도 api 코드 사용 (building_area_summary 테이블은 구 코드로 저장됨)
old_db_lookup = '''            db_total_area = self._get_total_exclusive_area_from_db(sigungu_cd, bjdong_cd, bun, ji)'''
new_db_lookup = '''            db_total_area = self._get_total_exclusive_area_from_db(api_sigungu_cd, api_bjdong_cd, bun, ji)'''

content = content.replace(old_db_lookup, new_db_lookup)
print("7. DB 조회 API 코드 변경 완료")

# 8. _get_single_ho_area 함수에도 api 코드 전달 필요
old_single_ho = '''                target_ho_area = self._get_single_ho_area(sigungu_cd, bjdong_cd, bun, ji, dong_nm, ho_nm)'''
new_single_ho = '''                target_ho_area = self._get_single_ho_area(api_sigungu_cd, api_bjdong_cd, bun, ji, dong_nm, ho_nm)'''

content = content.replace(old_single_ho, new_single_ho)
print("8. _get_single_ho_area API 코드 변경 완료")

# 파일 저장
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n패치 완료!")
print("서비스 재시작 필요")
