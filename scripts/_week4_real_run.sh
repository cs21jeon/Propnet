#!/bin/bash
# Week 4 — 실제 실행 (매칭 로직 정교화 버전)
set -a
. /home/webapp/goldenrabbit/backend/.env
set +a
export VWORLD_APIKEY PUBLIC_API_KEY DB_HOST DB_NAME DB_USER DB_PASSWORD

cd /home/webapp/goldenrabbit
mkdir -p logs
LOG=/home/webapp/goldenrabbit/logs/warm_building_cache_week4_real_$(date +%Y%m%d_%H%M%S).log

# Agent 순서대로: silverrabbit → propnet → goldenrabbit (적은 것부터)
# 이상 발견 시 중단할 수 있도록 개별 실행
for AGENT in silverrabbit propnet goldenrabbit; do
  echo "===== $AGENT 시작 ====="
  /home/webapp/goldenrabbit/backend/venv/bin/python scripts/warm_building_cache.py \
    --agent "$AGENT" --rate-limit 0.3 >> "$LOG" 2>&1
  RC=$?
  echo "===== $AGENT 완료 (exit=$RC) ====="
  if [ $RC -ne 0 ]; then
    echo "$AGENT 에서 에러 발생 — 계속 진행 (에러는 로그에 기록됨)"
  fi
done
echo "===== 전체 완료 =====" >> "$LOG"
echo "LOG=$LOG"
