#!/usr/bin/env python3
"""Patch propsheet.py: Update property-detail endpoint to support 3 property types"""
import re
import sys

FILE = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Find property-detail endpoint
old_pattern = r"@bp\.route\('/api/propsheet/property-detail'.*?return jsonify\(\{'error': str\(e\)\}\), 500"

# Find the last occurrence (there should be only one)
match = re.search(old_pattern, content, re.DOTALL)
if not match:
    print("ERROR: Could not find property-detail endpoint")
    sys.exit(1)

new_func = '''@bp.route('/api/propsheet/property-detail', methods=['GET'])
def get_property_detail():
    """PropSheet DB에서 매물 상세 정보 반환 (3개 테이블 지원)"""
    from decimal import Decimal
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    TABLES = {
        '39': 'goldenrabbit01_sales_building',
        '38': 'goldenrabbit01_sales_multi_unit',
        '43': 'sales_building_copy',
    }

    record_id = request.args.get('id', '')
    db_id = request.args.get('db_id', '39')  # 기본값: 단일부동산

    if not record_id:
        return jsonify({'error': 'record_id 필수'}), 400

    table_name = TABLES.get(db_id, TABLES['39'])

    def to_float(val):
        if val is None:
            return 0
        return float(val) if isinstance(val, Decimal) else (float(val) if val else 0)

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 테이블의 모든 컬럼 조회
                cur.execute(
                    f'SELECT * FROM {table_name} WHERE "record_id" = %s LIMIT 1',
                    (record_id,)
                )
                row = cur.fetchone()
                if not row:
                    return jsonify({'error': '매물을 찾을 수 없습니다.'}), 404

                # 대표사진 URL 추출
                import re as _re
                photo_url = ''
                photo_raw = row.get('대표사진', '') or ''
                if photo_raw:
                    m = _re.search(r'\\((/uploads/[^)]+)\\)', photo_raw)
                    if m:
                        photo_url = m.group(1)

                # 종류 → transaction_type
                kind = (row.get('종류', '') or '').strip()
                if kind == '전세':
                    txn = '전세'
                elif kind == '월세':
                    txn = '월세'
                else:
                    txn = '매매'

                # property_type
                if db_id == '38':
                    prop_type = 'jibhap'
                elif db_id == '43':
                    prop_type = 'bubun'
                else:
                    prop_type = 'danil'

                property_data = {
                    'address': row.get('지번 주소', '') or '',
                    'road_address': row.get('도로명주소', '') or '',
                    'building_name': row.get('건물명', '') or '',
                    'price': to_float(row.get('매가(만원)')),
                    'land_area': to_float(row.get('토지면적(㎡)')),
                    'total_area': to_float(row.get('연면적(㎡)')),
                    'bcr': to_float(row.get('건폐율(%)')),
                    'far': to_float(row.get('용적률(%)')),
                    'floors': row.get('층수', '') or row.get('총층수', '') or '',
                    'usage': row.get('주용도', '') or '',
                    'zoning': row.get('용도지역', '') or '',
                    'status': row.get('현황', '') or '',
                    'approval_date': str(row.get('사용승인일', '') or ''),
                    'deposit': to_float(row.get('보증금(만원)')),
                    'rent': to_float(row.get('월세(만원)')),
                    'loan': to_float(row.get('융자(만원)')),
                    'investment': to_float(row.get('실투자금')),
                    'yield_rate': to_float(row.get('융자제외수익률(%)')),
                    'description': row.get('광고(자동완성)', '') or '',
                    'photo': photo_url,
                    'station': row.get('인접역', '') or '',
                    'distance': to_float(row.get('거리(m)')),
                    'record_id': record_id,
                    'property_type': prop_type,
                    'transaction_type': txn,
                    'db_id': int(db_id),
                    # 집합/부분 전용 필드
                    'exclusive_area': to_float(row.get('전용면적(㎡)') or row.get('전용면적')),
                    'supply_area': to_float(row.get('공급면적(㎡)')),
                    'rooms': to_float(row.get('방')),
                    'bathrooms': to_float(row.get('화')),
                    'unit_no': row.get('호수', '') or '',
                    'property_subtype': row.get('물건종류', '') or '',
                    'room_type': row.get('룸형태', '') or '',
                    'maintenance_fee': to_float(row.get('관리비(만원)') or row.get('관리비')),
                    'move_in_date': row.get('입주가능일', '') or '',
                }

        # 에이전트 정보
        agent = None
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        'SELECT a.name, a.agency_name, a.phone, a.address, a.license_no '
                        'FROM agents a JOIN workspaces w ON w.agent_id = a.id '
                        'WHERE w.slug = %s AND a.is_active = true LIMIT 1',
                        ('goldenrabbit',)
                    )
                    r = cur.fetchone()
                    if r:
                        agent = dict(r)
        except Exception:
            pass

        return jsonify({'success': True, 'property': property_data, 'agent': agent})

    except Exception as e:
        import traceback
        logger.error(f"property-detail 조회 실패: {e}\\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500'''

new_content = content[:match.start()] + new_func + content[match.end():]

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"SUCCESS: Replaced property-detail endpoint ({match.start()}-{match.end()})")
