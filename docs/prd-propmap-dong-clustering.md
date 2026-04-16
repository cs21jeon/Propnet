# PRD — PropMap 동별 좌표 기반 매물 클러스터링 + 부속지번 수렴 통합

> 작성일: 2026-04-16
> 작성 주체: @pm-lead (발주: @propnet-coo, 승인: 오너/CEO)
> 버전: v1.0 (Week 1 초안)
> 선행 문서:
> - `docs/research-dong-coordinates-2026-04-16.md` (좌표 소스 확정)
> - `docs/vworld-16-api-final-proposal-2026-04-16.md` (16개 API 조합안)
> - `propedia/docs/plan-building-footprint-lookup.md` (부속지번 이슈)
> 구현 금지 단계 (설계 문서만)

---

## 0. TL;DR

1. 같은 지번(필지) 위에 있는 집합건물 각 동을 **지도에서 서로 다른 좌표로** 표시한다 (예: 잠실 파크리오 16개 동 분리).
2. 줌 레벨에 따라 **단지 1개 마커 ↔ 동별 N개 마커**로 자동 전환한다.
3. 지번주소/도로명주소/지도클릭 3경로가 **건물관리번호(`bd_mgt_sn`) 하나로 수렴**하여 "파크리오 이슈"(같은 건물인데 경로별로 다른 결과)를 근본 해결한다.
4. 단독주택·상가·아파트 전 유형에 적용. goldenrabbit 파일럿 없이 전체 agent 동시 적용.
5. Propedia/PropSheet UI는 변경 없음. 백엔드 캐시(`building_dong_geometry`) + 매물 테이블 `bd_mgt_sn` 필드 1개 추가로 구현.

---

## 1. 배경 (Problem)

### 1-1. 현재 문제 실측

| 문제 | 현재 동작 | 실측 근거 |
|---|---|---|
| **대단지 동 구분 불가** | `coordinates_lat/lon`이 지번 중심 1점. 파크리오 16개 동, 롯데캐슬 104·106동 모두 동일 좌표 | `research-dong-coordinates` L46-58 |
| **부속지번 주소 오류** | 송파 신천동 17 파크리오가 매물 등록 시 신천동 20으로 흘러 들어가는 케이스 | `plan-building-footprint-lookup.md` |
| **지번↔도로명↔지도클릭 불일치** | Propedia가 두 경로에서 다른 좌표 소스를 씀 (PNU 성공 → 필지중심 / 실패 → 카카오 키워드) | `vworld-16-api-final-proposal` Part B |
| **대단지 마커 겹침** | 줌 멀어도 16개 마커가 한 지점에 겹침 → 클릭 불가, 시각 혼잡 | 육안 확인 (오너 지시) |

### 1-2. 영향 범위

- **현재 영향**: 서울·성남 82건 매물 중 집합건물 비중 34%, 대단지 매물 다수
- **전체 agent 확장 시**: 각 agent DB의 `*_sales_multi_unit` 테이블 전량
- **사용자 체감**: 공인중개사가 파크리오 101동을 클릭해도 102동 매물이 섞여 나옴

---

## 2. 목표 (Goals)

### 2-1. 핵심 성공 지표 (KPI)

| 지표 | 현재 | 목표 (Week 4 종료) | 측정 방법 |
|---|---|---|---|
| **파크리오 동별 분리 표시** | 1개 좌표(100% 중첩) | 16개 동 100% 분리 | 지도 수동 검수 |
| **bd_mgt_sn 채움률 (집합건물)** | 0% | 95%+ | `SELECT COUNT(*) WHERE bd_mgt_sn IS NOT NULL / COUNT(*)` |
| **부속지번 조회 성공률** | 미측정 (신천동 17↔20 오류 확인) | 95%+ | 지번/도로명 두 경로 동일 `bd_mgt_sn` 수렴 비율 |
| **VWorld 호출량** | 매물 저장당 1회 (역지오코딩) | 캐시 히트 시 0회, 신규만 1회 | 서버 액세스 로그 |
| **매물 지도 평균 렌더 시간 (1만건 기준)** | N/A (신규) | < 1.5초 (클라이언트 측정) | 파일럿 측정 |

### 2-2. Non-goals (이번 범위 아님)

- Propedia/PropSheet UI 변경 (동/호 입력 UX는 현행 유지)
- 호수 단위 좌표(같은 동 내 1201호 vs 1202호 분리 — 불가능)
- 단독주택의 동명 강제 (현실적으로 없음 — 건물 중심 1점만)
- 과거 매물 이관 이후 실시간 변경 대응 (Week 4 이후 별도 과제)

---

## 3. 기능 요구사항 (Functional Requirements)

### FR-1. 줌 레벨별 지도 동작

| 줌 | 동작 | 클릭 시 |
|---|---|---|
| < 15 (멀리) | 단지 1개 집계 마커 + 매물 개수 배지 | 해당 단지 전체 매물 리스트 팝업 |
| >= 15 (가까이) | 동별 N개 마커 + 각 동 매물 개수 | 해당 동 매물 리스트 팝업 |
| >= 18 (매우 가까이) | 동별 마커 + 건물명·동명 라벨 표시 | 좌동 |

> 정확한 임계값은 @design-lead가 UX 문서에서 확정.

### FR-2. 단지/동 식별 기준

- **단지 ID**: `pnu` (19자리 필지고유번호) 또는 `bldrgst_pk` (건축물대장 PK)
- **동 ID**: `bd_mgt_sn` (25자리 건물관리번호) ← **Single Source of Truth**
- 매물 레코드의 `bd_mgt_sn`이 있으면 해당 동 좌표, 없으면 필지 중심 fallback

### FR-3. 3개 서비스 동기화 (CRITICAL — 매물지도-검색-결과지도 3곳)

- [ ] `propmap/map.html` (통합 매물지도)
- [ ] `propmap/index.html` (검색 화면)
- [ ] 홈페이지 `map.html` (검색결과 지도)

위 3곳 모두 동일한 `/map/dong-coords` API를 호출하여 일관된 좌표 렌더.

### FR-4. 매물 저장 시 좌표 파이프라인 (4단계 확장)

Propedia `_resolve_coordinates()`를 다음 4단계로 확장:

1. **캐시 조회**: `building_dong_geometry` where `(pnu, dong_nm)` 또는 `bd_mgt_sn`
2. **NSDI LdaregService**: `getBuldSnList` + `getBuldDongNmList`로 동 enumerate → `bd_mgt_sn` 획득
3. **VWorld WFS**: `LT_C_BLDGINFO` bbox 조회로 MultiPolygon 중심점 계산 → 캐시 저장
4. **Fallback**: 실패 시 지번 중심 좌표 (현행 로직 유지)

### FR-5. 부속지번 수렴

지번주소/도로명주소/지도클릭 3경로 모두 **최종적으로 `bd_mgt_sn` 1개로 수렴**:

- 지번 경로: PNU → `getBuldSnList` → `bd_mgt_sn`
- 도로명 경로: VWorld `LT_C_SPBD` → `bd_mgt_sn`
- 지도클릭: VWorld WFS POINT 쿼리 → `bd_mgt_sn`

### FR-6. 동별 매물 리스트 팝업

마커 클릭 시:
- 건물명/동명 헤더 (예: "파크리오 103동")
- 매물 카드 리스트 (현 PropMap 리스트 재사용)
- "이 단지 전체 보기" 버튼 → 단지 전체로 확장

---

## 4. 데이터 요구사항

### 4-1. 신규 테이블: `building_dong_geometry` (공용 캐시)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `bd_mgt_sn` | VARCHAR(25) PK | 건물관리번호 (SSoT) |
| `pnu` | VARCHAR(19) | 필지고유번호 (인덱스) |
| `dong_nm` | VARCHAR(50) | 동명 (예: "103동") |
| `bld_nm` | VARCHAR(200) | 건물명/단지명 |
| `center_lat` / `center_lon` | NUMERIC(10,7) | MultiPolygon 무게중심 |
| `geometry` | JSONB | 원본 폴리곤 (선택, 시각화용) |
| `road_addr` | VARCHAR(300) | 도로명주소 |
| `jibun_addr` | VARCHAR(300) | 지번주소 |
| `source` | VARCHAR(20) | `vworld_wfs`, `nsdi_ldareg`, `manual` |
| `fetched_at` | TIMESTAMP | 조회 시각 |
| `ttl_until` | TIMESTAMP | 캐시 만료 (기본 +1년) |

> DDL 확정은 @infra-lead가 `docs/infra-dong-clustering-schema.md`에서.

### 4-2. 매물 테이블 수정: `bd_mgt_sn` 컬럼 추가

- 대상: `{agent_slug}_sales_building`, `{agent_slug}_sales_multi_unit` 전체 agent
- 타입: `VARCHAR(25) NULL` (인덱스 `idx_{table}_bd_mgt_sn`)
- 이전 레코드: 배치 스크립트가 주소 → `bd_mgt_sn` 해석 후 일괄 UPDATE

### 4-3. 캐시 TTL 및 갱신 정책

- 기본 TTL 1년 (`fetched_at + INTERVAL '365 days'`)
- 신축/철거 감지 필요 시 수동 `TRUNCATE` 또는 `ttl_until = NOW()` UPDATE
- VWorld 호출 실패 시 기존 캐시 유지 (stale-while-error)

---

## 5. 비기능 요구사항

| 항목 | 요구 |
|---|---|
| **캐시 TTL** | 1년 (상술) |
| **VWorld 호출 최소화** | 동일 `(pnu, dong_nm)` 재조회 금지, 캐시 우선 |
| **배치 안전성** | 중단 가능/재개 가능, agent 단위 트랜잭션 |
| **API 응답 시간** | `/map/dong-coords` P95 < 300ms (캐시 히트 시) |
| **실패 격리** | NSDI/VWorld 장애 시 fallback 좌표로 서비스 정상 운영 |
| **데이터 정합성** | `bd_mgt_sn` → `building_dong_geometry` FK 관계 유지 (soft FK) |
| **로깅** | 캐시 미스, API 실패, 배치 진행률 모두 `journalctl` 기록 |

---

## 6. 릴리즈 범위 & 일정

### Phase 1 (Week 1): 문서 — **지금 진행 중**
- 본 PRD (@pm-lead)
- 기술 설계 (@dev-lead)
- DB 스키마 설계 (@infra-lead)
- UX 디자인 (@design-lead)

### Phase 2 (Week 2): 인프라 + 공유 서비스
- `building_dong_geometry` 테이블 생성 (@infra-lead)
- 매물 테이블 `bd_mgt_sn` ALTER (@infra-lead)
- `cadastral_service.py` 확장 + `ldareg_service.py` 신규 (@dev-lead)

### Phase 3 (Week 3): 서비스별 병렬 구현
- Propedia `_resolve_coordinates()` 4단계 (@propedia-dev)
- PropSheet 배치 스크립트 + 전체 agent UPDATE (@propsheet-dev)
- PropMap 3곳 렌더링 (@propmap-dev)

### Phase 4 (Week 4): 검증 & 배포
- goldenrabbit 파일럿 검증 → 전체 agent 동시 적용 (@qa-lead + @infra-lead)
- 파크리오 16개 동 육안 검수
- KPI 측정 및 오너 보고

---

## 7. 리스크 & 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| NSDI API 화이트리스트 필요 | 배포 지연 | Phase 1 내 @infra-lead가 확인 및 사전 신청 |
| VWorld 쿼터 초과 | 배치 중단 | 일일 쿼터 분할, 야간 배치 |
| 기존 매물 `bd_mgt_sn` 매칭 실패 | 캐시 커버리지 저하 | Fallback 좌표 유지, 실패 레코드 리포트 |
| 전체 agent 동시 적용 실패 | 서비스 장애 | DB 컬럼 추가는 ADD COLUMN NULL로 무중단, 코드는 기능 플래그로 점진 활성화 |
| 줌 전환 UX 혼란 | 사용자 이탈 | @design-lead가 애니메이션·라벨로 명확화 |

---

## 8. 수락 기준 (Acceptance Criteria)

- [ ] 파크리오(송파 신천동 7 또는 17) 지도에서 16개 동이 **모두 분리된 좌표**로 표시됨
- [ ] 단지 줌아웃 시 1개 마커 + "XX건" 배지, 줌인 시 동별 N개 마커
- [ ] 지번주소 입력 / 도로명주소 입력 / 지도클릭 3경로 모두 동일한 `bd_mgt_sn` 반환
- [ ] `building_dong_geometry` 커버리지(현 DB 매물 기준) 95%+
- [ ] `journalctl`에 VWorld/NSDI 실패 로그 기록 및 fallback 동작 확인
- [ ] PropMap 3곳(map.html, index.html, 홈 map)이 동일 API 사용, 일관된 렌더
- [ ] 신천동 17 파크리오가 신천동 20으로 흘러들어가는 버그 재현 불가 확인

---

## 9. 오픈 이슈 (Week 1 내 해소)

1. NSDI `LdaregService` 인증키 IP 화이트리스트 필요 여부 → @infra-lead 확인
2. 줌 전환 임계값 (15? 16?) → @design-lead 확정
3. 집합건물이 아닌 단독주택도 `bd_mgt_sn` 저장 여부 → @dev-lead 기술검토
4. 배치 실행 타임 슬롯 (새벽 2-5시?) → @infra-lead 제안
5. 동별 마커 9종 색상 팔레트 유지 vs 신규 → @design-lead 결정
