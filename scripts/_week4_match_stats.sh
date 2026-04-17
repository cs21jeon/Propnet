#!/bin/bash
# Week 4 — agent별 매칭률 및 좌표 변화 통계
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

echo "table                                     total  coord  bdmgt  orig   match%   moved>=100m"
for T in "${TABLES[@]}"; do
  $PSQL -t -A -F '|' <<SQL
SELECT
  rpad('$T', 41, ' '),
  lpad((SELECT count(*)::text FROM "$T"), 6, ' '),
  lpad((SELECT count(*)::text FROM "$T" WHERE coordinates_lat IS NOT NULL), 6, ' '),
  lpad((SELECT count(*)::text FROM "$T" WHERE bd_mgt_sn IS NOT NULL), 6, ' '),
  lpad((SELECT count(*)::text FROM "$T" WHERE coordinates_lat_orig IS NOT NULL), 6, ' '),
  lpad(
    CASE WHEN (SELECT count(*) FROM "$T") = 0 THEN '0%'
         ELSE round(100.0 * (SELECT count(*) FROM "$T" WHERE bd_mgt_sn IS NOT NULL)::numeric
                    / (SELECT count(*) FROM "$T"), 1)::text || '%'
    END, 8, ' '),
  lpad(
    (SELECT count(*)::text FROM "$T"
      WHERE coordinates_lat_orig IS NOT NULL
        AND coordinates_lat IS NOT NULL
        AND (abs(coordinates_lat - coordinates_lat_orig) > 0.001
             OR abs(coordinates_lon - coordinates_lon_orig) > 0.001)), 12, ' ')
;
SQL
done
