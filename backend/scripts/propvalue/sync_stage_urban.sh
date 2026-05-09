#!/bin/bash
# PropValue stage_urban 정기 동기화
# ArcGIS PROPEL_CD 수집 → stage_urban 저장 → stage 매핑 적용
#
# cron: 매주 월요일 06:00
# 0 6 * * 1 /home/webapp/goldenrabbit/backend/scripts/propvalue/sync_stage_urban.sh >> /var/log/propvalue_sync.log 2>&1

set -e

SCRIPT_DIR="/home/webapp/goldenrabbit/backend/scripts/propvalue"
VENV="/home/webapp/goldenrabbit/backend/venv/bin/activate"
ENV_FILE="/home/webapp/goldenrabbit/backend/.env"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') PropValue stage sync 시작 ====="

# 환경 로드
source "$VENV"
export $(grep -v '^#' "$ENV_FILE" | xargs)

# 1단계: ArcGIS PROPEL_CD → stage_urban 수집
echo "[1/2] enrich_stage_urban.py 실행..."
cd "$SCRIPT_DIR"
python3 enrich_stage_urban.py

# 2단계: stage_urban → stage 매핑
echo "[2/2] stage 매핑 적용..."
sudo -u postgres psql goldenrabbit_db <<'SQL'
UPDATE redevelopment_zones SET stage = CASE stage_urban
  -- 초기 → 구역지정
  WHEN '추진중 - 대상지선정' THEN '구역지정'
  WHEN '추진중 - 대상지 선정' THEN '구역지정'
  WHEN '추진중 - 후보지선정' THEN '구역지정'
  WHEN '추진중 - 예정지구지정' THEN '구역지정'
  WHEN '추진중 - 구역지정' THEN '구역지정'
  WHEN '추진중 - 구역변경' THEN '구역지정'
  WHEN '추진중 - 지구지정' THEN '구역지정'
  WHEN '추진중 - 지구변경' THEN '구역지정'
  WHEN '추진중 - 입안제안' THEN '구역지정'
  WHEN '추진중 - 열람공고' THEN '구역지정'
  WHEN '추진중 - 위원회심의' THEN '구역지정'
  WHEN '추진중 - 사전검토' THEN '구역지정'
  WHEN '추진중 - 사전자문' THEN '구역지정'
  WHEN '추진중 - 수립범위 자문' THEN '구역지정'
  WHEN '추진중 - 정비계획수립' THEN '구역지정'
  WHEN '추진중 - 관리지역고시' THEN '구역지정'
  WHEN '추진중 - 마중물사업(추진중)' THEN '구역지정'
  WHEN '추진중 - 활성화계획수립' THEN '구역지정'
  WHEN '추진중 - 결정고시' THEN '구역지정'
  WHEN '추진중 - 추진계획수립중' THEN '구역지정'
  WHEN '추진중 - 입안절차 진행' THEN '구역지정'
  WHEN '추진중 - 협상조정협의회 운영' THEN '구역지정'
  WHEN '추진중 - 제안서접수' THEN '구역지정'
  WHEN '추진중 - 촉진계획수립(변경)' THEN '구역지정'
  WHEN '완료 - 기획완료' THEN '구역지정'
  -- 초기 → 추진위
  WHEN '추진중 - 추진위구성' THEN '추진위'
  WHEN '추진중 - 조합설립추진중' THEN '추진위'
  WHEN '추진중 - 주민합의체 구성' THEN '추진위'
  -- 초기 → 안전진단
  WHEN '추진중 - 1차 안전진단' THEN '안전진단'
  WHEN '추진중 - 2차 안전진단' THEN '안전진단'
  -- 조합
  WHEN '추진중 - 조합설립인가 추진중(연번부여)' THEN '조합설립'
  WHEN '추진중 - 조합설립인가' THEN '조합설립'
  -- 사시
  WHEN '추진중 - 건축심의' THEN '사업시행'
  WHEN '추진중 - 사업시행인가' THEN '사업시행'
  WHEN '추진중 - 사업시행계획인가' THEN '사업시행'
  WHEN '추진중 - 사업계획승인' THEN '사업시행'
  WHEN '추진중 - 건축허가' THEN '사업시행'
  WHEN '추진중 - 지구계획승인(변경)' THEN '사업시행'
  WHEN '추진중 - 리모델링허가승인' THEN '사업시행'
  WHEN '추진중 - 추진계획승인' THEN '사업시행'
  WHEN '추진중 - 인허가 절차' THEN '사업시행'
  WHEN '추진중 - 실시계획인가' THEN '사업시행'
  -- 관처
  WHEN '추진중 - 관리처분계획인가' THEN '관리처분'
  -- 공사
  WHEN '공사중 - 착공' THEN '착공'
  WHEN '공사중 - 사용승인' THEN '착공'
  -- 완료
  WHEN '완료 - 준공' THEN '준공'
  WHEN '완료 - 준공(일부)' THEN '준공'
  WHEN '완료 - 입주' THEN '준공'
  WHEN '완료 - 사업완료' THEN '준공'
  WHEN '완료 - 입주자 모집공고 완료' THEN '준공'
  -- 해제
  WHEN '기타 - 취소' THEN '해제'
  WHEN '기타 - 구역해제' THEN '해제'
  WHEN '기타 - 구역취소' THEN '해제'
  WHEN '기타 - 해제' THEN '해제'
  WHEN '기타 - 중단' THEN '해제'
  WHEN '기타 - 중단(실효)' THEN '해제'
  ELSE stage
END
WHERE stage_urban <> '' AND stage_urban IS NOT NULL;
SQL

# 3단계: 해제 구역 숨김 처리
echo "[3/3] 해제 구역 숨김 처리..."
sudo -u postgres psql goldenrabbit_db -c "UPDATE redevelopment_zones SET is_hidden = true, hidden_reason = '해제/취소/중단' WHERE stage = '해제' AND is_hidden IS NOT TRUE;"
sudo -u postgres psql goldenrabbit_db -c "UPDATE redevelopment_zones SET is_hidden = true, hidden_reason = '준공 완료' WHERE stage = '준공' AND is_hidden IS NOT TRUE;"

# 4단계: stage_urban 없는 비숨김 구역 → 구역지정 (ArcGIS 미반영 신규 등록건)
echo "[4/4] 빈값 구역 기본 stage 설정..."
sudo -u postgres psql goldenrabbit_db -c "UPDATE redevelopment_zones SET stage = '구역지정' WHERE (stage = '' OR stage IS NULL) AND is_hidden IS NOT TRUE;"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') PropValue stage sync 완료 ====="
