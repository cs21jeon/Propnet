#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cadastral_service.py 확장 메서드 (동 단위 클러스터링 지원)
- 기존 CadastralService 클래스에 monkey-patch 형태로 메서드 주입
- get_building_by_coord: 좌표 → 건물 (LT_C_BLDGINFO)
- get_buildings_by_pnu: PNU → 단지 내 동 리스트 (주소→좌표→BBOX 조회)
- cache_building_geometry: building_dong_geometry 캐시 저장
- resolve_to_main_pnu: 부속지번 → 본번 역추적

Week 2: 공개 엔드포인트 `/map/dong-coords`의 내부 구현용.
Week 3 리팩터: WFS Filter XML 대신 VWorld /addrlink 좌표 조회 + BBOX+응답 후처리 방식.
Week 3에서 기능 플래그 `ENABLE_DONG_CLUSTERING=true`로 활성화.
"""
import os
import json
import logging
import math
import requests
from typing import Optional

from services.cadastral_service import CadastralService

logger = logging.getLogger(__name__)

_WFS_URL = 'https://api.vworld.kr/req/wfs'
_ADDR_URL = 'https://api.vworld.kr/req/address'
_DATA_URL = 'https://api.vworld.kr/req/data'  # VWorld Data API (PNU 조회)
_TIMEOUT = 15

# BBOX 확장 반경 (meter). 대형 단지(파크리오, 잠실 주공 등) 커버 위해 충분히 넓게.
# 필지 본번과 인접 지번이 단지를 공유할 수 있으므로 400m로 설정.
_BBOX_RADIUS_METER = 400.0


def _wfs_features(params: dict) -> list:
    """공통 WFS GetFeature 호출"""
    vworld_key = os.getenv('VWORLD_APIKEY')
    if not vworld_key:
        logger.error('[CadastralExt] VWORLD_APIKEY 미설정')
        return []
    base = {
        'key': vworld_key,
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'srsname': 'EPSG:4326',
        'output': 'application/json',
    }
    base.update(params)
    try:
        resp = requests.get(_WFS_URL, params=base, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get('features', []) or []
    except Exception as e:
        logger.error(f'[CadastralExt] WFS 호출 에러: {e}')
        return []


def _pnu_to_jibun(pnu: str) -> Optional[str]:
    """
    19자리 PNU → 지번 문자열 조회용 힌트
    - PNU 구조: 법정동코드(10) + 산여부(1, 1=일반/2=산) + 본번(4) + 부번(4)
    - 지번: 본번[-부번] (부번 0000이면 본번만)
    """
    if not pnu or len(pnu) != 19:
        return None
    try:
        san_flag = pnu[10]
        main = int(pnu[11:15])
        sub = int(pnu[15:19])
        jibun = f'산 {main}' if san_flag == '2' else str(main)
        if sub > 0:
            jibun = f'{jibun}-{sub}'
        return jibun
    except (ValueError, IndexError):
        return None


def _get_parcel_coord_by_pnu(pnu: str) -> Optional[dict]:
    """
    PNU로 필지 중심 좌표 획득 (Filter XML 없이)
    - 방법 1: VWorld Data API (geomfilter 없이 attrFilter로 pnu 조회)
    - 방법 2: /addrlink 주소 검색 (pnu → jibun → 좌표)
    - 반환: {'lat': float, 'lon': float, 'source': 'data'|'addrlink'} 또는 None
    """
    vworld_key = os.getenv('VWORLD_APIKEY')
    if not vworld_key:
        return None

    # 1차: VWorld Data API — 연속지적도 LP_PA_CBND_BUBUN attrFilter
    try:
        resp = requests.get(_DATA_URL, params={
            'key': vworld_key,
            'service': 'data',
            'version': '2.0',
            'request': 'GetFeature',
            'data': 'LP_PA_CBND_BUBUN',
            'attrFilter': f'pnu:=:{pnu}',
            'geometry': 'true',
            'size': 1,
            'format': 'json',
            'crs': 'EPSG:4326',
        }, timeout=_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        features = (body.get('response', {})
                        .get('result', {})
                        .get('featureCollection', {})
                        .get('features', [])) or []
        if features:
            geom = features[0].get('geometry') or {}
            center = _polygon_center(geom)
            if center:
                return {'lat': center[1], 'lon': center[0], 'source': 'data_api',
                        'geometry': geom}
    except Exception as e:
        logger.warning(f'[CadastralExt] Data API 조회 실패, addrlink fallback: {e}')

    # 2차: /addrlink 주소 검색 — pnu → 지번 → 좌표
    # (PNU만으로 addrlink를 호출할 수 없어, 행정동 + 지번 조합 필요)
    # 여기서는 우선 VWorld address API가 pnu 파라미터를 지원하지 않으므로 생략.
    # 호출자에서 jibun/주소를 함께 넘기도록 설계한 오버로드를 제공.
    return None


def _get_parcel_coord_by_address(address: str) -> Optional[dict]:
    """
    지번 주소로 좌표 조회 (/addrlink 지번 검색)
    - address 예: '서울특별시 송파구 신천동 17'
    """
    vworld_key = os.getenv('VWORLD_APIKEY')
    if not vworld_key or not address:
        return None
    try:
        resp = requests.get(_ADDR_URL, params={
            'service': 'address',
            'request': 'getCoord',
            'version': '2.0',
            'crs': 'epsg:4326',
            'address': address,
            'type': 'PARCEL',  # 지번(parcel) 기준
            'format': 'json',
            'key': vworld_key,
        }, timeout=_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        result = (body.get('response', {}) or {}).get('result', {}) or {}
        point = result.get('point') or {}
        x = point.get('x')
        y = point.get('y')
        if x and y:
            return {'lat': float(y), 'lon': float(x), 'source': 'addrlink'}
    except Exception as e:
        logger.warning(f'[CadastralExt] addrlink 조회 실패 (addr={address}): {e}')
    return None


def _bbox_from_center(lat: float, lon: float, radius_m: float = _BBOX_RADIUS_METER) -> str:
    """
    중심 좌표 + 반경(m) → WFS bbox 문자열 (EPSG:4326 minX,minY,maxX,maxY)
    - 위도 1도 ≈ 111320m
    - 경도 1도 ≈ 111320m * cos(lat)
    """
    lat_rad = math.radians(lat)
    d_lat = radius_m / 111320.0
    d_lon = radius_m / (111320.0 * max(math.cos(lat_rad), 0.01))
    return f'{lon - d_lon},{lat - d_lat},{lon + d_lon},{lat + d_lat}'


def get_building_by_coord(self, lat: float, lon: float) -> dict:
    """
    좌표 기반 건물 조회 (lt_c_bldginfo)
    - 클릭한 지점의 건물 하나를 반환
    """
    # 작은 BBOX로 조회 (약 30m 반경)
    delta = 0.0003
    bbox = f'{lon - delta},{lat - delta},{lon + delta},{lat + delta}'
    features = _wfs_features({
        'typename': 'lt_c_bldginfo',
        'bbox': bbox,
        'maxFeatures': 10,
    })
    if not features:
        return {'success': False, 'error': 'No building found'}

    # 가장 가까운 건물 선택 (간단히 첫번째)
    f = features[0]
    props = f.get('properties', {}) or {}
    return {
        'success': True,
        'building': {
            'bd_mgt_sn': props.get('ufid'),
            'pnu': props.get('pnu'),
            'dong_nm': props.get('dong_nm'),
            'bld_nm': props.get('bld_nm'),
            'grnd_flr': props.get('grnd_flr'),
            'archarea': props.get('archarea'),
            'geometry': f.get('geometry'),
        },
    }


def get_buildings_by_pnu(self, pnu: str, address: Optional[str] = None) -> dict:
    """
    PNU 기준 단지 내 동 리스트 조회 (Week 3 리팩터)

    Strategy:
      1. PNU → 필지 중심 좌표 (VWorld Data API `LP_PA_CBND_BUBUN` attrFilter)
         실패 시 /addrlink 주소 검색으로 폴백 (address 인자 제공 시)
      2. 중심 좌표 + 반경(기본 150m) → BBOX
      3. BBOX로 LT_C_BLDGINFO WFS 조회 (maxFeatures=200)
      4. 응답에서 PNU prefix(15자리) 일치하는 feature만 필터링
      5. 동별 중심 좌표 계산 후 반환

    WFS Filter XML을 사용하지 않아 'cannot be null' 에러 회피.
    """
    if not pnu or len(pnu) != 19:
        return {'success': False, 'error': 'Invalid PNU'}

    # 1. 필지 중심 좌표 획득
    center_info = _get_parcel_coord_by_pnu(pnu)

    # 1-a. 폴백: 주소 기반 좌표 조회
    if not center_info and address:
        center_info = _get_parcel_coord_by_address(address)

    # 1-b. 폴백: pnu로부터 지번 추정 (법정동코드까지는 있어도 주소 문자열이 없으므로 호출자 책임)
    if not center_info:
        return {'success': False, 'error': 'Parcel coordinate not resolved',
                'pnu': pnu, 'hint': 'provide address for /addrlink fallback'}

    center_lat = center_info['lat']
    center_lon = center_info['lon']
    logger.info(f'[CadastralExt] pnu={pnu} center=({center_lat:.6f},{center_lon:.6f}) src={center_info.get("source")}')

    # 2. BBOX 생성 (반경 150m)
    bbox = _bbox_from_center(center_lat, center_lon, _BBOX_RADIUS_METER)

    # 3. BBOX 내 건물 조회 (lt_c_bldginfo - VWorld WFS는 소문자 typename만 허용)
    bldg_features = _wfs_features({
        'typename': 'lt_c_bldginfo',
        'bbox': bbox,
        'maxFeatures': 200,
    })

    if not bldg_features:
        return {'success': False, 'error': 'No buildings in BBOX', 'pnu': pnu, 'bbox': bbox}

    # 4. PNU 필터링 전략:
    #   - 1단계: 입력 PNU의 15자리 prefix(법정동+산+본번) 일치 동을 "핵심"으로 수집
    #   - 2단계: 대형 단지는 인접 지번(예: 신천동 17, 20)에 분산 등록되므로
    #             단지명(bld_nm)이 핵심 동과 동일한 건물을 추가 편입
    #   - 3단계: 핵심이 0건이면 법정동+산(11자리) prefix로 폭넓게 재시도
    pnu_prefix_15 = pnu[:15]
    pnu_prefix_11 = pnu[:11]

    def _build_entry(f, tagged=None):
        props = f.get('properties', {}) or {}
        geometry = f.get('geometry') or {}
        center = _polygon_center(geometry)
        if not center:
            return None
        entry = {
            'bd_mgt_sn': props.get('ufid'),
            'pnu': (props.get('pnu') or '').strip() or pnu,
            'dong_nm': props.get('dong_nm'),
            'bld_nm': props.get('bld_nm'),
            'lat': center[1],
            'lon': center[0],
            'grnd_flr': props.get('grnd_flr'),
            'archarea': props.get('archarea'),
            'geometry': geometry,
        }
        if tagged:
            entry['match'] = tagged
        return entry

    # 1단계: 15자리 PNU prefix 매칭
    dongs = []
    seen_ufid = set()
    core_bld_names = set()
    for f in bldg_features:
        props = f.get('properties', {}) or {}
        f_pnu = (props.get('pnu') or '').strip()
        if f_pnu and f_pnu[:15] == pnu_prefix_15:
            entry = _build_entry(f, tagged='pnu15')
            if entry and entry['bd_mgt_sn'] not in seen_ufid:
                seen_ufid.add(entry['bd_mgt_sn'])
                dongs.append(entry)
                if entry.get('bld_nm'):
                    core_bld_names.add(entry['bld_nm'])

    # 2단계: 동일/포함 단지명(bld_nm) 기준으로 인접 지번에 분산된 동 편입
    # 파크리오 예: 본번 신천동 17 ("파크리오" 부속)과 신천동 20 ("파크리오 201동"~"파크리오 317동")
    # 부분 문자열 매칭으로 대형 단지의 주거동도 편입.
    def _is_same_complex(bld_nm: str, core_names: set) -> bool:
        if not bld_nm or not core_names:
            return False
        if bld_nm in core_names:
            return True
        # 핵심 단지명이 bld_nm에 포함되거나 그 역 (예: "파크리오" ⊂ "파크리오 201동")
        for core in core_names:
            if not core:
                continue
            if core in bld_nm or bld_nm in core:
                return True
        return False

    if core_bld_names:
        for f in bldg_features:
            props = f.get('properties', {}) or {}
            f_pnu = (props.get('pnu') or '').strip()
            if f_pnu and f_pnu[:15] == pnu_prefix_15:
                continue  # 이미 1단계에서 수집
            if f_pnu and f_pnu[:11] != pnu_prefix_11:
                continue  # 법정동이 완전히 다르면 제외
            bld_nm = props.get('bld_nm') or ''
            if not _is_same_complex(bld_nm, core_bld_names):
                continue
            entry = _build_entry(f, tagged='same_complex')
            if entry and entry['bd_mgt_sn'] not in seen_ufid:
                seen_ufid.add(entry['bd_mgt_sn'])
                dongs.append(entry)

    # 3단계: 1단계 결과가 0건이면 11자리 prefix로 재시도 (소형 단지/누락 대응)
    if not dongs:
        logger.warning(f'[CadastralExt] PNU 15자리 매칭 0건. 11자리 prefix로 재시도 (법정동 전체)')
        for f in bldg_features:
            props = f.get('properties', {}) or {}
            f_pnu = (props.get('pnu') or '').strip()
            if not f_pnu or f_pnu[:11] != pnu_prefix_11:
                continue
            entry = _build_entry(f, tagged='pnu11_fallback')
            if entry and entry['bd_mgt_sn'] not in seen_ufid:
                seen_ufid.add(entry['bd_mgt_sn'])
                dongs.append(entry)

    return {
        'success': True,
        'dongs': dongs,
        'count': len(dongs),
        'pnu': pnu,
        'center': {'lat': center_lat, 'lon': center_lon},
        'source': center_info.get('source'),
    }


def cache_building_geometry(self, bd_mgt_sn: str, pnu: str, dong_nm: Optional[str],
                            bld_nm: Optional[str], lat: float, lon: float,
                            geometry: dict, grnd_flr: Optional[int] = None,
                            archarea: Optional[float] = None,
                            raw_data: Optional[dict] = None) -> dict:
    """
    building_dong_geometry 캐시 저장 (UPSERT)
    """
    try:
        from services.database_service import get_db_connection
    except ImportError:
        logger.error('[CadastralExt] database_service import 실패')
        return {'success': False, 'error': 'db service unavailable'}

    if not bd_mgt_sn or not pnu:
        return {'success': False, 'error': 'bd_mgt_sn and pnu required'}

    # get_db_connection 은 contextmanager (services/database_service.py 참고)
    try:
        with get_db_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO building_dong_geometry
                            (bd_mgt_sn, pnu, dong_nm, bld_nm, lat, lon, geometry,
                             grnd_flr, archarea, raw_data, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb, NOW())
                        ON CONFLICT (bd_mgt_sn) DO UPDATE SET
                            pnu = EXCLUDED.pnu,
                            dong_nm = EXCLUDED.dong_nm,
                            bld_nm = EXCLUDED.bld_nm,
                            lat = EXCLUDED.lat,
                            lon = EXCLUDED.lon,
                            geometry = EXCLUDED.geometry,
                            grnd_flr = EXCLUDED.grnd_flr,
                            archarea = EXCLUDED.archarea,
                            raw_data = EXCLUDED.raw_data,
                            updated_at = NOW();
                        """,
                        (
                            bd_mgt_sn, pnu, dong_nm, bld_nm, lat, lon,
                            json.dumps(geometry) if geometry else None,
                            grnd_flr, archarea,
                            json.dumps(raw_data) if raw_data else None,
                        ),
                    )
                    conn.commit()
                return {'success': True}
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                logger.error(f'[CadastralExt] 캐시 저장 에러: {e}')
                return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f'[CadastralExt] 캐시 저장 DB 연결 에러: {e}')
        return {'success': False, 'error': str(e)}


def resolve_to_main_pnu(self, sub_pnu: str) -> dict:
    """
    부속지번 → 본번 리다이렉트 (Week 3 리팩터: WFS Filter XML 대신 Data API attrFilter)

    - PNU 구조: 법정동코드(10) + 산여부(1) + 본번(4) + 부번(4)
    - 부번 0000 이외면 본번만 남겨 실재 여부 확인 후 리다이렉트
    """
    if not sub_pnu or len(sub_pnu) != 19:
        return {'success': False, 'error': 'Invalid PNU'}

    bubun = sub_pnu[15:19]
    if bubun == '0000':
        return {'success': True, 'pnu': sub_pnu, 'redirected': False}

    main_pnu = sub_pnu[:15] + '0000'

    # VWorld Data API로 본번 존재 여부 확인 (Filter XML 미사용)
    coord = _get_parcel_coord_by_pnu(main_pnu)
    if coord:
        return {'success': True, 'pnu': main_pnu, 'redirected': True,
                'source': coord.get('source')}
    return {'success': True, 'pnu': sub_pnu, 'redirected': False}


# ---------- 유틸 ----------

def _flatten_coords(geom: dict) -> list:
    """GeoJSON geometry의 모든 좌표 [lon, lat] 평탄화"""
    if not geom:
        return []
    t = geom.get('type')
    c = geom.get('coordinates') or []
    out = []
    if t == 'Point':
        out.append(c)
    elif t == 'LineString':
        out.extend(c)
    elif t == 'Polygon':
        for ring in c:
            out.extend(ring)
    elif t == 'MultiPolygon':
        for poly in c:
            for ring in poly:
                out.extend(ring)
    return out


def _polygon_center(geom: dict):
    """Polygon/MultiPolygon의 단순 중심 (BBOX 중앙)"""
    pts = _flatten_coords(geom)
    if not pts:
        return None
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return [(min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2]


# ---------- monkey-patch ----------

def install():
    """CadastralService에 확장 메서드 주입 (멱등)"""
    CadastralService.get_building_by_coord = get_building_by_coord
    CadastralService.get_buildings_by_pnu = get_buildings_by_pnu
    CadastralService.cache_building_geometry = cache_building_geometry
    CadastralService.resolve_to_main_pnu = resolve_to_main_pnu
    logger.info('[CadastralExt] 확장 메서드 주입 완료')


# 모듈 import 시 자동 설치
install()
