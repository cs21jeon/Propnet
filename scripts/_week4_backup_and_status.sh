#!/bin/bash
# Week 4 Step 2 — 기존 좌표를 _orig 컬럼에 백업 (최초 1회)
# + 현재 bd_mgt_sn 매칭 현황 및 좌표 변경 여부 확인
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

echo "===== BEFORE 백업: 현재 매칭/좌표 현황 ====="
printf "%-40s %6s %6s %6s %6s\n" "table" "total" "coord" "bdmgt" "orig"
for T in "${TABLES[@]}"; do
  $PSQL -t -A -F '|' <<SQL
SELECT
  '$T',
  (SELECT count(*) FROM "$T"),
  (SELECT count(*) FROM "$T" WHERE coordinates_lat IS NOT NULL),
  (SELECT count(*) FROM "$T" WHERE bd_mgt_sn IS NOT NULL),
  (SELECT count(*) FROM "$T" WHERE coordinates_lat_orig IS NOT NULL)
;
SQL
done

echo
echo "===== 좌표 백업 수행 ====="
for T in "${TABLES[@]}"; do
  echo "[$T]"
  $PSQL -v ON_ERROR_STOP=1 <<SQL
UPDATE "$T"
   SET coordinates_lat_orig = coordinates_lat,
       coordinates_lon_orig = coordinates_lon
 WHERE coordinates_lat_orig IS NULL
   AND coordinates_lat IS NOT NULL;
SQL
done

echo
echo "===== AFTER 백업: 확인 ====="
printf "%-40s %6s %6s %6s %6s\n" "table" "total" "coord" "bdmgt" "orig"
for T in "${TABLES[@]}"; do
  $PSQL -t -A -F '|' <<SQL
SELECT
  '$T',
  (SELECT count(*) FROM "$T"),
  (SELECT count(*) FROM "$T" WHERE coordinates_lat IS NOT NULL),
  (SELECT count(*) FROM "$T" WHERE bd_mgt_sn IS NOT NULL),
  (SELECT count(*) FROM "$T" WHERE coordinates_lat_orig IS NOT NULL)
;
SQL
done

echo
echo "===== 좌표 변경 감지: orig와 현재 좌표 차이 (100m 이상) ====="
for T in "${TABLES[@]}"; do
  $PSQL -t -A -F '|' <<SQL
SELECT
  '$T' AS tbl,
  count(*) FILTER (WHERE coordinates_lat_orig IS NOT NULL
                      AND coordinates_lat IS NOT NULL
                      AND (abs(coordinates_lat - coordinates_lat_orig) > 0.001
                           OR abs(coordinates_lon - coordinates_lon_orig) > 0.001)) AS changed_100m,
  count(*) FILTER (WHERE coordinates_lat_orig IS NOT NULL
                      AND coordinates_lat IS NOT NULL
                      AND coordinates_lat = coordinates_lat_orig
                      AND coordinates_lon = coordinates_lon_orig) AS same
;
SQL
done
