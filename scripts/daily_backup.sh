#!/bin/bash
# =============================================================
# PropNet 일일 자동 백업 스크립트
# - PostgreSQL 전체 덤프 (goldenrabbit_db + voiceroom)
# - /uploads/ 폴더 증분 백업
# - Google Drive 전송 (rclone)
# - 서버 내 7일치만 보관
# - 성공/실패 이메일 알림 (backup_notify.py)
#
# crontab 등록은 run_backup.sh 래퍼를 통해 실행
# =============================================================

NOTIFY_SCRIPT="/home/webapp/goldenrabbit/scripts/backup_notify.py"

# 에러 트랩: 스크립트 실패 시 알림 발송
trap 'python3 "$NOTIFY_SCRIPT" failure "$(tail -5 /home/webapp/goldenrabbit/logs/daily_backup.log 2>/dev/null || echo unknown error)"' ERR

set -euo pipefail

# ── 설정 ──
DATE=$(date +%Y%m%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROJECT_ROOT="/home/webapp/goldenrabbit"
BACKUP_DIR="$PROJECT_ROOT/backups/daily"
LOG_PREFIX="[daily_backup $TIMESTAMP]"
RCLONE_REMOTE="gdrive"
RCLONE_DEST="$RCLONE_REMOTE:서버백업"
RETENTION_DAYS=1

# .env에서 DB 정보 로드
set -a
source "$PROJECT_ROOT/backend/.env"
set +a

echo "$LOG_PREFIX 백업 시작"

# ── 1. PostgreSQL 전체 덤프 ──
DB_DUMP="$BACKUP_DIR/db_all_${DATE}.sql.gz"

echo "$LOG_PREFIX [1/4] PostgreSQL 전체 덤프 시작..."
sudo -u postgres pg_dumpall | gzip > "$DB_DUMP"

DB_SIZE=$(du -h "$DB_DUMP" | cut -f1)
echo "$LOG_PREFIX [1/4] DB 덤프 완료: $DB_DUMP ($DB_SIZE)"

# ── 2. uploads 폴더 압축 (.env 제외) ──
UPLOADS_DUMP="$BACKUP_DIR/uploads_${DATE}.tar.gz"

echo "$LOG_PREFIX [2/4] uploads 폴더 압축 시작..."
tar -czf "$UPLOADS_DUMP" \
    --exclude='*.env' \
    --exclude='.env*' \
    -C "$PROJECT_ROOT" uploads/

UPLOADS_SIZE=$(du -h "$UPLOADS_DUMP" | cut -f1)
echo "$LOG_PREFIX [2/4] uploads 압축 완료: $UPLOADS_DUMP ($UPLOADS_SIZE)"

# ── 3. rclone으로 Google Drive 전송 ──
echo "$LOG_PREFIX [3/4] Google Drive 전송 시작..."

if command -v rclone &> /dev/null; then
    # rclone 설정 존재 확인
    if rclone listremotes 2>/dev/null | grep -q "^${RCLONE_REMOTE}:"; then
        rclone copy "$DB_DUMP" "$RCLONE_DEST/$DATE/" --progress 2>&1 | tail -1
        rclone copy "$UPLOADS_DUMP" "$RCLONE_DEST/$DATE/" --progress 2>&1 | tail -1
        echo "$LOG_PREFIX [3/4] Google Drive 전송 완료"

        # 전송 성공 확인 후 로컬 파일 즉시 삭제 (디스크 절약)
        if rclone ls "$RCLONE_DEST/$DATE/db_all_${DATE}.sql.gz" &>/dev/null; then
            rm -f "$DB_DUMP" "$UPLOADS_DUMP"
            echo "$LOG_PREFIX [3/4] 로컬 백업 파일 삭제 (Google Drive 전송 확인 완료)"
        else
            echo "$LOG_PREFIX [3/4] WARNING: Google Drive 전송 검증 실패, 로컬 파일 유지"
        fi

        # Google Drive에서도 오래된 백업 폴더 삭제 (14일)
        GDRIVE_CUTOFF=$(date -d "-14 days" +%Y%m%d 2>/dev/null || date -v-14d +%Y%m%d 2>/dev/null || echo "")
        if [ -n "$GDRIVE_CUTOFF" ]; then
            echo "$LOG_PREFIX Google Drive 오래된 백업 정리 (14일 이전)..."
            rclone lsd "$RCLONE_DEST/" 2>/dev/null | awk '{print $NF}' | while read -r folder; do
                if [[ "$folder" =~ ^[0-9]{8}$ ]] && [ "$folder" -lt "$GDRIVE_CUTOFF" ]; then
                    echo "$LOG_PREFIX  삭제: $RCLONE_DEST/$folder/"
                    rclone purge "$RCLONE_DEST/$folder/" 2>/dev/null || true
                fi
            done
        fi
    else
        echo "$LOG_PREFIX [3/4] WARNING: rclone remote '$RCLONE_REMOTE' 미설정. Google Drive 전송 건너뜀"
        echo "$LOG_PREFIX         'rclone config' 실행하여 '$RCLONE_REMOTE' 리모트를 설정하세요"
    fi
else
    echo "$LOG_PREFIX [3/4] WARNING: rclone 미설치. Google Drive 전송 건너뜀"
    echo "$LOG_PREFIX         설치: curl https://rclone.org/install.sh | sudo bash"
fi

# ── 4. 서버 내 오래된 백업 삭제 (7일) ──
echo "$LOG_PREFIX [4/4] 서버 내 오래된 백업 정리 (${RETENTION_DAYS}일 이전)..."
DELETED_COUNT=$(find "$BACKUP_DIR" -name "db_all_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
DELETED_COUNT=$((DELETED_COUNT + $(find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)))
echo "$LOG_PREFIX [4/4] 삭제된 파일: ${DELETED_COUNT}개"

# ── 요약 ──
echo ""
echo "$LOG_PREFIX ============================================"
echo "$LOG_PREFIX 백업 완료"
echo "$LOG_PREFIX   DB 덤프:      $DB_DUMP ($DB_SIZE)"
echo "$LOG_PREFIX   uploads:      $UPLOADS_DUMP ($UPLOADS_SIZE)"
echo "$LOG_PREFIX   로컬 보관:    ${RETENTION_DAYS}일"
echo "$LOG_PREFIX   Google Drive: $RCLONE_DEST/$DATE/"
echo "$LOG_PREFIX ============================================"

# ── 성공 알림 이메일 ──
python3 "$NOTIFY_SCRIPT" success "DB: $DB_SIZE / uploads: $UPLOADS_SIZE → Google Drive 전송 완료"
