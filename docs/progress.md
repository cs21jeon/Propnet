# PropNet 통합 개발 진행 기록

> 최종 업데이트: 2026-04-09
> 크로스 서비스 변경 및 인프라/공통 작업을 기록합니다.

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
