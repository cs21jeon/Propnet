#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
동 단위 매물 클러스터링 API (Week 2)

경로: /propsheet/api/propsheet/map/dong-coords
기능 플래그: ENABLE_DONG_CLUSTERING (기본 false)
- Week 2: 라우트만 배포, 플래그 off (500 대신 503 반환)
- Week 3: 플래그 on으로 활성화
"""
import os
import logging
from flask import Blueprint, request, jsonify

# CadastralService + 확장 (import 시 monkey-patch 설치)
from services.cadastral_service import CadastralService
from services import cadastral_service_dong_ext  # noqa: F401 - side-effect import

logger = logging.getLogger(__name__)

bp = Blueprint('map_dong', __name__)

_cadastral = CadastralService()


def _flag_enabled() -> bool:
    return os.getenv('ENABLE_DONG_CLUSTERING', 'false').lower() in ('1', 'true', 'yes', 'on')


@bp.route('/api/propsheet/map/dong-coords', methods=['GET'])
def dong_coords():
    """
    단지 내 동 좌표 조회

    Query:
      - pnu: 19자리 PNU (우선)
      - lat, lon: 좌표 (pnu 없을 때 fallback)

    Response:
      {
        "success": true,
        "pnu": "...",
        "dongs": [
          {"bd_mgt_sn": "...", "dong_nm": "101동", "lat": 37.5, "lon": 127.0, ...},
          ...
        ],
        "count": N
      }
    """
    if not _flag_enabled():
        return jsonify({
            'success': False,
            'error': 'Feature flag ENABLE_DONG_CLUSTERING is off',
            'enabled': False,
        }), 503

    pnu = (request.args.get('pnu') or '').strip()
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    address = (request.args.get('address') or '').strip() or None

    # 1. PNU가 없을 때: address 또는 (lat,lon)으로 PNU 역조회
    if not pnu:
        # 1-a. address만 주어진 경우: address → 좌표 → 건물 → PNU
        if address and (lat is None or lon is None):
            try:
                from services.cadastral_service_dong_ext import _get_parcel_coord_by_address
                coord = _get_parcel_coord_by_address(address)
                if coord:
                    lat = coord['lat']
                    lon = coord['lon']
            except Exception as e:
                logger.warning(f'[dong_coords] address 좌표 조회 실패: {e}')

        # 1-b. 여전히 좌표 없음 → 에러
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'pnu, address, or (lat,lon) required'}), 400

        # 1-c. 좌표 → 건물 → PNU
        bld = _cadastral.get_building_by_coord(lat, lon)
        if not bld.get('success'):
            return jsonify({'success': False, 'error': bld.get('error', 'building lookup failed')}), 404
        pnu = bld['building'].get('pnu') or ''

    if not pnu or len(pnu) != 19:
        return jsonify({'success': False, 'error': 'Invalid PNU', 'pnu': pnu}), 400

    # 2. 부속지번이면 본번 리다이렉트
    redirect_info = _cadastral.resolve_to_main_pnu(pnu)
    if redirect_info.get('success') and redirect_info.get('redirected'):
        pnu = redirect_info['pnu']

    # 3. 단지 내 동 리스트 (Week 3: BBOX+후처리 방식, Filter XML 미사용)
    result = _cadastral.get_buildings_by_pnu(pnu, address=address)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'buildings lookup failed'), 'pnu': pnu}), 404

    # 4. 캐시 저장 (best-effort)
    for d in result.get('dongs', []):
        bd_mgt_sn = d.get('bd_mgt_sn')
        if not bd_mgt_sn:
            continue
        try:
            _cadastral.cache_building_geometry(
                bd_mgt_sn=bd_mgt_sn,
                pnu=d.get('pnu') or pnu,
                dong_nm=d.get('dong_nm'),
                bld_nm=d.get('bld_nm'),
                lat=d['lat'],
                lon=d['lon'],
                geometry=d.get('geometry'),
                grnd_flr=d.get('grnd_flr'),
                archarea=d.get('archarea'),
                raw_data=None,
            )
        except Exception as e:
            logger.warning(f'[dong_coords] cache skip for {bd_mgt_sn}: {e}')

    return jsonify({
        'success': True,
        'pnu': pnu,
        'dongs': result.get('dongs', []),
        'count': result.get('count', 0),
    })


@bp.route('/api/propsheet/map/dong-coords/health', methods=['GET'])
def dong_coords_health():
    """기능 플래그/키 상태 헬스체크"""
    return jsonify({
        'success': True,
        'enabled': _flag_enabled(),
        'vworld_key': bool(os.getenv('VWORLD_APIKEY')),
        'public_api_key': bool(os.getenv('PUBLIC_API_KEY')),
    })
