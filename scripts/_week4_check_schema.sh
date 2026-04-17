#!/bin/bash
# Week 4 — 각 테이블 스키마 및 매칭 현황 조회
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
  echo "===== $T ====="
  $PSQL -t -A -F '|' <<SQL
SELECT
  '$T' AS tbl,
  (SELECT count(*) FROM "$T") AS total,
  (SELECT count(*) FROM "$T" WHERE coordinates_lat IS NOT NULL) AS has_coord,
  (SELECT count(column_name) FROM information_schema.columns WHERE table_name='$T' AND column_name='bd_mgt_sn') AS has_bdmgtsn_col,
  (SELECT count(column_name) FROM information_schema.columns WHERE table_name='$T' AND column_name='coordinates_lat_orig') AS has_lat_orig_col,
  (SELECT count(column_name) FROM information_schema.columns WHERE table_name='$T' AND column_name='coordinates_lon_orig') AS has_lon_orig_col
;
SQL
  echo
  echo "--- columns ---"
  $PSQL -t -A <<SQL
SELECT string_agg(column_name, ', ' ORDER BY ordinal_position)
  FROM information_schema.columns
 WHERE table_schema='public' AND table_name='$T';
SQL
  echo
done
