#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase E — 매물 테이블에 complex_pk 컬럼 추가 + 배치 매칭.

대상 테이블:
  - {agent}_sales_building       (일반건물 / 단일 토지)
  - {agent}_sales_multi_unit     (집합건물)

작업 순서:
  1) ALTER TABLE ... ADD COLUMN IF NOT EXISTS complex_pk VARCHAR(20) NULL  (무중단)
  2) CREATE INDEX IF NOT EXISTS ... CONCURRENTLY
  3) 기존 매물 배치 매칭:
     - bd_mgt_sn이 있으면: building_dong_geometry.pnu → complex_parcels → complex_pk
     - 없으면: 지번주소 + 건물명 → complex_master 검색 (유사도 기반)

사용:
  # 모든 agent 테이블에 컬럼 추가 + 인덱스
  python phase_e_add_complex_pk.py --apply-schema

  # 배치 매칭 (모든 agent)
  python phase_e_add_complex_pk.py --backfill

  # 특정 agent만
  python phase_e_add_complex_pk.py --backfill --agent goldenrabbit01

  # dry-run (변경 없음)
  python phase_e_add_complex_pk.py --apply-schema --dry-run
  python phase_e_add_complex_pk.py --backfill --dry-run

CRITICAL:
  - ALTER는 AccessExclusiveLock을 짧게 잡음 (ADD COLUMN NULL + default 없음 = 즉시)
  - CREATE INDEX CONCURRENTLY는 트랜잭션 밖에서 실행 필요 → autocommit
  - FK는 soft (일관성 체크만, ON DELETE 동작 없음)
"""
import argparse
import logging
import os
import re
import sys
import time

import psycopg2
import psycopg2.extras

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('phase_e')


# ------------------------------------------------------------------------------
# DB
# ------------------------------------------------------------------------------
def load_env_file(path='/home/webapp/goldenrabbit/backend/.env'):
    if not os.path.isfile(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())


def get_conn(autocommit=False):
    load_env_file()
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        port=int(os.environ.get('DB_PORT', '5432')),
        dbname=os.environ.get('DB_NAME', 'goldenrabbit_db'),
        user=os.environ.get('DB_USER', 'goldenrabbit_user'),
        password=os.environ.get('DB_PASSWORD', ''),
    )
    if autocommit:
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


# ------------------------------------------------------------------------------
# 대상 테이블 탐색
# ------------------------------------------------------------------------------
def list_sales_tables(conn, agent_slug=None):
    """모든 agent의 매물 테이블 이름 조회."""
    with conn.cursor() as cur:
        if agent_slug:
            cur.execute(
                """SELECT tablename FROM pg_tables
                   WHERE schemaname='public'
                     AND (tablename = %s OR tablename = %s)
                   ORDER BY tablename""",
                (f'{agent_slug}_sales_building', f'{agent_slug}_sales_multi_unit'),
            )
        else:
            cur.execute(
                """SELECT tablename FROM pg_tables
                   WHERE schemaname='public'
                     AND (tablename LIKE %s OR tablename LIKE %s)
                   ORDER BY tablename""",
                ('%_sales_building', '%_sales_multi_unit'),
            )
        return [r[0] for r in cur.fetchall()]


def has_column(conn, table, column):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name=%s AND column_name=%s""",
            (table, column),
        )
        return cur.fetchone() is not None


# ------------------------------------------------------------------------------
# 스키마 변경 (무중단)
# ------------------------------------------------------------------------------
def apply_schema(agent_slug=None, dry_run=False):
    conn = get_conn(autocommit=True)  # CONCURRENTLY 때문에 autocommit 필수
    tables = list_sales_tables(conn, agent_slug)
    if not tables:
        log.warning('대상 테이블이 없습니다.')
        conn.close()
        return

    log.info('대상 테이블: %s', ', '.join(tables))

    for t in tables:
        if has_column(conn, t, 'complex_pk'):
            log.info('[%s] complex_pk 이미 존재 — skip ADD COLUMN', t)
        else:
            sql = f'ALTER TABLE "{t}" ADD COLUMN complex_pk VARCHAR(20) NULL'
            log.info('[%s] %s', t, sql)
            if not dry_run:
                with conn.cursor() as cur:
                    cur.execute(sql)

        idx_name = f'idx_{t}_complex_pk'
        # 길이 제한 (PostgreSQL identifier 63자)
        if len(idx_name) > 63:
            idx_name = idx_name[:63]
        sql_idx = (
            f'CREATE INDEX CONCURRENTLY IF NOT EXISTS "{idx_name}" '
            f'ON "{t}" (complex_pk) WHERE complex_pk IS NOT NULL'
        )
        log.info('[%s] %s', t, sql_idx)
        if not dry_run:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql_idx)
            except psycopg2.errors.DuplicateTable:
                log.info('[%s] 인덱스 이미 존재 — skip', t)

    conn.close()
    log.info('스키마 변경 완료')


# ------------------------------------------------------------------------------
# 배치 매칭
# ------------------------------------------------------------------------------
# 매칭 전략:
#  1) bd_mgt_sn(표제부 PK) → building_dong_geometry.bd_mgt_sn → pnu
#     → complex_parcels.pnu → complex_pk (가장 정확)
#  2) 지번주소 parse → PNU 추정 → complex_parcels
#  3) 건물명 + 시군구 → complex_master 유사도 검색 (fallback)

# bd_mgt_sn → pnu → complex_pk 경로
SQL_BATCH_MATCH_BY_BDMGTSN = '''
WITH targets AS (
    SELECT t.id, t.bd_mgt_sn, t."지번 주소" AS jibun
    FROM "{table}" t
    WHERE t.complex_pk IS NULL
      AND t.bd_mgt_sn IS NOT NULL
      AND t.bd_mgt_sn <> ''
    LIMIT %s
),
matched AS (
    SELECT DISTINCT ON (tg.id)
           tg.id,
           cp.complex_pk
    FROM targets tg
    JOIN building_dong_geometry bg ON bg.bd_mgt_sn = tg.bd_mgt_sn
    JOIN complex_parcels cp ON cp.pnu = bg.pnu
    ORDER BY tg.id, cp.is_primary DESC, cp.confidence DESC NULLS LAST
)
UPDATE "{table}" AS t
SET complex_pk = m.complex_pk
FROM matched m
WHERE t.id = m.id
RETURNING t.id, t.complex_pk;
'''


# 지번주소 매칭: "송파구 신천동 17-4" 같은 패턴
# -> complex_master.address_jibun ILIKE '%신천동 17%'
#    AND name ILIKE '%건물명%'  (있으면)
SQL_BATCH_MATCH_BY_ADDR = '''
WITH targets AS (
    SELECT t.id, t."지번 주소" AS jibun, t."건물명" AS bldg_name
    FROM "{table}" t
    WHERE t.complex_pk IS NULL
      AND t."지번 주소" IS NOT NULL
      AND t."지번 주소" <> ''
    LIMIT %s
),
parsed AS (
    SELECT id, jibun, bldg_name,
           -- 동명 + 번지 추출 (예: "신천동 17-4" → "신천동 17")
           regexp_replace(jibun, E'^.*?(\\S+동)\\s+(\\d+)(?:-\\d+)?.*$', '\\1 \\2') AS dong_bun
    FROM targets
),
matched AS (
    SELECT DISTINCT ON (p.id)
           p.id,
           cm.complex_pk,
           similarity(cm.name, COALESCE(p.bldg_name, '')) AS name_sim
    FROM parsed p
    JOIN complex_master cm
      ON cm.address_jibun ILIKE '%%' || p.dong_bun || '%%'
    WHERE p.bldg_name IS NULL
       OR p.bldg_name = ''
       OR similarity(cm.name, p.bldg_name) > 0.3
       OR cm.name ILIKE '%%' || p.bldg_name || '%%'
       OR p.bldg_name ILIKE '%%' || cm.name || '%%'
    ORDER BY p.id, name_sim DESC NULLS LAST, cm.household_count DESC NULLS LAST
)
UPDATE "{table}" AS t
SET complex_pk = m.complex_pk
FROM matched m
WHERE t.id = m.id
RETURNING t.id, t.complex_pk;
'''


def backfill_table(conn, table, batch_size=500, dry_run=False):
    """테이블 하나에 대해 배치 매칭 수행."""
    total_matched = 0

    # --- 1단계: bd_mgt_sn 기반 매칭 (정확도 최고) ---
    log.info('[%s] 1단계: bd_mgt_sn 기반 매칭', table)
    sql1 = SQL_BATCH_MATCH_BY_BDMGTSN.format(table=table)
    while True:
        if dry_run:
            # dry-run: SELECT로 대상 수만 파악
            with conn.cursor() as cur:
                cur.execute(
                    f'SELECT count(*) FROM "{table}" WHERE complex_pk IS NULL AND bd_mgt_sn IS NOT NULL AND bd_mgt_sn <> \'\''
                )
                cnt = cur.fetchone()[0]
            log.info('[%s] [DRY-RUN] bd_mgt_sn 대상: %d 건', table, cnt)
            break

        with conn.cursor() as cur:
            cur.execute(sql1, (batch_size,))
            rows = cur.fetchall()
        conn.commit()
        n = len(rows)
        total_matched += n
        log.info('[%s] bd_mgt_sn 배치: +%d (누적 %d)', table, n, total_matched)
        if n == 0:
            break

    # --- 2단계: 지번주소 + 건물명 기반 매칭 (fallback) ---
    log.info('[%s] 2단계: 지번주소+건물명 기반 매칭', table)
    sql2 = SQL_BATCH_MATCH_BY_ADDR.format(table=table)
    batches = 0
    while True:
        if dry_run:
            with conn.cursor() as cur:
                cur.execute(
                    f'SELECT count(*) FROM "{table}" WHERE complex_pk IS NULL AND "지번 주소" IS NOT NULL AND "지번 주소" <> \'\''
                )
                cnt = cur.fetchone()[0]
            log.info('[%s] [DRY-RUN] 지번 대상: %d 건', table, cnt)
            break

        with conn.cursor() as cur:
            try:
                cur.execute(sql2, (batch_size,))
                rows = cur.fetchall()
            except Exception as e:
                log.warning('[%s] 지번 매칭 오류(배치 %d): %s', table, batches, e)
                conn.rollback()
                break
        conn.commit()
        n = len(rows)
        total_matched += n
        batches += 1
        log.info('[%s] 지번 배치 %d: +%d (누적 %d)', table, batches, n, total_matched)
        if n == 0:
            break
        if batches >= 50:
            log.warning('[%s] 지번 배치 50회 도달, 중단', table)
            break

    # --- 최종 집계 ---
    with conn.cursor() as cur:
        cur.execute(f'SELECT count(*) FROM "{table}" WHERE complex_pk IS NOT NULL')
        matched_count = cur.fetchone()[0]
        cur.execute(f'SELECT count(*) FROM "{table}"')
        total_count = cur.fetchone()[0]
    coverage = (matched_count / total_count * 100.0) if total_count else 0.0
    log.info('[%s] 완료: 이번 실행 +%d, 누적 매칭 %d/%d (%.1f%%)',
             table, total_matched, matched_count, total_count, coverage)

    return total_matched


def backfill_all(agent_slug=None, batch_size=500, dry_run=False):
    conn = get_conn()
    tables = list_sales_tables(conn, agent_slug)
    if not tables:
        log.warning('대상 테이블이 없습니다.')
        conn.close()
        return

    # 스키마 확인
    for t in tables:
        if not has_column(conn, t, 'complex_pk'):
            log.error('[%s] complex_pk 컬럼 없음. 먼저 --apply-schema 실행 필요.', t)
            conn.close()
            sys.exit(1)

    grand_total = 0
    for t in tables:
        grand_total += backfill_table(conn, t, batch_size=batch_size, dry_run=dry_run)

    conn.close()
    log.info('Backfill 전체 완료: 추가 매칭 %d', grand_total)


# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description='Phase E — matching columns + backfill')
    p.add_argument('--apply-schema', action='store_true',
                   help='ADD COLUMN complex_pk + CREATE INDEX CONCURRENTLY')
    p.add_argument('--backfill', action='store_true',
                   help='기존 매물에 complex_pk 일괄 매칭')
    p.add_argument('--agent', default=None,
                   help='특정 agent_slug만 처리 (기본: 전체)')
    p.add_argument('--batch-size', type=int, default=500)
    p.add_argument('--dry-run', action='store_true')
    return p.parse_args()


def main():
    args = parse_args()
    if not (args.apply_schema or args.backfill):
        log.error('--apply-schema 또는 --backfill 중 하나를 지정하세요')
        sys.exit(1)

    if args.apply_schema:
        apply_schema(agent_slug=args.agent, dry_run=args.dry_run)

    if args.backfill:
        backfill_all(
            agent_slug=args.agent,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )


if __name__ == '__main__':
    main()
