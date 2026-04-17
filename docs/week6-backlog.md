# Week 6 이관 과제 목록

> 작성일: 2026-04-17
> 근거: Week 5 종결(오너 2026-04-17 최종 결정) — PNU 확장 대신 `center_lat` 보강에 집중하기로 전략 변경. 파생된 UX·시각화·데이터 적재 과제를 Week 6로 이관.

## 개요

Week 5 종결 시점에 오너가 보류/이관을 지시한 과제를 한 곳에 모았다. 우선순위는 실제 사용자 효용과 의존관계를 기준으로 재정렬한다.

| # | 항목 | 의존/선행 조건 | 우선순위 |
|---|------|---------------|----------|
| 1 | PropSheet/Propedia 검색창 통합 (탭 구조 제거) | `unified-search.js` 재사용 가능, Phase D 진행 중이어도 가능 | 높음 |
| 2 | Phase G-4 — 단지 경계 폴리곤 렌더 | Phase D 완료 불필요 (경계는 VWorld 별도 호출) | 중간 |
| 3 | 매물 등록 시 단지 자동완성 → PNU/동 자동 채움 | 통합 검색 API 선행 | 중간 |
| 4 | 동정보 CSV Phase A-7 적재 (오너 전달 대기) | 오너가 별도 전달 예정 | 대기 |
| 5 | 이력 CSV Phase A-8 적재 (선택) | 데이터 확보 시 착수 | 낮음 |

---

## 1. PropSheet / Propedia 검색창 통합

### 배경

현재 PropSheet와 Propedia는 `주소/부동산명` 탭이 분리되어 있다. Week 5에서 PropMap 쪽은 `unified-search.js`로 `complex_master` + 주소검색을 단일 입력으로 제공하도록 정리했다. 같은 경험을 PropSheet(매물 등록·조회)와 Propedia(건축물 조회)에도 확장한다.

### 목표

- 검색창 1개로 "주소(지번/도로명) / 단지명 / 건물명"을 통합 검색
- 결과 드롭다운에서 선택 → 기존 탭별 필드에 자동 채움
- 탭 UI는 제거하거나 옵셔널 고급 모드로만 남김

### 범위

| 구성요소 | 서버 경로 | 비고 |
|---|---|---|
| `propsheet/templates/main.html` (검색창) | `/backend/propsheet/templates/main.html` | 탭 제거 + 통합 검색 박스 |
| `propedia/frontend/search.html` | `/frontend/public/app/search.html` | Propedia 웹(정적 HTML)도 동일 |
| `unified-search.js` | `propmap/js/unified-search.js` | 그대로 재사용, 결과 핸들러만 교체 |
| API | `/api/propsheet/complex-search` (Phase G-2 완성됨) | 변경 없음 — 재사용 |

### 수용 기준

1. "파크리오" 입력 → 단지 선택 → 주소/PNU/동 목록이 기존 폼 필드에 자동 채워짐
2. 기존 탭(주소/부동산명) 없어도 검색 결과는 동일하게 나옴
3. 3곳 지도 동기화 원칙 준수 — Propedia 웹, PropSheet 웹, PropMap 모두 동일 UX
4. 접근성: 드롭다운 키보드 내비게이션, ARIA 라벨

### 리스크

- Propedia 웹은 Flutter가 아니라 정적 HTML이라 앱+웹 모두 별도 수정 필요
- PropSheet 검색창은 Alpine.js 바인딩이라 상태 싱크 주의

---

## 2. Phase G-4 — 단지 경계 폴리곤 렌더

### 배경

Week 5 마지막 단계에서 "단지 선택 시 해당 단지 중심으로 이동 + 동별 마커 표시"까지만 구현했다. 오너 판단으로 단지 경계 폴리곤(녹지 영역 시각화)은 Week 6로 미뤘다.

### 목표

- 통합 검색으로 단지 선택 시, VWorld `LT_C_BLDGINFO` 또는 `LP_PA_CBND`의 단지 경계를 폴리곤으로 오버레이
- 클릭/호버 시 단지 개요 팝업 (세대수, 준공년도, 주소)

### 구현 포인트

- 데이터 소스: `complex_master` + VWorld 단지 경계 API (Week 3 조사 문서 참조: `docs/vworld-16-api-final-proposal-2026-04-16.md`)
- 캐시: 폴리곤 좌표가 크므로 `building_dong_geometry`에 단지단위 레코드 추가 or 별도 테이블 `complex_geometry`
- 렌더: 카카오맵 `Polygon` 객체, level<=4에서 표시, 줌아웃 시 숨김

### 수용 기준

1. 파크리오 선택 → 단지 경계 보라색 폴리곤 표시 (48개 주거동 포함)
2. 폴리곤 클릭 → "파크리오 · 6,864세대 · 2008준공" 팝업
3. 다른 단지 선택 시 이전 폴리곤 제거 (메모리 릭 없음)

---

## 3. 매물 등록 시 단지 자동완성 → PNU/동 자동 채움

### 배경

현재 매물 등록 시 지번/동/호수를 수동 입력한다. `complex_master`가 적재된 이후에는 단지명만 입력해도 소재지·PNU·대표 동 목록을 자동 채울 수 있다.

### 범위

| 서비스 | 파일 |
|---|---|
| PropSheet 등록 폼 | `propsheet/templates/record_edit.html`, `record_new.html` |
| Propedia 앱 등록 | `propedia/lib/presentation/pages/property_register/` |
| Propedia 웹 등록 | `frontend/public/app/register.html` |

### API

- `GET /api/propsheet/complex-search?q={단지명}` (Phase G-2 — 그대로 재사용)
- `GET /api/propsheet/complex/{complex_id}/dongs` (신규 — 해당 단지의 동 목록 + bd_mgt_sn)

### 수용 기준

1. 단지명 입력 → 드롭다운 후보 → 선택 → 지번·도로명·세대수·동 목록 자동 채움
2. 동 선택 시 `bd_mgt_sn`까지 히든 필드에 세팅 → 저장 시 `building_dong_geometry` 자동 연결
3. 단지가 `complex_master`에 없으면 기존 수동 입력으로 폴백

---

## 4. 동정보 CSV Phase A-7 적재 (오너 전달 대기)

### 상태

- 오너가 K-apt(공동주택관리정보시스템) 다운로드 예정
- 파일명 예상: `apt_dong_info_YYYYMMDD.csv`
- 받으면 즉시 적재 (별도 지시 없어도 됨)

### 적재 절차

1. `data/complex_master_raw/apt_dong_info_YYYYMMDD.csv` 배치
2. `backend/scripts/week5_complex_master/load_apt_dong_info_from_csv.py` 작성 (신규) — `complex_master.complex_id` 기준 JOIN
3. `complex_master_dong` 테이블 upsert (동명, 층수, 세대수, 준공일 등)
4. Phase D와 간섭 없음 — 별도 테이블

### 검증

- 파크리오 복수 동(101동~48동) 전체 레코드 확인
- `complex_master.dong_count` 와 `SELECT COUNT(*) FROM complex_master_dong WHERE complex_id=?` 일치

---

## 5. 이력 CSV Phase A-8 적재 (선택)

### 상태

- 단지별 준공·관리업체 변경 이력
- 저장 위치: `complex_master_history` (신규 테이블)
- 현재 활용처가 명확하지 않아 후순위

### 판단 기준

- Propedia 상세 페이지에서 이력 탭이 필요할 때만 착수
- 그전까지는 원본 CSV만 `data/complex_master_raw/`에 보관

---

## 완료 정의 (Week 6 종결 조건)

- [ ] PropSheet/Propedia 검색창 통합 배포 (3곳 동기화 확인)
- [ ] Phase G-4 단지 경계 폴리곤 운영 배포
- [ ] 매물 등록 자동완성 (PropSheet/Propedia 앱+웹 3곳)
- [ ] 동정보 CSV 수령 즉시 적재 (대기 상태 → 완료)
- [ ] 이력 CSV는 판단 후 착수 또는 Week 7 이관

> Phase D(center_lat 보강)는 Week 5에서 cron으로 장기 실행 중이며 Week 6 범위 아님. 완료(모든 `center_lat IS NOT NULL`)는 약 25일~1개월 뒤로 예상.
