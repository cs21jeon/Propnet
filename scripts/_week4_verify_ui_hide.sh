#!/bin/bash
# Week 4 — UI 필드 숨김 검증
set -e
set -a
. /home/webapp/goldenrabbit/backend/.env
set +a

export PGPASSWORD="$DB_PASSWORD"
PSQL="psql -h $DB_HOST -U $DB_USER -d $DB_NAME"

echo "===== UI 숨김 필드 정의 확인 ====="
grep "column_name NOT IN" /home/webapp/goldenrabbit/backend/property-manager/services/schema_service.py | head -2

echo
echo "===== get_table_columns 실제 반환값 테스트 (파이썬) ====="
cd /home/webapp/goldenrabbit/backend/property-manager
/home/webapp/goldenrabbit/backend/venv/bin/python <<'PY'
import sys
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
from services.schema_service import get_table_columns

for t in ['goldenrabbit01_sales_building', 'goldenrabbit01_sales_multi_unit', 'silverrabbit_multi_unit']:
    cols = get_table_columns(t)
    keys = [c['key'] for c in cols]
    forbidden = {'bd_mgt_sn', 'coordinates_lat', 'coordinates_lon', 'coordinates_lat_orig', 'coordinates_lon_orig'}
    leaked = [k for k in keys if k in forbidden]
    print(f'[{t}] total_columns={len(keys)}, leaked_internal_fields={leaked}')
    if leaked:
        print(f'  !!! LEAK DETECTED')
    else:
        print(f'  OK — no internal fields in UI columns')
PY
