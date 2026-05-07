#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PropValue API — 재개발/재건축 정비구역 조회 + 폴리곤 빌더

경로: /api/propvalue/zones, /api/propvalue/zones/<id>, /api/propvalue/stats
      /api/propvalue/parcels (VWorld 연속지적도 프록시)
      /api/propvalue/zones/<id>/geometry (폴리곤 저장)
"""
import json
import logging
import os
import urllib.request
import urllib.parse
from flask import Blueprint, request, jsonify
import psycopg2.extras

from services.database_service import get_db_connection

logger = logging.getLogger(__name__)

bp = Blueprint('propvalue', __name__)


def _simplify_geometry(geom, max_points=50):
    """GeoJSON geometry의 좌표 수를 줄여 전송량 절감.

    매 N번째 좌표만 남기되, 첫/마지막 좌표는 보존.
    max_points: 링당 최대 좌표 수.
    """
    if not geom or not isinstance(geom, dict):
        return geom
    coords = geom.get('coordinates')
    if not coords:
        return geom

    def simplify_ring(ring):
        if len(ring) <= max_points:
            return ring
        step = max(1, len(ring) // max_points)
        simplified = ring[::step]
        # 폴리곤 링의 첫/끝 좌표 일치 보장
        if simplified[-1] != ring[-1]:
            simplified.append(ring[-1])
        return simplified

    geom_type = geom.get('type', '')
    if geom_type == 'Polygon':
        geom['coordinates'] = [simplify_ring(r) for r in coords]
    elif geom_type == 'MultiPolygon':
        geom['coordinates'] = [[simplify_ring(r) for r in poly] for poly in coords]
    return geom


@bp.route('/api/propvalue/zones', methods=['GET'])
def list_zones():
    """정비구역 목록 조회

    뷰포트 최적화 파라미터:
      - include_geometry: true면 geometry 포함 (기본 false)
      - bounds: sw_lat,sw_lon,ne_lat,ne_lon — 뷰포트 범위 필터
      - simplify: true면 geometry 좌표 수를 줄임 (줌 레벨 낮을 때)
      - fields: 'minimal' 이면 마커용 최소 필드만 반환 (id, zone_name, project_type, stage, center_lat/lon, district, dong)
    """
    city = request.args.get('city', '').strip()
    district = request.args.get('district', '').strip()
    stage = request.args.get('stage', '').strip()
    project_type = request.args.get('project_type', '').strip()
    bounds = request.args.get('bounds', '').strip()
    include_geo = request.args.get('include_geometry', 'false').lower() == 'true'
    simplify = request.args.get('simplify', 'false').lower() == 'true'
    fields_mode = request.args.get('fields', '').strip().lower()
    query = request.args.get('q', '').strip()

    if fields_mode == 'minimal':
        cols = "id, zone_name, zone_code, city, district, dong, project_type, stage, center_lat, center_lon, area_sqm, households, completion_date, source, is_sinsoktong"
    else:
        cols = """id, zone_name, zone_code, city, district, dong, project_type, stage,
                  area_sqm, households, floors_plan, developer,
                  union_approved, biz_approved, mgmt_approved,
                  construction_start, completion_date,
                  center_lat, center_lon, source, is_hidden, hidden_reason"""
    if include_geo:
        cols += ", geometry"

    where_clauses = []
    params = []

    if city:
        where_clauses.append("city = %s")
        params.append(city)
    if district:
        where_clauses.append("district = %s")
        params.append(district)
    if stage:
        stages = [s.strip() for s in stage.split(',') if s.strip()]
        if stages:
            where_clauses.append("stage IN %s")
            params.append(tuple(stages))
    if project_type:
        types = [t.strip() for t in project_type.split(',') if t.strip()]
        if types:
            where_clauses.append("project_type IN %s")
            params.append(tuple(types))
    if query:
        where_clauses.append("zone_name ILIKE %s")
        params.append(f"%%{query}%%")
    if bounds:
        parts = bounds.split(',')
        if len(parts) == 4:
            try:
                sw_lat, sw_lon, ne_lat, ne_lon = [float(p) for p in parts]
                where_clauses.append(
                    "center_lat BETWEEN %s AND %s AND center_lon BETWEEN %s AND %s"
                )
                params.extend([sw_lat, ne_lat, sw_lon, ne_lon])
            except (ValueError, TypeError):
                pass

    # 기본 숨김: is_hidden 플래그 + 국토부 유형 + 행정동 이름만 있는 구역 (show_hidden=true로 해제)
    # 행정동 패턴: 사당4동, 성내2동, 암사동 등 (한글+숫자?+동+숫자?)
    show_hidden = request.args.get('show_hidden', 'false').lower() == 'true'
    if not show_hidden:
        where_clauses.append("(is_hidden IS NOT TRUE)")
        where_clauses.append("project_type != '국토부'")
        where_clauses.append("zone_name !~ '^[가-힣]+[0-9]*동[0-9]*$'")

    where = " AND ".join(where_clauses) if where_clauses else "1=1"
    sql = f"SELECT {cols} FROM redevelopment_zones WHERE {where} ORDER BY city, district, zone_name"

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            rows = cur.fetchall()

            zones = []
            for r in rows:
                zone = dict(r)
                for key in ('union_approved', 'biz_approved', 'mgmt_approved',
                            'construction_start', 'completion_date'):
                    if zone.get(key):
                        zone[key] = str(zone[key])
                for key in ('area_sqm', 'center_lat', 'center_lon'):
                    if zone.get(key) is not None:
                        zone[key] = float(zone[key])
                # 신속통합기획 여부 플래그 (DB 컬럼 기반)
                zone['is_sinsoktong'] = bool(zone.get('is_sinsoktong'))
                # geometry 간소화: 좌표 수가 많은 폴리곤을 줄임
                if include_geo and simplify and zone.get('geometry'):
                    zone['geometry'] = _simplify_geometry(zone['geometry'])
                zones.append(zone)

            cur.close()
            return jsonify({'success': True, 'zones': zones, 'count': len(zones)})

    except Exception as e:
        logger.error("propvalue zones error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/propvalue/zones/<int:zone_id>', methods=['GET'])
def zone_detail(zone_id):
    """단일 구역 상세 조회"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM redevelopment_zones WHERE id = %s", (zone_id,))
            row = cur.fetchone()
            cur.close()

            if not row:
                return jsonify({'success': False, 'error': 'Zone not found'}), 404

            zone = dict(row)
            for key in ('union_approved', 'biz_approved', 'mgmt_approved',
                        'construction_start', 'completion_date', 'created_at', 'updated_at'):
                if zone.get(key):
                    zone[key] = str(zone[key])
            for key in ('area_sqm', 'center_lat', 'center_lon'):
                if zone.get(key) is not None:
                    zone[key] = float(zone[key])

            return jsonify({'success': True, 'zone': zone})

    except Exception as e:
        logger.error("propvalue zone detail error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/propvalue/stats', methods=['GET'])
def stats():
    """통계 — 단계별/지역별/유형별 카운트"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            hidden_filter = "WHERE (is_hidden IS NOT TRUE) AND project_type != '국토부' AND zone_name !~ '^[가-힣]+[0-9]*동[0-9]*$'"

            cur.execute(f"SELECT COUNT(*) as total FROM redevelopment_zones {hidden_filter}")
            total = cur.fetchone()['total']

            cur.execute(f"""
                SELECT stage, COUNT(*) as count
                FROM redevelopment_zones {hidden_filter} GROUP BY stage ORDER BY count DESC
            """)
            by_stage = {r['stage']: r['count'] for r in cur.fetchall()}

            cur.execute(f"""
                SELECT city, district, COUNT(*) as count
                FROM redevelopment_zones {hidden_filter} GROUP BY city, district ORDER BY city, district
            """)
            by_district = [dict(r) for r in cur.fetchall()]

            cur.execute(f"""
                SELECT project_type, COUNT(*) as count
                FROM redevelopment_zones {hidden_filter} GROUP BY project_type ORDER BY count DESC
            """)
            by_type = {r['project_type']: r['count'] for r in cur.fetchall()}

            cur.close()
            return jsonify({
                'success': True,
                'total': total,
                'by_stage': by_stage,
                'by_district': by_district,
                'by_type': by_type,
            })

    except Exception as e:
        logger.error("propvalue stats error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ──────────────────────────────────────────
# 폴리곤 빌더 API
# ──────────────────────────────────────────

VWORLD_KEY = os.environ.get('VWORLD_APIKEY', '')


@bp.route('/api/propvalue/parse-gosi', methods=['POST'])
def parse_gosi():
    """고시 PDF 업로드 → 텍스트 정보 추출 + 도면 이미지 추출"""
    import base64
    import re
    import tempfile

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'file required'}), 400

    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'PDF only'}), 400

    try:
        import fitz
    except ImportError:
        return jsonify({'success': False, 'error': 'PyMuPDF not installed'}), 500

    try:
        # 임시 파일에 저장
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        doc = fitz.open(tmp_path)
        num_pages = len(doc)

        # 1) 모든 페이지에서 텍스트 추출
        all_text = ''
        for page in doc:
            all_text += page.get_text() + '\n'

        # 2) 정보 파싱 (텍스트가 있는 경우)
        info = {}
        if all_text.strip():
            # 구역명 패턴: "OO구역", "사당15" 등
            m = re.search(r'([가-힣]+\d+)\s*구역', all_text)
            if m:
                info['zone_name'] = m.group(1)

            # 주소: "OO동 NNN-N 일대"
            m = re.search(r'([가-힣]+동)\s+(\d+[\-\d]*)\s*일대', all_text)
            if m:
                info['dong'] = m.group(1)
                info['address'] = f"{m.group(1)} {m.group(2)} 일대"

            # 면적: NNN,NNN.N 또는 NNN,NNN
            areas = re.findall(r'([\d,]+\.?\d*)\s*(?:㎡|m²)', all_text)
            if areas:
                # 가장 큰 면적을 구역 면적으로 추정
                parsed = []
                for a in areas:
                    try:
                        parsed.append(float(a.replace(',', '')))
                    except ValueError:
                        pass
                if parsed:
                    info['area_sqm'] = max(parsed)

            # 자치구
            m = re.search(r'([가-힣]+구)', all_text)
            if m:
                info['district'] = m.group(1)

        # 3) 마지막 페이지에서 도면 영역만 크롭하여 이미지로 변환
        map_page = doc[-1]
        page_rect = map_page.rect
        # 도면은 보통 페이지 상단 여백과 하단 여백을 제외한 중앙 영역
        # 상단 15%, 하단 5% 제외하고 크롭
        crop_rect = fitz.Rect(
            page_rect.x0 + page_rect.width * 0.05,
            page_rect.y0 + page_rect.height * 0.12,
            page_rect.x1 - page_rect.width * 0.05,
            page_rect.y1 - page_rect.height * 0.05,
        )
        pix = map_page.get_pixmap(clip=crop_rect, dpi=150)
        img_bytes = pix.tobytes("png")
        map_image = f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}"

        # 4) DB에서 매칭되는 구역 찾기
        matched_zone_id = None
        zone_name = info.get('zone_name', '')
        dong = info.get('dong', '')
        if zone_name or dong:
            try:
                with get_db_connection() as conn:
                    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    if zone_name:
                        cur.execute(
                            "SELECT id, zone_name FROM redevelopment_zones WHERE zone_name ILIKE %s LIMIT 5",
                            (f"%%{zone_name}%%",)
                        )
                    elif dong:
                        cur.execute(
                            "SELECT id, zone_name FROM redevelopment_zones WHERE dong = %s LIMIT 10",
                            (dong,)
                        )
                    matches = [dict(r) for r in cur.fetchall()]
                    if matches:
                        matched_zone_id = matches[0]['id']
                    cur.close()
            except Exception:
                pass

        doc.close()
        os.unlink(tmp_path)

        return jsonify({
            'success': True,
            'info': info,
            'has_text': bool(all_text.strip()),
            'num_pages': num_pages,
            'map_image': map_image,
            'matched_zone_id': matched_zone_id,
        })

    except Exception as e:
        logger.error("parse-gosi error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/propvalue/parcels', methods=['GET'])
def list_parcels():
    """VWorld 연속지적도 프록시 — bbox 내 필지 폴리곤 조회"""
    bbox = request.args.get('bbox', '').strip()          # min_lon,min_lat,max_lon,max_lat
    dong_code = request.args.get('dong_code', '').strip()  # PNU 앞 10자리 (예: 1159010700)
    page = request.args.get('page', '1')
    size = request.args.get('size', '1000')

    if not bbox:
        return jsonify({'success': False, 'error': 'bbox required'}), 400

    params = {
        'service': 'data',
        'request': 'GetFeature',
        'data': 'LP_PA_CBND_BUBUN',
        'key': VWORLD_KEY,
        'format': 'json',
        'geometry': 'true',
        'attribute': 'true',
        'crs': 'EPSG:4326',
        'geomFilter': f'BOX({bbox})',
        'size': size,
        'page': page,
    }
    if dong_code:
        params['attrFilter'] = f'pnu:like:{dong_code}'

    url = f'https://api.vworld.kr/req/data?{urllib.parse.urlencode(params)}'
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())

        if data.get('response', {}).get('status') != 'OK':
            return jsonify({'success': False, 'error': 'VWorld API error',
                            'detail': data.get('response', {}).get('status')})

        features = data['response']['result']['featureCollection']['features']
        total = int(data['response']['record']['total'])
        return jsonify({'success': True, 'features': features, 'total': total,
                        'page': int(page), 'size': int(size)})
    except Exception as e:
        logger.error("parcels proxy error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/propvalue/geocode', methods=['GET'])
def geocode():
    """VWorld 주소 → 좌표 변환 프록시"""
    address = request.args.get('address', '').strip()
    if not address:
        return jsonify({'success': False, 'error': 'address required'}), 400

    params = urllib.parse.urlencode({
        'service': 'address', 'request': 'getcoord', 'version': '2.0',
        'crs': 'epsg:4326', 'address': address, 'refine': 'true',
        'simple': 'false', 'format': 'json', 'type': 'PARCEL',
        'key': VWORLD_KEY,
    })
    url = f'https://api.vworld.kr/req/address?{params}'
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        result = data.get('response', {})
        if result.get('status') == 'OK':
            point = result['result']['point']
            return jsonify({'success': True, 'lon': float(point['x']),
                            'lat': float(point['y'])})
        return jsonify({'success': False, 'error': 'Not found'})
    except Exception as e:
        logger.error("geocode error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


SEOUL_ARCGIS_BASE = 'https://urban.seoul.go.kr/proxy/proxy.jsp?http://98.33.2.225:6080/arcgis/rest/services/UPIS/20200526_WMS/MapServer'
SEOUL_LAYERS = {
    # BZ100 정비사업
    'BZ101': 94,   # 주택재개발
    'BZ102': 95,   # 주택재건축
    'BZ103': 96,   # 도시환경정비
    'BZ104': 97,   # 주거환경개선
    'BZ105': 98,   # 소규모재건축
    'BZ107': 99,   # 가로주택정비
    'BZ108': 100,  # 기타
    # BZ200 도시개발사업
    'BZ201': 101,  # 택지개발
    'BZ202': 102,  # 지구단위계획
    'BZ203': 103,  # 도시개발사업
    'BZ204': 104,  # 도시계획시설
    'BZ205': 105,  # 시가지조성
    # BZ300 재정비촉진(뉴타운)
    'BZ301': 106,  # 재정비촉진지구
    'BZ302': 107,  # 뉴타운-재개발
    'BZ303': 108,  # 뉴타운-재건축
    'BZ304': 109,  # 뉴타운-도시환경
    'BZ305': 110,  # 뉴타운-주거환경
    'BZ306': 111,  # 뉴타운-가로주택
    # BZ400 도시재생
    'BZ401': 112,  # 도시재생활성화
    'BZ402': 113,  # 도시재생일반
    'BZ403': 114,  # 중심시가지
    'BZ404': 115,  # 도시재생기타
    # BZ500 역세권
    'BZ501': 116,  # 역세권개발
    'BZ502': 117,  # 역세권기타
    # BZ600 국토부
    'BZ601': 118,  # 혁신도시
    'BZ602': 119,  # 기업도시
    'BZ603': 120,  # 경제자유구역
    'BZ604': 121,  # 국토부기타
    'BZ606': 122,  # 신도시
}


@bp.route('/api/propvalue/seoul-polygon', methods=['GET'])
def fetch_seoul_polygon():
    """서울도시공간포털에서 정비구역 공식 폴리곤 조회

    params:
      q: 검색어 (구역명/주소, 예: "사당동 419", "방배15")
      layer: 레이어 코드 (BZ101~BZ108, 기본: 전체)
    """
    q = request.args.get('q', '').strip()
    layer_code = request.args.get('layer', '').strip()

    if not q:
        return jsonify({'success': False, 'error': 'q (검색어) required'}), 400

    # 검색 대상 레이어
    if layer_code and layer_code in SEOUL_LAYERS:
        layers = {layer_code: SEOUL_LAYERS[layer_code]}
    else:
        layers = SEOUL_LAYERS

    all_results = []
    for code, lid in layers.items():
        try:
            where = urllib.parse.quote(f"DGM_NM LIKE '%{q}%'")
            url = (f"{SEOUL_ARCGIS_BASE}/{lid}/query?"
                   f"where={where}&outFields=*&returnGeometry=true&outSR=4326&f=json")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            for f in data.get('features', []):
                attrs = f.get('attributes', {})
                geom = f.get('geometry', {})
                rings = geom.get('rings', [])
                if not rings:
                    continue

                all_results.append({
                    'name': attrs.get('DGM_NM', ''),
                    'area': attrs.get('DGM_AR'),
                    'signgu': attrs.get('SIGNGU_SE', ''),
                    'layer': code,
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': rings,
                    },
                    'points': sum(len(r) for r in rings),
                })
        except Exception as e:
            logger.warning("seoul-polygon layer %s error: %s", code, e)

    return jsonify({
        'success': True,
        'results': all_results,
        'count': len(all_results),
        'query': q,
    })


@bp.route('/api/propvalue/zones/<int:zone_id>/geometry', methods=['PUT'])
def update_zone_geometry(zone_id):
    """구역 폴리곤(geometry) 업데이트 — 폴리곤 빌더에서 저장

    Body JSON:
      - geometry: GeoJSON (Polygon 또는 MultiPolygon)
      - geometries: 개별 필지 geometry 목록 (있으면 shapely union 수행)
      - parcels: 선택된 PNU 목록 (참고용)
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'JSON body required'}), 400

    parcels = data.get('parcels', [])
    geometry = data.get('geometry')
    geometries = data.get('geometries', [])
    clip_boundary = data.get('clip_boundary')  # 영역 선택 다각형 (경계 클리핑용)

    # 개별 geometry가 있으면 shapely union 시도
    if geometries:
        try:
            from shapely.geometry import shape, mapping
            from shapely.ops import unary_union
            polys = []
            for g in geometries:
                geom = shape(g)
                if not geom.is_valid:
                    geom = geom.buffer(0)
                polys.append(geom)
            merged = unary_union(polys)

            # clip_boundary가 있으면 영역 다각형으로 클리핑 (도로 등 경계 필지 자르기)
            if clip_boundary:
                clip_geom = shape(clip_boundary)
                if not clip_geom.is_valid:
                    clip_geom = clip_geom.buffer(0)
                merged = merged.intersection(clip_geom)
                logger.info("Clipped with boundary polygon, area ratio: %.1f%%",
                            merged.area / clip_geom.area * 100 if clip_geom.area else 0)

            geometry = mapping(merged)
        except ImportError:
            logger.warning("shapely not available, using raw MultiPolygon")
        except Exception as e:
            logger.warning("shapely union/clip failed: %s, using raw geometry", e)

    if not geometry or geometry.get('type') not in ('Polygon', 'MultiPolygon'):
        return jsonify({'success': False, 'error': 'Valid Polygon/MultiPolygon required'}), 400

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE redevelopment_zones
                SET geometry = %s, updated_at = NOW()
                WHERE id = %s
            """, (json.dumps(geometry), zone_id))

            if cur.rowcount == 0:
                conn.rollback()
                return jsonify({'success': False, 'error': 'Zone not found'}), 404

            # center 좌표 갱신
            coords = geometry['coordinates']
            ring = coords[0] if geometry['type'] == 'Polygon' else coords[0][0]
            lons = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            center_lon = sum(lons) / len(lons)
            center_lat = sum(lats) / len(lats)

            cur.execute("""
                UPDATE redevelopment_zones
                SET center_lat = %s, center_lon = %s
                WHERE id = %s
            """, (center_lat, center_lon, zone_id))

            conn.commit()
            cur.close()
            logger.info("Zone %d geometry updated (%d parcels, type=%s)",
                        zone_id, len(parcels), geometry.get('type'))
            return jsonify({'success': True, 'zone_id': zone_id,
                            'center_lat': center_lat, 'center_lon': center_lon})

    except Exception as e:
        logger.error("update geometry error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500
