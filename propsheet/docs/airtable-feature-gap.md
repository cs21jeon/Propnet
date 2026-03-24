# 에어테이블 vs Propsheet 기능 갭 분석

> 작성일: 2026-03-03 | 마지막 업데이트: 2026-03-24 (캘린더 뷰, time 필드, Proptalk 통화요약 연동, 전화번호 매칭)

---

## 1. 현재 기능 비교표

| 기능 | 에어테이블 | Propsheet | 상태 | 우선순위 |
|------|:---------:|:---------:|:----:|:-------:|
| **필드 타입** | | | | |
| Single line text | O | O | 완료 | - |
| Number | O | O | 완료 | - |
| Long text | O | O | 완료 | - |
| Single select | O | O | **완료** | - |
| Multiple select | O | O | **완료** | - |
| Date | O | O | **완료** | - |
| Formula | O | O | **완료** | - |
| Attachment | O | O | **완료** (이미지 썸네일/PDF, 업로드, 드래그앤드롭, 타입 변환 지원) | - |
| URL | O | △ | **부분구현** | P3 |
| Phone number | O | X | 미구현 | P3 |
| Checkbox | O | O | **완료** (셀 클릭 토글, 상세보기 체크박스, NULL=빈체크) | - |
| Time | O | O | **완료** (시/분 2단계 드롭다운, 10분 단위) | - |
| Currency | O | X | 미구현 | P3 |
| **뷰/필터** | | | | |
| 캘린더 뷰 | O | O | **완료** (월/주/일/년 4모드, 일정/할일, 담당자, 중요도) | - |
| 다중 뷰 (View) | O (4개) | O | **완료** | - |
| 고급 필터 (AND/OR) | O | O | **완료** | - |
| 정렬 | O | O | 완료 | - |
| 그룹화 | O | X | 미구현 | **P2** |
| 숨기기/표시 (컬럼) | O | O | 완료 | - |
| **데이터 관리** | | | | |
| 레코드 CRUD | O | O | 완료 | - |
| 인라인 편집 | O | O | **완료** | - |
| 행 확장 (상세 보기) | O | O | **완료** | - |
| 레코드 히스토리 | O | O | **완료** (audit_log, 필드별 이력, 되돌리기) | - |
| 휴지통/복원 | O | O | **완료** (소프트 삭제, 30일 보관, 복원/영구삭제) | - |
| **UI/UX** | | | | |
| 컬럼 순서 변경 (DnD) | O | O | 완료 | - |
| 컬럼 너비 조절 | O | O | **완료** (드래그+더블클릭 자동맞춤+뷰저장) | - |
| 조건부 서식 | O | X | 미구현 | P3 |
| 이미지 썸네일 | O | O | **완료** (셀 썸네일+클릭 확대+디테일패널) | - |
| 행 색상/태그 | O | X | 미구현 | P3 |
| **연동/공유** | | | | |
| CSV 내보내기 (뷰별) | O | O | **완료** (뷰 필터/정렬/컬럼 반영) | - |
| CSV 가져오기 | O | X | 미구현 | P3 |
| DB 공유 복제 (링크) | X | O | **완료** (토큰 링크, 7일 만료) | - |
| API 접근 | O | O | 완료 | - |
| 레코드 연결 (Link) | O | X | 미구현 | P3 |
| 웹훅/자동화 | O | X | 미구현 | P3 |
| **협업/관리** | | | | |
| 데이터베이스 복제 | O | O | **완료** | - |
| 낙관적 잠금 (충돌 감지) | O | O | **완료** | - |
| 사용자 관리 (Google OAuth) | O | O | **완료** | - |
| 멤버 초대 (역할 기반) | O | O | **완료** | - |
| 권한 라우트 적용 | O | O | **완료** | - |
| 랜딩/로그인 페이지 | O | O | **완료** | - |
| 실시간 동시 편집 | O | X | 미구현 | P3 |

---

## 2. P1 (핵심 기능) - 우선 개선 항목

### 2.1 수식(Formula) 엔진 강화

**현재 상태**: PostgreSQL SQL 기반 기본 수식 지원 (COALESCE 래핑)

**필요한 수식** (에어테이블에서 실제 사용 중):

```
# 융자제외수익률(%)
ROUND((({월세(만원)}*12)/({매가(만원)}-{보증금(만원)}))*100, 1)

# 126% 가격
ROUND({감정가(만원,랜드북)}*1.26, 0)

# 실투자금
{매가(만원)} - {보증금(만원)}

# 융자포함수익률
ROUND(((({월세(만원)}*12)-({매가(만원)}*0.05))/({매가(만원)}-({보증금(만원)}+{매가(만원)})))*100, 1)

# 홍보문구 (텍스트 조합 수식 - 가장 복잡)
"♣ 매물번호를 알려주시면..." & "\n" & {홍보문구} & "\n" &
"- 매매금액 : " & IF({매가} >= 10000, ...) & ...
```

**개선 방안**:
- 현재 PostgreSQL SQL 수식을 확장하여 텍스트 조합 수식 지원
- `IF()`, `ROUND()`, `FLOOR()`, `MOD()`, `CONCATENATE()` 함수 추가
- 에어테이블 수식 → SQL 변환기 구현
- `field_definitions` 테이블의 `formula` 컬럼 활용

### 2.2 뷰(View) 시스템 ✅ 완료 (2026-03-04)

**구현 완료**:
- `views` 테이블 생성 (database_id, name, slug, filter_config JSONB, sort_config JSONB, column_config JSONB)
- 뷰 전환 탭 UI (상단 탭 바)
- 뷰 생성/저장/삭제 기능
- 뷰별 필터/정렬/컬럼 설정 자동 저장 및 복원
- 기본 뷰(Grid View) 보호 (삭제 불가)
- 외부 클릭 시 뷰 생성 팝업 자동 닫힘

### 2.3 Select 필드 타입 ✅ 완료 (2026-03-04)

**구현 완료**:
- `field_definitions`의 `select_options TEXT[]` 컬럼 활용
- Single select: 드롭다운 UI (클릭 시 플로팅 드롭다운)
- Multiple select: 체크박스 드롭다운 UI (다중 선택/해제)
- 셀 렌더링 시 10색 팔레트 색상 뱃지로 표시
- 필터에서 Select 필드 옵션 체크박스 선택 UI 지원

### 2.4 고급 필터링 ✅ 완료 (2026-03-04)

**구현 완료**:
- AND/OR 필터 로직 토글 (UI 버튼으로 전환)
- 연산자 12개: `equals`, `not_equals`, `contains`, `not_contains`, `gt`, `lt`, `gte`, `lte`, `is_empty`, `is_not_empty`, `is_any_of`, `is_none_of`
- Select 필드용 필터: 옵션 체크박스 UI로 선택/미선택
- 빈값/비어있지 않음 연산자 (값 입력 불필요)

**미구현** (추후):
- 날짜 필드용 필터: 오늘 이전/이후, 최근 N일, 기간 범위

---

## 3. P2 (중요 기능) - 2차 개선 항목

### 3.1 날짜 필드 타입 ✅ 완료 (2026-03-04)

**구현 완료**:
- 날짜 피커 UI (네이티브 date input)
- 한국어 포맷 표시 (YYYY년 M월 D일)
- 날짜 기반 정렬/필터

### 3.2 첨부파일 필드 타입 — Phase 1 ✅ 완료 (2026-03-05)

**구현 완료 (Phase 1 — 에어테이블 백업 이미지 연동)**:
- 에어테이블 백업 이미지를 Nginx로 정적 서빙 (`/uploads/airtable/{airtable_id}/`)
- `attachment` 필드 타입 정식 지원 (schema_service)
- 셀 내 이미지 썸네일 표시 (32px, 클릭 시 전체화면 오버레이)
- PDF 첨부: 📄 아이콘 + 파일명 표시
- 디테일 패널에서 큰 썸네일 (120px)
- onerror 시 파일명 텍스트 대체 (이미지 404 대응)

**미구현 (Phase 2 — 향후)**:
- 직접 이미지/파일 업로드 (드래그앤드롭)
- PDF 백업 (현재 이미지만 백업됨)
- 에어테이블 → DB 마이그레이션 후 자체 저장

### 3.3 그룹화

- 필드 기준 레코드 그룹핑
- 그룹별 소계 (합계, 평균, 개수)
- 그룹 접기/펼치기

### 3.4 레코드 상세 보기 (Row Expansion) ✅ 완료 (2026-03-04~05)

**구현 완료**:
- ▶ 버튼 클릭 시 오른쪽 사이드패널 (640px) 오픈
- 모든 필드를 라벨+값 폼 형태로 표시
- 인라인 편집 (클릭 시 input/textarea 전환)
- Select 필드 드롭다운 편집
- URL 값 자동 감지 → 외부 링크 클릭 오픈
- 긴 텍스트 자동 textarea 전환 (60자 이상/줄바꿈 시 확장, Ctrl+Enter 저장)
- 전체 화면 편집 페이지 링크 (↗ 버튼)

### 3.5 CSV 뷰별 내보내기 ✅ 완료 (2026-03-05)

**구현 완료**:
- 현재 뷰의 필터/정렬/컬럼 설정 반영하여 CSV 내보내기
- `view_id` 파라미터 지원 (없으면 전체 내보내기, 하위 호환)

### 3.6 컬럼 너비 조절 ✅ 완료 (2026-03-05)

**구현 완료**:
- 드래그 리사이즈 (기존) + 더블클릭 자동맞춤 (autoFitColumn)
- 뷰별 컬럼 너비 저장 (`column_config: {columns, widths}` JSONB)
- 리사이즈 후 뷰 자동 저장

### 3.7 이미지 썸네일 ✅ 완료 (2026-03-05)

**구현 완료** (3.2 첨부파일 Phase 1에 통합)

---

## 4. P3 (부가 기능) - 3차 개선 항목

### 4.1 URL/Phone 필드 타입
- URL: 클릭 가능한 링크 렌더링 ✅ 부분 완료 (그리드/상세패널에서 https:// 자동 감지 링크)
- Phone: 전화 아이콘 + 클릭 시 tel: 프로토콜

### 4.2 레코드 연결 (Linked Records)
- 다른 테이블의 레코드 참조
- 양방향 연결

### 4.3 조건부 서식
- 셀 값에 따른 배경색/글자색 변경
- 규칙 기반 (예: 수익률 > 5% → 녹색)

### 4.4 변경 이력
- 레코드 수정 내역 추적
- 변경 전/후 값 기록
- 특정 시점으로 복원

### 4.5 Checkbox 필드
- 참/거짓 토글
- 체크된 항목 필터링

### 4.6 웹훅/자동화
- 레코드 변경 시 외부 알림
- 조건 기반 자동 액션

---

## 5. 에어테이블 수식 → Propsheet 변환 가이드

### 현재 에어테이블에서 사용 중인 수식 목록

| 필드명 | 에어테이블 수식 | Propsheet SQL 변환 |
|--------|---------------|-------------------|
| 126% | `ROUND({감정가}*1.26, 0)` | `ROUND(COALESCE("감정가(만원,랜드북)", 0) * 1.26, 0)` |
| 실투자금 | `{매가}-{보증금}` | `COALESCE("매가(만원)", 0) - COALESCE("보증금(만원)", 0)` |
| 거리(m) | `{매가}-{보증금}-{융자}` | `COALESCE("매가(만원)", 0) - COALESCE("보증금(만원)", 0) - COALESCE("융자(만원)", 0)` |
| 융자제외수익률(%) | `ROUND(...)` | `ROUND(((COALESCE("월세(만원)",0)*12)/(NULLIF(COALESCE("매가(만원)",0)-COALESCE("보증금(만원)",0),0)))*100, 1)` |
| 융자포함수익률 | `ROUND(...)` | (유사 변환) |
| 홍보문구 | 텍스트 조합 (복잡) | PostgreSQL CONCAT + CASE WHEN |

### 변환 규칙
1. `{필드명}` → `COALESCE("필드명", 0)` (숫자) 또는 `COALESCE("필드명", '')` (텍스트)
2. `ROUND(x, n)` → `ROUND(CAST(x AS NUMERIC), n)`
3. `IF(조건, 참, 거짓)` → `CASE WHEN 조건 THEN 참 ELSE 거짓 END`
4. `&` (문자열 연결) → `||` 또는 `CONCAT()`
5. `FLOOR()`, `MOD()` → 동일 함수명
6. `NULLIF()` 사용하여 0 나누기 방지

---

## 6. 구현 로드맵

### Phase 1 ✅ 완료 (2026-03-04)
- [x] 에어테이블 백업 → Propsheet DB 자동 동기화 (04:00 AM)
- [x] Single/Multiple Select 필드 타입 (드롭다운 + 색상 뱃지)
- [x] 뷰(View) 시스템 (생성/저장/삭제/전환, JSONB 설정 저장)
- [x] 고급 필터 (AND/OR 토글, 12개 연산자, Select 필드 체크박스 필터)

### Phase 2 ✅ 완료 (2026-03-04)
- [x] 인라인 편집 강화 (클릭 편집, Tab/Enter 네비게이션, 수식 읽기전용)
- [x] 수식 엔진 강화 (에어테이블 수식 → SQL 변환기, IF/텍스트 조합 지원)
- [x] 날짜 필드 + 피커 UI (네이티브 date input, 한국어 포맷)
- [x] 레코드 상세 보기 (사이드패널, 인라인 편집, 전체화면 링크)

### Phase 2+ ✅ UX 개선 (2026-03-05)
- [x] 상세패널 Select 필드 드롭다운 편집
- [x] URL 자동 링크 (그리드 셀 + 상세패널, https:// 감지 → 외부 링크 오픈)
- [x] 긴 텍스트 편집 UX (자동 textarea 전환, 내용에 맞춰 높이 확장, Ctrl+Enter 저장)
- [x] 상세패널 편집창 전체 너비 활용 (flex 레이아웃 최적화)
- [x] 상세패널 너비 확장 (500px → 640px)

### Phase 3 ✅ 완료 (2026-03-05)
- [x] 데이터베이스 복제 (테이블 구조 + 데이터 + 뷰 완전 복사)
- [x] 낙관적 잠금 (updated_at 기반 충돌 감지, 409 Conflict 응답)
- [x] 사용자 관리 (web_users 테이블, bcrypt 인증, 이중 로그인)
- [x] 멤버 초대 (워크스페이스별 owner/editor/viewer 역할, 초대 모달 UI)
- [x] 워크스페이스 디자인 v2 (Pretendard 폰트, 브랜드 블루, 반응형 레이아웃)

### Phase 3+ ✅ 완료 (2026-03-05)
- [x] Google OAuth 2.0 로그인 (기존 username/password → Google 통합)
- [x] 랜딩 페이지 (`/propsheet/` — Google 로그인 버튼, 브랜드 디자인)
- [x] 권한 데코레이터 라우트 적용 (propsheet.py, database.py, workspace_members.py)
- [x] 워크스페이스 멤버십 기반 필터링 (비멤버는 빈 화면)
- [x] 워크스페이스 생성 시 자동 owner 등록
- [x] 헤더에 Google 아바타/이름/로그아웃 표시
- [x] 로그인 시 Google 프로필 이름 자동 동기화 + '님' 표시

### Phase 4 ✅ 완료 (2026-03-05~16)
- [x] 컬럼 너비 조절 (드래그 리사이즈 + 더블클릭 자동맞춤 + 뷰별 너비 저장)
- [x] CSV 뷰별 내보내기 (현재 뷰 필터/정렬/컬럼 반영)
- [x] DB 공유 복제 (토큰 기반 URL, 7일 만료, 데이터+구조+뷰 복제)
- [x] 이미지/첨부파일 Phase 1 (에어테이블 백업 이미지 Nginx 서빙, 셀 썸네일, 클릭 확대, PDF 아이콘)
- [x] 랜딩 페이지 Propnet footer (회사 정보, 이메일)
- [x] Google OAuth 프로젝트 통합 (proptalk/proppedia 프로젝트로 이전)
- [x] 필드 정의 정리 (airtable_id formula 버그 수정, attachment 타입 정식 지원)
- [x] 동기화 스크립트 record_id 자동 생성 추가
- [x] 내부 메타 컬럼 숨김 (fields_hash, synced_at API 응답에서 제거)
- [x] Multi-select 필터 버그 수정 (is_any_of/is_none_of 부분 포함 매칭)

### Phase 4+ ✅ 필드 설정 강화 + 마이그레이션 (2026-03-17)

**필드 설정 UI 개선**:
- [x] ID 필드 시스템 타입 전환 (편집/삭제 불가, "시스템 필드" 표시)
- [x] Select 옵션 태그 UI (콤마 텍스트 → 색상 태그 + 추가/삭제/색상 팔레트)
- [x] Select 옵션 드래그앤드롭 순서 변경
- [x] Select 옵션 색상 DB 저장 (field_definitions.select_colors JSONB)
- [x] 숫자 형식 설정 (천단위 쉼표, 소수점 자릿수, 음수 허용 — field_definitions.number_format JSONB)
- [x] 날짜 형식 설정 (7가지: 한글, 점, 대시, 슬래시, 8자리, 6자리, 년도만 — field_definitions.date_format JSONB)
- [x] 수식 필드 숫자 결과 자동 포맷 (천단위 쉼표, 소수점, 오른쪽 정렬)
- [x] 필드 설정 저장 후 컬럼 순서 유지

**컬럼 헤더 UX 개선**:
- [x] 정렬을 ▲▼ 버튼으로만 동작 (실수 방지, "정렬" 툴팁)
- [x] 헤더 클릭 시 컬럼 선택 (파란 하이라이트)
- [x] Ctrl/Shift+클릭 다중 선택
- [x] 선택한 컬럼들 드래그앤드롭으로 함께 이동

**에어테이블 데이터 마이그레이션**:
- [x] 범용 임포트 스크립트 (API → PostgreSQL 자동 테이블 생성 + 필드 타입 감지)
- [x] 6개 베이스 임포트 완료 (임대차/토지건물/상담문의/상담내역/순번/아파트)
- [x] 에어테이블 → Propsheet 동기화 크론 비활성화 (Propsheet가 원본)

**서비스 아키텍처 적응**:
- [x] basePath `/property-manager` → `/propsheet` 변경 (포트 5020 분리 반영)
- [x] 폰트 경로 `/propsheet/static/fonts/` 수정
- [x] 네비게이션 링크 `/propsheet/workspaces` 수정
- [x] API 인증 실패 시 JSON 401 반환 (login_required 개선)
- [x] JS 세션 만료 감지 → 자동 로그인 리다이렉트 (_checkAuth)
- [x] 정렬 컬럼 미존재 시 created_at/id 자동 대체
- [x] airtable_id 컬럼 미존재 테이블 호환 (_raw_airtable_id 조건부)

**워크스페이스 UX 개선**:
- [x] 데이터베이스 정렬 (이름순, 최근 열어본 순, 최근 생성순)
- [x] 보기 방식 전환 (카드 그리드 / 목록 리스트)
- [x] 즐겨찾기 (★ 항상 표시, 즐겨찾기 항목 상단 고정)
- [x] 아이콘 확장 (워크스페이스 105개, 데이터베이스 109개)

### Phase 4++ ✅ 복제 안정화 + DB 이동 + UX (2026-03-17~18)

**워크스페이스/DB 복제 안정화**:
- [x] clone_database_views() JSONB 크래시 수정 (psycopg2.extras.Json 래핑)
- [x] 단일 트랜잭션 clone_database_full() (테이블+데이터+뷰 원자적 복제)
- [x] 시퀀스 리셋 (MAX(id)+1로 자동 설정)
- [x] psycopg2.sql 모듈로 % 컬럼명 안전 처리
- [x] 실패 시 자동 롤백 + 테이블/메타데이터 정리
- [x] 고아 메타데이터 탐지/정리 유틸리티 (find_orphaned_databases)
- [x] 복제 후 검증 (테이블 존재 + 레코드 수 확인)

**DB 워크스페이스 간 복제/이동**:
- [x] 다른 워크스페이스로 DB 복제 (데이터+구조+뷰 복사, 원본 유지)
- [x] 다른 워크스페이스로 DB 이동 (workspace_id 변경, 즉시 완료)
- [x] 모달 UI (대상 워크스페이스 선택, 현재 WS 제외)
- [x] slug 전역 UNIQUE → workspace별 UNIQUE 확인, 복제 시 원본 slug 유지

**Multi-select UX 개선**:
- [x] 확인 버튼 추가 (체크 후 확인으로 저장)
- [x] 바깥 클릭 시 현재 상태 저장 (투명 backdrop)
- [x] ✕ 버튼은 닫기, 초기화 버튼 별도 분리
- [x] 드롭다운 위치 자동 보정 (화면 밖 방지)
- [x] Select 옵션 중복 제거 (방향 필드 남동향 2개 → 1개)

**기타 수정**:
- [x] "전체 보기" → "필터 초기화" 버튼명 변경
- [x] 레코드 표시 수 "전체" 옵션 추가 (per_page 상한 10000)
- [x] 필드 관리 패널 폭 확장 (280→360px), 버튼 줄바꿈 방지
- [x] database_shares 테이블 권한 부여
- [x] Select 옵션 누락 필드 자동 보정 (SH가능)

### Phase 4+++ ✅ field_definitions DB별 격리 + 필드명 변경 (2026-03-17~18)

**field_definitions per-database 격리**:
- [x] database_id 컬럼 추가 + UNIQUE(database_id, field_name) 제약
- [x] 글로벌 189개 정의 → 9개 DB에 각각 분배 (368개 per-DB)
- [x] 글로벌 정의 완전 삭제 (0개)
- [x] schema_service, routes, database_service 모두 database_id 필터링
- [x] UPDATE/INSERT WHERE에 database_id 스코핑
- [x] 복제 시 field_definitions도 함께 복사 (clone_field_definitions_impl)
- [x] select_options NULL 복원 (실제 데이터에서 자동 추출)
- [x] select_options 저장 버그 수정 (else 블록이 null 덮어쓰기 → 제거)

**필드명 변경 + API Key**:
- [x] field_definitions에 api_key 컬럼 추가 (field_name에서 자동 복사)
- [x] display_name으로 화면 표시명 관리 (DB 컬럼명 변경 없이)
- [x] 필드 설정 모달: 필드 이름 수정 가능 (시스템 필드 제외)
- [x] API Key 읽기 전용 표시 + 복사 버튼 (외부 연동용 고정 식별자)

### Phase 5 ✅ 파일업로드 + 이력관리 + 레코드 관리 (2026-03-18)

**파일 업로드 (Phase 2 첨부파일)**:
- [x] 파일 업로드 API (POST /api/database/{db_id}/upload, 1GB/DB 제한)
- [x] 파일 삭제 API (DELETE /api/database/{db_id}/file/{id})
- [x] file_attachments 테이블 (메타데이터 관리)
- [x] Nginx /uploads/propsheet/ 서빙 (50MB 업로드 제한)
- [x] 상세 패널 드래그앤드롭 + 클릭 업로드 영역
- [x] 업로드 후 셀 값 자동 업데이트 (formatCell 호환 형식)
- [x] formatCell: /uploads/propsheet/ 경로 + /uploads/airtable/ 경로 모두 지원
- [x] 업로드 후 상세 패널 즉시 갱신
- [x] 에어테이블 대표사진 298개 로컬 경로 매핑 (CDN 만료 방지)
- [x] 에어테이블 건축물대장 PDF 404건 다운로드 + 로컬 매핑
- [x] File (파일/이미지) 필드 타입 드롭다운에 추가

**변경 이력 + Ctrl+Z**:
- [x] audit_log 테이블 (database_id, record_id, field, old/new value, user, timestamp)
- [x] 모든 인라인 편집 시 자동 기록 (update_single_field에 _log_audit 추가)
- [x] Ctrl+Z 되돌리기 (undoStack 50건, 세션 내)
- [x] undo 시 낙관적 잠금 스킵 (force 플래그)
- [x] undo 후 updated_at 갱신 (재편집 충돌 방지)
- [x] 상세 패널 🕐 이력 버튼 (필드별 변경 타임라인)
- [x] 이력에서 특정 시점으로 되돌리기

**휴지통**:
- [x] deleted_records 테이블 (레코드 JSONB 보관, 30일 만료)
- [x] 삭제 시 소프트 삭제 (영구 삭제 아님)
- [x] 🗑 휴지통 버튼 + 모달 UI (목록, 복원, 영구삭제)
- [x] Decimal 타입 직렬화 수정

**레코드 선택 + 벌크 액션**:
- [x] 행 체크박스 (▶ 옆, 좌측 고정)
- [x] Shift+클릭 범위 선택, Ctrl+클릭 추가 선택
- [x] 헤더 체크박스 전체 선택/해제
- [x] 벌크 삭제 / 복제 / 선택 해제 액션 바
- [x] 레코드 복제 API (source_id, psql.Literal로 % 안전 처리)

**기타**:
- [x] 상세 패널 필드명 옆 ⚙ 설정 버튼
- [x] 필드 설정 모달 z-index 수정 (상세 패널 위)
- [x] ▶ 상세보기 버튼 좌우 스크롤 시 고정 (sticky)
- [x] 색상 팔레트 위쪽으로 열리도록 수정

### Phase 6 ✅ 광고 자동완성 + 테이블 구조 + UI 개선 (2026-03-19~20)

**광고(자동완성) 트리거 시스템**:
- [x] 단일부동산: format_ad_text() — 홍보문구(최상단)+매매금액+임대내역+건물현황+면적(평환산)+층수(지하/지상파싱)+주차+승강기+방향+주용도+용도지역+위반건축물+사용승인일
- [x] 부분부동산: format_ad_text_partial() — 임대전용. 홍보문구+물건종류+임대종류+보증금/월세(전세/월세분기)+관리비+전용면적+방/화+방향+위반건축물+입주가능일
- [x] 집합부동산: format_ad_text_multi() — 매매/전세/월세 3종분기+관리비(매매제외)+전용/공급/대지면적(평환산)+총세대수+총주차+승강기+사용승인일+용도지역+공시가격+방/화+방향+입주가능일
- [x] field_definitions에 formula 타입 및 수식 등록 (트리거+수식 이중구조)
- [x] psycopg2 % 이스케이프 수정 (formula SQL 내 LIKE 패턴 %% 변환)

**부분부동산 테이블 구조 변경**:
- [x] 컬럼 삭제: 실투자금, 실투자금(융자포함), 융자제외수익률(%), 융자포함수익률, 층(복사본)
- [x] 컬럼 추가: 호수, 물건종류, 호실, 전용면적, 관리비, 방, 화, 입주가능일

**UI 개선**:
- [x] 상세보기 줄바꿈 표시 (white-space: pre-line)
- [x] Attachment 필드 클릭 시 편집모드 진입 방지
- [x] 브로커 카드 전화번호 클릭-복사 (점선밑줄, "클립보드에 복사됨" 피드백)
- [x] 체크박스/상세보기 컬럼 순서 변경 + sticky 위치 조정
- [x] 스크롤 시 인라인 편집 자동 저장+닫기
- [x] "전체보기" 옵션 제거 (25/50/100개씩만 선택 가능)

**렌더링 속도 개선 시도 (실패 → 원복)**:
- 시도 1: 셀 포맷 결과 캐싱 (_buildCellCache, _getCachedCell) — formatCell 호출 제거 목적. 체감 개선 미미
- 시도 2: visibleColumnObjects getter 캐싱 — filter() 반복 호출 제거. 체감 개선 미미
- 시도 3: :class 바인딩 간소화 (6개 조건 → 1문자열) — 체감 개선 미미
- 시도 4: 플로팅 에디터 (셀 내 isEditing x-if 제거, 단일 position:fixed input) — 스크롤 시 에디터가 셀과 분리되어 떠다니는 문제
- 시도 5: 배치 렌더링 (30행 먼저 → 나머지 requestAnimationFrame) — Alpine이 2번 전체 리렌더하여 오히려 더 느림
- 시도 6: 가상 스크롤 (보이는 30행만 DOM 생성) — Alpine.js _접두사 변수 접근 불가, thead 고정 깨짐, 컨테이너 레이아웃 문제
- **근본 원인**: Alpine.js x-for가 모든 행을 DOM에 생성하는 구조. 프로덕션 도구(Airtable, NocoDB)는 가상 스크롤/Canvas로 해결하나, Alpine.js 위에서는 호환성 문제로 적용 어려움
- **현재 우회**: 페이지네이션 최대 100행으로 제한하여 DOM 부담 감소

### Phase 6+ ✅ 실시간 동기화 + 서브에이전트 + 데이터 마이그레이션 (2026-03-20)

**실시간 동기화 (3초 폴링)**:
- [x] sync_events 테이블 생성 (모든 변경 이벤트 통합 기록)
- [x] cell_update, record_add/delete, field_add/delete 이벤트 자동 기록
- [x] /api/database/changes 폴링 API
- [x] 프론트엔드 3초 간격 pollChanges() — 다른 사용자 변경 실시간 반영
- [x] 내 변경은 스킵, 셀 변경은 해당 셀만 업데이트 (전체 리로드 아님)

**서브에이전트 시스템**:
- [x] web_users에 role + agent_id 컬럼 추가
- [x] workspaces에 agent_id 컬럼 추가 (agent별 워크스페이스 격리)
- [x] 서브에이전트 초대/관리 API (invite, remove, cancel)
- [x] 팀 관리 모달 UI (agent만 표시, 슬롯 관리, 초대/해제)
- [x] Google 로그인 시 pending 초대 자동 승인 + 워크스페이스 자동 접근
- [x] 단일 디바이스 세션 (active_session_id, 다른 기기 로그인 시 이전 세션 종료)
- [x] 브로커 카드 동적 표시 (agents 테이블에서 정보 로드)
- [x] 샘플 워크스페이스 생성 (admin 전용 템플릿, 새 agent 등록 시 복제용)

**데이터 마이그레이션 (골든래빗 → 금토끼부동산)**:
- [x] 건물매물(367행) → 단일부동산: 컬럼 추가 31개, 데이터 복사, record_id 생성
- [x] 공동주택매물(85행) → 집합부동산: 컬럼 추가 13개, 데이터 복사
- [x] 임대차매물(113행) → 부분부동산: 필드명 매핑(지번→지번주소, 호→호수 등), 컬럼 추가 15개
- [x] 현황→광고 필드 분리 (3개 DB 모두): 광고매체를 multi-select 광고 필드로 이동, 현황은 등록/등록대기로 정리
- [x] 종류 필드 정리: 단일부동산=매매, 부분부동산=전세/월세(보증금/월세 기준 자동판단)
- [x] 물건종류 설정: 다가구주택/상가/사무실 분류
- [x] 룸형태 매칭: 임대차 종류(원룸/투룸/3룸/1.5룸) → 부분부동산 룸형태
- [x] 공시가(만원) → 주택공시가(만원) 통합 후 삭제
- [x] 특징 → 비공개메모 앞에 [특징] 태그로 이동 후 삭제
- [x] 생성일자 → created_at 강제 주입 (레코드생성일자 system_generated_value로 표시)

**건축물대장 API 연동 (부분부동산)**:
- [x] 공공데이터 건축물대장 표제부 API 조회 (getBrTitleInfo)
- [x] 지번 주소 → 시군구코드+법정동코드+본번+부번 자동 파싱
- [x] 동작구/관악구/서초구 법정동 매핑 지원
- [x] 110/113건 건축물 정보 일괄 반영 (건물명, 주구조, 도로명주소, 사용승인일 등)
- [x] 건축물대장 PDF 업로드: 구글드라이브에서 72개 PDF → 서버 업로드 + DB 연결 (23건 매칭)

**기타 수정**:
- [x] 뷰 전환 시 현재 뷰 자동 저장 (switchView에 saveCurrentView 추가)
- [x] system_generated_value 필드 정렬 시 실제 매핑 컬럼으로 치환

### Phase 6++ ✅ Formula 실시간 반영 + 뷰/컬럼 순서 수정 (2026-03-21)

**Formula 실시간 반영**:
- [x] openDetailPanel: get_property(SELECT *) → list_properties(formula 포함) API로 변경
- [x] refreshRecord: 스프레드 연산자 → Object.keys 직접 프로퍼티 수정 (Alpine 반응성 보장)
- [x] saveInlineEdit, saveSelectValue, saveDetailField 후 refreshRecord 호출
- [x] 셀 편집 + 상세보기 편집 모두 formula 결과 즉시 갱신

**뷰/컬럼 순서 수정**:
- [x] 뷰 전환 시 allColumns를 뷰의 column_config 순서로 재정렬
- [x] loadColumns() 후 뷰 순서 자동 재적용 (applyViewColumnOrder)
- [x] 뷰에 column_config 없으면 localStorage 무시하고 전체 필드 표시
- [x] clone_database_full에 clone_field_definitions_impl 호출 추가 (누락 수정)

**기타**:
- [x] 폴링(3초) 제거 — 서버 트래픽 부담. sync_events 테이블/API는 유지 (향후 활용)
- [x] Nginx static 캐시 7일 → 1시간으로 축소
- [x] 워크스페이스/DB slug 변경 (goldenrabbit01→goldenrabbit, single/part/multi-unit)
- [x] Checkbox 필드 타입 추가 (셀 클릭 토글, 상세보기 체크박스, NULL=빈체크)
- [x] Select 옵션 순서 변경 UI: 인라인 태그 → 세로 리스트 + 행 드래그
- [x] 날짜 표시 형식: 상세보기에서도 col.dateFormat 반영
- [x] 용도지역 필드 양식 전체 DB 통일 (단일부동산 기준)
- [x] % 컬럼명 편집 오류 수정 (audit SELECT/UPDATE에 %% 이스케이프)
- [x] 다크모드 구현 (CSS 변수 기반, 🌙/☀️ 토글, localStorage 저장, Select 태그 bg↔text 반전)
- [x] 로딩 오버레이 (전체 화면 반투명 스피너, $nextTick + double rAF로 렌더링 완료 감지)

### Phase 6+++ ✅ 캘린더 뷰 + 일정관리 + time 필드 (2026-03-24)

**캘린더 뷰 시스템**:
- [x] views 테이블에 view_type 컬럼 추가 (grid / calendar)
- [x] 캘린더 라우트 추가 (`/workspace/{ws}/database/{db}/calendar`)
- [x] 캘린더 API 추가 (`GET /api/database/calendar?db=&year=&month=`)
- [x] 캘린더 프론트엔드: calendar.html + calendar.css + calendar.js (Alpine.js)
- [x] 4가지 뷰 모드: 월간(monthly), 주간(weekly), 일간(daily), 연간(yearly)
- [x] 이벤트 칩 표시 (카테고리별 색상, 완료 취소선)
- [x] 사이드 패널: 이벤트 생성/수정/삭제
- [x] 뷰 전환 토글: 스프레드시트 ↔ 캘린더 아이콘 (database_list.html 헤더)
- [x] 다크모드 지원 (기존 CSS 변수 재활용)
- [x] 할일 사이드바: 미완료 할일 목록 (시작일순, 체크박스 완료 토글)
- [x] 연간 뷰: 12개 미니 월 그리드, 이벤트 도트 표시, 월 클릭 → 월간 뷰 이동

**일정관리 DB 템플릿**:
- [x] workspace_service.py에 create_calendar_database_table() 함수
- [x] 워크스페이스에서 DB 생성 시 "일정관리" 템플릿 선택 가능 (workspaces.html/js)
- [x] 템플릿 필드: 제목, 시작일, 종료일, 시작시간, 종료시간, 종일, 유형(일정/할일), 상태(예정/진행중/완료/취소), 우선순위(높음/보통/낮음), 중요도(★★★/★★/★), 카테고리(업무/미팅/외출/개인/기타), 담당자, 메모, 비고
- [x] 기본 캘린더 뷰(view_type='calendar') 자동 생성

**time 필드 타입**:
- [x] field_type='time' 추가 (schema_service.py에서 인식)
- [x] 스프레드시트 상세 패널: 시/분 2단계 드롭다운 (시: 00~23, 분: 10분 단위)
- [x] 캘린더 사이드 패널: 시/분 2단계 드롭다운
- [x] 종일 체크 시 00:00~23:50 자동 설정, 해제 시 09:00~10:00 기본값

**담당자 시스템**:
- [x] `/api/agent/assignees` API (agents + subagent 이름 목록)
- [x] 캘린더 패널 + 스프레드시트에서 담당자 드롭다운 선택

**기타 수정**:
- [x] saveInlineCheckbox() 함수 추가 (database_list.js — 체크박스 셀 클릭 즉시 저장)
- [x] create_new_property() rollback 버그 수정 (레코드생성일자 없는 테이블에서 transaction aborted)
- [x] view_service.py create_view()에 view_type 파라미터 추가

### Phase 6++++ ✅ Proptalk 통화요약 연동 + 전화번호 매칭 (2026-03-24)

**Proptalk 통화요약 DB 템플릿**:
- [x] `proptalk_service.py` 신규 — voiceroom DB 연결 + 채팅방/음성파일 조회
- [x] DB 생성 모달에 "📞 통화요약" 템플릿 추가 (agent/subagent 전용)
- [x] 채팅방 선택 드롭다운 (Proptalk 방 목록 API 연동)
- [x] 통화요약 테이블 자동 생성 (날짜/이름/전화번호/요약/통화내용/길이/Drive링크/상태/업로더/메모)
- [x] 생성 시 기존 음성 파일 전체 가져오기 (voiceroom → goldenrabbit_db)
- [x] databases 테이블 확장: `external_source`, `external_config` JSONB 컬럼
- [x] 스프레드시트 열 때 새 오디오 자동 동기화 (INSERT only, 편집 데이터 보존)
- [x] 편집 가능: PropSheet에서 자유 편집, Proptalk에는 반영 안 됨 (단방향)

**전화번호 ↔ 통화기록 매칭**:
- [x] `check_matched_phones()` — 전화번호 일괄 매칭 (숫자 정규화, 하이픈/공백/메모 대응)
- [x] `get_audio_by_phone()` — 특정 전화번호의 통화 요약 목록
- [x] `POST /api/proptalk/check-phones`, `GET /api/proptalk/audio-by-phone` API
- [x] 페이지 로드 시 현재 페이지 전화번호 일괄 매칭 체크
- [x] 매칭된 셀에 📞+건수 아이콘 표시 (formatCell)
- [x] 클릭 시 사이드패널: 통화 기록 목록 (날짜/이름/AI요약/길이/Drive링크/전문보기)
- [x] 실제 매칭 확인: 단일부동산 소유주연락처 ↔ 금토끼채팅방 4건 일치

**Nginx 캐시 개선**:
- [x] `/propsheet/static/` 캐시: `expires 1h` → `ETag + no-cache, must-revalidate`
- [x] JS/CSS 수정 시 새로고침만으로 즉시 반영 (Ctrl+Shift+R 불필요)

**기타 버그 수정**:
- [x] `getDetailDisplayValue()` col 변수 TDZ 에러 수정 (선언 위치 이동)
- [x] 체크박스 `saveCheckboxField()` refreshRecord race condition 수정
- [x] time 필드 상세패널 "완료" 버튼 추가 (시/분 모두 선택 후 저장)
- [x] time 필드 저장 후 그리드 실시간 반영
- [x] time 필드 인라인 클릭 → 상세패널 시/분 피커로 이동
- [x] 캘린더 select 옵션 동적 로드 (field_definitions 기반, 하드코딩 제거)
- [x] 캘린더 `$nextTick` 타이밍 수정 (select/time 값 렌더링 후 바인딩)

### Phase 7 (다음 단계)

**실시간 동기화 (보류 — 서버 트래픽 고려)**:
- [ ] 폴링 재도입 시 간격 조정 (10~30초) 또는 WebSocket 전환
- [ ] sync_events 테이블 + /api/database/changes API 이미 구현됨 (프론트만 연결하면 됨)
- [ ] 동시 접속 시에만 폴링 활성화하는 방식 검토

**핵심 기능 (우선)**:
- [ ] 그룹화 — 필드 기준 레코드 그룹핑, 그룹별 소계, 접기/펼치기
- [ ] Phone 필드 — 전화 아이콘 + tel: 프로토콜 클릭
- [ ] 날짜 필터 강화 — 오늘 이전/이후, 최근 N일, 기간 범위

**UX 개선**:
- [ ] 조건부 서식 — 셀 값 기반 배경색/글자색 규칙
- [ ] 행 색상/태그

**데이터 관리**:
- [ ] CSV 가져오기 — 파일 업로드, 컬럼 매핑 UI, 미리보기
- [ ] 휴지통 자동 정리 크론 (30일 만료 레코드 삭제)

**고급 기능 (장기)**:
- [ ] 레코드 연결 (Linked Records) — 다른 테이블 참조, 양방향 연결
- [ ] 웹훅/자동화 — 레코드 변경 시 외부 알림
- [ ] 실시간 동시 편집 (WebSocket)
- [ ] 갤러리/캘린더 뷰
