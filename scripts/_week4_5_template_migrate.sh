#!/bin/bash
# Week 4-5 — 샘플(template) 워크스페이스 부동산 DB 3개 스키마 동기화
# - bd_mgt_sn, coordinates_lat_orig, coordinates_lon_orig 컬럼 추가
# - bd_mgt_sn 인덱스 생성 (CONCURRENTLY, 무중단)
# - 기존 coordinates_lat/lon → _orig 백업
set -e
set -a
. /home/webapp/goldenrabbit/backend/.env
set +a

# PGPASSWORD은 반드시 $DB_PASSWORD (서버 .env 로드) 에서만 주입.
# 하드코딩 금지 — pre-commit hook으로 차단됨.
export PGPASSWORD="$DB_PASSWORD"
PSQL="psql -h $DB_HOST -U $DB_USER -d $DB_NAME"

TABLES=(
  template_single
  template_part
  template_multi_unit
)

echo "===== [Week 4-5] template 테이블 3개 스키마 동기화 시작 ====="
for T in "${TABLES[@]}"; do
  echo "========================================="
  echo "[$T] 백업 컬럼 + bd_mgt_sn 추가"
  echo "========================================="

  # 1) ALTER TABLE (트랜잭션 내 가능, 무중단)
  $PSQL -v ON_ERROR_STOP=1 <<SQL
ALTER TABLE "$T"
  ADD COLUMN IF NOT EXISTS bd_mgt_sn VARCHAR(32),
  ADD COLUMN IF NOT EXISTS coordinates_lat_orig DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS coordinates_lon_orig DOUBLE PRECISION;
SQL
  echo "  [$T] 컬럼 추가 OK"

  # 2) bd_mgt_sn 인덱스 (CONCURRENTLY - 트랜잭션 밖에서 실행)
  IDX_NAME="idx_${T}_bdmgtsn"
  if [ ${#IDX_NAME} -gt 63 ]; then
    IDX_NAME="idx_$(echo -n "$T" | md5sum | cut -c1-16)_bdmgtsn"
  fi
  $PSQL -v ON_ERROR_STOP=1 -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS \"$IDX_NAME\" ON \"$T\" (bd_mgt_sn) WHERE bd_mgt_sn IS NOT NULL;" \
    || echo "  [$T] 인덱스 경고(이미 존재 가능)"
  echo "  [$T] 인덱스 OK (name=$IDX_NAME)"

  # 3) 기존 좌표 → _orig 백업 (아직 비어있을 때만)
  $PSQL -v ON_ERROR_STOP=1 <<SQL
UPDATE "$T"
   SET coordinates_lat_orig = coordinates_lat,
       coordinates_lon_orig = coordinates_lon
 WHERE coordinates_lat_orig IS NULL
   AND coordinates_lat IS NOT NULL;
SQL
  echo "  [$T] _orig 백업 OK"
  echo
done

echo "===== 최종 검증 ====="
for T in "${TABLES[@]}"; do
  $PSQL -t -A -F '|' <<SQL
SELECT
  '$T' AS tbl,
  (SELECT count(*) FROM "$T") AS total,
  (SELECT count(*) FROM "$T" WHERE coordinates_lat IS NOT NULL) AS has_coord,
  (SELECT count(*) FROM "$T" WHERE coordinates_lat_orig IS NOT NULL) AS has_orig,
  (SELECT count(column_name) FROM information_schema.columns WHERE table_name='$T' AND column_name='bd_mgt_sn') AS col_bdmgtsn,
  (SELECT count(column_name) FROM information_schema.columns WHERE table_name='$T' AND column_name='coordinates_lat_orig') AS col_lat_orig,
  (SELECT count(column_name) FROM information_schema.columns WHERE table_name='$T' AND column_name='coordinates_lon_orig') AS col_lon_orig,
  (SELECT count(*) FROM pg_indexes WHERE tablename='$T' AND indexdef LIKE '%bd_mgt_sn%') AS idx_bdmgtsn
;
SQL
done
echo "===== 완료 ====="
