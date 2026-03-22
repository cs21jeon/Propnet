# VoiceRoom 설치 가이드 (Cafe24 서버)

## 1단계: DB 생성

```bash
# PostgreSQL 접속
sudo -u postgres psql

# DB 생성
CREATE DATABASE voiceroom;
GRANT ALL PRIVILEGES ON DATABASE voiceroom TO goldenrabbit;
\q

# 테이블 생성
psql -U goldenrabbit -d voiceroom -f init_db.sql

# 법적 컴플라이언스 마이그레이션 (user_consents, access_logs)
psql -U goldenrabbit -d voiceroom -f server/deploy/migrate_consents.sql

# 결제 시스템 마이그레이션 (billing_plans, user_billing, payment_transactions, usage_logs)
sudo -u postgres psql -d voiceroom -f server/init_billing.sql

# 결제 테이블 권한 부여
sudo -u postgres psql -d voiceroom -c "
GRANT ALL PRIVILEGES ON TABLE billing_plans, user_billing, payment_transactions, usage_logs TO goldenrabbit_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO goldenrabbit_user;
"
```

## 2단계: Google Cloud 설정

### 2-1. Google Cloud Console (https://console.cloud.google.com)

> 프로젝트: `speech-to-text-goldenrabbit` (846392940969)

1. **OAuth 2.0 클라이언트 ID** (Google Auth Platform → Clients)
   - **웹 애플리케이션**: `846392940969-a7k37gkon1p451mlnhp0oj9qaok1d8o1` (서버 토큰 교환용)
   - **Android**: `846392940969-ro1j6gm1r9mdsmfjkfv40311l0053s5a`
     - 패키지: `biz.goldenrabbit.proptalk`
     - SHA-1: `FA:53:98:5C:4B:D3:69:C1:A2:36:87:19:A8:79:BC:E3:68:F6:D0:98`

2. **Google Drive API 활성화**
   - APIs & Services → Library → "Google Drive API" → Enable

3. **OAuth 동의화면 스코프** (Google Auth Platform → Data Access)
   - `drive.file` 스코프 추가 (비민감, 별도 심사 불필요)

4. **OAuth 동의화면 사용자** (Google Auth Platform → Audience)
   - 테스트 모드: 테스트 사용자 수동 추가 (최대 100명)
   - 프로덕션: 모든 Google 계정 허용 (출시 시 전환)

### 2-2. Flutter 앱 설정

**Android** (`android/app/build.gradle`):
```gradle
android {
    defaultConfig {
        minSdkVersion 21
    }
}
```

**Android** (`android/app/src/main/res/values/strings.xml`):
```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="default_web_client_id">YOUR_WEB_CLIENT_ID.apps.googleusercontent.com</string>
</resources>
```

**iOS** (`ios/Runner/Info.plist`):
```xml
<!-- Google Sign-In URL Scheme 추가 -->
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>com.googleusercontent.apps.YOUR_IOS_CLIENT_ID</string>
        </array>
    </dict>
</array>
```

## 3단계: 서버 설치

```bash
# 디렉토리 구조
mkdir -p /home/hosting_users/goldenrabbit/chat_stt/{server,credentials,uploads,logs}
cd /home/hosting_users/goldenrabbit/chat_stt/server

# 파일 업로드 (모든 .py 파일 + requirements.txt + ecosystem.config.js + init_db.sql)

# Python 가상환경
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# FFmpeg 확인
ffmpeg -version  # 없으면: sudo apt install -y ffmpeg

# Whisper 모델 미리 다운로드
python3 -c "import whisper; whisper.load_model('small')"
```

## 4단계: ecosystem.config.js 수정

```bash
# 실제 값으로 수정
nano ecosystem.config.js

# 수정할 항목:
# - DB_PASS
# - SECRET_KEY (랜덤 문자열)
# - JWT_SECRET (랜덤 문자열)
# - GOOGLE_CLIENT_ID (Web 클라이언트 ID)
# - GOOGLE_CLIENT_SECRET (Web 클라이언트 Secret)
# - OPENAI_API_KEY
# - CLAUDE_API_KEY
# - ENABLE_DRIVE_BACKUP ('true' / 'false')
#
# 결제 시스템 (토스페이먼츠):
# - TOSS_CLIENT_KEY (토스 클라이언트 키)
# - TOSS_SECRET_KEY (토스 시크릿 키)
# - TOSS_WEBHOOK_SECRET (토스 웹훅 시크릿)
# - BILLING_ENCRYPTION_KEY (AES-256 billingKey 암호화 키, 32바이트)
#   생성: python3 -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"
```

## 5단계: PM2 실행

```bash
cd /home/hosting_users/goldenrabbit/chat_stt/server
pm2 start ecosystem.config.js
pm2 save
pm2 logs voiceroom  # 로그 확인
```

## 6단계: Nginx 설정

> **중요**: 실제 Nginx 설정 파일은 `/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf`
> (`/etc/nginx/sites-enabled/goldenrabbit`에서 symlink됨)

아래 내용 추가:

```nginx
# VoiceRoom API + WebSocket
location /api/ {
    proxy_pass http://127.0.0.1:5060;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # 파일 업로드
    client_max_body_size 50M;
    
    # 타임아웃 (STT 변환 대기)
    proxy_read_timeout 300s;
    proxy_connect_timeout 10s;
    proxy_send_timeout 300s;
}

# WebSocket
location /socket.io/ {
    proxy_pass http://127.0.0.1:5060;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
}
```

```nginx
# Proptalk 결제 웹페이지
location /proptalk/billing/ {
    proxy_pass http://127.0.0.1:5060/proptalk/billing/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 7단계: 테스트

```bash
# 서버 상태
curl https://goldenrabbit.biz/api/health

# 예상 응답:
# {"status":"ok","service":"VoiceRoom STT"}
```

## 8단계: Flutter 앱 설정

```bash
# flutter/lib/services/api_service.dart 에서 baseUrl 확인
static const String baseUrl = 'https://goldenrabbit.biz';

# 빌드 & 실행
cd flutter
flutter pub get
flutter run
```

---

## 전체 플로우 요약

```
1. 사용자가 Google 계정으로 로그인
2. 채팅방 생성 또는 초대코드로 참여
3. 채팅방에서 음성파일 업로드 (파일 선택 또는 직접 녹음)
4. 서버에서 자동으로:
   a. 파일명에서 전화번호/날짜/이름 AI 파싱
   b. Whisper로 음성→텍스트 변환
   c. 변환 결과를 자동 댓글로 달기
   d. Google Drive에 음성파일 백업 저장
5. 모든 메타데이터(전화번호, 날짜) DB에 저장
6. 검색 기능으로 전화번호/날짜별 음성파일 조회 가능
```

## 주의사항

- **STT**: OpenAI Whisper API 사용 ($0.006/분), 로컬 모델 아님
- **포맷**: Android 통화 녹음(3GP)은 서버에서 자동 MP3 변환 (ffmpeg 필수)
- **Drive**: 방장의 OAuth 토큰으로 Drive 저장, Service Account 아님
- **토큰 갱신**: access_token 1시간 만료, refresh_token으로 자동 갱신
- **보안**: JWT_SECRET, SECRET_KEY, GOOGLE_CLIENT_SECRET 절대 git에 커밋하지 말 것
- **PM2**: 환경변수 변경 시 `pm2 delete` → `pm2 start` 방식 사용 (restart --update-env 캐시 문제)
- **법적 동의**: 로그인 후 서버에서 consent_required 반환 → 미동의 시 동의 화면 표시
- **감사 로그**: access_logs 테이블에 자동 기록, cleanup_service.py에서 3개월 초과 삭제
- **RBAC**: admin 전용 API에 `room_role_required('admin')` 데코레이터 적용
- **결제**: 토스페이먼츠 웹결제 사용, billingKey는 AES-256-CBC 암호화 저장
- **결제 크론**: 구독 자동결제(03:00), 만료 처리(04:00), 주문 정리(매시간) - cleanup_service.py
- **결제 로그**: payment_transactions 테이블에 5년 보관 (전자상거래법)
- **Nginx**: /proptalk/billing/ 경로 → Flask 5060 포트 프록시 필수
