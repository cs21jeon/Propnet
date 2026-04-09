# Proptalk 개발 진행 기록

> 최종 업데이트: 2026-04-10

## 2026-04-10: 사용 가이드 페이지 전면 리뉴얼

- guide.html 전면 리뉴얼: 6개 → 8개 섹션 구조 개편
  - 앱 설치, 로그인 & 알림, 홈 화면, 업무 채팅방, 음성 요약, 음성파일 원본 & 오디오 플레이어, 프로필 & 설정, PropSheet 연동(중개사 전용)
- 최신 앱 캡쳐 이미지 30장 교체 (Guide페이지용 캡쳐 폴더)
  - Play Store 검색/설치, 로그인, 알림 허용, 홈 화면, 채팅방 CRUD, 음성 요약 리스트/상세/검색, 오디오 플레이어, Drive 연결, 프로필 라이트/다크모드, 계정 삭제, PropSheet 연동 4장
- 중개사 전용 섹션 신설: PropSheet 매물장 전화번호 연결, 통화 요약 팝업, 채팅방 연동 뷰
- 디자인 개선: 중개사 전용 오렌지 배지, 웹 스크린샷 넓은 레이아웃, 맨 위로 돌아가기 버튼

## 2026-04-09: 요금제 설명 개선 + 가이드 초대코드 + 계정 삭제 soft delete

- 요금제 Agent Regular "기본(1시간)" 표기, 3개 카드 배지 "Propsheet, PropMap 포함"
- 요금제 하단 설명: Proppedia/Propsheet/PropMap 서비스 포함 상세 안내
- 가이드 페이지에 "팀원 초대하기 & 참여하기" 섹션 추가 (스크린샷 2장)
- 계정 삭제 FK 위반(payment_transactions) 오류 수정
  - `DELETE FROM users` → `UPDATE SET is_active=FALSE` + 개인정보 익명화
  - `models.py`: find_by_google_id에 is_active=TRUE 필터, create에 재활성화 로직
  - DB: voiceroom.users에 is_active BOOLEAN 컬럼 추가

## 2026-04-09: 음성 요약 검색 기능 추가

- 음성 요약 목록에 텍스트 키워드 검색 기능 추가 (채팅방 메시지 검색과 동일 UX)
  - 검색 대상: 요약 내용, 변환 텍스트, 파일명, 발신자명, 전화번호 (ILIKE)
  - 백엔드: `routes_audio.py` q 파라미터, `models.py` list_summaries_for_user query 조건
  - 웹앱: 요약 패널 상단 검색바 + 결과 카운트 표시
  - Flutter 앱: `summary_list_screen.dart` 검색 입력 필드, `api_service.dart` query 파라미터

## 2026-04-09: 읽음 처리(mark-read) 전면 개선 + 공지사항 API

- 메시지 전송 시 발신자 last_read_message_id 자동 업데이트 (텍스트/음성/파일)
- WebSocket 개인 room(user_{id}) 방식으로 read_update 전파 전환
- 채팅방 밖(목록 화면)에서도 read_update 실시간 수신
- 웹앱 markRead에 REST API 백업 호출 추가
- auth.py: propnet_auth 2차 fallback에서 sub→service_user_links 변환 수정
- /api/notices: goldenrabbit_db.app_notices 기반 Proptalk 공지 조회
- /api/app-version: app_version.json 기반 인앱 업데이트 체크
- PropSheet 채팅등록일시 필드 연동 (system_generated_value)
- 관리자 대시보드 공지사항 CRUD + 권한 만료 시 로그인 리다이렉트
- docs 정리: ARCHITECTURE, BUSINESS_CHECKLIST, LAUNCH_PLAN, SETUP_GUIDE, 결제계획서 → archive 이동
- 마케팅 guide.html 업데이트

## 2026-04-09: v1.0.8+9 — 읽음 확인 실시간 업데이트, 인앱 업데이트 알림

- 읽음 확인 실시간 업데이트 수정 — 채팅방 밖에서도 read_update 수신 (개인 room 방식)
- 채팅방 목록 unread badge 실시간 갱신 (read_update + new_message 스트림 구독)
- 인앱 업데이트 알림 기능 추가 — 새 버전 출시 시 다이얼로그 + Play Store 이동
- 강제 업데이트 지원 (min_version_code 이하 버전은 업데이트 필수)
- 웹앱 mark-read REST API 백업 호출 추가

## 2026-04-03: v1.0.5+8 — PropNet 통합 브랜딩, 웹앱 출시, 읽음 확인

- Proptalk 웹앱(/proptalk/web/) 신규 출시 - PC 브라우저에서 앱과 동일한 기능
- 메시지 읽음 확인 기능 (카카오톡 스타일 안 읽은 수 표시)
- PropNet 통합요금제 전환 (Proptalk → PropNet 브랜딩)
- 요금제 페이지 비로그인 열람 허용, URL /billing/ 통합
- 웹앱 클립보드 이미지 붙여넣기, 파일 메시지 카드 UI
- PWA 설치 지원, 다크모드/라이트모드 토글

## 2026-04-01: v1.0.4+7 — 답글 기능, 실시간 동기화 안정화

- 메시지 답글(댓글) 기능 추가 (롱프레스 → 답글, 원문 인용 표시)
- 답글에서 원문 메시지로 즉시 이동 + 되돌아가기 버튼
- 실시간 동기화 안정화 (WebSocket 연결 유지 개선)
- 알림 탭 시 앱이 열리지 않던 버그 수정

## 2026-03-29: v1.0.3+6 — FCM 푸시 알림, 서버 안정성

- FCM 푸시 알림 활성화 (요약 완료/실패, 텍스트, 파일 업로드)
- 알림 탭 시 해당 채팅방으로 바로 이동
- Claude API 요약 재시도 로직 (3회, exponential backoff)
- 서버 gunicorn + eventlet 전환 (WebSocket 안정화)

## 2026-03-25: v1.0.2+5 — 서버 버그 수정, 음성 요약 UI 리디자인

- 채팅방 삭제 시 usage_logs FK 위반 버그 수정
- 음성 요약 화면 2단계 구조 (채팅방 선택 → 요약 목록)
- 요금제 안내 서버 API 동적 로딩 (하드코딩 제거)
- 관리자 대시보드 버전 관리 자동화 (CHANGELOG.json 연동)

## 2026-03-15 이전: 초기 개발

- Google OAuth + Drive 연동, 채팅방, 음성 업로드, STT(Whisper), Claude 요약
- 파일명 파싱, Drive 프록시 다운로드, WebSocket 실시간 업데이트
- 서비스 이용 동의, RBAC 권한, 회원 탈퇴, 프로필 화면
- 톡방 참여 승인, 톡방 관리(삭제/이름변경/나가기/즐겨찾기)
- 결제 시스템 (Toss Payments 연동)
