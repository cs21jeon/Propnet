@bp.route('/api/propsheet/map-data', methods=['GET'])
def get_map_data():
    """PropSheet DB에서 매물 데이터를 좌표와 함께 반환 (3개 테이블: 단일/집합/부분)"""
    from decimal import Decimal
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor
    import re as _re

    def to_float(val):
        if val is None:
            return 0
        return float(val) if isinstance(val, Decimal) else (float(val) if val else 0)

    def extract_photo(raw):
        if not raw:
            return ''
        m = _re.search(r'\((/uploads/[^)]+)\)', raw)
        return m.group(1) if m else ''

    def format_price_label(transaction_type, price, deposit, monthly):
        def to_display(v):
            if not v or v <= 0:
                return '미정'
            if v >= 10000:
                eok = v / 10000
                return f"{eok:.0f}억" if eok == int(eok) else f"{eok:.1f}억"
            return f"{int(v)}만"

        if transaction_type == '월세':
            dep_str = to_display(deposit) if deposit and deposit > 0 else '0'
            mon_str = f"{int(monthly)}" if monthly and monthly > 0 else '0'
            return f"월세{dep_str}/{mon_str}"
        elif transaction_type == '전세':
            return f"전세{to_display(deposit)}"
        else:
            return f"매매{to_display(price)}"

    status_filter = request.args.get('status', '')
    types_param = request.args.get('types', 'danil,jibhap,bubun')
    txn_param = request.args.get('txn', '')
    valid_types = ('danil', 'jibhap', 'bubun')
    requested_types = [t.strip() for t in types_param.split(',') if t.strip() in valid_types]
    requested_txns = [t.strip() for t in txn_param.split(',') if t.strip()] if txn_param else []

    markers = []
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # === 단일부동산 ===
                if 'danil' in requested_types:
                    if not requested_txns or '매매' in requested_txns:
                        base_query = (
                            'SELECT "지번 주소", "도로명주소", "건물명", "매가(만원)",'
                            ' "토지면적(㎡)", "연면적(㎡)", "건폐율(%%)", "용적률(%%)",'
                            ' "층수", "주용도", "용도지역", "현황", "사용승인일",'
                            ' "보증금(만원)", "월세(만원)", "융자(만원)",'
                            ' "실투자금", "융자제외수익률(%%)",'
                            ' "광고(자동완성)", "대표사진", "인접역", "거리(m)",'
                            ' "record_id", coordinates_lat, coordinates_lon'
                            ' FROM goldenrabbit01_sales_building'
                            ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
                        )
                        params = []
                        if status_filter:
                            base_query += ' AND "현황" = %s'
                            params.append(status_filter)
                        if params:
                            cur.execute(base_query, params)
                        else:
                            cur.execute(base_query.replace('%%', '%'))

                        for row in cur.fetchall():
                            price = to_float(row.get('매가(만원)'))
                            markers.append({
                                'lat': to_float(row['coordinates_lat']),
                                'lon': to_float(row['coordinates_lon']),
                                'address': row.get('지번 주소', ''),
                                'road_address': row.get('도로명주소', '') or '',
                                'building_name': row.get('건물명', '') or '',
                                'price': price,
                                'land_area': to_float(row.get('토지면적(㎡)')),
                                'total_area': to_float(row.get('연면적(㎡)')),
                                'bcr': to_float(row.get('건폐율(%)')),
                                'far': to_float(row.get('용적률(%)')),
                                'floors': row.get('층수', '') or '',
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
                                'photo': extract_photo(row.get('대표사진', '')),
                                'station': row.get('인접역', '') or '',
                                'distance': to_float(row.get('거리(m)')),
                                'record_id': row.get('record_id', ''),
                                'property_type': 'danil',
                                'transaction_type': '매매',
                                'db_id': 39,
                                'price_label': format_price_label('매매', price, 0, 0),
                            })

                # === 집합부동산 ===
                if 'jibhap' in requested_types:
                    base_query = (
                        'SELECT "지번 주소", "도로명주소", "건물명", "매가(만원)",'
                        ' "토지면적(㎡)", "연면적(㎡)", "건폐율(%%)", "용적률(%%)",'
                        ' "총층수" AS "층수", "주용도", "용도지역", "현황", "사용승인일",'
                        ' "보증금(만원)", "월세(만원)", "융자(만원)",'
                        ' "전용면적(㎡)", "공급면적(㎡)", "대지면적(㎡)",'
                        ' "방", "화", "종류", "호수", "물건종류",'
                        ' "관리비(만원)", "입주가능일",'
                        ' "광고(자동완성)", "대표사진", "인접역", "거리(m)",'
                        ' "record_id", coordinates_lat, coordinates_lon'
                        ' FROM goldenrabbit01_sales_multi_unit'
                        ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
                    )
                    params = []
                    if status_filter:
                        base_query += ' AND "현황" = %s'
                        params.append(status_filter)
                    if params:
                        cur.execute(base_query, params)
                    else:
                        cur.execute(base_query.replace('%%', '%'))

                    for row in cur.fetchall():
                        kind = (row.get('종류', '') or '').strip()
                        txn = '전세' if kind == '전세' else ('월세' if kind == '월세' else '매매')
                        if requested_txns and txn not in requested_txns:
                            continue
                        price = to_float(row.get('매가(만원)'))
                        deposit = to_float(row.get('보증금(만원)'))
                        monthly = to_float(row.get('월세(만원)'))
                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'address': row.get('지번 주소', ''),
                            'road_address': row.get('도로명주소', '') or '',
                            'building_name': row.get('건물명', '') or '',
                            'price': price,
                            'land_area': to_float(row.get('토지면적(㎡)') or row.get('대지면적(㎡)')),
                            'total_area': to_float(row.get('연면적(㎡)')),
                            'exclusive_area': to_float(row.get('전용면적(㎡)')),
                            'supply_area': to_float(row.get('공급면적(㎡)')),
                            'bcr': to_float(row.get('건폐율(%)')),
                            'far': to_float(row.get('용적률(%)')),
                            'floors': row.get('층수', '') or '',
                            'usage': row.get('주용도', '') or '',
                            'zoning': row.get('용도지역', '') or '',
                            'status': row.get('현황', '') or '',
                            'approval_date': str(row.get('사용승인일', '') or ''),
                            'deposit': deposit,
                            'rent': monthly,
                            'loan': to_float(row.get('융자(만원)')),
                            'rooms': to_float(row.get('방')),
                            'bathrooms': to_float(row.get('화')),
                            'unit_no': row.get('호수', '') or '',
                            'property_subtype': row.get('물건종류', '') or '',
                            'maintenance_fee': to_float(row.get('관리비(만원)')),
                            'move_in_date': row.get('입주가능일', '') or '',
                            'description': row.get('광고(자동완성)', '') or '',
                            'photo': extract_photo(row.get('대표사진', '')),
                            'station': row.get('인접역', '') or '',
                            'distance': to_float(row.get('거리(m)')),
                            'record_id': row.get('record_id', ''),
                            'property_type': 'jibhap',
                            'transaction_type': txn,
                            'db_id': 38,
                            'price_label': format_price_label(txn, price, deposit, monthly),
                        })

                # === 부분부동산 ===
                if 'bubun' in requested_types:
                    base_query = (
                        'SELECT "지번 주소", "도로명주소", "건물명",'
                        ' "토지면적(㎡)", "연면적(㎡)", "건폐율(%%)", "용적률(%%)",'
                        ' "층수", "주용도", "용도지역", "현황", "사용승인일",'
                        ' "보증금(만원)", "월세(만원)", "융자(만원)",'
                        ' "전용면적", "공급면적(㎡)",'
                        ' "방", "화", "종류", "호수", "물건종류", "룸형태",'
                        ' "관리비", "입주가능일",'
                        ' "광고(자동완성)", "대표사진", "인접역", "거리(m)",'
                        ' "record_id", coordinates_lat, coordinates_lon'
                        ' FROM sales_building_copy'
                        ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
                    )
                    params = []
                    if status_filter:
                        base_query += ' AND "현황" = %s'
                        params.append(status_filter)
                    if params:
                        cur.execute(base_query, params)
                    else:
                        cur.execute(base_query.replace('%%', '%'))

                    for row in cur.fetchall():
                        kind = (row.get('종류', '') or '').strip()
                        txn = '전세' if kind == '전세' else ('월세' if kind == '월세' else '매매')
                        if requested_txns and txn not in requested_txns:
                            continue
                        deposit = to_float(row.get('보증금(만원)'))
                        monthly = to_float(row.get('월세(만원)'))
                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'address': row.get('지번 주소', ''),
                            'road_address': row.get('도로명주소', '') or '',
                            'building_name': row.get('건물명', '') or '',
                            'price': 0,
                            'land_area': to_float(row.get('토지면적(㎡)')),
                            'total_area': to_float(row.get('연면적(㎡)')),
                            'exclusive_area': to_float(row.get('전용면적')),
                            'supply_area': to_float(row.get('공급면적(㎡)')),
                            'bcr': to_float(row.get('건폐율(%)')),
                            'far': to_float(row.get('용적률(%)')),
                            'floors': row.get('층수', '') or '',
                            'usage': row.get('주용도', '') or '',
                            'zoning': row.get('용도지역', '') or '',
                            'status': row.get('현황', '') or '',
                            'approval_date': str(row.get('사용승인일', '') or ''),
                            'deposit': deposit,
                            'rent': monthly,
                            'loan': to_float(row.get('융자(만원)')),
                            'rooms': to_float(row.get('방')),
                            'bathrooms': to_float(row.get('화')),
                            'unit_no': row.get('호수', '') or '',
                            'property_subtype': row.get('물건종류', '') or '',
                            'room_type': row.get('룸형태', '') or '',
                            'maintenance_fee': to_float(row.get('관리비')),
                            'move_in_date': row.get('입주가능일', '') or '',
                            'description': row.get('광고(자동완성)', '') or '',
                            'photo': extract_photo(row.get('대표사진', '')),
                            'station': row.get('인접역', '') or '',
                            'distance': to_float(row.get('거리(m)')),
                            'record_id': row.get('record_id', ''),
                            'property_type': 'bubun',
                            'transaction_type': txn,
                            'db_id': 43,
                            'price_label': format_price_label(txn, 0, deposit, monthly),
                        })

    except Exception as e:
        import traceback
        logger.error(f"map-data 조회 실패: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

    # 에이전트 정보
    agent = None
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    'SELECT a.name, a.agency_name, a.phone, a.address, a.license_no, a.slug '
                    'FROM agents a JOIN workspaces w ON w.agent_id = a.id '
                    'WHERE w.slug = %s AND a.is_active = true LIMIT 1',
                    ('goldenrabbit',)
                )
                row = cur.fetchone()
                if row:
                    agent = dict(row)
    except Exception:
        pass

    return jsonify({'success': True, 'markers': markers, 'total': len(markers), 'agent': agent})
