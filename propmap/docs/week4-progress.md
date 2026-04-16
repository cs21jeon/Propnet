# Week 4 진행 기록 — 자동매칭률 개선 + 스키마 정합화

> 작성일: 2026-04-16
> 상태: 진행 중 (캐시 워밍 실행 중)
> 커밋: 보류 (오너 최종 지시 대기)

## 배경

Week 3 공개 운영 후 측정된 문제:

- **자동매칭률 3.7%** — 매물의 `동` 필드가 비어있거나 공백이어서 캐시 동 geometry와 매칭 실패
- goldenrabbit 매물 테이블(`goldenrabbit01_sales_multi_unit`) 분포:
  - EMPTY (NULL/공백): 54건 (65.85%)
  - `'동 없음'` 문자열: 9건 (10.98%)
  - `WITH_동` (정상, `101동` 등): 17건 (20.73%)
  - OTHER: 2건

## 원인 분석

1. **매칭 로직의 엄격성**: `dong-cluster-renderer.js`가 `(p.dong || p['동']).trim() === dongNm` 정확 일치 매칭. 빈 값, `'동 없음'` 등을 모두 실패로 처리.
2. **단일동 단지 미처리**: 소형 빌라의 경우 단지 내 동이 1개뿐인데 매물에 동이 빈 값으로 들어감 → 그 1개 동과 매칭돼야 맞지만 안 됨.
3. **건물명 폴백 부재**: `험프리스 힐스 N동`처럼 건물명 자체가 동명 역할을 하는 케이스가 있으나 매칭 규칙이 이를 쓰지 않음.
4. **agent 테이블 스키마 비균일**: Week 2에서 goldenrabbit만 `bd_mgt_sn` 추가. propnet/silverrabbit 테이블에는 부재.

## 변경사항

### 1. 렌더러 매칭 관대화 (`propmap/js/dong-cluster-renderer.js`)

- `_normalizeDong()` 추가: 공백, `'동 없음'`, `'없음'`, `'-'`, `'none'`, `'null'` → `''`로 정규화.
- `_dongMatches()` 추가: 정확 일치 + **숫자 부분 일치** (예: 매물 `'101'` == 캐시 `'101동'`, `'제101동'` == `'101동'`).
- `_renderDongsForGroup()` 매칭 우선순위:
  1. 매물 `동` 값으로 정확/숫자 매칭
  2. 실패 시 매물 `건물명`으로 매칭 (예: `험프리스 힐스 N동` → cache `N동`)
  3. 매물 `동`이 빈 값이고 단지가 **단일 동** 단지이면 그 동으로 귀속
- click 핸들러의 `matched` 필터도 동일 규칙 적용.

### 2. 저장 서비스 `동` 필드 강화 (`services/propsheet_save_service.py`)

`_build_multi_unit_record()` 우선순위:
1. `area_data.dong_nm`
2. `area_data.dong_title_info.dong_nm`
3. `building_info.dong_nm`

### 3. Agent 테이블 스키마 정합화

6개 테이블에 `bd_mgt_sn varchar` 컬럼 + `WHERE bd_mgt_sn IS NOT NULL` partial index 추가:

- `propnet_multi_unit` / `propnet_single` / `propnet_part`
- `silverrabbit_multi_unit` / `silverrabbit_single` / `silverrabbit_part`

인덱스 이름 규칙: `idx_{table_name}_bdmgtsn` (goldenrabbit와 일관).
무중단 (`ADD COLUMN IF NOT EXISTS` + `CREATE INDEX CONCURRENTLY`).

### 4. 캐시 UPSERT (pnu, dong_nm) 충돌 폴백 (`services/cadastral_service_dong_ext.py`)

`building_dong_geometry`에 UNIQUE(pnu, dong_nm) 제약이 있어, 같은 동에 다른 `bd_mgt_sn`이 이미 있으면 INSERT 실패했던 문제 해결.

- 1차 시도: `ON CONFLICT (bd_mgt_sn) DO UPDATE` — PK 충돌은 갱신.
- 2차 예외 처리: `(pnu, dong_nm)` 유니크 키 충돌 감지 → `{success: True, skipped: 'pnu_dong_nm_conflict'}` 반환.

### 5. 캐시 워밍 전체 agent 재실행

`scripts/warm_building_cache.py` 백그라운드 실행 (`nohup`). 로그: `/home/webapp/goldenrabbit/logs/warm_building_cache_week4.log`.
대상:
- goldenrabbit: 82 + 373 = 455건
- propnet: 4건
- silverrabbit: 18건 (multi_unit 6 + single 6 + part 6)

## 매칭률 시뮬 결과 (goldenrabbit multi_unit 82건 기준)

| 모드 | 매칭 | 비율 | 개선 |
|------|------|------|------|
| before (기존) | 10 | 12.20% | baseline |
| +norm | 10 | 12.20% | - |
| +single | 10 | 12.20% | - |
| +numeric | 10 | 12.20% | - |
| **+bld_fallback (최종)** | **18** | **21.95%** | **+9.75%p** |

(참고: 오너 메모상 "3.7%"는 프론트에서 `zoom level<=3` 상태 + 뷰포트 매물 기준으로 측정된 값. 시뮬은 모든 82건 대상이라 더 낙관적.)

## 미스 케이스 분류 (총 63건)

- `BLD_DIFF` 40건 (47%): 매물 `건물명`이 cache와 완전히 다름 → 캐시 미확보 또는 위치 정확도 문제. Week 5 별도 분석.
- `EMPTY_MULTI` 22건 (26%): 건물명도 동도 없음 → UI 강화 및 UX 개선 필요.
- `BLD_MISS` 1건: 매물에 `동`은 있는데 건물명 없음 → 동 값만으로 매칭 실패.

## 남은 과제

- 과제 4: 2단계 bld_nm 부분매칭 false positive 모니터링 → warming 완료 후 로그 분석
- 과제 5: `frontend/public/map.html` 동 클러스터 적용 → Week 5 유보 권장 (영향 범위 확인 필요)
- 과제 6: 최종 QA 종합 테스트 → warming 완료 후 실행
- 과제 1 후속: PropSheet 웹 매물 등록 UI에 "동 선택 필수" 가이드 표시 검토

## 배포 상태

- 서버 코드: property-manager, proppedia, propsheet 재시작 완료 (3 서비스 동시 반영, CRITICAL 규칙 2) — 에러 로그 없음 확인
- 프론트: `propmap/js/dong-cluster-renderer.js`, `frontend/public/app/result.html` 배포 (정적 파일)
- DB: ALTER + INDEX 완료 (중복 인덱스 2개 DROP으로 정리), building_dong_geometry warming 완료
- Git 커밋: **보류** (오너 지시 대기)

## Warming 최종 결과

- 전체 실행 시간: 약 7분 (goldenrabbit) + 2분 (silverrabbit+propnet)
- **캐시 증분: 12,254 → 15,096 (+2,842건, +23%)**
- **PNU 증분: 10,963 → 13,454 (+2,491 PNU)**
- **건물명 엔트리: 1,735종 (distinct bld_nm)**
- bd_mgt_sn 자동 채움: goldenrabbit multi_unit 82건 중 15건 (18%)
- (pnu, dong_nm) 충돌 스킵: 최소 1건 (UPSERT 폴백 정상 작동 확인)

## 최종 매칭률 (goldenrabbit multi_unit 82건, 실제 API 기반 시뮬)

| 모드 | 매칭 | 비율 |
|------|------|------|
| before (기존 렌더러) | 10 | **12.20%** |
| Week 4 후 (bld_fallback 포함) | 18 | **21.95%** |

- **절대 향상**: +9.75%p (3.7% 원본 기준이면 +5~+10%p 추정)
- **상대 향상**: +80%

## 미스 케이스 (63건, 오너 Week 5 검토)

- `BLD_DIFF` 40건 (47%): 매물 `건물명`이 cache와 완전히 다름 → 위치 정확도 또는 캐시 미확보
- `EMPTY_MULTI` 22건 (26%): 건물명/동 모두 없음 → UI 경고 + 재수집 필요
- `BLD_MISS` 1건: 건물명 없이 동만 있음

## Week 5 권장 과제

1. 매물 좌표 정확도 개선 (BLD_DIFF 원인 규명)
2. 기존 매물 일괄 `bd_mgt_sn` 재매칭 배치 (warming 스크립트 재실행)
3. `frontend/public/map.html` 홈페이지용 동 클러스터 적용
4. 2단계 bld_nm 부분매칭 false positive 실운영 모니터링

## 파일 변경 목록

### 서버
- `/home/webapp/goldenrabbit/backend/property-manager/services/propsheet_save_service.py` (dong 강화)
- `/home/webapp/goldenrabbit/backend/property-manager/services/cadastral_service_dong_ext.py` (UPSERT 폴백)
- `/home/webapp/goldenrabbit/frontend/public/propmap/js/dong-cluster-renderer.js` (매칭 관대화)

### 로컬 리포
- `propmap/js/dong-cluster-renderer.js` (서버와 동기화)
- `propmap/docs/week4-progress.md` (이 문서)

### 백업 파일 (서버)
- `propsheet_save_service.py.bak.week4`
- `cadastral_service_dong_ext.py.bak.week4`
- `dong-cluster-renderer.js.bak.week4`

---

## 오너 최종 결정 반영 (2026-04-16 후반)

오너 최종 지시: **C안 + 위도/경도 내부 필드화 + 전체 agent 적용 + 매칭 로직 정교화**.

### 1. 전체 agent 스키마 확장 (8개 테이블)

```sql
ALTER TABLE {table}
  ADD COLUMN IF NOT EXISTS coordinates_lat_orig DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS coordinates_lon_orig DOUBLE PRECISION;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_{table}_bdmgtsn ON {table}(bd_mgt_sn);
```

대상: goldenrabbit01_sales_building/multi_unit, propnet_single/multi_unit/part, silverrabbit_single/multi_unit/part. 무중단.

### 2. 좌표 백업 (C안)

477건 전체에서 `coordinates_lat/lon` → `coordinates_lat_orig/lon_orig` 복사 완료. 복원 가능.

### 3. 매칭 로직 정교화 (`scripts/warm_building_cache.py`)

신규 유틸:
- `_normalize_dong()`: `None`, `'동 없음'`, `'-'`, `'n/a'`, `'none'`, `'0'` 등 → 빈 문자열. 전각/반각 통일. 숫자부 추출. `'103'` ↔ `'103동'` 표준화.
- `_match_dong()`: canonical 일치 → 숫자부 일치(후보 1개일 때만, false positive 방지) → 단일동 자동 매칭.

C안 반영: `WHERE bd_mgt_sn IS NULL` 조건 제거 → 전체 레코드 재매칭. 좌표 변경 거리 측정 + 100m 이상 변화 로그.

유닛 테스트: **12/12 normalize** + **7/7 match** 통과.

### 4. UI 내부 필드 숨김 (`services/schema_service.py`)

`get_table_columns()`의 `NOT IN` 리스트에 5개 필드 추가:
- `bd_mgt_sn`
- `coordinates_lat`, `coordinates_lon`
- `coordinates_lat_orig`, `coordinates_lon_orig`

단일 SSoT 패치로 PropSheet 웹 UI, Propedia 앱, Propedia 웹 자동 반영. API 응답에서는 값 계속 반환 (지도 렌더링용).

**검증**: 3개 테이블 테스트 결과 leak 0건 (모든 내부 필드가 UI 컬럼에서 제외됨).

### 5. 추가 파일

로컬:
- `scripts/warm_building_cache.py` (정교화 버전)
- `scripts/_week4_test_matching.py` (유닛 테스트)
- `scripts/_week4_*.sh` (실행 자동화 7개)
- `scripts/_week4_patch_schema_service.py` (UI 숨김 패치)
- `docs/week4-final-qa-report.md` (최종 QA 리포트)

서버:
- `/backend/property-manager/services/schema_service.py.bak.week4`
- `/home/webapp/goldenrabbit/scripts/warm_building_cache.py` (정교화 버전)
- `/home/webapp/goldenrabbit/logs/warm_building_cache_week4_real_*.log`

### 6. 오너 결정 vs 실측 결과

| 항목 | 결정 | 결과 |
|------|------|------|
| 백업 컬럼 추가 | C안 | 8/8 테이블 완료 |
| 좌표 백업 | 최초 1회 | 477/477건 완료 |
| 건물 중심 좌표 덮어쓰기 | 매칭 성공 시 | 진행 중 (goldenrabbit 실행 중) |
| 전체 agent | 3개 agent 모두 | silverrabbit (18), propnet (4), goldenrabbit (455) 순차 처리 |
| 매칭 정교화 | 5개 규칙 | 모두 반영 |
| UI 필드화 | 5개 내부 필드 | 모두 숨김 |

### 7. 매칭 재실행 결과 (중간)

| Agent | 매칭 성공 | 매칭 실패 | 업데이트 |
|-------|----------|----------|----------|
| silverrabbit | 1 | 17 | 1 |
| propnet | 0 | 4 | 0 |
| goldenrabbit | (진행 중) | — | — |

**낮은 매칭률 원인**: `동=None` + 다수 동(9~55개) 조합에서 false positive 방지를 위해 의도적으로 매칭 실패 처리. `동 없음` 문자열도 정규화 후 빈 값으로 처리되므로 단일동 아니면 매칭 불가. 이는 **안전한 보수적 동작**이며, 데이터 품질(동 필드 필수 입력) 개선으로 Week 5에 해결 예정.

### 8. 주의사항 (Week 5 과제)

- 지방 지번(태안, 평택 등)에서 VWorld PNU 15자리 매칭 실패 시 11자리 prefix fallback이 법정동 전체(최대 994개) 동을 반환 → 숫자 매칭 모호로 스킵
- `동='1' + dongs=979` 같은 케이스는 매칭 모호로 실패 → 정상 동작
- 좌표 변경 100m 이상 케이스 로그 기록 후 오너 검토 필요
