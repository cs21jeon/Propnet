#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
building_unified_service.py 패치 스크립트
- DB에서 전유면적 합계 조회 로직 추가
"""

import re

# 파일 읽기
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. import 추가 (psycopg2, dotenv)
old_imports = '''import os
import logging
import requests
from cachetools import TTLCache
from time import sleep
from services.vworld_service import VWorldService'''

new_imports = '''import os
import logging
import requests
import psycopg2
from cachetools import TTLCache
from time import sleep
from dotenv import load_dotenv
from services.vworld_service import VWorldService

# .env 파일 로드
load_dotenv()'''

content = content.replace(old_imports, new_imports)
print("1. import 추가 완료")

# 2. __init__에 DB 연결 추가 (vworld_service 다음에)
old_init_end = '''        self.vworld_service = VWorldService()'''

new_init_end = '''        self.vworld_service = VWorldService()

        # PostgreSQL 연결 정보
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'goldenrabbit'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }'''

content = content.replace(old_init_end, new_init_end)
print("2. __init__ DB 설정 추가 완료")

# 3. DB 조회 메서드 추가 (_normalize_value 앞에)
old_normalize = '''    def _normalize_value(self, value):
        """빈 문자열, 공백, None을 '-'로 정규화"""'''

new_db_methods = '''    def _get_total_exclusive_area_from_db(self, sigungu_cd, bjdong_cd, bun, ji):
        """
        DB에서 건물 전체 전유면적 합계 조회
        100세대 이상 대단지만 저장되어 있음
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            cur.execute("""
                SELECT total_exclusive_area, unit_count
                FROM building_area_summary
                WHERE sigungu_cd = %s AND bjdong_cd = %s AND bun = %s AND ji = %s
            """, (sigungu_cd, bjdong_cd, bun, ji))

            result = cur.fetchone()
            conn.close()

            if result:
                logger.info(f"[DB 캐시 HIT] 전유면적 합계: {result[0]}㎡ ({result[1]}세대)")
                return float(result[0])
            else:
                logger.info(f"[DB 캐시 MISS] 전유면적 합계 없음 - API 조회 필요")
                return None

        except Exception as e:
            logger.error(f"DB 조회 오류: {e}")
            return None

    def _get_single_ho_area(self, sigungu_cd, bjdong_cd, bun, ji, dong_nm, ho_nm):
        """
        해당 동/호의 전유면적만 조회 (DB 캐시 사용 시)
        """
        try:
            sleep(self.api_delay)

            params = {
                'serviceKey': self.api_key,
                'sigunguCd': sigungu_cd,
                'bjdongCd': bjdong_cd,
                'bun': bun,
                'ji': ji,
                '_type': 'json',
                'numOfRows': 100,
                'pageNo': 1
            }

            url = f"{self.base_url}/getBrExposPubuseAreaInfo"
            response = requests.get(url, params=params, timeout=self.api_timeout)
            response.raise_for_status()

            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

            if not isinstance(items, list):
                items = [items]

            # 동명/호명 정규화
            dong_nm_normalized = dong_nm.replace('동', '').strip() if dong_nm else ''
            ho_variants = [
                ho_nm,
                ho_nm.replace('호', '').strip(),
                f"{ho_nm.replace('호', '').strip()}호"
            ]

            # 첫 페이지에서 찾기 시도
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
                            logger.info(f"해당 호 전유면적 조회 성공: {item_dong} {item_ho} = {area}㎡")
                            return area

            logger.warning(f"첫 페이지에서 해당 호 찾지 못함: {dong_nm} {ho_nm}")
            return None

        except Exception as e:
            logger.error(f"해당 호 전유면적 조회 오류: {e}")
            return None

    def _normalize_value(self, value):
        """빈 문자열, 공백, None을 '-'로 정규화"""'''

content = content.replace(old_normalize, new_db_methods)
print("3. DB 조회 메서드 추가 완료")

# 4. _calculate_land_share_manually 수정 - DB 조회 먼저 시도
old_section = '''            # 2. 전체 호의 전유면적 조회 (모든 페이지)
            items = []
            page_no = 1
            num_of_rows = 100  # API 최대 100개 제한
            total_count = 0

            while True:
                sleep(self.api_delay)'''

new_section = '''            # 2. DB에서 전유면적 합계 조회 시도 (빠름)
            db_total_area = self._get_total_exclusive_area_from_db(sigungu_cd, bjdong_cd, bun, ji)

            # DB에 있으면 해당 호 전유면적만 조회
            if db_total_area:
                # 해당 호의 전유면적 조회
                target_ho_area = self._get_single_ho_area(sigungu_cd, bjdong_cd, bun, ji, dong_nm, ho_nm)
                if target_ho_area:
                    # 대지지분 계산
                    land_share = (target_ho_area / db_total_area) * land_area
                    logger.info(f"[DB 기반 계산] 대지지분:")
                    logger.info(f"  해당 호 전유면적: {target_ho_area:.2f}㎡")
                    logger.info(f"  전체 전유면적 (DB): {db_total_area:.2f}㎡")
                    logger.info(f"  토지면적: {land_area:.2f}㎡")
                    logger.info(f"  대지지분: {land_share:.2f}㎡")
                    return round(land_share, 2)
                else:
                    logger.warning(f"해당 호 전유면적 조회 실패 - API 전체 조회로 fallback")

            # 3. DB에 없으면 기존 방식 (API 페이징)
            logger.info("[API Fallback] DB에 없음 - 전체 페이지 조회")
            items = []
            page_no = 1
            num_of_rows = 100  # API 최대 100개 제한
            total_count = 0

            while True:
                sleep(self.api_delay)'''

content = content.replace(old_section, new_section)
print("4. _calculate_land_share_manually DB 로직 추가 완료")

# 파일 저장
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n패치 완료!")
print("서비스 재시작 필요: sudo systemctl restart goldenrabbit-property")
