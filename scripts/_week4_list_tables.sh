#!/bin/bash
# Week 4 — 전체 agent 매물 테이블 목록 조회
set -a
. /home/webapp/goldenrabbit/backend/.env
set +a

PSQL="psql -h $DB_HOST -U $DB_USER -d $DB_NAME"
export PGPASSWORD="$DB_PASSWORD"

$PSQL -t -A -F '|' <<'SQL'
SELECT w.slug, d.table_name
  FROM databases d
  JOIN workspaces w ON d.workspace_id = w.id
 WHERE d.table_name IS NOT NULL
   AND w.slug IS NOT NULL
   AND w.slug <> 'template'
   AND (d.table_name LIKE '%sales_building'
        OR d.table_name LIKE '%sales_multi_unit'
        OR d.table_name LIKE '%_single'
        OR d.table_name LIKE '%_multi_unit'
        OR d.table_name LIKE '%_part')
 ORDER BY w.slug, d.table_name;
SQL
