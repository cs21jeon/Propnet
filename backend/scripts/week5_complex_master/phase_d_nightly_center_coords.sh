#!/bin/bash
# Phase D (재설계) — 매일 밤 center_lat/lon VWorld 보강 배치.
#
# 실행 (수동):
#   nohup bash phase_d_nightly_center_coords.sh > /var/log/propnet/phase_d.log 2>&1 &
#
# cron 등록 (매일 02:00):
#   0 2 * * * /home/webapp/goldenrabbit/backend/scripts/week5_complex_master/phase_d_nightly_center_coords.sh >> /var/log/propnet/phase_d.log 2>&1
#
# 특징:
#   - 1일 배치 약 20,000 단지 (0.3s × 20000 = 1.7시간)
#   - household_count 내림차순 (큰 단지 우선)
#   - re-run 안전 (center_lat IS NULL만 처리)
#   - VWorld 쿼터 모니터링: 호출 실패 5회 연속이면 조기 종료

set -u

LOG_DIR=/var/log/propnet
mkdir -p "$LOG_DIR" 2>/dev/null || true

PROJECT_ROOT=/home/webapp/goldenrabbit/backend
cd "$PROJECT_ROOT"
source venv/bin/activate

BATCH_LIMIT="${BATCH_LIMIT:-20000}"
RATE_LIMIT="${RATE_LIMIT:-0.3}"

echo "$(date '+%Y-%m-%d %H:%M:%S') Phase D nightly 시작 (limit=$BATCH_LIMIT, rate=$RATE_LIMIT)"

python scripts/week5_complex_master/phase_f_fill_center_coords.py \
    --mode vworld \
    --limit "$BATCH_LIMIT" \
    --rate-limit "$RATE_LIMIT"

RC=$?
echo "$(date '+%Y-%m-%d %H:%M:%S') Phase D nightly 종료 (exit=$RC)"

# DB 상태 보고
python -c "
import psycopg2, os
def load_env(p='/home/webapp/goldenrabbit/backend/.env'):
    if os.path.isfile(p):
        for line in open(p, 'r', encoding='utf-8'):
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            k,v=line.split('=', 1); os.environ.setdefault(k.strip(), v.strip())
load_env()
conn = psycopg2.connect(
    host=os.environ.get('DB_HOST','127.0.0.1'),
    port=int(os.environ.get('DB_PORT','5432')),
    dbname=os.environ.get('DB_NAME','goldenrabbit_db'),
    user=os.environ.get('DB_USER','goldenrabbit_user'),
    password=os.environ.get('DB_PASSWORD',''),
)
cur = conn.cursor()
cur.execute(\"\"\"SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE center_lat IS NOT NULL) AS filled FROM complex_master\"\"\")
total, filled = cur.fetchone()
pct = filled / total * 100 if total else 0
print(f'   [status] total={total}, filled={filled} ({pct:.1f}%)')
"

exit $RC
