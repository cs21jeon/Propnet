# PropMap 개발 진행 기록

> 최종 업데이트: 2026-04-17

## 2026-04-17: PropMap UI 개선 — 검색창 비활성화 + 내 위치 버튼 + 레이아웃 수정

- 통합 검색창 임시 비활성화 (HTML/JS 주석 처리, 나중에 다시 활성화 가능)
- 전체보기/돌아가기 버튼 삭제 (중개사무소 버튼으로 대체)
- 내 위치 버튼 추가 (지도 우하단, Material `my_location` SVG 아이콘)
  - `watchPosition`으로 백그라운드 위치 캐싱 → 버튼 클릭 시 즉시 이동
  - 앱에서 `myloc=` URL 파라미터로 GPS 좌표 전달 → 캐시 초기화
- 중개사무소 버튼 위치: `top:12px; left:12px` (필터 그룹과 겹침 방지)
- 모바일 바텀시트 `max-height: 50vh → 70vh` (중개사무소 하단 잘림 해결)
- `autoloc=1` URL 파라미터: 위치 동의 다이얼로그 건너뛰기 (앱 WebView용)
  - index.html에서 iframe src에 autoloc 파라미터 전달

## 2026-04-17: Week 5 종결 — 통합 검색 UX (complex_master 연동)

- `propmap/js/unified-search.js` 신규 — 단지명 + 주소 단일 입력 검색
  - `/api/propsheet/complex-search` 호출 (PropSheet 백엔드)
  - 디바운스 200ms, 결과 최대 10건, 키보드 내비게이션(↑↓/Enter/Esc), ARIA 라벨
  - 결과 클릭 시 `center_lat`/`center_lon`으로 지도 이동 (level=3) + 동별 마커 재사용
- `propmap/map.html` 검색창 영역 교체
  - 기존 단일 주소 입력 → `<input id="unifiedSearch">` + 드롭다운 컨테이너
  - 선택 결과 하이라이트 처리 (Phase G-4 축소안 — 경계 폴리곤은 Week 6 이관)
- `propmap/index.html` iframe 호스트에서도 `postMessage`로 검색 결과 전달
- 에이전트별 페이지 동기화: `{goldenrabbit,silverrabbit,propnet}/map.html` 동일 UX 적용
- 실측
  - API p50 72ms / p95 218ms
  - 단지 선택 → 지도 이동 560ms (카카오 타일 로드 포함)
- Playwright E2E
  - "파크리오" 입력 → 1순위 후보(household=6,864) → 클릭 → 지도 이동 → 48개 주거동 마커
  - 스크린샷: `week5_unified_search_demo.png`, `week5_unified_search_selected.png`
- Week 6 이관 과제 (`docs/week6-backlog.md`)
  - Phase G-4 단지 경계 폴리곤 렌더 (현재는 선택 시 하이라이트만)
  - PropSheet/Propedia 검색창 통합 (탭 제거 + unified-search.js 재사용)
  - 매물 등록 시 단지 자동완성 → PNU/동 자동 채움
- 기반 데이터 (PropSheet DB 공통)
  - `complex_master` 307k 단지 (K-apt `apt_basic_info_20250918`)
  - `center_lat` 보강은 Phase D 야간 cron(02:00)으로 약 25일 진행 — PropMap은 `center_lat IS NOT NULL`만 지도 이동 대상

## 2026-04-17: PropMap 버튼 겹침 수정 (검색/필터/전체보기/지도유형 분리)

- `propmap/map.html` + agent별 3개 파일 CSS 버튼 위치 재배치
  - **filter-toggle-btn**: `top:46px → top:8px, right:8px` (map-type-control과 겹침 해소)
  - **map-type-control (모바일)**: `top:46px, right:8px → bottom:30px, left:8px` (하단 좌측 이동)
  - **map-nav-control (모바일)**: `left:50% → right:60px` (검색창과 겹침 방지)
  - **search-overlay (모바일)**: `max-width: calc(100% - 160px)` (전체보기+필터 공간 확보)
  - **filter-panel.open**: `top:90px → top:46px` (필터 토글 위치 변경에 맞춤)
- 적용 대상 4곳: `propmap/map.html`, `{goldenrabbit,silverrabbit,propnet}/map.html`
- 서비스 재시작 불필요 (Nginx 정적 서빙)

## 2026-04-17: 모바일 반응형 전면 개선 (Proppedia 앱 WebView 대응)

- `propmap/index.html` 바텀시트 UX
  - Safe area 적용: `viewport-fit=cover` + `env(safe-area-inset-bottom)` — 기기 홈버튼/제스처바 회피
  - 모바일 접힘 상태에서 PropMap 로고 대신 "N개 중개사무소 보기 ▲" 힌트 라벨 노출 (`renderAgentList`에서 지도 범위 내 개수 실시간 동기화)
  - 중개사 카드 탭 시 시트 자동 닫힘 로직 제거 (연속 선택을 위해 유지)
  - 에이전트 카드 높이 절반 축소: 아바타 48→32px, padding 12→6px, 전화번호 숨김, 폰트 축소
  - 시트 `max-height: 75vh → 50vh`로 지도 가시 영역 확보
- `propmap/map.html` 및 에이전트별 `{goldenrabbit,silverrabbit,propnet}/map.html`
  - 모바일(≤768px)에서 우측 필터 패널을 기본 숨김 → 우측 상단 "필터" 토글 버튼 추가
  - JS: `filterToggleBtn` 클릭 시 `.filter-panel.open` 토글 (+ 버튼 activated 스타일)
- 에이전트별 페이지(`goldenrabbit/index.html` 등) "PropMap 전체 매물지도로 돌아가기" 버튼 강조 — 풀폭 파란색(#136dec) + 화살표 아이콘 (Python 스크립트로 3개 파일 일괄 패치)
- propnet.kr 랜딩(`/propnet/index.html`) 모바일 overflow 수정
  - `html, body { overflow-x: hidden; max-width: 100%; }` 전역 방어
  - `header`에 `left:0; right:0; max-width: 100vw;` + `.header-content { flex-wrap: wrap; min-width: 0; }` 보강
  - 600px 이하 전용: `.services-grid` 1열 전환(기존 968px→2열 규칙 하위에 없던 케이스 보완), 헤더 로고/폰트 축소
- 랜딩(`/propnet/`, `/proppedia/`) 헤더 라벨 통일: "PropNet 홈" → "PropNet 전체 서비스"

## 2026-04-16: Week 4 마무리 — 매칭 로직 정교화 + C안 + 전체 agent + 샘플 워크스페이스

- 매칭 로직 정교화 (`_normalize_dong` + `_match_dong`)
  - `None`, `'동 없음'`, `' '` 등 빈 값 처리
  - `'103'` ↔ `'103동'` 숫자 매칭
  - 건물명 끝 공백 trim, 반각/전각 통일
- C안 구현 (백업 후 덮어쓰기)
  - `coordinates_lat_orig` / `coordinates_lon_orig` 컬럼 추가 (11개 테이블 전체)
  - 480건 좌표 `_orig`에 백업 후 건물 중심으로 덮어쓰기 실행
- UI 내부 필드 5개 숨김 처리 (`schema_service.py` SSoT NOT IN)
  - `bd_mgt_sn`, `coordinates_lat/lon`, `coordinates_lat_orig/lon_orig`
  - PropSheet/Propedia/PropNet 모든 agent + 샘플 워크스페이스 적용
- 샘플 워크스페이스 동기화 (workspace_id=12, slug=template)
  - `template_single/part/multi_unit` 3개 테이블 동일 구조 반영
  - 신규 agent 가입 시 `CREATE TABLE LIKE`로 컬럼 자동 상속 확인
  - 인덱스 재생성 로직은 Week 5 이관 과제로 정리
- silverrabbit/propnet 6개 테이블 스키마 정합화
- 매칭률: 3.6% → 5.5% (전체 477건 기준, 상대 +53%)
- Playwright E2E 검증 완료 (파크리오 48개 주거동 + 부속지번 20-6 리다이렉트)
- 관련 문서: `propmap/docs/week4-progress.md`, `docs/week4-5-final-consolidated-report.md`

## 2026-04-16: Week 3 동 단위 클러스터링 + 단지 팝업 대표 이미지

- 공통 모듈 신규: `propmap/js/dong-cluster-renderer.js`
  - kakao `zoom_changed` 리스너, level<=3 에서 동 마커 렌더링
  - `/propsheet/api/propsheet/map/dong-coords` 호출 + 중복 요청 방지 캐시
  - 동별 매물 카운트 → 진한 파랑(매물 있음) / 반투명 점선 회색(매물 없음)
  - 기존 `createClusterPopup` 재사용 (작업 지시 준수)
- `propmap/map.html`:
  - 동 마커 hover/empty CSS 추가
  - `createClusterPopup` 확장: 대표 이미지(hero) + "동별 보기" 버튼 + 매물별 동 배지
  - 스크립트 로드 + DongClusterRenderer.init 호출
- `propmap/index.html`: iframe으로 map.html 사용 → 별도 수정 불필요
- `frontend/public/propmap/index.html` / `frontend/public/index.html` / `frontend/public/map.html`: 서버 MCP 필요 (Week 3 별도 단계)
- 백엔드 리팩터 연동:
  - `cadastral_service_dong_ext.get_buildings_by_pnu` WFS Filter XML → VWorld Data API `LP_PA_CBND_BUBUN` attrFilter 전환
  - BBOX 150m 반경 + PNU prefix 후처리 필터링
  - `resolve_to_main_pnu`도 Filter XML 제거
  - `routes/map_dong.py`에 `address` 쿼리 파라미터 추가 (/addrlink 폴백 힌트)
- 캐시 워밍 스크립트 신규: `scripts/warm_building_cache.py`
  - `--dry-run` / `--agent` / `--rate-limit` / `--fallback-ldareg` 옵션
- 문서: `docs/week3-wfs-test-results.md`, `docs/week3-qa-report.md` 뼈대 작성
- 기능 플래그 `ENABLE_DONG_CLUSTERING`은 여전히 false 유지 (QA 통과 시 on 예정)

## 2026-04-13: 마커 색상 체계 개편 + 중복 매물 클러스터 + 네비게이션 버튼

- 마커 색상 9종 체계 (유형×거래 조합, 명도 차이)
  - 단일=파랑, 집합=녹색, 부분=주황 × 매매=진한, 전세=중간, 월세=옅은
  - 필터 버튼 색상도 마커와 일치 (매매/전세/월세 → 진한/중간/옅은 회색)
- 마커에서 거래유형 텍스트 제거, 금액만 표시
- 중복 매물 클러스터: 같은 좌표에 여러 매물 → 숫자 마커 → 클릭 시 목록 팝업 → 선택 시 상세
  - 필터 적용 시 클러스터 숫자 동적 업데이트, 1개만 남으면 금액 마커로 전환
- 네비게이션 버튼: 통합지도↔agent별 지도 이동
  - 통합지도: agent 카드에 "매물만 보기" 링크
  - agent별: 매물지도 위에 "전체 매물지도 보기" 버튼
- 우측 패널 agent 카드 레이아웃 정비: 주소/전화번호 세로 배치 (넘침 방지)
- 적용 대상: propmap/map.html, propmap/index.html, map.html(홈페이지), propmap/{agent_slug}/map.html, propmap/{agent_slug}/index.html

## 2026-04-11: PropMap 로고 경로 변경 + 레거시 로고 정리

- map.html 로고 URL: propsheet 경로 → `/propmap/assets/logo/Propmap_transparent.png` 변경
- 레거시 로고 파일 삭제 (`propmap/assets/images/logo/` → `propmap/assets/logo/`로 이동)

## 2026-04-11: 통합 PropMap 문의 API 수정 + propnet agent 페이지 생성

- 통합 PropMap(`/propmap/index.html`) 문의 폼 수정
  - API: `/propsheet/api/propsheet/inquiry`(404) → `/api/submit-inquiry` (올바른 엔드포인트)
  - 필드명: `property_type` → `propertyType` (API 기대 키에 맞춤)
  - 에러 핸들링 추가 (성공/실패/네트워크 오류 alert)
- propnet agent 매물지도 페이지 자동 생성 (`/propmap/propnet/`)
  - agent 가입 강제완료 → 환경 셋업 중 PropMap 페이지 생성

## 2026-04-10: 매물 상세보기 버그 수정

- property-detail API 호출 파라미터 불일치 수정 (`record_id=` → `id=`)
- API 응답 구조 변경 대응: `{success, agent, property}` 래핑 구조에서 `property` 추출
- 필드명 매핑 수정: 한글 필드명 → 영문 필드명 (`land_area`, `floors`, `zoning` 등)
- API 응답의 agent 정보 활용 (로컬 agents 배열 fallback 유지)
- 수정 파일: `propmap/index.html` (fetchPropertyDetail, showPropertyDetail)

## 2026-04-09: PropMap 통합 매물지도 구축 + 문서 정리

- propnet.kr/propmap/ 통합 매물지도 서비스 구축
- agents-public API 기반 중개사무소 패널 + 배지 표시
- agent_slug=all 모드 (전체 매물 통합 표시)
- 멀티 agent 지원: 개별 agent 토글 필터링
- 현위치 다이얼로그, 지도 범위 연동 (범위 밖 agent 자동 숨김)
- 부동산 분류방법 팝업 (단일/집합/부분)
- postMessage 통신: index↔map 양방향 (filterAgent, filterAgents, mapMoved, markerCounts)
- Nginx: propnet.kr/propmap/ 서빙, goldenrabbit.biz/propmap/ 301 리다이렉트
- 문서 정리: update-log.md 삭제, changelog-map-center-dynamic.md 이관, progress.md 신설

## 2026-04-08: 지도 center 좌표 동적화

- 하드코딩 center 좌표를 DB 기반 동적 조회로 변경
- agents-public API에서 center_lat/center_lng 반환
- agent별 지도 초기 위치 자동 설정
- 변경 파일: propsheet.py, map.html (goldenrabbit, silverrabbit, 루트)

## 2026-04-04: 물건종류(세부유형) 필터 추가

- 매물지도(map.html) + 조건검색(index.html)에 물건종류 필터 기능 추가
- 단일(매물종류), 집합(물건종류), 부분(룸형태) 지원
- → PropSheet API 연동 (propsheet.py map-data, search-map)

## 2026-04-01: 집합/부분부동산 지도 표시 + 검색 기능 추가

- 기존 단일부동산만 표시 → 집합/부분부동산 추가
- 부동산유형별 색상 마커: 단일=파랑, 집합=초록, 부분=주황 (거래유형별 명도 차이)
- 우측 필터 패널: 부동산유형(단일/집합/부분) + 거래유형(매매/전세/월세) 조합 필터링
- 검색 폼: 단일/집합/부분 탭, 유형별 동적 검색 필드
- 상세 모달: 유형 뱃지, 거래유형별 가격 표시
- API 확장: map-data(3개 테이블 합산), search-map(유형별 다른 조건), property-detail(db_id 파라미터)
- 동기화 규칙: map.html + index.html(검색+상세) + 검색결과지도 3곳 항상 함께 수정
