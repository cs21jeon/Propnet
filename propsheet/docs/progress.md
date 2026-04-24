# PropSheet 개발 진행 기록

> 최종 업데이트: 2026-04-24

## 2026-04-24: 상세보기 파일 삭제 시 파일명 잔존 버그 수정

- 레코드 상세보기에서 첨부파일 X 버튼 클릭 후 파일명이 UI에 남아있는 버그 수정
  - `database_list.html`: 삭제 핸들러의 `fetchItems()` → `loadData()` + `detailPanel.item` 갱신
  - 원인: 미정의 함수 `fetchItems()` 호출 → ReferenceError → `detailPanel.item[col.key]` 미갱신 → fallback 템플릿이 삭제 전 파일명 재표시

## 2026-04-23: 대표사진 필드 이미지 전용 업로드 제한

- 대표사진 필드에 PDF 등 비이미지 파일 업로드 시 차단 (jpg/jpeg/png/gif/webp만 허용)
  - `routes/database.py`: `IMAGE_ONLY_FIELDS`, `IMAGE_EXTENSIONS` 추가 + 업로드 시 검증
- 상도1동 324-3 매물(db_id=38, id=181) 파일 필드 교정: PDF→건축물대장, JPG→대표사진

## 2026-04-20: 현황→등록 자동 geocoding + 가이드 CTA

- 현황을 '등록'으로 변경 시, 좌표가 없으면 지번 주소로 VWorld 자동 geocoding
  - `routes/database.py` update_single_field에 auto-geocode 로직 추가
  - audit_log에 coordinates_lat/lon 변경도 기록
- 가이드 헤더에 회원가입/PropSheet 시작하기 CTA 버튼 추가
  - `guide.css`: `.guide-cta-btn`, `.guide-cta-primary`, `.guide-cta-outline` 스타일
  - `guide/_base.html`: 헤더 우측에 CTA 링크 2개

## 2026-04-15: 워크스페이스 DB 우클릭 컨텍스트 메뉴

- DB 카드/목록 아이템에 우클릭 시 커스텀 컨텍스트 메뉴 표시
  - "새 탭에서 열기" / "새 창에서 열기" 2개 옵션
  - 새 창은 화면 80% 크기로 중앙에 독립 윈도우로 열림
- `workspaces.js`: getDatabaseUrl() 헬퍼 추출, showContextMenu/openInNewTab/openInNewWindow 추가
- `workspaces.html`: DB 카드에 @contextmenu 바인딩 + 메뉴 HTML
- `workspaces.css`: 컨텍스트 메뉴 스타일 (라이트/다크모드)

## 2026-04-13: 현황→등록 변경 시 PropMap 광고 면책 확인 다이얼로그

- `database_list.js`: 현황 필드를 '등록'으로 변경 시 확인 다이얼로그 추가 (2곳: 그리드 뷰 + 디테일 패널)
  - "등록으로 수정하면 PropMap에 광고가 등록됩니다. 광고 정보에 대한 모든 책임은 등록한 중개사무소에 있습니다."
- 이용약관 제6조/제8조에 이미 면책 조항 확인됨

## 2026-04-11: 레코드생성일자 필드 통합 + 컬럼 show/hide 서버 동기화 + 필드 정합성 정리

- 레코드생성일자 필드 마이그레이션
  - goldenrabbit: `날짜`(NULL) 컬럼 삭제, `레코드생성일자`(timestamp) 유지, type→system_generated_value
  - template/propnet/silverrabbit single: `날짜`→`레코드생성일자` rename
  - part/multi-unit: 이미 `레코드생성일자` 존재, type만 통일
  - propsheet_save_service.py: 하드코딩 `레코드생성일자` 복원 (모든 테이블에 컬럼 존재 보장)
  - view column_config에 `레코드생성일자` 추가 (날짜→rename 후 누락 보정)
- 컬럼 show/hide 서버 동기화 (database_list.js)
  - toggleColumn/selectAll/deselectAll: localStorage→서버 view API에 debounce(500ms) 저장
  - 페이지 리로드 후에도 컬럼 가시성 유지
- 전체 워크스페이스 필드 정합성 감사 및 정리 (20건→0건)
  - view 유령 필드 74개 제거 (template에서 goldenrabbit 전용 필드 참조)
  - part DB field_definitions 104개 보충
  - 레거시 field_def 제거 (airtable_id, 번호, 생성일자, 테스트3 등)

## 2026-04-10: PropSheet ↔ Proppedia 양방향 연동 버튼 추가

- 부동산 DB(단일/부분/집합)에 "Proppedia 조회" 버튼 추가 (database_list.html)
  - database.slug 기반 조건부 표시 (single/part/multi-unit만) — DB 이름 변경에 안전
  - 새 탭으로 /proppedia/ 열기, SSO 쿠키 자동 연동
  - 기존 "부동산 조회" 버튼 → "워크스페이스"로 라벨 변경
- Proppedia 저장 성공 시 "PropSheet에서 보기" 바로가기 모달 추가 (result.html)
  - save API 응답에 agent_slug/db_slug 추가 (propsheet_save.py, proppedia/app.py)
  - alert() → 성공 모달로 교체, PropSheet DB 페이지 새 탭 열기
- Nginx: /api/auth/ → 5010 라우팅 추가 (SSO token-sync 수정)
  - 기존: /api/ → 5000으로만 라우팅되어 session-sync 실패 → Proppedia 로그인 풀림
  - 수정: /api/auth/ → 5010(proppedia) 우선 매칭

## 2026-04-09: 채팅등록일시 시스템필드 + 정렬 자동 저장 + 문서 정리

- 채팅등록일시 system_generated_value 필드 추가 (채팅방 DB 전용)
  - proptalk_service.py: 동기화 시 voiceroom audio_files.created_at 저장
  - database_service.py: system_value_key가 실제 컬럼명이면 직접 참조
  - database_list.html: 시스템값 드롭다운에 채팅등록일시 옵션 (채팅방 DB에서만 표시)
- 정렬 변경 시 뷰에 자동 저장 (toggleSort → saveCurrentView 호출 추가)
- 뷰 없는 DB에 기본 뷰 자동 생성 + 빈 sort_config 보정
- → Proptalk mark-read 개선 연동
- 문서 정리: system-status.md 삭제, airtable-feature-gap.md 갱신

## 2026-04-08: PropMap 지도 center 좌표 동적화

- 지도 center 좌표를 하드코딩에서 DB 기반 동적 조회로 변경
- agents-public API에서 center_lat/center_lng 반환

## 2026-04-07: 통합 인증 + agent 온보딩 + billing 연동

- propnet_users SSoT 전환 완료
- 웹 SSO 쿠키 동기화 (propnet.kr)
- agent_slug 기반 URL 구조 전환 (require_agent_access 데코레이터)
- billing_check 모듈: admin도 agent owner로 PropSheet 접근 허용
- Gmail 점 정규화 적용

## 2026-04-04: 물건종류(세부유형) 필터 기능 추가

- 매물지도 + 조건검색에 물건종류 필터 추가
- 유형별 매핑: 단일=매물종류(DB 39), 집합=물건종류(DB 38), 부분=룸형태(DB 43)
- map-data API: 단일 SELECT에 매물종류 추가, 부분 property_subtype을 룸형태로 변경
- search-map API: 3개 타입 모두 subtype_values 배열 IN 쿼리 지원
- map.html: 세부종류 패널 (부동산유형 클릭→왼쪽 float), 매물 개수 표시
- index.html: 세부종류 체크박스 칩 UI (복수 선택), 검색 폼 최상단 배치

## 2026-03-26: Airtable 완전 제거 → PropSheet DB 전환

- 모든 매물 데이터, 이미지, 건축물대장이 PropSheet DB + 로컬 파일 시스템으로 전환
- Airtable API, backup 스크립트, backup 디렉토리 제거
