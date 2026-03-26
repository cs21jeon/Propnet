# Proptalk Project Rules

## Architecture
- Flutter 3.x Android app + Flask backend (Cafe24 server 175.119.224.71)
- PostgreSQL `voiceroom` DB with psycopg2 connection pooling
- **systemd** 서비스 관리 (`proptalk.service`)
- SSH: `ssh root@175.119.224.71`

## CRITICAL: Git 보안
- **절대 커밋 금지**: `.env`, `ecosystem.config.js`(API 키 포함), OAuth 토큰/시크릿 파일, `google-services.json`, `*firebase-adminsdk*.json`
- 커밋 전 `git diff --cached`로 API 키, 비밀번호, 토큰 노출 여부 반드시 확인
- 서버 `.env` 값을 코드/문서에 하드코딩 금지

## CRITICAL: Whisper STT - OpenAI API ONLY
- **MUST use OpenAI Whisper API (`whisper-1` model) via `whisper_service.py`**
- **NEVER use local whisper model (import whisper / whisper.load_model)**
- The server has only 956MB RAM - local Whisper crashes with oneDNN errors
- `whisper_service.py` on server handles: format conversion, file splitting, API calls
- Usage: `from whisper_service import transcribe_audio`
- Returns: `{'text': '...', 'segments': [...]}`
- OPENAI_API_KEY is configured in .env

## Deploy
- Server files: `/home/webapp/goldenrabbit/chat_stt/server/`
- SCP 후 `sudo systemctl restart proptalk`
- 환경변수: `/home/webapp/goldenrabbit/chat_stt/server/.env` (systemd EnvironmentFile)
- venv: `/home/webapp/goldenrabbit/chat_stt/server/venv/`
- 로그: `journalctl -u proptalk -f`

## Version Management
- 버전 정보 단일 소스: `CHANGELOG.json` (로컬 + 서버)
- "버전 업해줘" 요청 시 작업 순서:
  1. CHANGELOG.json에 새 릴리즈 추가 (current 업데이트 + releases 배열 앞에 추가)
  2. flutter/pubspec.yaml의 version 갱신
  3. 서버에 changelog.json 배포 (MCP write_file)
  4. 필요 시 앱 빌드 및 서버 재시작
- 서버 파일 위치: /home/webapp/goldenrabbit/chat_stt/server/changelog.json
- 대시보드 자동 반영: routes_admin.py가 changelog.json을 읽어서 동적 렌더링

## Web Pages (Flask 서빙, Nginx → 포트 5030 프록시)

### 랜딩페이지
- **URL**: `https://goldenrabbit.biz/proptalk/`
- **서버 파일**: `/home/webapp/goldenrabbit/chat_stt/marketing/proptalk/index.html`
- **라우트**: `billing_web.py` → `send_from_directory('marketing/proptalk', 'index.html')`
- **이미지**: `/home/webapp/goldenrabbit/chat_stt/images/Capture/` (Flask `/proptalk/images/` 라우트)
- **로컬**: `marketing/proptalk/index.html`

### 결제 페이지
- **URL**: `https://goldenrabbit.biz/proptalk/billing/`
- **라우트**: `billing_web.py` → `render_template('billing/plans.html')`
- **요금제 API**: `/api/billing/plans?user_type=general|agent` (DB에서 동적 로드)
- **요금제 구분**: 일반(General) / 중개사(Agent) - Flutter 앱에서는 plan code prefix(`agent_`)로 필터링

### 법적 문서
- 이용약관: `/proptalk/terms-of-service.html`
- 개인정보처리방침: `/proptalk/privacy-policy.html`
- 결제약관: `/proptalk/payment-terms` → `billing-terms.html`
- 계정 삭제: `/proptalk/delete-account`

## Key Server Files
- `routes_messages.py` - message/audio upload/download endpoints
- `whisper_service.py` - OpenAI Whisper API wrapper (DO NOT replace with local whisper)
- `claude_service.py` - Claude API for transcript summarization
- `models.py` - DB models (User, Room, Message, AudioFile, DeviceToken)
- `notification_service.py` - FCM push notification (firebase-admin)
- `billing_service.py` - usage billing/deduction
- `billing_web.py` - 랜딩페이지/결제페이지/법적문서 라우트
- `routes_billing.py` - 결제 API 라우트
- `models_billing.py` - 요금제/결제 DB 모델

## 향후 계획: propnet.kr 마이그레이션 (Phase 4)

### URL 변경
| 현재 (goldenrabbit.biz) | 신규 (propnet.kr) |
|---|---|
| `/proptalk/` (랜딩) | `/proptalk/home` |
| `/proptalk/admin/*` | `/proptalk/dashboard/*` |
| `/proptalk/billing/*` | `/proptalk/billing/*` (변경 없음) |
| `/voiceroom/*` | `/voiceroom/*` (변경 없음, 앱 의존) |

### 수정 대상 파일
1. **Flask 라우트**: 랜딩 `/proptalk/` → `/proptalk/home`, admin → dashboard
2. **Flutter App**: 5개 파일 URL 변경
   - `flutter/lib/services/api_service.dart` → baseUrl
   - `flutter/lib/services/socket_service.dart` → 소켓 URL
   - `flutter/lib/services/billing_service.dart` → 결제 URL
   - `flutter/lib/constants/terms.dart` → 약관 URL
   - `flutter/lib/screens/settings_screen.dart` → 관리자 URL
3. `/voiceroom/*` 경로는 양쪽 도메인 모두 유지 (변경 없음)
