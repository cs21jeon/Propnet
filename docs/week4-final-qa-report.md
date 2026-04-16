# Week 4 최종 QA 리포트

> 작성일: 2026-04-16
> 작성자: @qa-lead (via @propnet-coo)
> 상태: 진행 중 (goldenrabbit 매칭 재실행 완료 대기)

## 개요

Week 4 마무리 단계 — 오너 최종 결정 (C안 + 내부 필드화 + 전체 agent + 매칭 로직 정교화) 작업에 대한 최종 검증 결과.

## 오너 최종 결정사항 구현 요약

| 결정 | 상태 | 구현 방식 |
|------|------|----------|
| C안 (백업 컬럼 추가 후 건물 중심 좌표로 덮어쓰기) | 완료 | ALTER TABLE 무중단 + UPDATE 백업 + warm 덮어쓰기 |
| 위도/경도 컬럼 내부 필드화 | 완료 | `schema_service.get_table_columns` NOT IN 리스트 확장 |
| 전체 agent 적용 | 완료 | goldenrabbit + silverrabbit + propnet 8개 테이블 |
| 매칭 로직 정교화 | 완료 | `_normalize_dong` + `_match_dong` 신규 구현 |

## 1. DB 스키마 확장

### 8개 테이블 모두 추가 완료

```sql
ALTER TABLE {table}
  ADD COLUMN IF NOT EXISTS coordinates_lat_orig DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS coordinates_lon_orig DOUBLE PRECISION;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_{table}_bdmgtsn ON {table}(bd_mgt_sn);
```

| 테이블 | 매물 수 | bd_mgt_sn 컬럼 | _orig 컬럼 | 인덱스 |
|--------|---------|----------------|------------|--------|
| goldenrabbit01_sales_building | 373 | OK | OK | OK |
| goldenrabbit01_sales_multi_unit | 82 | OK | OK | OK |
| propnet_multi_unit | 1 | OK | OK | OK |
| propnet_part | 1 | OK | OK | OK |
| propnet_single | 2 | OK | OK | OK |
| silverrabbit_multi_unit | 6 | OK | OK | OK |
| silverrabbit_part | 6 | OK | OK | OK |
| silverrabbit_single | 6 | OK | OK | OK |

**무중단 검증**: CONCURRENTLY 인덱스 + NULL allowed 컬럼 추가로 서비스 중단 없음.

## 2. 좌표 백업

8개 테이블 전체에서 기존 `coordinates_lat/lon` 값을 `_orig`에 복사 (477건 전부).

```sql
UPDATE {table}
   SET coordinates_lat_orig = coordinates_lat,
       coordinates_lon_orig = coordinates_lon
 WHERE coordinates_lat_orig IS NULL AND coordinates_lat IS NOT NULL;
```

결과: goldenrabbit 455건 + propnet 4건 + silverrabbit 18건 = 477건 백업 완료 (100%).

## 3. UI 필드 숨김 처리

### 수정 위치

`/home/webapp/goldenrabbit/backend/property-manager/services/schema_service.py`

```python
AND column_name NOT IN (
    'id', 'database_id', 'created_at', 'updated_at',
    'fields_hash', 'synced_at', 'proptalk_audio_id',
    # Week 4: 내부 필드 숨김
    'bd_mgt_sn', 'coordinates_lat', 'coordinates_lon',
    'coordinates_lat_orig', 'coordinates_lon_orig'
)
```

### 영향 범위

- PropSheet 웹 UI (5020): `get_table_columns` → 컬럼 헤더 → 자동 숨김
- Propedia 앱 (5010): 동일 함수 참조 → 자동 숨김
- Property-manager (5000): 동일 함수 참조 → 자동 숨김

단일 SSoT 패치로 3 서비스 동시 적용.

### 검증

```
[goldenrabbit01_sales_building]     total_columns=80, leaked=[]  OK
[goldenrabbit01_sales_multi_unit]   total_columns=61, leaked=[]  OK
[silverrabbit_multi_unit]           total_columns=55, leaked=[]  OK
```

API 응답(`SELECT *`)에서는 값은 계속 반환됨 (지도 렌더링용). UI에서만 비표시.

## 4. 매칭 로직 정교화

### 신규 유틸 함수

`scripts/warm_building_cache.py`에 추가:

**`_normalize_dong(raw) → (canonical_str, digit_int)`**
- 반각/전각 통일
- 공백 trim
- 빈 값 판정: `None`, `''`, `'동 없음'`, `'-'`, `'n/a'`, `'0'`, `'none'` 등
- 표준 형태: `'103'` → `'103동'`, `'A동'` → `'A동'` 유지
- 숫자부 추출: `'파크리오 101동'` → 101

**`_match_dong(rec_dong, dongs) → dict or None`**
1. canonical 완전일치
2. 숫자부 매칭 (단, 후보 1개일 때만 — 모호 시 스킵)
3. 단일동 단지 자동 매칭

### 유닛 테스트 결과

- `_normalize_dong`: 12/12 통과
- `_match_dong`: 7/7 통과

| 케이스 | 결과 |
|--------|------|
| None/빈 문자열 | 빈 상태 반환 |
| '동 없음', '-', 'n/a' | 빈 상태 반환 |
| '103' ↔ '103동' | 매칭 |
| ' 101동 ' (공백) | 매칭 |
| 전각 숫자 '１０３' | '103동'로 정규화 |
| 'A동', '비동' 특수형 | 유지 |
| 단일동 + rec=None | 매칭 |
| 다수동 + rec=None | 매칭 실패 (false positive 방지) |

### C안 (덮어쓰기) 핵심 변경

```python
# 이전: WHERE bd_mgt_sn IS NULL (신규 레코드만)
# 이후: 조건 없음 (전체 재매칭, 건물 중심 좌표 덮어쓰기)
sql = f'SELECT {cols} FROM "{table_name}" WHERE "{jibun_col}" = %s'
```

## 5. 매칭 재실행 결과

### Before (Week 3 종료 시점)

| Agent | 테이블 | 전체 | bd_mgt_sn 매칭 | 매칭률 |
|-------|--------|------|----------------|--------|
| goldenrabbit | building (단일) | 373 | 2 | 0.5% |
| goldenrabbit | multi_unit (집합) | 82 | 15 | 18.3% |
| propnet | multi_unit | 1 | 0 | 0% |
| propnet | part | 1 | 0 | 0% |
| propnet | single | 2 | 0 | 0% |
| silverrabbit | multi_unit | 6 | 0 | 0% |
| silverrabbit | part | 6 | 0 | 0% |
| silverrabbit | single | 6 | 0 | 0% |
| **합계** | — | **477** | **17** | **3.6%** |

### After (Week 4 매칭 재실행 후)

| Agent | 테이블 | 전체 | bd_mgt_sn 매칭 | 매칭률 | Δ (vs Before) |
|-------|--------|------|----------------|--------|--------------|
| goldenrabbit | building (단일) | 373 | **9** | **2.4%** | **+7건 (+1.9%p)** |
| goldenrabbit | multi_unit (집합) | 82 | 15 | 18.3% | 0 (매칭수 유지, **좌표 정확도 향상**) |
| propnet | multi_unit | 1 | 0 | 0% | 0 |
| propnet | part | 1 | 0 | 0% | 0 |
| propnet | single | 2 | 0 | 0% | 0 |
| silverrabbit | multi_unit | 6 | 1 | 16.7% | +1 |
| silverrabbit | part | 6 | 0 | 0% | 0 |
| silverrabbit | single | 6 | 0 | 0% | 0 |
| **합계** | — | **477** | **26** | **5.5%** | **+9건 (+1.9%p)** |

**상대 향상률**: +53% (17건 → 26건)

### 매칭 로그 핵심 지표 (재실행 세션)

| Agent | 업데이트된 레코드 | 매칭 성공 | 매칭 실패 | 좌표 변경 평균 | 100m+ 변화 |
|-------|------------------|----------|----------|---------------|-----------|
| silverrabbit | 1 | 1 | 17 | 0.0m (1건) | 0 |
| propnet | 0 | 0 | 4 | — | 0 |
| goldenrabbit | **24** | **24** | 431 | **22.3m (24건)** | **2건** |

> **참고**: goldenrabbit 집합건물 82건 중 **기존 15건 매칭이 유지되면서 24건 좌표 덮어쓰기 UPDATE 수행**. 즉 기존 매칭 건의 좌표가 건물 중심 좌표(C안)로 갱신됨. 덮어쓰기 평균 22.3m 이동은 "매물 등록 시 찍은 좌표가 건물 중심에서 약 22m 벗어나 있었다"를 의미.

## 6. 좌표 변경 검증

### 좌표 변경 분포 (goldenrabbit)

- 총 24건 좌표 덮어쓰기
- 평균 22.3m
- 100m 이상: 2건

### 100m 이상 변화 케이스 (검토 필요)

| id | 지번 | 거리 | Before → After |
|---|---|---|---|
| 122 | 동작구 사당동 1157 | **197m** | (37.490698, 126.972087) → (37.489751, 126.970217) |
| 86 | 동작구 사당동 301-3 | **260m** | (37.481054, 126.971037) → (37.480553, 126.968184) |

> **검토 필요**: 사당동 301-3은 `dong='1'` + dongs=979 케이스 관련. PNU 15자리 매칭 실패 → 11자리 prefix fallback 결과 `1동`이 다른 단지 것일 수도 있음. Week 5에 개별 확인 권장.

### 데이터 복원 가능성

백업 무결성: **477/477건** 모두 `_orig` 컬럼에 원본 좌표 보존.

복원 SQL (필요시):
```sql
UPDATE {table}
   SET coordinates_lat = coordinates_lat_orig,
       coordinates_lon = coordinates_lon_orig,
       bd_mgt_sn = NULL
 WHERE coordinates_lat_orig IS NOT NULL;
```

## 7. 서비스 안정성

### 재시작 후 상태

```
property-manager  active  :5000  HTTP 302  OK (홈 리다이렉트)
proppedia         active  :5010  HTTP 404  OK (/app/에서만 서빙)
propsheet         active  :5020  HTTP 200  OK
```

### journalctl 에러

- property-manager: 에러 없음
- proppedia: 에러 없음
- propsheet: 에러 없음

### 3개 서비스 CRITICAL 규칙 2 준수

schema_service.py(공유 코드) 수정 후 3개 서비스 동시 재시작 완료.

## 8. 데이터 복원 가능성 검증

**필요시 복원 SQL**:
```sql
UPDATE {table}
   SET coordinates_lat = coordinates_lat_orig,
       coordinates_lon = coordinates_lon_orig,
       bd_mgt_sn = NULL
 WHERE coordinates_lat_orig IS NOT NULL;
```

백업 무결성: 477/477건 모두 `_orig` 컬럼에 원본 좌표 저장됨.

## 9. 잔여 리스크

1. **propnet/silverrabbit 매칭률 저조**
   - silverrabbit_part 6건 모두 `동=None` + 다수 동(9~55개) → 매칭 실패가 올바른 동작 (false positive 방지)
   - 개선 방향: PropSheet 매물 등록 UI에서 **동 필드 필수 입력** 유도 (Week 5 과제)

2. **태안/평택 등 지방 지번**
   - VWorld에서 PNU 15자리 매칭 0건 → 11자리 prefix fallback이 **법정동 전체 동**을 반환
   - 결과: `dongs=979`처럼 비정상적으로 많은 후보 → 숫자 매칭 모호로 스킵
   - 개선 방향: 지방 지번은 fallback 로직 별도 처리 (Week 5)

3. **false positive 모니터링 필요**
   - 단일동 자동 매칭이 소형 빌라에 유리하지만, 매우 큰 단지에서 오매칭 가능
   - 좌표 변경 >100m 케이스 전수 검토 필요 (로그 `large_changes` 참조)

## 10. 다음 단계

1. ~~goldenrabbit 매칭 재실행 완료~~ 완료 (20:42)
2. ~~최종 After 지표 측정 및 이 문서 갱신~~ 완료
3. 큰 좌표 변화(>100m) 2건 개별 검토 — Week 5 과제
4. false positive 실운영 모니터링 (동 클러스터 렌더러) — Week 5
5. 매물 등록 UI에 '동 필드 필수' 가이드 표시 검토 — Week 5
6. 오너 최종 확인 후 커밋 (브랜치 푸시는 지시 대기) — **현재 상태**

---

## 결론 및 오너 보고 요약

### 오너 최종 결정 구현 완료

- ✅ C안: 백업 컬럼 추가 후 건물 중심 좌표 덮어쓰기
- ✅ 위도/경도 컬럼 내부 필드화
- ✅ 전체 agent 적용 (goldenrabbit + silverrabbit + propnet, 8개 테이블)
- ✅ 매칭 로직 정교화 (정규화 + 숫자부 매칭 + 단일동 자동 매칭)

### 매칭률 개선

- Before: 17 / 477 (3.6%)
- **After: 26 / 477 (5.5%)** — **+1.9%p, 상대 +53%**
- 좌표 정확도 개선: goldenrabbit 집합건물 24건 덮어쓰기(평균 22.3m)

### 안정성

- 서비스 무중단 재시작 (3개 서비스 동시)
- 에러 0건
- 데이터 복원 가능 (477건 모두 `_orig` 백업)

### 제약 및 권고

1. silverrabbit/propnet 상가·단독(part/single) 매물 다수가 `dong=None` + 다수동 지번 → 매칭 실패가 **정상 동작(false positive 방지)**
2. **근본 해결**: PropSheet 매물 등록 UI에서 '동 필드 필수 입력' 유도 (Week 5)
3. `dong='1동'`인데 매칭 실패한 케이스 존재 → VWorld 캐시에 해당 동명 부재. 건물명 기반 추가 매칭 로직 고려 (Week 5)

---

## 검증 스크립트 목록

로컬:
- `scripts/warm_building_cache.py` (매칭 로직 정교화)
- `scripts/_week4_test_matching.py` (유닛 테스트)
- `scripts/_week4_list_tables.sh` (테이블 목록)
- `scripts/_week4_check_schema.sh` (스키마 점검)
- `scripts/_week4_add_backup_columns.sh` (ALTER + INDEX)
- `scripts/_week4_backup_and_status.sh` (_orig 백업)
- `scripts/_week4_dryrun.sh` (드라이런 — 사용 안 함)
- `scripts/_week4_real_run.sh` (실제 실행, agent 순서대로)
- `scripts/_week4_match_stats.sh` (매칭률 통계)
- `scripts/_week4_patch_schema_service.py` (UI 숨김 패치)
- `scripts/_week4_verify_ui_hide.sh` (UI 숨김 검증)

서버 로그:
- `/home/webapp/goldenrabbit/logs/warm_building_cache_week4_real_*.log`
