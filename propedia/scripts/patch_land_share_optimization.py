#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대지지분 계산 최적화 패치
- 이미 조회한 exclusive_area를 _get_land_share에 전달
- _calculate_land_share_manually에서 중복 API 호출 제거
"""

import re

# 파일 읽기
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. _get_land_share 함수 시그니처 변경 (exclusive_area 파라미터 추가)
old_get_land_share = '''    def _get_land_share(self, pnu, dong_nm, ho_nm):
        """'''
new_get_land_share = '''    def _get_land_share(self, pnu, dong_nm, ho_nm, exclusive_area=None):
        """'''

content = content.replace(old_get_land_share, new_get_land_share)
print("1. _get_land_share 시그니처 변경 완료")

# 2. _calculate_land_share_manually 호출 시 exclusive_area 전달
old_calc_call1 = '''            logger.info("대지지분을 수동으로 계산 시도")
            return self._calculate_land_share_manually(pnu, dong_nm, ho_nm)'''
new_calc_call1 = '''            logger.info("대지지분을 수동으로 계산 시도")
            return self._calculate_land_share_manually(pnu, dong_nm, ho_nm, exclusive_area)'''

content = content.replace(old_calc_call1, new_calc_call1)
print("2. _calculate_land_share_manually 호출 수정 (1) 완료")

# 3. _calculate_land_share_manually 함수 시그니처 변경
old_calc_sig = '''    def _calculate_land_share_manually(self, pnu, dong_nm, ho_nm):
        """
        대지지분 수동 계산 (VWorld API 실패 시 fallback)
        대지지분 = (해당 세대 전유면적 / 모든 세대 전유면적의 합) × (본번 + 부속지번 토지면적의 합)
        """'''
new_calc_sig = '''    def _calculate_land_share_manually(self, pnu, dong_nm, ho_nm, known_exclusive_area=None):
        """
        대지지분 수동 계산 (VWorld API 실패 시 fallback)
        대지지분 = (해당 세대 전유면적 / 모든 세대 전유면적의 합) × (본번 + 부속지번 토지면적의 합)

        Args:
            known_exclusive_area: 이미 조회한 전유면적 (있으면 API 재조회 스킵)
        """'''

content = content.replace(old_calc_sig, new_calc_sig)
print("3. _calculate_land_share_manually 시그니처 변경 완료")

# 4. _get_land_share 호출하는 부분에 exclusive_area 전달
old_land_share_call = '''                if pnu:
                    land_share = self._get_land_share(pnu, item.get('dongNm', ''), item.get('hoNm', ''))'''
new_land_share_call = '''                if pnu:
                    # 이미 조회한 전유면적을 전달하여 중복 API 호출 방지
                    known_exclusive = result.get('exclusive_area')
                    land_share = self._get_land_share(pnu, item.get('dongNm', ''), item.get('hoNm', ''), known_exclusive)'''

content = content.replace(old_land_share_call, new_land_share_call)
print("4. _get_land_share 호출 시 exclusive_area 전달 완료")

# 5. _get_single_ho_area 호출 부분을 known_exclusive_area 우선 사용으로 변경
# 기존 코드에서 target_ho_area = self._get_single_ho_area(...) 부분을 찾아서 수정
old_single_ho_call = '''                target_ho_area = self._get_single_ho_area(api_sigungu_cd, api_bjdong_cd, bun, ji, dong_nm, ho_nm)'''
new_single_ho_call = '''                # 이미 조회한 전유면적이 있으면 사용, 없으면 API 조회
                if known_exclusive_area and known_exclusive_area > 0:
                    target_ho_area = known_exclusive_area
                    logger.info(f"이미 조회된 전유면적 사용: {target_ho_area}㎡ (API 재조회 스킵)")
                else:
                    target_ho_area = self._get_single_ho_area(api_sigungu_cd, api_bjdong_cd, bun, ji, dong_nm, ho_nm)'''

content = content.replace(old_single_ho_call, new_single_ho_call)
print("5. known_exclusive_area 우선 사용 로직 추가 완료")

# 파일 저장
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n패치 완료!")
print("- 이미 조회한 전유면적을 _get_land_share에 전달")
print("- _calculate_land_share_manually에서 중복 API 호출 제거")
print("- 예상 시간 단축: 30초 → 5초 이내")
