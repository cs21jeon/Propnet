#!/bin/bash
# PropNet 보고 시스템 서버 배포 스크립트
# 사용법: scp 후 서버에서 bash deploy.sh
set -e

SERVER_DIR="/home/webapp/goldenrabbit/backend/daily-report"
SYSTEMD_DIR="/etc/systemd/system"
VENV="/home/webapp/goldenrabbit/backend/venv"

echo "=== PropNet 보고 시스템 배포 ==="

# 1. 디렉토리 생성
echo "[1/6] 디렉토리 생성..."
mkdir -p "$SERVER_DIR/reports"
mkdir -p "$SERVER_DIR/collectors"
mkdir -p "$SERVER_DIR/analyzers"
mkdir -p "$SERVER_DIR/report/templates"
mkdir -p "$SERVER_DIR/storage"

# 2. 파이썬 의존성 설치
echo "[2/6] 의존성 설치..."
$VENV/bin/pip install anthropic jinja2 psycopg2-binary 2>/dev/null || echo "의존성 이미 설치됨"

# 3. propnet_reports 테이블 생성
echo "[3/6] DB 테이블 확인..."
$VENV/bin/python -c "
import sys
sys.path.insert(0, '$SERVER_DIR')
from storage.report_storage import ensure_table
ensure_table()
"

# 4. systemd 서비스/타이머 설치
echo "[4/6] systemd 설치..."
cp "$SERVER_DIR/systemd/propnet-daily-report.service" "$SYSTEMD_DIR/"
cp "$SERVER_DIR/systemd/propnet-daily-report.timer" "$SYSTEMD_DIR/"
cp "$SERVER_DIR/systemd/propnet-weekly-report.service" "$SYSTEMD_DIR/"
cp "$SERVER_DIR/systemd/propnet-weekly-report.timer" "$SYSTEMD_DIR/"
systemctl daemon-reload

# 5. 타이머 활성화
echo "[5/6] 타이머 활성화..."
systemctl enable propnet-daily-report.timer
systemctl start propnet-daily-report.timer
systemctl enable propnet-weekly-report.timer
systemctl start propnet-weekly-report.timer

# 6. 확인
echo "[6/6] 상태 확인..."
echo "--- Daily Timer ---"
systemctl status propnet-daily-report.timer --no-pager || true
echo ""
echo "--- Weekly Timer ---"
systemctl status propnet-weekly-report.timer --no-pager || true
echo ""
echo "--- 다음 실행 예정 ---"
systemctl list-timers propnet-* --no-pager || true

echo ""
echo "=== 배포 완료 ==="
echo "테스트: $VENV/bin/python $SERVER_DIR/daily_report.py --mode daily --dry-run"
