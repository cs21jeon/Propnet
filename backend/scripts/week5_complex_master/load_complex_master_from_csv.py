#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 5 — 한국부동산원 공동주택 단지 식별정보 CSV → complex_master 적재.

CSV (apt_basic_info_YYYYMMDD.csv) 컬럼:
    단지고유번호, 필지고유번호, 주소, 단지명_공시가격, 단지명_건축물대장,
    단지명_도로명주소, 단지종류, 동수, 세대수, 사용승인일

UPSERT 전략:
    complex_master   : complex_pk PK로 UPSERT (raw_row 덮어씀)
    complex_aliases  : (complex_pk, alias_type, name, year) UNIQUE → ON CONFLICT DO NOTHING
    complex_parcels  : (complex_pk, pnu) UNIQUE → ON CONFLICT DO NOTHING (is_primary=TRUE 유지)

사용 예시:
    python load_complex_master_from_csv.py \\
        --csv /home/webapp/goldenrabbit/data/complex_master/raw/apt_basic_info_20250918.csv \\
        --sigungu 11710,11590,11620 \\
        --dry-run

    python load_complex_master_from_csv.py \\
        --csv /home/webapp/goldenrabbit/data/complex_master/raw/apt_basic_info_20250918.csv \\
        --sido 11

    python load_complex_master_from_csv.py \\
        --csv /home/webapp/goldenrabbit/data/complex_master/raw/apt_basic_info_20250918.csv
"""
import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime

import psycopg2
import psycopg2.extras

# ------------------------------------------------------------------------------
# 로깅
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('complex_loader')


# ------------------------------------------------------------------------------
# DB 연결 정보 (.env 또는 환경변수)
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


def get_conn():
    load_env_file()
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        port=int(os.environ.get('DB_PORT', '5432')),
        dbname=os.environ.get('DB_NAME', 'goldenrabbit_db'),
        user=os.environ.get('DB_USER', 'goldenrabbit_user'),
        password=os.environ.get('DB_PASSWORD', ''),
    )


# ------------------------------------------------------------------------------
# 헬퍼
# ------------------------------------------------------------------------------
CSV_HEADERS = [
    '단지고유번호', '필지고유번호', '주소', '단지명_공시가격', '단지명_건축물대장',
    '단지명_도로명주소', '단지종류', '동수', '세대수', '사용승인일',
]


def to_int(v):
    if v is None:
        return None
    v = v.strip() if isinstance(v, str) else v
    if v == '' or v == 'null':
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def to_date(v):
    if not v:
        return None
    v = v.strip()
    if not v:
        return None
    for fmt in ('%Y-%m-%d', '%Y%m%d', '%Y/%m/%d'):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def nz(s):
    """None-safe strip."""
    if s is None:
        return ''
    return s.strip() if isinstance(s, str) else str(s)


def pnu_sigungu(pnu):
    """PNU 앞 5자리 = 시군구 코드."""
    if not pnu or len(pnu) < 5:
        return None
    return pnu[:5]


def pnu_sido(pnu):
    """PNU 앞 2자리 = 시도 코드."""
    if not pnu or len(pnu) < 2:
        return None
    return pnu[:2]


# ------------------------------------------------------------------------------
# 업서트 SQL
# ------------------------------------------------------------------------------
SQL_UPSERT_MASTER = """
INSERT INTO complex_master (
    complex_pk, name, complex_type_code, address_jibun, representative_pnu,
    dong_count, household_count, completion_date, source, confidence, raw_row
) VALUES %s
ON CONFLICT (complex_pk) DO UPDATE SET
    name = EXCLUDED.name,
    complex_type_code = EXCLUDED.complex_type_code,
    address_jibun = EXCLUDED.address_jibun,
    representative_pnu = EXCLUDED.representative_pnu,
    dong_count = EXCLUDED.dong_count,
    household_count = EXCLUDED.household_count,
    completion_date = EXCLUDED.completion_date,
    source = EXCLUDED.source,
    raw_row = EXCLUDED.raw_row,
    updated_at = NOW()
"""

SQL_UPSERT_ALIAS = """
INSERT INTO complex_aliases (complex_pk, alias_type, name, year, source) VALUES %s
ON CONFLICT (complex_pk, alias_type, name, (COALESCE(year, 0))) DO NOTHING
"""

SQL_UPSERT_PARCEL = """
INSERT INTO complex_parcels (complex_pk, pnu, is_primary, source, confidence) VALUES %s
ON CONFLICT (complex_pk, pnu) DO NOTHING
"""


# ------------------------------------------------------------------------------
# 배치 처리
# ------------------------------------------------------------------------------
def flush_batch(conn, master_rows, alias_rows, parcel_rows, dry_run=False):
    if not master_rows and not alias_rows and not parcel_rows:
        return 0

    if dry_run:
        log.info(
            '[DRY-RUN] master=%d aliases=%d parcels=%d (미적용)',
            len(master_rows), len(alias_rows), len(parcel_rows),
        )
        return len(master_rows)

    with conn.cursor() as cur:
        if master_rows:
            psycopg2.extras.execute_values(
                cur, SQL_UPSERT_MASTER, master_rows, page_size=500,
            )
        if alias_rows:
            psycopg2.extras.execute_values(
                cur, SQL_UPSERT_ALIAS, alias_rows, page_size=500,
            )
        if parcel_rows:
            psycopg2.extras.execute_values(
                cur, SQL_UPSERT_PARCEL, parcel_rows, page_size=500,
            )
    conn.commit()
    return len(master_rows)


# ------------------------------------------------------------------------------
# 메인 로직
# ------------------------------------------------------------------------------
def load_csv(
    csv_path,
    sido_filter=None,
    sigungu_filter=None,
    batch_size=2000,
    dry_run=False,
    source_tag='reb_csv_20250918',
):
    sido_set = set(sido_filter) if sido_filter else None
    sigungu_set = set(sigungu_filter) if sigungu_filter else None

    log.info('CSV 파일: %s', csv_path)
    log.info('필터: sido=%s  sigungu=%s', sido_set, sigungu_set)
    log.info('배치 크기: %d  DRY-RUN: %s', batch_size, dry_run)

    # 파일 크기 예측 (라인 수 셈)
    file_size = os.path.getsize(csv_path)
    log.info('파일 크기: %.1f MB', file_size / 1024 / 1024)

    conn = None if dry_run else get_conn()

    master_batch = []
    alias_batch = []
    parcel_batch = []

    total_read = 0
    total_inserted = 0
    total_skipped = 0
    total_filtered = 0
    start_time = time.time()
    batch_start = time.time()

    # utf-8-sig → BOM 제거
    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)

        # 헤더 검증
        expected = set(CSV_HEADERS)
        actual = set(reader.fieldnames or [])
        missing = expected - actual
        if missing:
            log.error('CSV 헤더 누락: %s', missing)
            log.error('실제 헤더: %s', reader.fieldnames)
            return

        for row in reader:
            total_read += 1

            complex_pk = nz(row.get('단지고유번호'))
            rep_pnu = nz(row.get('필지고유번호'))
            address = nz(row.get('주소'))
            name_gongsi = nz(row.get('단지명_공시가격'))
            name_bldreg = nz(row.get('단지명_건축물대장'))
            name_road = nz(row.get('단지명_도로명주소'))
            type_code = to_int(row.get('단지종류'))

            if not complex_pk or not rep_pnu or not address:
                total_skipped += 1
                continue

            # 지역 필터
            if sido_set and pnu_sido(rep_pnu) not in sido_set:
                total_filtered += 1
                continue
            if sigungu_set and pnu_sigungu(rep_pnu) not in sigungu_set:
                total_filtered += 1
                continue

            # 기본 name은 공시가격 우선, 없으면 건축물대장, 도로명 순
            primary_name = name_gongsi or name_bldreg or name_road
            if not primary_name:
                total_skipped += 1
                continue

            if type_code not in (1, 2, 3):
                # CSV 원본에 0/빈값 있으면 스킵
                total_skipped += 1
                continue

            dong_count = to_int(row.get('동수'))
            household = to_int(row.get('세대수'))
            completion = to_date(row.get('사용승인일'))

            # raw_row 원본 보관 (감사용)
            raw_json = json.dumps(row, ensure_ascii=False)

            master_batch.append((
                complex_pk, primary_name, type_code, address, rep_pnu,
                dong_count, household, completion, source_tag, 1.00, raw_json,
            ))

            # aliases — 3종 중 비어있지 않은 것을 type별로, 단 같은 (type,name) 중복은 DB UNIQUE가 처리
            # 동일한 이름 여러 타입 중복도 각 타입별로 저장 (파크리오 == 파크리오 == 파크리오 허용)
            seen_alias = set()
            for alias_type, name in (
                ('gongsi', name_gongsi),
                ('bldreg', name_bldreg),
                ('road', name_road),
            ):
                if not name:
                    continue
                key = (alias_type, name)
                if key in seen_alias:
                    continue
                seen_alias.add(key)
                alias_batch.append((complex_pk, alias_type, name, None, source_tag))

            # 대표 PNU
            parcel_batch.append((
                complex_pk, rep_pnu, True, source_tag, 1.00,
            ))

            # 배치 flush
            if len(master_batch) >= batch_size:
                inserted = flush_batch(
                    conn, master_batch, alias_batch, parcel_batch, dry_run=dry_run,
                )
                total_inserted += inserted
                master_batch.clear()
                alias_batch.clear()
                parcel_batch.clear()

                if total_inserted % 10000 < batch_size:
                    elapsed = time.time() - batch_start
                    rate = batch_size / elapsed if elapsed > 0 else 0
                    pct = total_read / 307408 * 100  # 307408 = 예상 row수
                    log.info(
                        '진행: read=%d 적재=%d skip=%d filter=%d (%.1f%%, %.0f rows/s)',
                        total_read, total_inserted, total_skipped, total_filtered, pct, rate,
                    )
                    batch_start = time.time()

    # 잔여 배치
    if master_batch:
        inserted = flush_batch(
            conn, master_batch, alias_batch, parcel_batch, dry_run=dry_run,
        )
        total_inserted += inserted

    if conn:
        conn.close()

    total_elapsed = time.time() - start_time
    log.info('=' * 60)
    log.info('완료')
    log.info('  총 read:   %d', total_read)
    log.info('  적재:      %d', total_inserted)
    log.info('  skip:      %d (필수 필드 누락 등)', total_skipped)
    log.info('  filtered:  %d (지역 필터)', total_filtered)
    log.info('  경과시간:  %.1f초 (%.0f rows/s)', total_elapsed, total_read / max(total_elapsed, 0.001))
    log.info('=' * 60)


# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description='공동주택 단지 CSV 적재')
    p.add_argument('--csv', required=True, help='CSV 파일 경로')
    p.add_argument('--sido', default=None,
                   help='시도 코드 2자리 CSV (예: 11 / 11,26,27)')
    p.add_argument('--sigungu', default=None,
                   help='시군구 코드 5자리 CSV (예: 11710 / 11710,11590,11620)')
    p.add_argument('--batch-size', type=int, default=2000)
    p.add_argument('--dry-run', action='store_true', help='DB 미적용, 로그만 출력')
    p.add_argument('--source-tag', default='reb_csv_20250918',
                   help='source 컬럼에 기록할 태그')
    return p.parse_args()


def main():
    args = parse_args()

    sido_filter = None
    if args.sido:
        sido_filter = [s.strip() for s in args.sido.split(',') if s.strip()]

    sigungu_filter = None
    if args.sigungu:
        sigungu_filter = [s.strip() for s in args.sigungu.split(',') if s.strip()]

    if not os.path.isfile(args.csv):
        log.error('CSV 파일 없음: %s', args.csv)
        sys.exit(1)

    load_csv(
        csv_path=args.csv,
        sido_filter=sido_filter,
        sigungu_filter=sigungu_filter,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        source_tag=args.source_tag,
    )


if __name__ == '__main__':
    main()
