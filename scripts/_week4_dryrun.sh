#!/bin/bash
# Week 4 — Dry-run 매칭 로직 검증
set -a
. /home/webapp/goldenrabbit/backend/.env
set +a
export VWORLD_APIKEY PUBLIC_API_KEY DB_HOST DB_NAME DB_USER DB_PASSWORD

cd /home/webapp/goldenrabbit
mkdir -p logs
LOG=/home/webapp/goldenrabbit/logs/warm_building_cache_week4_dryrun.log
/home/webapp/goldenrabbit/backend/venv/bin/python scripts/warm_building_cache.py --dry-run --rate-limit 0.3 > "$LOG" 2>&1 &
PID=$!
echo "PID=$PID"
echo "LOG=$LOG"
