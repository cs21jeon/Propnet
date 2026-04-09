# PropNet 시스템 현황 문서

> 최종 업데이트: 2026-04-09

---

## 1. 프로젝트 개요

**PropNet**은 부동산 정보 관리 및 조회를 위한 통합 플랫폼입니다.
단일 서버(`175.119.224.71`, 도메인 `propnet.kr` / `goldenrabbit.biz`)에서 4개 서비스를 운영합니다.

- **프로덕션 URL**: https://propnet.kr (메인), https://goldenrabbit.biz (레거시, 리다이렉트)
- **서버**: 175.119.224.71 (Cafe24 호스팅)
- **Airtable 완전 제거 완료** (2026-03-26): 모든 데이터가 PropSheet DB + 로컬 파일 시스템으로 전환됨

---

## 2. 시스템 아키텍처

### 2.1 서비스 구조

```
[클라이언트]
    │
    ▼
[Nginx] ── SSL (Let's Encrypt)
    │
    ├── /propsheet/*      → PropSheet (Port 5020)
    ├── /app/*            → Propedia (Port 5010)
    ├── /proptalk/*       → Proptalk (Port 5030)
    ├── /propmap/*        → 정적 HTML (Nginx 직접 서빙)
    ├── /property-manager/* → Property Manager (Port 5000)
    └── /                 → 정적 파일 (frontend/public/)
```

| 서비스 | 포트 | systemd 서비스명 | 역할 | 서버 경로 |
|--------|------|------------------|------|-----------|
| Property Manager | 5000 | `property-manager` | 홈페이지 매물 API, SNS 공유, PropSheet CRUD API | `/backend/property-manager/` |
| Propedia | 5010 | `proppedia` | Propedia 앱 API, 관리자 대시보드 | `/backend/proppedia/` |
| PropSheet | 5020 | `propsheet` | PropSheet 웹 UI (사용자 접속) | `/backend/propsheet/` |
| Proptalk | 5030 | `proptalk` | 음성 채팅 서비스 | `/chat_stt/server/` |
| PropMap | - | - | 매물지도 (정적 HTML) | `frontend/public/propmap/` |

> **코드 공유 구조**: 5000, 5010, 5020 모두 `/backend/property-manager/`의 routes/services/templates를 `sys.path`로 임포트하여 재사용.

### 2.2 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3 + Flask (gunicorn) |
| Frontend (PropSheet) | HTMX + Alpine.js |
| Frontend (PropMap) | Vanilla HTML/JS + 카카오맵 SDK |
| Mobile (Propedia/Proptalk) | Flutter 3.x |
| Database | PostgreSQL (`goldenrabbit_db` 공유 + `voiceroom` Proptalk 전용) |
| 인증 | PropNet 통합 인증 (propnet_users SSoT + SSO 쿠키) |
| 프로세스 관리 | systemd |
| 웹 서버 | Nginx (리버스 프록시 + SSL) |
| SSL | Let's Encrypt |

---

## 3. 서버 설정

### 3.1 디렉토리 구조

```
/home/webapp/goldenrabbit/
├── backend/
│   ├── property-manager/         # 공유 코드 (routes, services, templates, static)
│   │   ├── routes/               # propsheet.py, database.py, oauth.py, register.py 등
│   │   ├── services/             # database_service.py, proptalk_service.py 등
│   │   ├── templates/            # propsheet/, admin/, register/ 등
│   │   └── static/               # js/propsheet/, css/propsheet/
│   ├── proppedia/                # Propedia app.py (5010)
│   ├── propsheet/                # PropSheet app.py (5020)
│   ├── shared/                   # 공유 모듈 (propnet_auth 라이브러리)
│   ├── .env                      # 환경변수 (공유)
│   └── venv/                     # Python 가상환경 (5000/5010/5020 공유)
├── chat_stt/
│   └── server/                   # Proptalk 서버 (5030)
│       ├── app.py, auth.py, websocket.py, models.py
│       ├── routes_messages.py, routes_rooms.py
│       ├── whisper_service.py, claude_service.py
│       ├── billing_service.py, notification_service.py
│       ├── .env                  # Proptalk 전용 환경변수
│       └── venv/                 # Proptalk 전용 가상환경
├── frontend/
│   └── public/                   # Nginx 정적 파일
│       ├── propmap/              # PropMap (index.html, map.html)
│       │   ├── goldenrabbit/     # 금토끼 매물지도
│       │   └── silverrabbit/     # 은토끼 매물지도
│       ├── propnet/              # PropNet 랜딩
│       └── index.html, map.html  # 홈페이지 (레거시)
├── config/
│   └── nginx/
│       ├── goldenrabbit.conf     # goldenrabbit.biz Nginx 설정
│       └── propnet.conf          # propnet.kr Nginx 설정
└── uploads/
    └── propsheet/{db_id}/{record_id}/  # 파일 업로드
```

### 3.2 Systemd 서비스

```bash
# 서비스 관리
sudo systemctl restart property-manager   # Port 5000
sudo systemctl restart proppedia          # Port 5010
sudo systemctl restart propsheet          # Port 5020
sudo systemctl restart proptalk           # Port 5030

# 로그 확인
journalctl -u property-manager -f
journalctl -u proppedia -f
journalctl -u propsheet -f
journalctl -u proptalk -f
```

> **중요**: `/backend/property-manager/`의 routes/services 수정 시 **3개 서비스 모두 재시작** 필수: `sudo systemctl restart property-manager proppedia propsheet`

### 3.3 Nginx 설정

- 설정 파일: `/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf`, `propnet.conf`
- **주의**: `/etc/nginx/sites-enabled/`에 복사 후 적용:
  ```bash
  sudo nginx -t && sudo systemctl reload nginx
  ```
- SSL: Let's Encrypt (`propnet.kr` + `goldenrabbit.biz`)
- 이미지 서빙: `/uploads/propsheet/` → 물리 경로 정적 서빙

---

## 4. 인증 체계

### 4.1 PropNet 통합 인증 (2026-04-07 완료)

- **SSoT**: `propnet_users` 테이블 (role, agent_id는 여기서만 읽기)
- **서비스 연결**: `service_user_links` (propnet_user_id ↔ 서비스별 local_user_id)
- **SSO 쿠키**: `propnet_token`(HttpOnly) + `propnet_uid`(JS용) — propnet.kr 도메인
- **JWT**: propnet_auth 공유 라이브러리 (다중 secret 지원)
- **Gmail 점 정규화**: `cs21.jeon@gmail.com` == `cs21jeon@gmail.com`

### 4.2 권한 체계

| 역할 | 설명 |
|------|------|
| `admin` | 시스템 관리자 (goldenrabbit owner) |
| `agent` | 공인중개사 (PropSheet/PropMap 사용) |
| `subagent` | 소속 직원 (agent 초대 전용) |
| `user` | 일반 사용자 |

- PropSheet: `owner > editor > viewer` 3단계 권한
- Agent 데이터 격리: agent 간 데이터 완전 격리, admin도 타 agent 접근 불가

---

## 5. 데이터베이스 스키마 (PostgreSQL)

### 5.1 goldenrabbit_db (공유)

#### 핵심 인프라 테이블

| 테이블 | 설명 |
|--------|------|
| `propnet_users` | 통합 사용자 (SSoT: role, agent_id) |
| `service_user_links` | propnet_user_id ↔ 서비스별 local_user_id 매핑 |
| `propnet_consents` | 통합 동의 기록 |
| `agents` | 중개사무소 정보 (slug, agency_name, lat/lon) |
| `web_users` | PropSheet 웹 사용자 (레거시, propnet_users 참조 필수) |
| `app_users` | Propedia 앱 사용자 (레거시) |
| `app_notices` | 앱 공지사항 (target_app: all/propedia/proptalk) |

#### PropSheet 구조 테이블

| 테이블 | 설명 |
|--------|------|
| `workspaces` | 워크스페이스 (name, slug, icon) |
| `workspace_members` | 멤버 (user_id, role: owner/editor/viewer) |
| `databases` | 데이터베이스 (workspace_id, table_name, external_source) |
| `field_definitions` | 필드 정의 (12종 타입, system_value_key) |
| `views` | 뷰 (grid/calendar, filter/sort/column config) |
| `database_shares` | DB 공유 토큰 |
| `file_attachments` | 파일 업로드 메타데이터 |
| `sync_events` | 감사 로그 |

#### 매물 데이터 테이블 (agent별 동적)

| 테이블 | agent | 유형 |
|--------|-------|------|
| `goldenrabbit01_sales_building` | 금토끼 | 단일부동산 (db_id=39) |
| `goldenrabbit01_sales_multi_unit` | 금토끼 | 집합부동산 (db_id=38) |
| `sales_building_copy` | 금토끼 | 부분부동산 (db_id=43) |
| `goldenrabbit_talk` | 금토끼 | 채팅방 (db_id=65) |
| `silverrabbit_*` | 은토끼 | 단일/집합/부분/채팅 |
| `template_*` | 템플릿 | 신규 agent 복제 원본 |

#### DB 트리거 (자동 계산)

- `format_ad_text()` — 단일부동산 광고(자동완성) 자동 생성
- `format_ad_text_partial()` — 부분부동산 광고(자동완성)
- `format_ad_text_multi()` — 집합부동산 광고(자동완성)
- `update_map_link()` — 지도 링크 자동 생성 (지번 주소 → 카카오맵 URL)
- `calculate_property_values()` — 수식 필드 자동 계산 (수익률, 실투자금 등)

### 5.2 voiceroom (Proptalk 전용)

| 테이블 | 설명 |
|--------|------|
| `users` | Proptalk 사용자 (Google OAuth) |
| `rooms` | 채팅방 |
| `room_members` | 멤버 (role, last_read_message_id) |
| `messages` | 메시지 (text/audio/file/transcript/system) |
| `audio_files` | 음성 파일 메타데이터 (STT 결과, Drive URL) |
| `file_attachments` | 파일 첨부 |
| `device_tokens` | FCM 푸시 토큰 |
| `user_consents` | 동의 기록 |
| `usage_logs` | 사용량 로그 (과금용) |
| `billing_*` | 요금제/결제 테이블 |

---

## 6. 외부 서비스 연동

| 서비스 | 용도 | 환경변수 |
|--------|------|----------|
| OpenAI Whisper API | Proptalk STT (음성→텍스트) | `OPENAI_API_KEY` |
| Claude API | Proptalk 음성 요약 | `ANTHROPIC_API_KEY` |
| Google OAuth 2.0 | 로그인 (Propedia/Proptalk/PropSheet) | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |
| Google Drive API | Proptalk 음성 파일 백업 | 사용자별 OAuth 토큰 |
| Firebase (FCM) | Proptalk 푸시 알림 | `firebase-adminsdk` 서비스 계정 |
| VWorld API | 주소→좌표 변환 (건축물대장) | `VWORLD_API_KEY` |
| 카카오맵 SDK | PropMap/PropSheet 지도 | `KAKAO_APP_KEY` |
| Toss Payments | 결제 (요금제 구독) | `TOSS_CLIENT_KEY`, `TOSS_SECRET_KEY` |

---

## 7. 도메인 구조

| 도메인 | 용도 | 상태 |
|--------|------|------|
| `propnet.kr` | 메인 도메인 (SSO 쿠키 기준) | 운영 중 |
| `goldenrabbit.biz` | 레거시 (propnet.kr로 리다이렉트) | 리다이렉트 |

### URL 매핑

| URL | 서비스 |
|-----|--------|
| `propnet.kr/propsheet/` | PropSheet 웹 UI |
| `propnet.kr/propmap/` | PropMap 통합 매물지도 |
| `propnet.kr/propmap/{agent_slug}/` | Agent별 매물지도 |
| `propnet.kr/proptalk/` | Proptalk 랜딩/웹앱 |
| `propnet.kr/app/` | Propedia 웹(PWA) |
| `propnet.kr/proppedia/` | Propedia 가이드/랜딩 |
