#!/bin/bash
# Week 4 Step 1 — 백업 컬럼 추가 + 인덱스 (무중단 ALTER)
# C안: coordinates_lat_orig/lon_orig 추가 → 기존 좌표 백업 → 건물 중심 좌표로 덮어쓰기 예정
set -e
set -a
. /home/webapp/goldenrabbit/backend/.env
set +a

export PGPASSWORD="$DB_PASSWORD"
PSQL="psql -h $DB_HOST -U $DB_USER -d $DB_NAME"

TABLES=(
  goldenrabbit01_sales_building
  goldenrabbit01_sales_multi_unit
  propnet_multi_unit
  propnet_part
  propnet_single
  silverrabbit_multi_unit
  silverrabbit_part
  silverrabbit_single
)

for T in "${TABLES[@]}"; do
  echo "========================================="
  echo "[$T] 백업 컬럼 추가 시작"
  echo "========================================="

  # 1. 백업 컬럼 추가 (NULL allowed, 무중단)
  $PSQL -v ON_ERROR_STOP=1 <<SQL
ALTER TABLE "$T"
  ADD COLUMN IF NOT EXISTS coordinates_lat_orig DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS coordinates_lon_orig DOUBLE PRECISION;
SQL
  echo "  [$T] 컬럼 추가 완료"

  # 2. bd_mgt_sn 인덱스 (CONCURRENTLY - 무중단)
  # CONCURRENTLY는 트랜잭션 외부에서만 실행 가능
  IDX_NAME="idx_${T}_bdmgtsn"
  # 인덱스명이 63자 초과하지 않게 체크
  if [ ${#IDX_NAME} -gt 63 ]; then
    IDX_NAME="idx_$(echo -n "$T" | md5sum | cut -c1-16)_bdmgtsn"
  fi
  echo "  [$T] 인덱스명: $IDX_NAME"

  $PSQL -v ON_ERROR_STOP=1 -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS \"$IDX_NAME\" ON \"$T\" (bd_mgt_sn);" || echo "  [$T] 인덱스 생성 경고(이미 존재 가능)"

  echo "  [$T] 완료"
  echo
done

echo "===== 최종 스키마 확인 ====="
for T in "${TABLES[@]}"; do
  $PSQL -t -A -F '|' <<SQL
SELECT '$T' AS tbl,
  (SELECT count(column_name) FROM information_schema.columns WHERE table_name='$T' AND column_name='bd_mgt_sn') AS has_bdmgtsn,
  (SELECT count(column_name) FROM information_schema.columns WHERE table_name='$T' AND column_name='coordinates_lat_orig') AS has_lat_orig,
  (SELECT count(column_name) FROM information_schema.columns WHERE table_name='$T' AND column_name='coordinates_lon_orig') AS has_lon_orig,
  (SELECT count(*) FROM pg_indexes WHERE tablename='$T' AND indexdef LIKE '%bd_mgt_sn%') AS bdmgtsn_idx_count
;
SQL
done
echo "===== 스키마 확장 완료 ====="
