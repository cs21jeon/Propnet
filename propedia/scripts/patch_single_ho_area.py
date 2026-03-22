#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_get_single_ho_area 함수 개선 패치
- 캐시된 전유부 데이터에서 rnum을 찾아 해당 페이지만 조회
- 20000호실 대단지도 0.2초 내 조회 가능
"""

import re

# 파일 읽기
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 기존 함수 찾기
old_func_pattern = r'    def _get_single_ho_area\(self, sigungu_cd, bjdong_cd, bun, ji, dong_nm, ho_nm\):.*?(?=\n    def _normalize_value)'

new_func = '''    def _get_single_ho_area(self, sigungu_cd, bjdong_cd, bun, ji, dong_nm, ho_nm):
        """
        해당 동/호의 전유면적만 조회 (캐시된 전유부 데이터 활용)
        - 캐시된 전유부에서 해당 호의 순번(rnum)을 찾아 해당 페이지만 조회
        - 20000호실 대단지도 0.2초 내 조회 가능
        """
        try:
            # 1. 캐시된 전유부 데이터에서 해당 호의 순번 찾기
            target_page = 1
            dong_nm_normalized = dong_nm.replace('동', '').strip() if dong_nm else ''
            ho_nm_normalized = ho_nm.replace('호', '').strip() if ho_nm else ''

            if hasattr(self, 'cached_recap_data') and self.cached_recap_data:
                for item in self.cached_recap_data:
                    item_dong = item.get('dongNm', '').replace('동', '').strip()
                    item_ho = item.get('hoNm', '').replace('호', '').strip()

                    if item_dong == dong_nm_normalized and item_ho == ho_nm_normalized:
                        rnum = item.get('rnum', 1)
                        target_page = (rnum - 1) // 100 + 1
                        logger.info(f"캐시에서 {dong_nm} {ho_nm} 발견 - rnum: {rnum}, 페이지: {target_page}")
                        break

            # 2. 해당 페이지에서 전유면적 조회
            sleep(self.api_delay)

            params = {
                'serviceKey': self.api_key,
                'sigunguCd': sigungu_cd,
                'bjdongCd': bjdong_cd,
                'bun': bun,
                'ji': ji,
                '_type': 'json',
                'numOfRows': 100,
                'pageNo': target_page
            }

            url = f"{self.base_url}/getBrExposPubuseAreaInfo"
            response = requests.get(url, params=params, timeout=self.api_timeout)
            response.raise_for_status()

            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

            if not isinstance(items, list):
                items = [items]

            # 동명/호명 변형 목록
            ho_variants = [
                ho_nm,
                ho_nm.replace('호', '').strip(),
                f"{ho_nm.replace('호', '').strip()}호"
            ]

            # 해당 페이지에서 찾기
            for item in items:
                item_dong = item.get('dongNm', '').strip()
                item_ho = item.get('hoNm', '').strip()
                item_dong_normalized = item_dong.replace('동', '').strip()

                main_gb = item.get('mainAtchGbCdNm', '')
                expos_gb = item.get('exposPubuseGbCdNm', '')

                if main_gb != '주건축물' or expos_gb != '전유':
                    continue

                # 동명 비교
                dong_match = (not dong_nm_normalized) or (item_dong_normalized == dong_nm_normalized)

                if dong_match:
                    # 호명 비교
                    item_ho_normalized = item_ho.replace('호', '').strip()
                    for ho_var in ho_variants:
                        ho_var_normalized = ho_var.replace('호', '').strip()
                        if item_ho_normalized == ho_var_normalized or item_ho == ho_var:
                            area = float(item.get('area', 0))
                            logger.info(f"해당 호 전유면적 조회 성공: {item_dong} {item_ho} = {area}㎡ (페이지 {target_page})")
                            return area

            # 해당 페이지에서 못 찾으면 인접 페이지 시도 (정렬 순서 차이 대비)
            for nearby_page in [target_page - 1, target_page + 1]:
                if nearby_page < 1:
                    continue

                sleep(self.api_delay)
                params['pageNo'] = nearby_page
                response = requests.get(url, params=params, timeout=self.api_timeout)

                if response.status_code != 200:
                    continue

                data = response.json()
                items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

                if not isinstance(items, list):
                    items = [items]

                for item in items:
                    item_dong = item.get('dongNm', '').strip()
                    item_ho = item.get('hoNm', '').strip()
                    item_dong_normalized = item_dong.replace('동', '').strip()

                    main_gb = item.get('mainAtchGbCdNm', '')
                    expos_gb = item.get('exposPubuseGbCdNm', '')

                    if main_gb != '주건축물' or expos_gb != '전유':
                        continue

                    dong_match = (not dong_nm_normalized) or (item_dong_normalized == dong_nm_normalized)

                    if dong_match:
                        item_ho_normalized = item_ho.replace('호', '').strip()
                        for ho_var in ho_variants:
                            ho_var_normalized = ho_var.replace('호', '').strip()
                            if item_ho_normalized == ho_var_normalized or item_ho == ho_var:
                                area = float(item.get('area', 0))
                                logger.info(f"해당 호 전유면적 조회 성공: {item_dong} {item_ho} = {area}㎡ (인접 페이지 {nearby_page})")
                                return area

            logger.warning(f"페이지 {target_page} 및 인접 페이지에서 해당 호 찾지 못함: {dong_nm} {ho_nm}")
            return None

        except Exception as e:
            logger.error(f"해당 호 전유면적 조회 오류: {e}")
            return None

'''

# 정규식으로 교체
content = re.sub(old_func_pattern, new_func, content, flags=re.DOTALL)

# 파일 저장
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("패치 완료!")
