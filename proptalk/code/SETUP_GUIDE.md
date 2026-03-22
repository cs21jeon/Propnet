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
```

## 2단계: Google Cloud 설정

### 2-1. Google Cloud Console (https://console.cloud.google.com)

1. **프로젝트 생성** (또는 기존 프로젝트 사용)

2. **OAuth 2.0 클라이언트 ID 생성**
   - API 및 서비스 → 사용자 인증 정보
   - OAuth 클라이언트 ID 만들기
   - 유형: **웹 애플리케이션** (서버 검증용)
   - 유형: **Android** (Flutter 앱용, SHA-1 필요)
   - 유형: **iOS** (Flutter 앱용)
   - `GOOGLE_CLIENT_ID` 메모

3. **Service Account 생성** (Google Drive 업로드용)
   - IAM 및 관리자 → 서비스 계정
   - 서비스 계정 만들기
   - JSON 키 다운로드 → 서버에 업로드
   - 경로: `/home/hosting_users/goldenrabbit/chat_stt/credentials/service-account.json`

4. **Google Drive API 활성화**
   - API 및 서비스 → 라이브러리 → "Google Drive API" 검색 → 사용

5. **Drive 폴더 공유**
   - Google Drive에서 "VoiceRoom" 폴더 생성
   - 폴더를 Service Account 이메일과 공유 (편집자 권한)
   - 폴더 ID 메모 (URL에서 추출: drive.google.com/drive/folders/FOLDER_ID)

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
# - GOOGLE_CLIENT_ID
# - GOOGLE_DRIVE_FOLDER_ID
```

## 5단계: PM2 실행

```bash
cd /home/hosting_users/goldenrabbit/chat_stt/server
pm2 start ecosystem.config.js
pm2 save
pm2 logs voiceroom  # 로그 확인
```

## 6단계: Nginx 설정

```bash
sudo nano /etc/nginx/sites-available/goldenrabbit.biz
```

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

- **메모리**: Whisper small 모델 약 2GB 필요. Cafe24 서버 메모리 확인 필수
- **CPU 변환 시간**: 1분 음성 ≈ 60초 소요 (small 모델 기준)
- **동시 처리**: workers=1이므로 동시에 여러 파일 변환 시 큐잉됨
- **보안**: JWT_SECRET, SECRET_KEY는 반드시 랜덤 문자열로 변경
- **Service Account JSON**: 절대 git에 커밋하지 말 것
