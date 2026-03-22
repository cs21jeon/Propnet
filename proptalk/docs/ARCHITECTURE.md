# Proptalk - 음성 채팅방 STT 플랫폼

> 최종 업데이트: 2026-03-04 (결제 시스템 - 토스페이먼츠 웹결제 추가)

## 전체 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                    Flutter App (Android)                          │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐    │
│  │ Google    │ │ 채팅방   │ │ 음성파일 │ │ 실시간 메시지   │    │
│  │ 로그인   │ │ 목록/생성│ │ 업로드   │ │ (폴링+Socket)  │    │
│  │ +Drive   │ │ +Drive   │ │ +3GP변환 │ │ +MD 렌더링     │    │
│  └────┬──────┘ └────┬─────┘ └────┬─────┘ └───────┬────────┘    │
└───────┼──────────────┼───────────┼────────────────┼─────────────┘
        │              │           │                │
        ▼              ▼           ▼                ▼
┌──────────────────────────────────────────────────────────────────┐
│               Cafe24 서버 (goldenrabbit.biz:5060)                │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  Flask + SocketIO Server                    │  │
│  │  /api/auth/*      - Google OAuth + Drive 토큰 교환         │  │
│  │  /api/rooms/*     - 채팅방 CRUD + Drive 폴더 생성          │  │
│  │  /api/rooms/*/audio - 음성 업로드 → STT → 요약 → Drive     │  │
│  │  /api/audio/*/download - 다운로드 (로컬 → Drive 프록시)    │  │
│  └───────┬────────────┬──────────────┬────────────────────────┘  │
│          │            │              │                            │
│  ┌───────▼────┐ ┌────▼─────┐ ┌─────▼──────┐                    │
│  │ PostgreSQL │ │ OpenAI   │ │ Anthropic  │ │ TossPayments │   │
│  │ - users    │ │ Whisper  │ │ Claude     │ │ (결제)       │   │
│  │ - rooms    │ │ API      │ │ API        │ │ - 카드결제   │   │
│  │ - messages │ │ (STT)    │ │ (요약)     │ │ - 자동결제   │   │
│  │ - audio    │ └──────────┘ └────────────┘ │ - 환불       │   │
│  │ - billing  │                              └──────────────┘   │
│  └────────────┘                                                  │
└──────────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────┐
│  Google Drive      │
│  (방장 OAuth)      │
│  Proptalk/방이름/  │
└────────────────────┘
```

## DB 스키마

```sql
-- 사용자
users: id, google_id, email, name, avatar_url, google_tokens(JSONB), created_at

-- 채팅방
rooms: id, name, description, created_by, invite_code, drive_folder_id, created_at, updated_at

-- 채팅방 멤버
room_members: room_id, user_id, role(admin/member), joined_at

-- 메시지 (텍스트 + 음성 + 자동댓글)
messages: id, room_id, user_id, type(text/audio/transcript/system),
          content, parent_id(댓글용), created_at

-- 음성 파일 기록
audio_files: id, message_id, room_id, user_id,
             original_filename, file_size, drive_file_id, drive_url,
             phone_number, record_date, parsed_name, parsed_memo,
             transcript_text, transcript_summary, transcript_segments,
             status, drive_status, error_message, created_at, completed_at

-- 사용자 동의 이력 (법적 컴플라이언스)
user_consents: id, user_id, consent_type(terms/privacy/overseas_transfer/audio_processing),
               version, agreed, agreed_at, withdrawn_at, ip_address, user_agent

-- 접속기록 감사 로그 (안전성확보조치 §8)
access_logs: id, user_id, action(login/upload/download/create_room/join_room/remove_member),
             resource_type, resource_id, ip_address, user_agent, details(JSONB), created_at

-- 결제 시스템 (토스페이먼츠)
billing_plans: id, code(free/pack_1h/pack_10h/basic_30h/pro_90h), name, plan_type(free/one_time/subscription),
              minutes_included, price, billing_cycle, overage_rate_per_minute, is_active

user_billing: id, user_id, remaining_seconds(기본 600초=10분), current_plan_id, subscription_status,
             subscription_expires_at, auto_renew, billing_key_encrypted, billing_key_iv, customer_key

payment_transactions: id, user_id, plan_id, order_id, payment_key, amount, status(pending/approved/failed/refunded),
                     billing_type, method, minutes_granted, receipt_url, raw_response(JSONB), error_message

usage_logs: id, user_id, audio_file_id, seconds_used, seconds_before, seconds_after, description
```

## 핵심 플로우

### 1. 로그인 + 동의 + Drive 연동
1) Flutter에서 Google Sign-In (email + profile + drive.file 스코프)
2) `serverAuthCode` + `idToken` 서버로 전송
3) 서버에서 idToken 검증 → JWT 발급
4) serverAuthCode → Google token endpoint에서 access_token + refresh_token 교환
5) tokens를 users.google_tokens에 저장
6) 서버가 `consent_required: true/false` 반환 → 미동의 시 동의 화면 표시
7) 약관/개인정보/국외이전 3항목 필수 동의 → `POST /api/auth/consent`

### 2. 방 생성 + Drive 폴더
1) 방장이 채팅방 생성
2) 방장의 Drive 토큰이 있으면 → Proptalk/{방이름} 폴더 자동 생성
3) drive_folder_id를 rooms 테이블에 캐시

### 3. 음성 업로드 → STT → 요약 → Drive 저장
1) 사용자가 음성파일 업로드
2) 서버에서 음성 메시지 생성 → WebSocket 알림
3) 백그라운드 스레드:
   a. 파일명 파싱 (전화번호/날짜/이름)
   b. 3GP/AMR 감지 → MP3 변환 (ffprobe + ffmpeg)
   c. OpenAI Whisper API로 STT 변환
   d. Claude API로 마크다운 구조화 요약
   e. 자동 댓글 (summary + Drive 저장 여부 메시지)
   f. 방장 Drive에 파일 업로드
   g. Drive 성공 → 서버 파일 삭제 / 실패 → 24시간 로컬 보관

### 4. 다운로드 (프록시)
1) 서버 로컬 파일 있으면 → 직접 전송
2) 없으면 → 방장 Drive에서 프록시 다운로드 (토큰 자동 갱신)

### 5. 결제 플로우 (토스페이먼츠 웹결제)

**시간팩 (일회성):**
1) 앱에서 url_launcher로 `goldenrabbit.biz/proptalk/billing/?token={jwt}` 열기
2) 웹에서 플랜 선택 → `/api/billing/order` 호출 → order_id 생성
3) Toss SDK `requestPayment()` → 카드 결제
4) 성공 시 `/api/billing/confirm` → `add_time()` → 잔여 시간 증가

**월정액 (구독):**
1) 웹에서 Toss SDK `requestBillingKeyAuth()` → 카드 등록
2) 서버에서 billingKey 발급 → AES-256 암호화 저장
3) 즉시 첫 달 결제 `charge_billing_key()`
4) user_billing 업데이트: status='active', expires_at=+30일

**자동 갱신:**
1) 매일 03:00 크론: 만료 1일 전 구독 → billingKey 복호화 → 자동 결제
2) 성공 → expires_at +30일, remaining_seconds 리셋
3) 실패 → status='past_due', 3일 후 → 'expired'

## 기술 스택

| 구분 | 기술 |
|------|------|
| 앱 | Flutter 3.x (Android) |
| 서버 | Flask + Flask-SocketIO + PM2 |
| DB | PostgreSQL (psycopg2) |
| 인증 | Google Sign-In + JWT + OAuth2 (drive.file) |
| STT | OpenAI Whisper API ($0.006/분) |
| 요약 | Anthropic Claude API (마크다운) |
| 실시간 | 3초 폴링 + WebSocket (병행) |
| 파일저장 | Google Drive API (방장 OAuth 토큰) |
| 포맷변환 | ffprobe + ffmpeg (3GP/AMR → MP3) |
| 법적 동의 | 서버 DB 기반 동의 관리 (버전 추적) |
| 감사 로그 | access_logs (3개월 보관, cron 자동 삭제) |
| RBAC | room_members.role (admin/member) 데코레이터 |
| 결제 | 토스페이먼츠 웹결제 (카드/자동결제/환불) |
| 결제 암호화 | AES-256-CBC (billingKey 암호화 저장) |
| 결제 크론 | APScheduler (자동결제/만료 처리/주문 정리) |

## 파일 구조

```
Proptalk/
├── server/                      # 백엔드 (원격 서버 배포)
│   ├── app.py                   # 메인 Flask 앱
│   ├── config.py                # 설정 (환경변수 기반)
│   ├── models.py                # DB 모델 (User, Room, Message, UserConsent, AccessLog)
│   ├── auth.py                  # OAuth + JWT + 동의 API + RBAC + 계정 삭제
│   ├── routes_rooms.py          # 채팅방 API + Drive 폴더 + 멤버 추방
│   ├── routes_messages.py       # 음성 업로드 + STT + Drive 저장 + 감사 로그
│   ├── whisper_service.py       # OpenAI Whisper API + 포맷 변환
│   ├── claude_service.py        # Claude 마크다운 요약
│   ├── drive_service.py         # Drive 업로드/다운로드 (토큰 자동 갱신)
│   ├── filename_parser.py       # 파일명 파싱
│   ├── cleanup_service.py       # 24시간 파일 삭제 + 감사 로그 삭제 + 구독 자동결제/만료 크론
│   ├── models_billing.py        # 결제 모델 (BillingPlan, UserBilling, PaymentTransaction, UsageLog)
│   ├── billing_service.py       # 과금 로직 (잔액확인/차감/충전/구독/AES-256 암호화)
│   ├── toss_service.py          # 토스페이먼츠 API (결제승인/빌링키/자동결제/환불/웹훅)
│   ├── routes_billing.py        # 결제 API 엔드포인트 9개
│   ├── billing_web.py           # 결제 웹페이지 라우트
│   ├── templates/billing/       # 결제 웹 UI (base/plans/checkout/success/fail/manage.html)
│   ├── init_billing.sql         # 결제 DB 스키마
│   ├── ecosystem.config.js      # PM2 환경변수
│   └── deploy/                  # 배포용 파일
│
├── flutter/                     # Flutter 앱
│   ├── lib/
│   │   ├── main.dart                     # 동의 화면 라우팅 로직
│   │   ├── constants/
│   │   │   └── terms.dart                # 법적 문서 텍스트 (약관/처리방침/동의문)
│   │   ├── screens/
│   │   │   ├── login_screen.dart         # 법적 문서 링크
│   │   │   ├── consent_screen.dart       # 서비스 동의 화면 (3항목)
│   │   │   ├── rooms_screen.dart         # 설정 메뉴 추가
│   │   │   ├── settings_screen.dart      # 법적 문서/동의 관리/계정 삭제
│   │   │   ├── chat_screen.dart          # 폴링 + 마크다운 + 음성 동의
│   │   │   └── audio_picker_screen.dart  # 파일 권한 처리
│   │   └── services/
│   │       ├── auth_service.dart          # drive.file + 동의 상태 관리
│   │       ├── api_service.dart           # API + Drive + 동의/탈퇴 + 결제
│   │       ├── billing_service.dart      # 결제 서비스 (ChangeNotifier)
│   │       └── socket_service.dart
│   └── pubspec.yaml                      # url_launcher, shared_preferences
│
├── docs/
│   ├── ARCHITECTURE.md          # 이 파일
│   ├── SETUP_GUIDE.md
│   ├── LAUNCH_PLAN.md
│   └── PROGRESS.md
│
└── images/                      # 로고/아이콘
```
