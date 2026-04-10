# PropSheet 개발 진행 기록

> 최종 업데이트: 2026-04-10

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
