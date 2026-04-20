# Proptalk 개발 진행 기록

> 최종 업데이트: 2026-04-20

## 2026-04-20: 파일 공유 인텐트 확장 + 이미지 썸네일 + 웹 링크

- **외부 공유(Share Intent) 확장**: 오디오만 → 이미지(image/*), PDF(application/pdf) 추가
  - AndroidManifest.xml: intent-filter 추가 + READ_MEDIA_IMAGES 권한
  - main.dart: 오디오/일반 파일 분기 라우팅
  - ShareRoomPickerScreen: isAudio 파라미터, 일반 파일은 과금 체크 건너뛰기
- **서버 이미지 썸네일 생성**: 업로드 시 Pillow로 300x300 JPEG 썸네일 자동 생성
  - DB: file_attachments에 saved_filename, thumbnail_path 컬럼 추가
  - API: GET /api/files/{id}/thumbnail, GET /api/files/{id}/download 엔드포인트
  - config.py: THUMBNAIL_FOLDER, THUMBNAIL_MAX_SIZE 설정
- **앱 채팅 이미지 썸네일**: file_type=image → 200px 둥근 썸네일, 탭 → 풀스크린 뷰어
  - fullscreen_image_viewer.dart: 검정 배경 + InteractiveViewer 핀치줌
  - 버블 패딩 조건 분기 (이미지=축소, 텍스트=기본)
- **웹 채팅 이미지 썸네일**: img 태그 + token 쿼리 인증, 클릭 시 풀스크린 오버레이
- **웹 URL 링크화**: renderContent()에 URL→<a> 태그 변환 추가
- 수정 파일: AndroidManifest.xml, MainActivity.kt, main.dart, chat_screen.dart, share_room_picker_screen.dart, api_service.dart, fullscreen_image_viewer.dart(신규), config.py, models.py, routes_messages.py, app.html, app.js, migrate_file_thumbnails.sql(신규)

## 2026-04-17: 웹 댓글(Reply) 기능 구현 — 앱과 연동

- **WebSocket new_message 핸들러 수정** (app.js): parent_id가 있는 비텍스트 메시지(transcript, system)를 부모 메시지의 replies 배열에 중첩 추가. 기존에는 독립 메시지로 표시되어 앱과 불일치
- **답글 전송 기능** (app.js): replyToMsg()에서 parent_id 저장, sendMessage()에서 서버에 parent_id 전달. 웹에서도 특정 메시지에 답글 가능
- **답글 UI 추가** (app.html + app.css):
  - 입력창 위 reply-preview-bar: 답글 대상 프리뷰 + 취소 버튼
  - 텍스트 답글 메시지 내 reply-quote: 원본 메시지 인용 표시, 클릭 시 원본으로 스크롤
  - 라이트/다크 모드 + own-message(파란 배경) 색상 대응
- **캐시 버스팅**: app.css, app.js에 ?v=2 쿼리 파라미터 추가
- **white-space: pre-wrap 여백 수정**: reply-quote와 본문 사이 HTML 공백이 렌더링되는 문제 → 인라인화
- 수정 파일: app.js, app.css, app.html (서버 동시 배포 완료)

## 2026-04-15: 메시지 삭제 + 이모지 리액션 기능

- **메시지 삭제 기능**: 본인 메시지 + 방장(admin) 삭제 권한
  - `DELETE /api/messages/<id>`: DB + Google Drive + Google Sheets + 로컬 파일 일괄 정리
  - 자식 메시지(replies: system/transcript) 함께 삭제
  - WebSocket `message_deleted` 이벤트로 실시간 반영
- **이모지 리액션 기능**: 6종 (👍❤️😂😮😢🙏) 토글 방식
  - `message_reactions` 테이블 신규 (UNIQUE: message_id + user_id + emoji)
  - `POST /api/messages/<id>/reactions`: 있으면 제거, 없으면 추가
  - `Message.list_for_room()` 쿼리에 reactions 서브쿼리 포함
  - WebSocket `reaction_updated` 이벤트로 실시간 반영
- **Flutter 앱**: 길게 터치 → 이모지 6개 바 + 답글/복사/삭제 바텀시트, 리액션 배지 UI
- **웹 UI**: 호버 `⋮` 버튼 + 우클릭 컨텍스트 메뉴, 리액션 배지, 삭제 확인 모달
- **sheets_service.py**: `delete_record()` 추가 — 파일명으로 Sheets 행 검색 후 삭제
- 수정 파일: models.py, routes_messages.py, sheets_service.py, chat_screen.dart, api_service.dart, socket_service.dart, app.html, app.js, app.css

## 2026-04-12: Billing 시스템 전면 점검 및 모니터링 구축

- **propnet_user_id 누락 수정**: user_billing INSERT 시 propnet_user_id 미설정 → 조회 불가 버그 수정
  - admin_dashboard_service.py update_billing() + UserBilling.ensure() 자동 조회 추가
- **set_plan 액션 버그 수정**: 요금제 변경 시 시간 미추가 → plan_type별 분기 (time_pack: 시간 추가, subscription: 시간 설정+상태 활성화)
- **구독 만료 자동 처리 크론 추가** (04:05): active/cancelled + expires_at 경과 → expired 전환
- **과금 알림 시스템 구축** (FCM 4종):
  - 잔여시간 5분 이하 진입 / 시간 소진 / 구독 만료 3일 전 / 자동결제 실패
- **STT 후 앱 잔여시간 자동 갱신**: audio_status WebSocket에 billing 정보 포함 → Flutter updateFromServer()
- **Admin 대시보드 보완**:
  - 구독상태 표시 개선 (시간팩/충전됨/결제실패/해지예정 구분)
  - /admin/billing 페이지 → 결제 이력 중심 개편 (유저별 조작은 /admin/users로 통일)
  - PropNet admin 구독 해지 버튼 추가
  - Proptalk admin 유저 상세에 PropNet 연결 정보 표시
  - Proptalk admin 유저 목록에 검색/필터 추가
- **모니터링 인프라 구축**:
  - /admin/api/billing-health: 구독현황, 오늘 결제, STT 사용량, 잔여0유저, 최근 에러 등 한번에 조회
  - billing_daily_summary 테이블 + 크론(23:55): 일간 매출/결제/가입/사용량 자동 집계
  - billing_error_logs 테이블: Toss 결제 실패, 갱신 실패 구조화 기록
  - access_logs 감사 로그 활성화: admin 과금 조작, role 변경 자동 기록
- **role ↔ agent_id 정합성 규칙 구현**:
  - user로 변경 시 소속(agent_id) 해제 확인 다이얼로그
  - subagent 변경 시 agent_id 없으면 차단
  - agent 변경 시 agents 레코드 + agent_id 자동 연결
- **유저 검색 필터 확장**: 이름/이메일 + 사무소명 + 역할 + 요금제 + 구독상태 5종 필터

## 2026-04-11: Proptalk 웹 PWA standalone → browser 변경

- manifest.json `display: standalone` → `display: browser` 변경
  - 이메일 "PC 웹 열기" 클릭 시 별도 앱 창 대신 일반 브라우저 탭에서 열림
- app.html manifest 캐시 버스팅 v4 → v5

## 2026-04-10: 크로스 서비스 네비게이션 링크 추가

- 랜딩 페이지 헤더/푸터에 "PropNet 서비스 모두 보기" 버튼 추가
- 가이드 페이지 헤더에 "PropNet 홈" 링크 추가
- → PropNet 메인 랜딩에 Proptalk 사용가이드 링크 반영

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
