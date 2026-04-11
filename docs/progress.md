# PropNet 통합 개발 진행 기록

> 최종 업데이트: 2026-04-11
> 크로스 서비스 변경 및 인프라/공통 작업을 기록합니다.

## 2026-04-11: 승인 이메일 개선 + Proptalk PWA 설정 변경

- [통합] 승인 환영 이메일 PropSheet 링크 "PC/모바일 웹 열기" → "PC 웹 열기" 변경
- [Proptalk] manifest.json display: standalone → browser (웹앱 창 대신 브라우저 탭)
- [PropMap] map.html 로고 경로 변경 + 레거시 로고 파일 정리

## 2026-04-11: Agent 환경 셋업 복구 + 필드 정합성 + 문의 API 수정

- [PropSheet] 레코드생성일자 필드 통합 마이그레이션 (날짜↔레코드생성일자 불일치 해소)
- [PropSheet] 컬럼 show/hide 변경이 서버 view config에 자동 저장되도록 수정
- [PropSheet] 전체 워크스페이스 필드 정합성 감사 — 유령 필드/레거시 정리 (20건→0건)
- [PropMap] 통합지도 문의 API 엔드포인트 수정 (존재하지 않는 URL → /api/submit-inquiry)
- [PropMap] propnet agent 매물지도 페이지 생성
- [인프라] Agent 가입 강제완료 시 환경 셋업 타임아웃 분석 및 수동 복구 스크립트

## 2026-04-10: PropSheet ↔ Proppedia 양방향 연동

- [PropSheet] 부동산 DB에 "Proppedia 조회" 버튼 추가 (slug 기반, 모든 agent 공통)
- [Proppedia] 저장 성공 모달에 "PropSheet에서 보기" 바로가기 추가
- [인프라] Nginx /api/auth/ → 5010 라우팅 추가 (SSO session-sync 수정)

## 2026-04-10: 서비스 간 크로스 링크 네비게이션 추가

- [통합] propnet.kr 메인 → Proptalk 사용가이드 링크 추가 (서비스 카드 + 푸터)
- [Proptalk] 랜딩 페이지 헤더/푸터에 "PropNet 서비스 모두 보기" 버튼 추가
- [Proptalk] 가이드 페이지 헤더에 "PropNet 홈" 링크 추가
- [Propedia] 랜딩 페이지 헤더/푸터에 "PropNet 홈" 버튼 추가
- [Propedia] 가이드 페이지 헤더에 "PropNet 홈" 링크 추가
- [문서] CLAUDE.md에 정적 페이지 서버 경로 매핑 테이블 추가
  - propnet.kr 루트는 `frontend/public/propnet/index.html` (index.html 아님)
  - Nginx 설정 2개 분리: goldenrabbit.conf + propnet.conf

## 2026-04-10: Proptalk 사용 가이드 전면 리뉴얼

- [Proptalk] guide.html 6개→8개 섹션 개편, 최신 캡쳐 이미지 30장 교체
- [Proptalk] 중개사 전용 PropSheet 연동 섹션 신설

## 2026-04-09: 랜딩 페이지 네비게이션 개선 + Proptalk 계정 삭제 수정

- [통합] propnet.kr 랜딩 페이지에 중개사 시작 가이드 링크 추가 (헤더/CTA/푸터)
- [통합] PropMap 카드 "서비스 예정" → "운영 중" 전환, /propmap/ 링크 연결
- [통합] PropSheet 배지 "중개사 전용" 표기 추가
- [Proptalk] 요금제 Agent Regular "기본(1시간)" 표기, Propsheet+PropMap 포함 설명 추가
- [Proptalk] 가이드 페이지에 초대코드 참여 설명+스크린샷 추가
- [Proptalk] 계정 삭제 FK 위반 오류 수정: hard delete → soft delete 전환
  - voiceroom.users에 is_active 컬럼 추가, 탈퇴 시 개인정보 익명화
  - 재가입 시 is_active=TRUE 자동 재활성화

## 2026-04-09: Proptalk 음성 요약 검색 + 서버 백업 실패 알림

- [Proptalk] 음성 요약 검색 기능 추가 (웹+앱, 5개 필드 ILIKE 검색)
- [인프라] daily_backup.sh 실행 권한 수정 + 실패 시 이메일 알림 추가

## 2026-04-09: Proptalk 읽음 처리 개선 + PropSheet 채팅등록일시 + 문서 구조 개편

- [Proptalk] mark-read 전면 개선: 발신자 자동 읽음 처리, WebSocket 개인 room 전파
- [PropSheet] 채팅등록일시 system_generated_value 필드 추가 (Proptalk 동기화 연동)
- [PropSheet] 정렬 설정 자동 저장 (toggleSort → saveCurrentView)
- [관리자] 공지사항 CRUD + app_notice_service target_app 필터
- [인증] billing_check: admin도 agent owner로 PropSheet 접근 허용
- [회원가입] subagent 역할 직접 가입 차단 (초대 전용)
- [Nginx/SEO] sitemap, robots.txt, PropMap/Proptalk 랜딩 업데이트
- [통합] 문서 구조 개편: 오래된 docs 6개 삭제 → archive 이동
- [통합] pushupdate 스킬 추가 (.claude/skills/pushupdate/)

## 2026-04-08: PropMap 통합 매물지도 구축

- [PropMap] propnet.kr/propmap/ 통합 매물지도 서비스 신규 구축
- [PropSheet] agents-public API: center 좌표 동적화

## 2026-04-07: 통합 인증 체계 완성 + agent 온보딩

- [인증] propnet_users SSoT + SSO 쿠키(propnet.kr) + 보안 수정
- [PropSheet] agent_slug 기반 URL 구조 전환, require_agent_access 데코레이터
- [인증] agent 신청→심사→결제→활성화 흐름, billing 통합
- [Proptalk] 라이트/다크모드 배경-콘텐츠 색상 대비 개선

## 2026-04-04: 물건종류 필터 + propnet.kr 마이그레이션

- [PropSheet/PropMap] 매물지도 + 조건검색에 물건종류(세부유형) 필터 추가
- [인프라] propnet.kr 도메인 마이그레이션 Phase 0~4 + SSO 쿠키 전환

## 2026-03-26: Airtable 완전 제거

- [PropSheet] 모든 매물 데이터 → PropSheet DB + 로컬 파일 시스템 전환
- [전체] Airtable API, backup 스크립트, backup 디렉토리 제거 완료
