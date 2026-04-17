#!/bin/bash
# Phase D — VWorld 기반 PNU 확장 야간 배치 래퍼.
#
# 실행:
#   nohup bash phase_d_nightly_vworld.sh > /var/log/propnet/phase_d.log 2>&1 &
#
# 특징:
#   - 우선순위: 서울 → 경기/인천 → 6대 광역시 → 전국
#   - 각 단계 끝날 때마다 상태 로그 기록
#   - 재시작 안전 (expand_pnu_by_bbox.py가 parcels >=2인 단지 skip)
#   - Ctrl+C 시 다음 루프 시작 전에 정상 종료

set -u  # unset var 에러로 종료 (완전 set -e는 쓰지 않음; VWorld 일시 실패 허용)

LOG_DIR=/var/log/propnet
mkdir -p "$LOG_DIR"

PROJECT_ROOT=/home/webapp/goldenrabbit/backend
cd "$PROJECT_ROOT"

# 가상환경 활성화
source venv/bin/activate

# 시군구 우선순위 (상위일수록 먼저 처리)
# 서울 전체
SEOUL=(11110 11140 11170 11200 11215 11230 11260 11290 11305 11320 11350 11380 11410 11440 11470 11500 11530 11545 11560 11590 11620 11650 11680 11710 11740)
# 인천 전체
INCHEON=(28110 28140 28170 28185 28200 28237 28245 28260 28710 28720)
# 경기 (대표 시만 — 전체는 너무 많음. 이후 전국 단계에서 채움)
GYEONGGI=(41111 41113 41115 41117 41131 41133 41135 41150 41171 41173 41190 41210 41220 41250 41270 41280 41285 41290 41310 41360 41370 41390 41410 41430 41450 41461 41463 41465 41480 41500 41550 41570 41590 41610 41630 41650 41670 41800 41820 41830)
# 6대 광역시 (부산/대구/광주/대전/울산/세종)
METRO=(26110 26140 26170 26200 26230 26260 26290 26320 26350 26380 26410 26440 26470 26500 26530 26710 27110 27140 27170 27200 27230 27260 27290 27710 27720 29110 29140 29155 29170 29200 30110 30140 30170 30200 30230 31110 31140 31170 31200 31710 36110)

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*"
}

run_phase() {
    local label="$1"
    shift
    local sigungu_csv
    sigungu_csv=$(IFS=,; echo "$*")
    log "========================================"
    log "[$label] 시작 (${#@}개 시군구)"
    log "========================================"

    python scripts/week5_complex_master/expand_pnu_by_bbox.py \
        --mode vworld \
        --sigungu "$sigungu_csv" \
        --limit 1000 \
        --rate-limit 0.3 \
        || log "[$label] 경고: 스크립트 종료 코드 $?"

    log "[$label] 완료"
}

# 진행
log "Phase D 전국 VWorld 확장 시작"

run_phase "SEOUL" "${SEOUL[@]}"
run_phase "INCHEON" "${INCHEON[@]}"
run_phase "GYEONGGI" "${GYEONGGI[@]}"
run_phase "METRO" "${METRO[@]}"

log "Phase D 전체 단계 1회 완료"
log "남은 미확장 단지는 이후 반복 실행 시 재시도됨"
