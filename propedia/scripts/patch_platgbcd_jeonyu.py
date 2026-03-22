#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전유부 조회 platGbCd 처리 패치
"""

# 파일 읽기
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 전유부 조회 부분 - params에 platGbCd 추가
old_jeonyu_params = '''                try:
                    params = {
                        'serviceKey': self.api_key,
                        'sigunguCd': sigungu_cd,
                        'bjdongCd': bjdong_cd,
                        'bun': bun,
                        'ji': ji,
                        '_type': 'json',
                        'numOfRows': num_of_rows,
                        'pageNo': page_no
                    }

                    url = f"{self.base_url}/getBrExposInfo"'''

new_jeonyu_params = '''                try:
                    # platGbCd는 첫 페이지에서 결정됨 (self._plat_gb_cd에 저장)
                    params = {
                        'serviceKey': self.api_key,
                        'sigunguCd': sigungu_cd,
                        'bjdongCd': bjdong_cd,
                        'bun': bun,
                        'ji': ji,
                        '_type': 'json',
                        'numOfRows': num_of_rows,
                        'pageNo': page_no
                    }

                    # 이미 확인된 platGbCd가 있으면 사용
                    if hasattr(self, '_current_plat_gb_cd') and self._current_plat_gb_cd:
                        params['platGbCd'] = self._current_plat_gb_cd

                    url = f"{self.base_url}/getBrExposInfo"'''

content = content.replace(old_jeonyu_params, new_jeonyu_params)
print("1. 전유부 조회 params에 platGbCd 추가 완료")

# _get_all_pages 함수 시작 부분에 platGbCd 감지 로직 추가
old_get_all_pages_start = '''    def _get_all_pages(self, sigungu_cd, bjdong_cd, bun, ji):
        all_items = []
        cache_key = f"{sigungu_cd}_{bjdong_cd}_{bun}_{ji}_jeonyu"

        # 캐시 확인 (전유부 - 대용량 데이터)
        if cache_key in JEONYU_CACHE:
            logger.info(f"[CACHE HIT] 전유부: {cache_key}")
            return JEONYU_CACHE[cache_key]

        page_no = 1'''

new_get_all_pages_start = '''    def _get_all_pages(self, sigungu_cd, bjdong_cd, bun, ji, plat_gb_cd=None):
        all_items = []
        cache_key = f"{sigungu_cd}_{bjdong_cd}_{bun}_{ji}_jeonyu"

        # 캐시 확인 (전유부 - 대용량 데이터)
        if cache_key in JEONYU_CACHE:
            logger.info(f"[CACHE HIT] 전유부: {cache_key}")
            return JEONYU_CACHE[cache_key]

        # platGbCd 저장 (페이징 시 동일 값 사용)
        self._current_plat_gb_cd = plat_gb_cd

        page_no = 1'''

content = content.replace(old_get_all_pages_start, new_get_all_pages_start)
print("2. _get_all_pages 함수 시그니처에 plat_gb_cd 추가 완료")

# 파일 저장
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n패치 완료!")
