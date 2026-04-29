#!/usr/bin/env python3
"""app_api.py의 map_click_jibun에 complex_parcels 역매핑 + 단지정보 추가."""

filepath = '/home/webapp/goldenrabbit/backend/property-manager/routes/app_api.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

if 'complex_info' in content and 'complex_parcels' in content:
    print('already patched')
    exit(0)

# 기존 코드
old_code = '''        # VWorld 역지오코딩
        result = cadastral_service.get_jibun_from_coords(lat, lng)

        return jsonify(result)

    except Exception as e:
        logger.error(f"[앱] 지도 클릭 오류: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500'''

# 새 코드: 역지오코딩 후 complex_parcels 역매핑 추가
new_code = '''        # VWorld 역지오코딩
        result = cadastral_service.get_jibun_from_coords(lat, lng)

        # complex_parcels 역매핑: PNU → 소속 단지 검색
        if result.get('success') and result.get('jibun_info', {}).get('pnu'):
            pnu = result['jibun_info']['pnu']
            try:
                from services.database_service import get_db_connection
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT cm.complex_pk, cm.name, cm.household_count, "
                            "cm.dong_count, cm.address_jibun, cm.representative_pnu, "
                            "cm.center_lat, cm.center_lon "
                            "FROM complex_parcels cp "
                            "JOIN complex_master cm ON cm.complex_pk = cp.complex_pk "
                            "WHERE cp.pnu = %s LIMIT 1",
                            (pnu,),
                        )
                        row = cur.fetchone()
                        if row:
                            result['complex_info'] = {
                                'complex_pk': str(row[0]),
                                'name': row[1],
                                'household_count': row[2],
                                'dong_count': row[3],
                                'address': row[4],
                                'representative_pnu': row[5],
                                'center_lat': float(row[6]) if row[6] else None,
                                'center_lon': float(row[7]) if row[7] else None,
                            }
                            # 부속지번이면 본번 PNU도 제공
                            if row[5] and row[5] != pnu:
                                result['jibun_info']['main_pnu'] = row[5]
                            logger.info(f"[앱] 단지 매칭: {pnu} → {row[1]} ({row[2]}세대)")
            except Exception as e:
                logger.warning(f"[앱] 단지 매칭 실패: {e}")

        return jsonify(result)

    except Exception as e:
        logger.error(f"[앱] 지도 클릭 오류: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('patched OK')
else:
    print('ERROR: target code block not found')
    exit(1)
