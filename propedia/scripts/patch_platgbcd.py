#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
platGbCd (대지구분코드) 처리 패치
- 기본 조회 실패 시 platGbCd=1 (산번지)로 재시도
"""

# 파일 읽기
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 총괄표제부 조회 부분 수정 - platGbCd 재시도 로직 추가
old_recap = '''            params = {
                'serviceKey': self.api_key,
                'sigunguCd': sigungu_cd,
                'bjdongCd': bjdong_cd,
                'bun': bun,
                'ji': ji,
                '_type': 'json',
                'numOfRows': 10,
                'pageNo': 1
            }

            url = f"{self.base_url}/getBrRecapTitleInfo"
            response = requests.get(url, params=params, timeout=self.api_timeout)
            response.raise_for_status()

            data = response.json()
            body = data.get('response', {}).get('body', {})
            total_count = int(body.get('totalCount', 0))

            if total_count > 0:
                logger.info(f"총괄표제부 데이터 발견")
                RECAP_TITLE_CACHE[cache_key] = body
                logger.info(f"[CACHE SAVE] 총괄표제부: {cache_key}")
                return body
            else:
                logger.info("총괄표제부 데이터 없음")
                RECAP_TITLE_CACHE[cache_key] = None
                return None'''

new_recap = '''            # platGbCd: 0=대지, 1=산 (공공데이터포털 기준)
            # PNU는 1=대지, 2=산으로 다름 - 불일치 케이스 대응
            for plat_gb_cd in ['0', '1']:  # 대지 먼저, 없으면 산번지 시도
                params = {
                    'serviceKey': self.api_key,
                    'sigunguCd': sigungu_cd,
                    'bjdongCd': bjdong_cd,
                    'platGbCd': plat_gb_cd,
                    'bun': bun,
                    'ji': ji,
                    '_type': 'json',
                    'numOfRows': 10,
                    'pageNo': 1
                }

                url = f"{self.base_url}/getBrRecapTitleInfo"
                response = requests.get(url, params=params, timeout=self.api_timeout)
                response.raise_for_status()

                data = response.json()
                body = data.get('response', {}).get('body', {})
                total_count = int(body.get('totalCount', 0))

                if total_count > 0:
                    logger.info(f"총괄표제부 데이터 발견 (platGbCd={plat_gb_cd})")
                    RECAP_TITLE_CACHE[cache_key] = body
                    logger.info(f"[CACHE SAVE] 총괄표제부: {cache_key}")
                    return body

            # 둘 다 없으면
            logger.info("총괄표제부 데이터 없음 (platGbCd 0, 1 모두 시도)")
            RECAP_TITLE_CACHE[cache_key] = None
            return None'''

content = content.replace(old_recap, new_recap)
print("1. 총괄표제부 조회 platGbCd 재시도 로직 추가 완료")

# 파일 저장
with open('/home/webapp/goldenrabbit/backend/property-manager/services/building_unified_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n패치 완료!")
print("- 총괄표제부 조회 시 platGbCd=0 (대지) 먼저 시도")
print("- 없으면 platGbCd=1 (산번지)로 재시도")
