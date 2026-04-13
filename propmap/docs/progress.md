# PropMap 개발 진행 기록

> 최종 업데이트: 2026-04-13

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
