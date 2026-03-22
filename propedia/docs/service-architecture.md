# PropNet 서비스 아키텍처 정리

> 작성일: 2026-02-11
> 최종 업데이트: 2026-03-16

## 개요

PropNet은 부동산 정보 관리 및 조회를 위한 통합 플랫폼입니다.
단일 서버(`175.119.224.71`, 도메인 `goldenrabbit.biz`)에서 운영되며,
Nginx 리버스 프록시 뒤에 **5개 Systemd 서비스**가 동작합니다.

### 서비스 목록

| # | 서비스 | 포트 | 설명 |
|---|--------|------|------|
| 1 | **PropNet API + Property Manager** | 5000 | 공통 API(매물/VWorld/블로그) + 관리자 건축물 조회 |
| 2 | **Proppedia** | 5010 | 부동산백과 앱 API + 관리자 대시보드 |
| 3 | **PropSheet** | 5020 | 워크스페이스 기반 데이터베이스 관리 |
| 4 | **Proptalk** | 5030 | 음성 STT, 실시간 채팅, 결제 |
| 5 | **Shorts** | 5040 | 부동산 쇼츠 영상 자동 생성 |

> 포트 8000 `goldenrabbit-api.service`는 Threads 인증/웹훅만 처리하는 레거시 서비스로, 추후 제거 예정.

---

## 전체 요청 흐름도

```
[사용자/앱]
      │
      ▼
https://goldenrabbit.biz (port 443)
      │
      ▼
   [Nginx 리버스 프록시]
      │
      ├─ /api/*  ───────────→ [PropNet API :5000]  ───→ Airtable, VWorld API
      │   /property-manager/*                           PostgreSQL, 공공데이터 API
      │   /services
      │
      ├─ /app/api/*  ──────→ [Proppedia :5010]  ──────→ PostgreSQL (app_users)
      │   /app/dashboard/*                               공공데이터 API (apis.data.go.kr)
      │
      ├─ /propsheet/*  ────→ [PropSheet :5020]  ──────→ SQLite (workspace.db)
      │                                                  PostgreSQL (web_users)
      │
      ├─ /proptalk/*  ─────→ [Proptalk :5030]  ───────→ PostgreSQL (voiceroom)
      │   /voiceroom/*                                   OpenAI Whisper, Toss Payments
      │
      ├─ /shorts/*  ───────→ [Shorts :5040]
      │   /api/shorts
      │
      ├─ /app/*  ──────────→ [정적 파일] frontend/public/app/ (Flutter 웹 빌드)
      └─ /*  ──────────────→ [정적 파일] frontend/public/ (메인 웹페이지)
```

---

## 포트 및 서비스 매핑

| 포트 | 서비스 | Systemd Unit | WorkingDirectory | 역할 |
|------|--------|-------------|------------------|------|
| 80/443 | Nginx | `nginx.service` | - | 리버스 프록시 + 정적 파일 |
| **5000** | PropNet API | `property-manager.service` | `/backend/property-manager/` | 공통 API (매물/VWorld/블로그) |
| **5010** | Proppedia | `proppedia.service` | `/backend/proppedia/` | 앱 API + 관리자 대시보드 |
| **5020** | PropSheet | `propsheet.service` | `/backend/propsheet/` | 워크스페이스 데이터베이스 관리 |
| **5030** | Proptalk | `proptalk.service` | `/chat_stt/server/` | STT 음성인식 + 실시간 채팅 |
| **5040** | Shorts | `shorts-automation.service` | `/backend/shorts_automation/` | 쇼츠 영상 자동 생성 |
| 8000 | (레거시) Threads 인증 | `goldenrabbit-api.service` | `/backend/api/` | Threads 웹훅만 처리 |

---

## Nginx URL 라우팅 맵

설정 파일: `/etc/nginx/sites-enabled/goldenrabbit`
(원본: `/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf`)

```
요청 URL                        → 프록시 대상         → 서비스
──────────────────────────────────────────────────────────────────
/app/api/auth/*                 → port 5010          → Proppedia (앱 인증)
/app/api/admin/*                → port 5010          → Proppedia (관리자)
/app/api/*                      → port 5010          → Proppedia (앱 API)
/app/dashboard                  → port 5010          → Proppedia (관리자 대시보드)
/app/*                          → 정적 파일           → frontend/public/app/ (PWA)

/propsheet/*                    → port 5020          → PropSheet
# /property-manager/* → 제거됨 (2026-03-16)

/api/vworld                     → port 5000          → PropNet API (VWorld 프록시)
/api/vtile                      → port 5000          → PropNet API (타일 프록시)
/api/wms                        → port 5000          → PropNet API (WMS 프록시)
/api/shorts                     → port 5040          → Shorts
/api/*                          → port 5000          → PropNet API (매물/블로그/뉴스 등)
/property/{id}                  → port 5000          → PropNet API (SNS 공유 메타태그)
/services                       → port 5000          → PropNet API

/(auth|webhook|deauth)/threads  → port 8000          → 레거시 (Threads 인증)

/shorts/*                       → port 5040          → Shorts (Flask)

/proptalk/*                     → port 5030          → Proptalk (Flask)
/voiceroom/api/*                → port 5030          → Proptalk (REST API)
/voiceroom/socket.io/*          → port 5030          → Proptalk (WebSocket)

/                               → 정적 파일           → frontend/public/
/proppedia/                     → 정적 파일           → frontend/public/proppedia/
/airtable_backup/*              → 정적 파일           → backups/airtable/
/blog_thumbs/*                  → 정적 파일           → frontend/public/blog_thumbs/
/uploads/airtable/*             → 정적 파일           → backups/airtable/images/
/uploads/blog/*                 → 정적 파일           → backend/uploads/blog/
```

### 보안 규칙
- `location ~ /\.` → 모든 dot파일 차단 (`.env`, `.htaccess` 등)
- HTTP → HTTPS 강제 리다이렉트
- SSL: Let's Encrypt (`/etc/letsencrypt/live/goldenrabbit.biz/`)

### 캐싱 정책
- HTML: 캐시 없음 (항상 최신)
- CSS/JS: 7일
- 이미지: 30일
- PWA manifest/service worker: 캐시 없음

---

## Systemd 서비스 상세

### property-manager.service (포트 5000) — PropNet API + Property Manager

```ini
# /etc/systemd/system/property-manager.service
[Service]
WorkingDirectory=/home/webapp/goldenrabbit/backend/property-manager
Environment="PYTHONPATH=/home/webapp/goldenrabbit/backend"
ExecStart=/home/webapp/goldenrabbit/backend/venv/bin/python app.py
Restart=always
```

**MultiPrefixMiddleware**로 다중 URL 접두사 처리 + fallback:
- `/propsheet` → PropSheet (port 5020과 공유)
- `/app` → Proppedia 앱 API (port 5010과 공유)
- fallback → `/api/*`, `/property/*`, `/services` (PropNet API)
- `/property-manager` → 제거됨 (2026-03-16)

주요 블루프린트:
```
propnet_api.bp     → (no prefix)     PropNet API (매물/VWorld/블로그/뉴스/이미지)
airtable.bp        → /api            Airtable 저장
search_map.bp      → /api            지도 검색
blog.bp            → /api            블로그
# auth.bp, search.bp, property.bp → 제거됨 (Property Manager UI 제거)
```

### proppedia.service (포트 5010) — Proppedia 앱 API

```ini
# /etc/systemd/system/proppedia.service
[Service]
WorkingDirectory=/home/webapp/goldenrabbit/backend/proppedia
Environment="PYTHONPATH=/home/webapp/goldenrabbit/backend:/home/webapp/goldenrabbit/backend/property-manager"
ExecStart=/home/webapp/goldenrabbit/backend/venv/bin/python app.py
Restart=always
```

property-manager의 routes/services를 PYTHONPATH로 재사용:
```
app_api.bp         → /api            건축물 검색 API
app_auth.bp        → /api/auth       Google 인증 (JWT) + role_required 데코레이터
app_user_data.bp   → /api/user       즐겨찾기, 검색 기록
admin_dashboard.bp → (no prefix)     관리자 대시보드 (사용자 역할 관리 포함)
airtable (직접등록) → /api/airtable   Airtable 저장 (editor/admin 권한 보호)
```

**역할 기반 권한 시스템 (RBAC)**:
- `app_users.role` 컬럼: `user` (기본) / `editor` (Airtable 저장) / `admin` (전체 관리)
- `@token_required` + `@role_required('editor', 'admin')` 데코레이터로 API 보호
- 관리자 대시보드에서 사용자 역할 변경 가능 (`PUT /api/admin/users/<id>/role`)

### propsheet.service (포트 5020) — PropSheet

```ini
# /etc/systemd/system/propsheet.service
[Service]
WorkingDirectory=/home/webapp/goldenrabbit/backend/propsheet
Environment="PYTHONPATH=/home/webapp/goldenrabbit/backend:/home/webapp/goldenrabbit/backend/property-manager"
ExecStart=/home/webapp/goldenrabbit/backend/venv/bin/python app.py
Restart=always
```

property-manager의 routes/services를 PYTHONPATH로 재사용:
```
propsheet.bp          → (no prefix)       워크스페이스/데이터베이스 UI
oauth.bp              → (no prefix)       Google OAuth 로그인
share.bp              → (no prefix)       공유 링크
workspace_members.bp  → /api              멤버 관리
workspace.bp          → /api              워크스페이스 API
database.bp           → /api              데이터베이스 API
```

### proptalk.service (포트 5030) — Proptalk / VoiceRoom

```ini
# /etc/systemd/system/proptalk.service
[Service]
WorkingDirectory=/home/webapp/goldenrabbit/chat_stt/server
EnvironmentFile=/home/webapp/goldenrabbit/backend/.env
Environment="DB_NAME=voiceroom"
Environment="DB_USER=goldenrabbit_user"
ExecStart=/home/webapp/goldenrabbit/chat_stt/server/venv/bin/python app.py
Restart=always
```

독립 venv 사용 (`chat_stt/server/venv/`), 독립 DB (`voiceroom`).

### shorts-automation.service (포트 5040) — Shorts

```ini
# /etc/systemd/system/shorts-automation.service
[Service]
WorkingDirectory=/home/webapp/goldenrabbit/backend/shorts_automation
ExecStart=/home/webapp/goldenrabbit/backend/venv/bin/python app.py
Restart=always
```

---

## Propedia Flutter 앱의 API 연결

### Base URL
```dart
// lib/core/network/api_client.dart
static const String baseUrl = 'https://goldenrabbit.biz';
```

### 앱이 사용하는 엔드포인트

| 카테고리 | 메서드 | 경로 | 서버 |
|----------|--------|------|------|
| **인증** | POST | `/app/api/auth/google` | Proppedia :5010 |
| | GET | `/app/api/auth/me` | Proppedia :5010 |
| | POST | `/app/api/auth/refresh` | Proppedia :5010 |
| | POST | `/app/api/auth/logout` | Proppedia :5010 |
| **건축물 검색** | POST | `/app/api/search/road` | Proppedia :5010 |
| | POST | `/app/api/search/jibun` | Proppedia :5010 |
| | POST | `/app/api/search/bdmgtsn` | Proppedia :5010 |
| | GET | `/app/api/bjdong/search` | Proppedia :5010 |
| | POST | `/app/api/area` | Proppedia :5010 |
| **지도** | POST | `/app/api/map/click-jibun` | Proppedia :5010 |
| | GET | `/app/api/map/parcel-boundary` | Proppedia :5010 |
| | GET | `/app/api/map/geocode` | Proppedia :5010 |
| **사용자 데이터** | GET/POST/DELETE | `/app/api/user/favorites` | Proppedia :5010 |
| | GET/POST/DELETE | `/app/api/user/history` | Proppedia :5010 |
| | GET | `/app/api/user/usage-stats` | Proppedia :5010 |
| **공지사항** | GET | `/app/api/notices` | Proppedia :5010 |
| **매물 정보** | GET | `/api/property-list` | PropNet :5000 |
| | GET | `/api/category-properties` | PropNet :5000 |
| | GET | `/api/property-detail` | PropNet :5000 |
| | GET | `/api/check-image` | PropNet :5000 |
| | GET | `/api/coordinates` | PropNet :5000 |
| | POST | `/api/search-map` | PropNet :5000 |

### 인증 흐름
1. Google Sign-In SDK → `idToken` 획득
2. `POST /app/api/auth/google` → JWT `access_token` + `refresh_token` 발급
3. `AuthInterceptor`가 모든 요청에 `Authorization: Bearer {token}` 자동 추가
4. 401 응답 시 → `/app/api/auth/refresh`로 토큰 갱신 → 실패 시 로그아웃

### 토큰 저장
- **모바일**: FlutterSecureStorage (암호화)
- **웹**: SharedPreferences (localStorage)

### Google OAuth Client IDs
- **serverClientId (모바일)**: `846392940969-a7k37gkon1p451mlnhp0oj9qaok1d8o1.apps.googleusercontent.com`
- **Web Client ID**: `846392940969-sv2936v0tm85j8hvdn3srcmtei1kk25e.apps.googleusercontent.com`
- Android Debug: `846392940969-g2afoiuc6m7kp64vp4fdo48rp2iqkt30.apps.googleusercontent.com`
- Android Release: `846392940969-1sdp4mc01gbsq2dgne4h8mnuvobi5644.apps.googleusercontent.com`

---

## 공유 리소스

### 환경 변수
```
/home/webapp/goldenrabbit/backend/.env    # 대부분 서비스 공유
```

주요 변수: `AIRTABLE_API_KEY`, `PUBLIC_API_KEY`, `VWORLD_APIKEY`, `GOOGLE_SCRIPT_URL`, `FLASK_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, `ANTHROPIC_API_KEY`, `KAKAO_REST_API_KEY`, `JWT_SECRET_KEY`, `DB_*` (PostgreSQL)

### 가상환경
```
/home/webapp/goldenrabbit/backend/venv/         # PropNet, Proppedia, PropSheet, Shorts 공유
/home/webapp/goldenrabbit/chat_stt/server/venv/ # Proptalk 전용
```

### 로그 디렉토리
```
logs/
├── api/                 # 레거시 API Server (port 8000)
├── property-manager/    # PropNet API + Property Manager (port 5000)
│   └── app.log          # RotatingFileHandler (10MB x 5)
├── proppedia/           # Proppedia (port 5010)
│   └── app.log
├── propsheet/           # PropSheet (port 5020)
│   └── app.log
└── nginx/
    ├── access.log
    └── error.log
```

### 데이터베이스
- **PostgreSQL `goldenrabbit_db`** (user: `goldenrabbit_user`) — app_users, app_notices, web_users, workspaces 등
- **PostgreSQL `voiceroom`** (user: `goldenrabbit_user`) — Proptalk 채팅/결제 데이터
- **SQLite** `/backend/property-manager/workspace.db` — PropSheet 워크스페이스/데이터베이스

---

## Cron Jobs

```bash
# Airtable 백업 (매일 오전 2시)
0 2 * * * /usr/bin/python3 /home/webapp/goldenrabbit/backend/scripts/airtable_backup.py
# → 출력: backups/airtable/all_properties.json, coordinates.json

# 지도 생성 (매일 오전 3시)
0 3 * * * /usr/bin/python3 /home/webapp/goldenrabbit/backend/scripts/generate_map.py
# → 출력: frontend/public/airtable_map.html
```

---

## 서비스 관리 명령어

```bash
# PropNet API + Property Manager (포트 5000)
sudo systemctl start|stop|restart|status property-manager
journalctl -u property-manager -f

# Proppedia 앱 API (포트 5010)
sudo systemctl start|stop|restart|status proppedia
journalctl -u proppedia -f

# PropSheet (포트 5020)
sudo systemctl start|stop|restart|status propsheet
journalctl -u propsheet -f

# Proptalk (포트 5030)
sudo systemctl start|stop|restart|status proptalk
journalctl -u proptalk -f

# Shorts (포트 5040)
sudo systemctl start|stop|restart|status shorts-automation
journalctl -u shorts-automation -f

# 레거시 - Threads 인증 (포트 8000)
sudo systemctl start|stop|restart|status goldenrabbit-api

# Nginx
sudo nginx -t          # 설정 테스트
sudo systemctl reload nginx

# 포트 확인
ss -tlnp | grep -E '5000|5010|5020|5030|5040|8000|80|443'
```

---

## 주요 파일 경로

```
/home/webapp/goldenrabbit/
├── backend/
│   ├── .env                              # 공유 환경 변수
│   ├── venv/                             # 공유 가상환경
│   ├── property-manager/
│   │   ├── app.py                        # PropNet API + Property Manager (port 5000)
│   │   ├── routes/
│   │   │   ├── propnet_api.py            # PropNet API Blueprint (기존 port 8000 흡수)
│   │   │   ├── app_api.py                # 앱 건축물 검색 API
│   │   │   ├── app_auth.py               # 앱 Google 인증 (JWT)
│   │   │   ├── app_user_data.py          # 앱 사용자 데이터
│   │   │   ├── admin_dashboard.py        # 관리자 대시보드
│   │   │   ├── search.py                 # Property Manager 검색
│   │   │   ├── property.py               # 건축물 정보
│   │   │   ├── propsheet.py              # PropSheet 라우트
│   │   │   ├── oauth.py                  # Google OAuth
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── app_user_service.py       # 앱 사용자/JWT 서비스
│   │   │   ├── building_unified_service.py # 통합 건축물 조회
│   │   │   ├── google_auth_service.py    # Google OAuth 서비스
│   │   │   ├── pdf_service_v2.py         # PDF 생성
│   │   │   └── ...
│   │   └── workspace.db                  # PropSheet SQLite DB
│   ├── proppedia/app.py                  # Proppedia (port 5010)
│   ├── propsheet/app.py                  # PropSheet (port 5020)
│   ├── api/app.py                        # 레거시 API Server (port 8000, Threads만)
│   ├── shorts_automation/app.py          # Shorts (port 5040)
│   ├── real-estate-newsletter/           # Threads 뉴스레터
│   └── scripts/                          # 유틸리티 스크립트
├── chat_stt/server/
│   ├── app.py                            # Proptalk (port 5030)
│   ├── config.py                         # Proptalk 설정
│   └── venv/                             # Proptalk 전용 가상환경
├── config/
│   ├── nginx/goldenrabbit.conf           # Nginx 설정 원본
│   └── systemd/                          # Systemd 서비스 파일
├── frontend/public/
│   ├── index.html                        # 메인 웹페이지
│   ├── app/                              # Flutter 웹 빌드 (PWA)
│   └── proppedia/                        # Proppedia 랜딩 페이지
├── backups/airtable/                     # Airtable 백업 데이터/이미지
└── logs/                                 # 로그 디렉토리
```

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-03-16 | **포트 재구성 마이그레이션 완료**: Proppedia 앱 API를 5010으로 분리, API Server(8000)를 PropNet API로 5000에 흡수, PropSheet를 5020으로 분리, Proptalk를 5060→5030으로 이전(systemd 서비스 신규 생성), Shorts를 5002→5040으로 이전. 포트 8000 중복 auth 제거. |
| 2026-03-11 | PM2 좀비 프로세스 정리, goldenrabbit-property.service 삭제, Shorts/VoiceRoom/PropTalk 서비스 추가, Flutter 앱 API 엔드포인트 추가, Google OAuth 설정 추가 |
| 2026-02-23 | 초기 작성 |
