#!/usr/bin/env python3
"""map_dong.py에 단지 마커 API 엔드포인트 추가."""

filepath = '/home/webapp/goldenrabbit/backend/property-manager/routes/map_dong.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

if 'complex-markers' in content:
    print('already patched')
    exit(0)

endpoint_code = '''

@bp.route('/api/propsheet/map/complex-markers', methods=['GET'])
def complex_markers():
    """
    bbox 내 단지 마커 목록 반환 (complex_master 기반).

    Query:
      - swLat, swLng, neLat, neLng: bbox 좌표 (필수)
      - min_hh: 최소 세대수 (기본 50)
      - limit: 최대 반환 수 (기본 500)

    Response:
      {
        "success": true,
        "markers": [
          {"complex_pk": "...", "name": "파크리오", "lat": 37.52, "lon": 127.11,
           "household_count": 6864, "dong_count": 66, "address": "..."},
          ...
        ],
        "count": N
      }
    """
    from services.database_service import get_db_connection

    try:
        sw_lat = request.args.get('swLat', type=float)
        sw_lng = request.args.get('swLng', type=float)
        ne_lat = request.args.get('neLat', type=float)
        ne_lng = request.args.get('neLng', type=float)
        min_hh = request.args.get('min_hh', 50, type=int)
        limit = request.args.get('limit', 500, type=int)

        if None in (sw_lat, sw_lng, ne_lat, ne_lng):
            return jsonify({'success': False, 'error': 'bbox required (swLat, swLng, neLat, neLng)'}), 400

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT complex_pk, name, center_lat, center_lon, "
                    "household_count, dong_count, address_jibun "
                    "FROM complex_master "
                    "WHERE center_lat IS NOT NULL "
                    "  AND center_lat BETWEEN %s AND %s "
                    "  AND center_lon BETWEEN %s AND %s "
                    "  AND household_count >= %s "
                    "ORDER BY household_count DESC "
                    "LIMIT %s",
                    (sw_lat, ne_lat, sw_lng, ne_lng, min_hh, limit),
                )
                rows = cur.fetchall()

        markers = []
        for r in rows:
            markers.append({
                'complex_pk': str(r[0]),
                'name': r[1],
                'lat': float(r[2]),
                'lon': float(r[3]),
                'household_count': r[4],
                'dong_count': r[5],
                'address': r[6],
            })

        return jsonify({
            'success': True,
            'markers': markers,
            'count': len(markers),
        })

    except Exception as e:
        logger.error(f'[complex_markers] error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
'''

content += endpoint_code

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('patched OK')
