#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 4-5 — template(샘플) 워크스페이스 전용 dry-run 매칭 스크립트.

warm_building_cache.py는 w.slug <> 'template' 필터가 있어 샘플을 제외함.
이 스크립트는 오직 샘플 DB 3개 (template_single, template_part, template_multi_unit)에
대해 기존 매칭 함수 (_normalize_dong, _match_dong, update_records_with_dong)를
dry-run 모드로 호출하여 매칭 결과만 리포트함.

실제 UPDATE는 수행하지 않음 (dry-run 고정).

Usage:
    python _week4_5_template_dryrun.py
"""
import logging
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(HERE, '..', 'backend', 'property-manager'))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# warm_building_cache.py 위치도 추가
if HERE not in sys.path:
    sys.path.insert(0, HERE)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger('template_dryrun')

from services.cadastral_service import CadastralService
from services import cadastral_service_dong_ext  # noqa: F401
from services.database_service import get_db_connection
from warm_building_cache import (
    list_jibuns_from_table,
    jibun_to_pnu,
    update_records_with_dong,
)

TEMPLATE_TABLES = [
    ('template', 'template_single'),
    ('template', 'template_part'),
    ('template', 'template_multi_unit'),
]


def main():
    stats = {
        'tables_total': len(TEMPLATE_TABLES),
        'jibun_total': 0,
        'pnu_resolved': 0,
        'pnu_failed': 0,
        'dongs_cached': 0,
        'records_updated': 0,
        'errors': [],
    }
    cadastral = CadastralService()

    with get_db_connection() as conn:
        for slug, table_name in TEMPLATE_TABLES:
            logger.info(f'--- agent={slug} table={table_name} (DRY-RUN) ---')
            jibuns = list_jibuns_from_table(conn, table_name)
            stats['jibun_total'] += len(jibuns)
            logger.info(f'  유니크 지번: {len(jibuns)}건')
            if not jibuns:
                continue

            unique_jibuns = sorted({j[0] for j in jibuns})
            logger.info(f'  PNU 해석 대상: {len(unique_jibuns)}건')

            pnu_map = {}
            for jibun in unique_jibuns:
                pnu = jibun_to_pnu(cadastral, jibun)
                if pnu:
                    pnu_map[jibun] = pnu
                    stats['pnu_resolved'] += 1
                    logger.info(f'    PNU OK: {jibun} → {pnu}')
                else:
                    stats['pnu_failed'] += 1
                    logger.warning(f'    PNU FAIL: {jibun}')
                time.sleep(0.3)

            for jibun, pnu in pnu_map.items():
                try:
                    res = cadastral.get_buildings_by_pnu(pnu, address=jibun)
                    if not res.get('success'):
                        stats['errors'].append(f'{slug}/{jibun}: {res.get("error")}')
                        continue
                    dongs = res.get('dongs', [])
                    stats['dongs_cached'] += len(dongs)
                    logger.info(f'  pnu={pnu} jibun={jibun} dongs_found={len(dongs)}')
                    for d in dongs:
                        logger.info(
                            f'    - bd_mgt_sn={d.get("bd_mgt_sn")} '
                            f'dong={d.get("dong_nm")!r} bld={d.get("bld_nm")!r} '
                            f'lat={d.get("lat")} lon={d.get("lon")}'
                        )
                    # dry_run=True 고정
                    updated = update_records_with_dong(
                        conn, table_name, jibun, dongs, dry_run=True, stats=stats
                    )
                    stats['records_updated'] += updated
                except Exception as e:
                    logger.exception(f'    에러 ({slug}/{jibun}): {e}')
                    stats['errors'].append(f'{slug}/{jibun}: {e}')
                time.sleep(0.3)

    logger.info('=== DRY-RUN 완료 ===')
    logger.info(f'대상 테이블: {stats["tables_total"]}')
    logger.info(f'유니크 지번: {stats["jibun_total"]}')
    logger.info(f'PNU 해석 성공: {stats["pnu_resolved"]}')
    logger.info(f'PNU 해석 실패: {stats["pnu_failed"]}')
    logger.info(f'캐시된 동 수: {stats["dongs_cached"]}')
    logger.info(f'업데이트될 레코드(시뮬레이션): {stats["records_updated"]}')
    logger.info(f'매칭 성공: {stats.get("match_ok", 0)}')
    logger.info(f'매칭 실패: {stats.get("match_fail", 0)}')
    if stats.get('change_count'):
        avg = stats.get('total_change_m', 0) / stats['change_count']
        logger.info(f'좌표 변경 평균(예상): {avg:.1f}m (총 {stats["change_count"]}건)')
    if stats.get('large_changes'):
        logger.warning(f'큰 좌표 변경 예상 (>100m) {len(stats["large_changes"])}건:')
        for e in stats['large_changes']:
            logger.warning(f'  {e}')
    if stats.get('match_fail_samples'):
        logger.info(f'매칭 실패 샘플:')
        for e in stats['match_fail_samples']:
            logger.info(f'  {e}')
    if stats['errors']:
        logger.warning(f'에러 {len(stats["errors"])}건:')
        for e in stats['errors']:
            logger.warning(f'  {e}')


if __name__ == '__main__':
    main()
