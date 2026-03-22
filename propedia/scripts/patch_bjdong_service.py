#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bjdong_service.py 패치 - 신규 행정구역만 구 코드 변환
"""

import re

# 파일 읽기
with open('/home/webapp/goldenrabbit/backend/property-manager/services/bjdong_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 기존 함수 찾기
old_func_pattern = r'    def get_old_bjdong_code\(self, bjdong_code\):.*?(?=\n    def parse_codes)'

new_func = '''    def get_old_bjdong_code(self, bjdong_code):
        """
        신 법정동코드에 대한 구 법정동코드 조회
        (2026년 신규 행정구역만 처리 - 화성시 동탄구/만세구/병점구/효행구, 세종시 일부)

        Args:
            bjdong_code: 신 법정동 코드 (10자리)

        Returns:
            str: 구 법정동 코드 (신규 행정구역이 아니면 None)
        """
        try:
            if not bjdong_code or len(bjdong_code) < 5:
                return None

            sigungu_cd = bjdong_code[:5]

            # 2026년 신규 행정구역만 처리
            # 화성시: 만세구(41591), 효행구(41593), 병점구(41595), 동탄구(41597)
            NEW_ADMIN_HWASEONG = ['41591', '41593', '41595', '41597']

            # 세종시 신규 동 (36110 + 11xxx ~ 12xxx)
            is_sejong_new = (sigungu_cd == '36110' and
                            len(bjdong_code) >= 7 and
                            bjdong_code[5:7] in ['11', '12'])

            # 신규 행정구역이 아니면 None 반환 (구 코드 변환 불필요)
            if sigungu_cd not in NEW_ADMIN_HWASEONG and not is_sejong_new:
                return None

            # 신규 행정구역만 DB 조회
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            sql = """
                SELECT old_bjdong_code
                FROM bjdong_codes
                WHERE bjdong_code = %s AND old_bjdong_code IS NOT NULL AND old_bjdong_code != ''
            """

            cursor.execute(sql, (bjdong_code,))
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result and result.get('old_bjdong_code'):
                logger.info(f"[신규행정구역] 구 코드 변환: {bjdong_code} → {result['old_bjdong_code']}")
                return result['old_bjdong_code']
            return None

        except Exception as e:
            logger.error(f"구 법정동코드 조회 오류: {e}")
            return None

'''

# 정규식으로 교체
content = re.sub(old_func_pattern, new_func, content, flags=re.DOTALL)

# 파일 저장
with open('/home/webapp/goldenrabbit/backend/property-manager/services/bjdong_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("패치 완료!")
print("- 화성시 신규 구(41591, 41593, 41595, 41597)만 구 코드 변환")
print("- 세종시 신규 동(36110 11xxx~12xxx)만 구 코드 변환")
print("- 나머지 지역은 신 코드 그대로 사용")
