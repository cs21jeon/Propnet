@bp.route('/api/propsheet/search-map', methods=['POST'])
def search_map_db():
    """PropSheet DB 기반 매물 검색 (3개 테이블 지원)"""
    from decimal import Decimal
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor
    import html as html_module

    TABLES = {
        'danil': 'goldenrabbit01_sales_building',
        'jibhap': 'goldenrabbit01_sales_multi_unit',
        'bubun': 'sales_building_copy',
    }

    def to_float(val):
        if val is None:
            return 0
        return float(val) if isinstance(val, Decimal) else (float(val) if val else 0)

    search = request.json or {}
    property_type = search.get('property_type', 'danil')
    table_name = TABLES.get(property_type, TABLES['danil'])
    markers = []

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                conditions = [
                    'coordinates_lat IS NOT NULL',
                    'coordinates_lon IS NOT NULL',
                    '"현황" = %s'
                ]
                params = ['등록']

                if property_type == 'danil':
                    price_val = search.get('price_value', '').strip()
                    price_cond = search.get('price_condition', 'all')
                    if price_val and price_cond != 'all':
                        op = '>= %s' if price_cond == 'above' else '<= %s'
                        conditions.append('"매가(만원)" ' + op)
                        params.append(float(price_val))

                    inv_val = search.get('investment_value', '').strip()
                    inv_cond = search.get('investment_condition', 'all')
                    if inv_val and inv_cond != 'all':
                        op = '>= %s' if inv_cond == 'above' else '<= %s'
                        conditions.append('"실투자금" ' + op)
                        params.append(float(inv_val))

                    yield_val = search.get('yield_value', '').strip()
                    yield_cond = search.get('yield_condition', 'all')
                    if yield_val and yield_cond != 'all':
                        op = '>= %s' if yield_cond == 'above' else '<= %s'
                        conditions.append('"융자제외수익률(%%)" ' + op)
                        params.append(float(yield_val))

                    area_val = search.get('area_value', '').strip()
                    area_cond = search.get('area_condition', 'all')
                    if area_val and area_cond != 'all':
                        op = '>= %s' if area_cond == 'above' else '<= %s'
                        conditions.append('"토지면적(㎡)" ' + op)
                        params.append(float(area_val))

                    query = (
                        'SELECT "지번 주소", "매가(만원)", "토지면적(㎡)", "층수", "주용도",'
                        ' "record_id", coordinates_lat, coordinates_lon'
                        ' FROM ' + table_name +
                        ' WHERE ' + ' AND '.join(conditions)
                    )

                elif property_type == 'jibhap':
                    price_val = search.get('price_value', '').strip()
                    price_cond = search.get('price_condition', 'all')
                    if price_val and price_cond != 'all':
                        op = '>= %s' if price_cond == 'above' else '<= %s'
                        conditions.append('"매가(만원)" ' + op)
                        params.append(float(price_val))

                    dep_val = search.get('deposit_value', '').strip()
                    dep_cond = search.get('deposit_condition', 'all')
                    if dep_val and dep_cond != 'all':
                        op = '>= %s' if dep_cond == 'above' else '<= %s'
                        conditions.append('"보증금(만원)" ' + op)
                        params.append(float(dep_val))

                    rent_val = search.get('rent_value', '').strip()
                    rent_cond = search.get('rent_condition', 'all')
                    if rent_val and rent_cond != 'all':
                        op = '>= %s' if rent_cond == 'above' else '<= %s'
                        conditions.append('"월세(만원)" ' + op)
                        params.append(float(rent_val))

                    area_val = search.get('exclusive_area_value', '').strip()
                    area_cond = search.get('exclusive_area_condition', 'all')
                    if area_val and area_cond != 'all':
                        op = '>= %s' if area_cond == 'above' else '<= %s'
                        conditions.append('"전용면적(㎡)" ' + op)
                        params.append(float(area_val))

                    rooms_val = search.get('rooms_value', '').strip()
                    rooms_cond = search.get('rooms_condition', 'all')
                    if rooms_val and rooms_cond != 'all':
                        op = '>= %s' if rooms_cond == 'above' else '<= %s'
                        conditions.append('"방" ' + op)
                        params.append(float(rooms_val))

                    query = (
                        'SELECT "지번 주소", "매가(만원)", "보증금(만원)", "월세(만원)",'
                        ' "전용면적(㎡)", "종류", "방",'
                        ' "record_id", coordinates_lat, coordinates_lon'
                        ' FROM ' + table_name +
                        ' WHERE ' + ' AND '.join(conditions)
                    )

                else:  # bubun
                    dep_val = search.get('deposit_value', '').strip()
                    dep_cond = search.get('deposit_condition', 'all')
                    if dep_val and dep_cond != 'all':
                        op = '>= %s' if dep_cond == 'above' else '<= %s'
                        conditions.append('"보증금(만원)" ' + op)
                        params.append(float(dep_val))

                    rent_val = search.get('rent_value', '').strip()
                    rent_cond = search.get('rent_condition', 'all')
                    if rent_val and rent_cond != 'all':
                        op = '>= %s' if rent_cond == 'above' else '<= %s'
                        conditions.append('"월세(만원)" ' + op)
                        params.append(float(rent_val))

                    area_val = search.get('exclusive_area_value', '').strip()
                    area_cond = search.get('exclusive_area_condition', 'all')
                    if area_val and area_cond != 'all':
                        op = '>= %s' if area_cond == 'above' else '<= %s'
                        conditions.append('"전용면적" ' + op)
                        params.append(float(area_val))

                    subtype_val = search.get('subtype_value', '').strip()
                    if subtype_val:
                        conditions.append('"물건종류" = %s')
                        params.append(subtype_val)

                    rooms_val = search.get('rooms_value', '').strip()
                    rooms_cond = search.get('rooms_condition', 'all')
                    if rooms_val and rooms_cond != 'all':
                        op = '>= %s' if rooms_cond == 'above' else '<= %s'
                        conditions.append('"방" ' + op)
                        params.append(float(rooms_val))

                    query = (
                        'SELECT "지번 주소", "보증금(만원)", "월세(만원)",'
                        ' "전용면적", "종류", "물건종류", "방",'
                        ' "record_id", coordinates_lat, coordinates_lon'
                        ' FROM ' + table_name +
                        ' WHERE ' + ' AND '.join(conditions)
                    )

                cur.execute(query, params)

                for row in cur.fetchall():
                    address = row.get('지번 주소', '') or ''
                    record_id = row.get('record_id', '')
                    addr_esc = html_module.escape(address, quote=True)

                    if property_type == 'danil':
                        price_num = to_float(row.get('매가(만원)'))
                        price_eok = price_num / 10000
                        if price_eok >= 1:
                            price_display = f"{price_eok:.1f}억원"
                        else:
                            price_display = f"{price_num:.0f}만원" if price_num else "가격미정"
                        land_area = to_float(row.get('토지면적(㎡)'))
                        land_pyeong = land_area / 3.3058 if land_area else 0
                        land_str = f"{land_pyeong:.0f}평 ({land_area:.1f}㎡)" if land_area else "면적미정"
                        floors = str(row.get('층수', '') or '')
                        usage = str(row.get('주용도', '') or '')
                        popup = (
                            '<button class="close-btn">&times;</button>'
                            + f'<div class="address">{addr_esc}</div>'
                            + f'<div class="info-row">매가: {price_display}</div>'
                            + f'<div class="info-row">토지: {land_str}</div>'
                            + f'<div class="info-row">층수: {html_module.escape(floors)}</div>'
                            + f'<div class="info-row">용도: {html_module.escape(usage)}</div>'
                            + f'<button class="btn-detail" data-record="{record_id}">상세내역보기</button>'
                            + f'<button class="btn-consult" data-address="{addr_esc}">이 매물 문의하기</button>'
                        )
                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': price_num,
                            'price_display': price_display,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                        })
                    elif property_type == 'jibhap':
                        kind = (row.get('종류', '') or '').strip()
                        txn = '전세' if kind == '전세' else ('월세' if kind == '월세' else '매매')
                        price_num = to_float(row.get('매가(만원)'))
                        deposit = to_float(row.get('보증금(만원)'))
                        monthly = to_float(row.get('월세(만원)'))
                        excl = to_float(row.get('전용면적(㎡)'))
                        rooms = to_float(row.get('방'))
                        if txn == '월세':
                            pd = f"월세 {deposit:.0f}/{monthly:.0f}만"
                        elif txn == '전세':
                            pd = f"전세 {deposit/10000:.1f}억" if deposit >= 10000 else f"전세 {deposit:.0f}만"
                        else:
                            pe = price_num / 10000
                            pd = f"매매 {pe:.1f}억" if pe >= 1 else (f"매매 {price_num:.0f}만" if price_num else "가격미정")
                        excl_str = f"{excl/3.3058:.0f}평 ({excl:.1f}㎡)" if excl else ""
                        popup = (
                            '<button class="close-btn">&times;</button>'
                            + f'<div class="address">{addr_esc}</div>'
                            + f'<div class="info-row">{pd}</div>'
                            + (f'<div class="info-row">전용: {excl_str}</div>' if excl_str else '')
                            + (f'<div class="info-row">방: {int(rooms)}개</div>' if rooms else '')
                            + f'<button class="btn-detail" data-record="{record_id}">상세내역보기</button>'
                            + f'<button class="btn-consult" data-address="{addr_esc}">이 매물 문의하기</button>'
                        )
                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': price_num or deposit,
                            'price_display': pd,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                        })
                    else:  # bubun
                        kind = (row.get('종류', '') or '').strip()
                        txn = '전세' if kind == '전세' else ('월세' if kind == '월세' else '매매')
                        deposit = to_float(row.get('보증금(만원)'))
                        monthly = to_float(row.get('월세(만원)'))
                        excl = to_float(row.get('전용면적'))
                        rooms = to_float(row.get('방'))
                        subtype = row.get('물건종류', '') or ''
                        if txn == '월세':
                            pd = f"월세 {deposit:.0f}/{monthly:.0f}만"
                        elif txn == '전세':
                            pd = f"전세 {deposit/10000:.1f}억" if deposit >= 10000 else f"전세 {deposit:.0f}만"
                        else:
                            pd = "매매"
                        excl_str = f"{excl/3.3058:.0f}평 ({excl:.1f}㎡)" if excl else ""
                        popup = (
                            '<button class="close-btn">&times;</button>'
                            + f'<div class="address">{addr_esc}</div>'
                            + f'<div class="info-row">{pd}</div>'
                            + (f'<div class="info-row">전용: {excl_str}</div>' if excl_str else '')
                            + (f'<div class="info-row">종류: {html_module.escape(subtype)}</div>' if subtype else '')
                            + (f'<div class="info-row">방: {int(rooms)}개</div>' if rooms else '')
                            + f'<button class="btn-detail" data-record="{record_id}">상세내역보기</button>'
                            + f'<button class="btn-consult" data-address="{addr_esc}">이 매물 문의하기</button>'
                        )
                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': deposit,
                            'price_display': pd,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                        })

    except Exception as e:
        import traceback
        logger.error(f"search-map DB 조회 실패: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

    import json as json_module
    kakao_key = import_kakao_key()
    map_html = _generate_search_map_html(kakao_key, markers)

    return jsonify({
        'map_html': map_html,
        'markers': markers,
        'count': len(markers),
        'statistics': {
            'markers_added': len(markers),
            'source': 'propsheet_db',
            'property_type': property_type
        }
    })
