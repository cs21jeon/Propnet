#!/usr/bin/env python3
"""cadastral_service_dong_ext.py에 캐시 우선 조회 로직 추가."""

filepath = '/home/webapp/goldenrabbit/backend/property-manager/services/cadastral_service_dong_ext.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 이미 패치됨
if '_cache_lookup' in content:
    print('already patched')
    exit(0)

# 1) 캐시 조회 헬퍼 함수 추가 (get_buildings_by_pnu 바로 앞)
cache_fn = '''
def _cache_lookup(pnu: str) -> Optional[dict]:
    """
    building_dong_geometry 캐시에서 PNU 기반 동 리스트 조회.
    complex_parcels를 통해 같은 단지의 모든 PNU도 함께 조회.
    """
    try:
        from services.database_service import get_db_connection
    except ImportError:
        return None

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 같은 단지의 모든 PNU
                cur.execute(
                    "SELECT DISTINCT cp2.pnu "
                    "FROM complex_parcels cp1 "
                    "JOIN complex_parcels cp2 ON cp2.complex_pk = cp1.complex_pk "
                    "WHERE cp1.pnu = %s",
                    (pnu,),
                )
                related_pnus = [r[0] for r in cur.fetchall()]
                if not related_pnus:
                    related_pnus = [pnu]

                cur.execute(
                    "SELECT bd_mgt_sn, pnu, dong_nm, bld_nm, lat, lon, "
                    "geometry, grnd_flr, archarea "
                    "FROM building_dong_geometry "
                    "WHERE pnu = ANY(%s) ORDER BY dong_nm",
                    (related_pnus,),
                )
                rows = cur.fetchall()
                if not rows:
                    return None

                dongs = []
                for r in rows:
                    entry = {
                        'bd_mgt_sn': r[0], 'pnu': r[1],
                        'dong_nm': r[2], 'bld_nm': r[3],
                        'lat': float(r[4]) if r[4] else None,
                        'lon': float(r[5]) if r[5] else None,
                        'geometry': r[6],
                        'grnd_flr': r[7],
                        'archarea': float(r[8]) if r[8] else None,
                        'match': 'cache',
                    }
                    if entry['lat'] and entry['lon']:
                        dongs.append(entry)

                if not dongs:
                    return None

                avg_lat = sum(d['lat'] for d in dongs) / len(dongs)
                avg_lon = sum(d['lon'] for d in dongs) / len(dongs)
                logger.info(f'[CadastralExt] cache hit: pnu={pnu}, {len(dongs)} dongs')
                return {
                    'success': True,
                    'dongs': dongs,
                    'count': len(dongs),
                    'pnu': pnu,
                    'center': {'lat': avg_lat, 'lon': avg_lon},
                    'source': 'cache',
                }
    except Exception as e:
        logger.debug(f'[CadastralExt] cache lookup failed: {e}')
        return None


'''

target = 'def get_buildings_by_pnu(self, pnu: str, address: Optional[str] = None) -> dict:'
content = content.replace(target, cache_fn + target)

# 2) get_buildings_by_pnu 내부에 캐시 체크 삽입
old_block = (
    "    if not pnu or len(pnu) != 19:\n"
    "        return {'success': False, 'error': 'Invalid PNU'}\n"
    "\n"
    "    # 1. "
)
new_block = (
    "    if not pnu or len(pnu) != 19:\n"
    "        return {'success': False, 'error': 'Invalid PNU'}\n"
    "\n"
    "    # 0. cache lookup (building_dong_geometry)\n"
    "    cached = _cache_lookup(pnu)\n"
    "    if cached:\n"
    "        return cached\n"
    "\n"
    "    # 1. "
)
content = content.replace(old_block, new_block, 1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('patched OK')
