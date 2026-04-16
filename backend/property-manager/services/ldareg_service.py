#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NSDI 대지권등록정보 서비스 (공공데이터포털 15056691 계열)
- 건물동명조회: VWorld lt_c_bldginfo의 dong_nm이 null인 경우 fallback
- 호수/층수/일련번호 조회는 필요 시 확장

키: PUBLIC_API_KEY (공공데이터포털, NSDI/BldRgstHubService와 동일)
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)


class LdaregService:
    """대지권등록정보 서비스"""

    def __init__(self):
        self.api_key = os.getenv('PUBLIC_API_KEY')
        # NSDI 대지권등록정보 (표준 endpoint 계열)
        self.base_url = 'https://apis.data.go.kr/1611000/nsdi/LdaregService'
        self.timeout = 15

    def _get(self, endpoint: str, params: dict) -> dict:
        """공통 GET 헬퍼"""
        if not self.api_key:
            logger.error('[LdaregService] PUBLIC_API_KEY 미설정')
            return {'success': False, 'error': 'PUBLIC_API_KEY not configured'}

        url = f'{self.base_url}/{endpoint}'
        base_params = {
            'serviceKey': self.api_key,
            '_type': 'json',
            'numOfRows': 100,
            'pageNo': 1,
        }
        base_params.update(params)

        try:
            resp = requests.get(url, params=base_params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return {'success': True, 'data': data}
        except requests.exceptions.RequestException as e:
            logger.error(f'[LdaregService] HTTP 에러: {e}')
            return {'success': False, 'error': f'HTTP error: {e}'}
        except ValueError as e:
            logger.error(f'[LdaregService] JSON 파싱 에러: {e}')
            return {'success': False, 'error': f'JSON parse error: {e}'}

    def get_dong_list(self, pnu: str) -> dict:
        """
        건물동명조회 (NSDI 15056691 계열)
        - VWorld dong_nm이 null일 때 fallback 용도

        Returns:
            {
                'success': True,
                'dong_list': [{'dong_nm': '101동', ...}, ...]
            }
        """
        if not pnu or len(pnu) != 19:
            return {'success': False, 'error': 'Invalid PNU'}

        result = self._get('getLdaregAplyInfo', {'pnu': pnu})
        if not result['success']:
            return result

        try:
            items = (
                result['data']
                .get('response', {})
                .get('body', {})
                .get('items', {})
                .get('item', [])
            )
            if isinstance(items, dict):
                items = [items]

            # 중복 제거 (dong_nm 기준)
            seen = set()
            dong_list = []
            for it in items:
                dong_nm = it.get('dongNm') or it.get('dong_nm') or ''
                if dong_nm and dong_nm not in seen:
                    seen.add(dong_nm)
                    dong_list.append({
                        'dong_nm': dong_nm,
                        'bld_nm': it.get('bldNm') or it.get('bld_nm') or '',
                        'raw': it,
                    })

            return {'success': True, 'dong_list': dong_list}
        except Exception as e:
            logger.error(f'[LdaregService] 파싱 에러: {e}')
            return {'success': False, 'error': str(e)}
