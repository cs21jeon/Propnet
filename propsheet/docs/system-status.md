# Propsheet 시스템 현황 문서

> 작성일: 2026-03-03 | 마지막 업데이트: 2026-03-25 (홈페이지 매물지도/검색/상세 PropSheet DB 전환)

---

## 1. 프로젝트 개요

**GoldenRabbit**은 한국 부동산 데이터 관리 시스템으로, 공공 API(공공데이터포털, VWorld)와 Airtable을 연동하여 매물 정보를 관리합니다. **Propsheet**는 에어테이블을 자체 스프레드시트 솔루션으로 대체하기 위한 프로젝트입니다.

- **프로덕션 URL**: https://goldenrabbit.biz
- **서버**: 175.119.224.71 (Cafe24 호스팅)
- **MCP 연결**: SSH를 통해 `@modelcontextprotocol/server-filesystem` 사용

---

## 2. 시스템 아키텍처

### 2.1 Two-Server Architecture

```
[클라이언트]
    │
    ▼
[Nginx] ── SSL (Let's Encrypt)
    │
    ├── /api/*           → API Server (Port 8000)
    ├── /property-manager/* → Property Manager (Port 5000)
    ├── /propsheet/*     → Propsheet (Property Manager 내 Blueprint)
    └── /                → Static Files (frontend/public/)
```

| 서비스 | 포트 | 역할 | 진입점 |
|--------|------|------|--------|
| API Server | 8000 | 공개 API (VWorld, Airtable 매물, 블로그, SNS) | `backend/api/app.py` |
| Property Manager | 5000 | 관리자 인터페이스 (건물조회, PDF, Propsheet) | `backend/property-manager/app.py` |
| Frontend | Nginx | 정적 HTML/CSS/JS | `frontend/public/` |

### 2.2 서비스 레이어 패턴

```
routes/ → services/ → External APIs (공공데이터포털, VWorld, Airtable)
                     → PostgreSQL Database
```

### 2.3 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3 + Flask |
| Database | PostgreSQL (goldenrabbit_db) |
| Frontend | HTML/CSS/JS + Alpine.js + HTMX |
| 외부 서비스 | Airtable, VWorld, 공공데이터포털, Claude API |
| 프로세스 관리 | systemd |
| 웹 서버 | Nginx (리버스 프록시) |
| SSL | Let's Encrypt |

---

## 3. 서버 설정

### 3.1 디렉토리 구조

```
/home/webapp/goldenrabbit/
├── backend/
│   ├── api/                      # API 서버
│   ├── property-manager/         # Property Manager + Propsheet
│   │   ├── routes/
│   │   │   ├── propsheet.py      # Propsheet 라우트 (워크스페이스/DB CRUD, 복제, 권한)
│   │   │   ├── database.py       # DB CRUD 라우트 (낙관적 잠금 + 역할 기반 권한)
│   │   │   ├── auth.py           # 인증 (Google OAuth로 리다이렉트)
│   │   │   ├── oauth.py          # Google OAuth 블루프린트 (로그인/콜백/로그아웃) (2026-03-05 추가)
│   │   │   ├── workspace_members.py  # 멤버 관리 API (2026-03-05 추가)
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── workspace_service.py   # 워크스페이스 관리 + DB 뷰 복제
│   │   │   ├── database_service.py    # PostgreSQL 연산
│   │   │   ├── formula_service.py     # 에어테이블 수식 → SQL 변환 (2026-03-04 추가)
│   │   │   ├── schema_service.py      # 필드 정의/스키마 관리
│   │   │   ├── view_service.py        # 뷰 CRUD (2026-03-04 추가)
│   │   │   ├── web_user_service.py    # 사용자 CRUD, Google OAuth 지원 (2026-03-05 추가)
│   │   │   ├── workspace_member_service.py  # 멤버 초대/역할 관리 (2026-03-05 추가)
│   │   │   ├── permission_service.py  # 권한 데코레이터 3종 (2026-03-05 추가)
│   │   │   ├── google_auth_service.py # Google OAuth 플로우 (2026-03-05 추가)
│   │   │   ├── share_service.py     # DB 공유 토큰 CRUD (2026-03-05 추가)
│   │   │   ├── record_id_service.py # Propsheet 고유 record_id 생성
│   │   │   ├── airtable_service.py  # Airtable 저장
│   │   │   └── ...
│   │   ├── templates/
│   │   │   └── propsheet/
│   │   │       ├── workspaces.html    # 워크스페이스 목록 (DB 생성 시 일정관리 템플릿 선택)
│   │   │       ├── database_list.html # 스프레드시트 UI (time 필드 시/분 피커, 캘린더 뷰 토글)
│   │   │       ├── calendar.html      # 캘린더 뷰 (월/주/일/년 4가지 모드) (2026-03-24 추가)
│   │   │       ├── share.html         # DB 공유 미리보기/복제 페이지 (2026-03-05 추가)
│   │   │       └── landing.html       # 랜딩 페이지 (Propnet 정보)
│   │   └── static/
│   │       ├── css/propsheet/
│   │       │   ├── calendar.css       # 캘린더 뷰 스타일 (2026-03-24 추가)
│   │       │   └── ...
│   │       └── js/propsheet/
│   │           ├── calendar.js        # 캘린더 Alpine.js 컴포넌트 (2026-03-24 추가)
│   │           └── ...
│   ├── shared/                   # 공유 모듈
│   ├── scripts/                  # 유틸리티 스크립트
│   │   ├── airtable_backup.py    # 에어테이블 백업 (02:00 AM)
│   │   ├── generate_map.py       # 지도 생성 (03:00 AM)
│   │   ├── airtable_to_propsheet_sync.py  # Propsheet 동기화 (04:00 AM)
│   │   └── migration/            # DB 마이그레이션
│   │       └── add_sync_columns.sql  # fields_hash, synced_at 추가
│   ├── .env                      # 환경 변수 (공유)
│   ├── requirements.txt
│   └── venv/                     # Python 가상환경
├── frontend/
│   └── public/                   # Nginx 정적 파일
├── config/
│   ├── nginx/goldenrabbit.conf
│   └── systemd/                  # 서비스 파일
├── backups/
│   ├── airtable/                 # 에어테이블 백업 (JSON + 이미지)
│   ├── airtable_safe/            # 안전 백업 (롤백용)
│   ├── airtable_temp/            # 임시 백업 (작업 중)
│   └── database/                 # DB 백업
├── logs/
│   ├── api/
│   ├── property-manager/
│   └── nginx/
└── scripts/                      # 운영 스크립트
```

### 3.2 Systemd 서비스

```bash
# API Server
sudo systemctl status goldenrabbit-api
# Property Manager
sudo systemctl status goldenrabbit-property

# 재시작
sudo systemctl restart goldenrabbit-api goldenrabbit-property
```

- 서비스 파일: `/home/webapp/goldenrabbit/config/systemd/`
- PYTHONPATH: `/home/webapp/goldenrabbit/backend`
- 공유 가상환경: `/home/webapp/goldenrabbit/backend/venv/`

### 3.3 Nginx 설정

- 설정 파일: `/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf`
- **주의**: `/etc/nginx/sites-enabled/goldenrabbit`는 심볼릭 링크가 아닌 복사본. 설정 변경 시 복사 필요:
  ```bash
  cp /home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf /etc/nginx/sites-enabled/goldenrabbit
  nginx -t && systemctl reload nginx
  ```
- SSL: `/etc/letsencrypt/live/goldenrabbit.biz/`
- 이미지 서빙: `/uploads/airtable/` → `/home/webapp/goldenrabbit/backups/airtable/images/` (7일 캐시)

### 3.4 인증

- **Google OAuth 2.0** (2026-03-05 전환)
  - Google Cloud Console 프로젝트: proptalk/proppedia/propsheet 통합 프로젝트
  - OAuth 클라이언트: `Propsheet_Web` (Web application 타입)
  - Client ID: `846392940969-h70f...apps.googleusercontent.com`
  - Redirect URI: `https://goldenrabbit.biz/propsheet/auth/google/callback`
  - Scopes: `openid`, `email`, `profile`
  - 랜딩 페이지: `/propsheet/` (미인증 시 Google 로그인 버튼 표시)
- `web_users` 테이블 (google_id + avatar_url 저장, password 불필요)
- 세션: `user_id`, `user_email`, `is_admin`, `avatar_url`, `username` 저장
- 로그인할 때마다 Google 프로필 이름/아바타 자동 동기화
- 새 사용자: Google 로그인 시 자동 가입 → 자신의 워크스페이스 생성 가능
- 기존 Property Manager 로그인 → Google OAuth로 통합 리다이렉트
- 역할 기반 접근 제어: owner > editor > viewer 계층
- **권한 데코레이터 3종**:
  - `@propsheet_login_required` — 인증 필수
  - `@require_workspace_role(role)` — workspace_slug 기반 역할 체크
  - `@require_database_role(role)` — database_id → workspace 역할 체크

---

## 4. 데이터베이스 스키마 (PostgreSQL)

### 4.1 연결 설정

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'dbname': 'goldenrabbit_db',
    'user': 'goldenrabbit_user',
    'password': '***'
}
```

### 4.2 Propsheet 핵심 테이블

#### workspaces

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| name | TEXT | 워크스페이스 이름 (한글) |
| slug | VARCHAR | URL용 영문 식별자 (unique) |
| description | TEXT | 설명 |
| icon | TEXT | 이모지 아이콘 |
| display_order | INTEGER | 정렬 순서 |

#### databases

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| workspace_id | INTEGER FK | workspaces.id 참조 |
| name | TEXT | 데이터베이스 이름 |
| slug | VARCHAR | URL용 영문 식별자 |
| table_name | VARCHAR | 실제 PostgreSQL 테이블명 |
| description | TEXT | 설명 |
| icon | TEXT | 이모지 아이콘 |
| color | VARCHAR | 테마 색상 |
| display_order | INTEGER | 정렬 순서 |
| external_source | VARCHAR(50) | 외부 데이터 소스 (`proptalk` 등) (2026-03-24 추가) |
| external_config | JSONB | 외부 연동 설정 (`{"room_id": 5}` 등) (2026-03-24 추가) |

#### field_definitions

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| field_name | TEXT | 필드명 |
| field_type | TEXT | 필드 타입 (text, number, date, time, single-select, multi-select, checkbox, formula, long-text, attachment, url, system_generated_value) |
| formula | TEXT | 수식 (nullable) |
| system_value_key | TEXT | 시스템 값 키 |
| select_options | TEXT[] | Select 필드 선택지 목록 (PostgreSQL 배열) |
| is_editable | BOOLEAN | 편집 가능 여부 |
| display_order | INTEGER | 정렬 순서 |

#### views (2026-03-04 추가, 2026-03-24 view_type 추가)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| database_id | INTEGER FK | databases.id 참조 |
| name | VARCHAR(100) | 뷰 이름 |
| slug | VARCHAR(100) | URL용 식별자 (UNIQUE with database_id) |
| view_type | VARCHAR(20) | 뷰 타입: `grid` (스프레드시트) / `calendar` (캘린더) (2026-03-24 추가) |
| filter_config | JSONB | 필터 규칙 배열 [{field, operator, value}] |
| sort_config | JSONB | 정렬 설정 {sort_by, sort_order} |
| column_config | JSONB | 표시 컬럼 키 배열 (캘린더 뷰: {calendar: {date_field, end_date_field, title_field, color_field}}) |
| display_order | INTEGER | 정렬 순서 |
| is_default | BOOLEAN | 기본 뷰 여부 (삭제 불가) |
| created_at | TIMESTAMP | 생성일 |
| updated_at | TIMESTAMP | 수정일 |

#### web_users (2026-03-05 추가)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| email | VARCHAR(255) UNIQUE | 이메일 (로그인 ID) |
| password_hash | VARCHAR(255) | bcrypt 해시 비밀번호 |
| name | VARCHAR(100) | 사용자 이름 |
| is_active | BOOLEAN | 활성 상태 (기본 TRUE) |
| created_at | TIMESTAMP | 생성일 |
| updated_at | TIMESTAMP | 수정일 |

#### workspace_members (2026-03-05 추가)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| workspace_id | INTEGER FK | workspaces.id 참조 (CASCADE) |
| user_id | INTEGER FK | web_users.id 참조 (CASCADE) |
| role | VARCHAR(20) | owner / editor / viewer |
| invited_by | INTEGER FK | web_users.id 참조 |
| invited_at | TIMESTAMP | 초대일 |
| accepted_at | TIMESTAMP | 수락일 |
| | UNIQUE | (workspace_id, user_id) |

#### sales_building (매물 데이터 테이블)

에어테이블 필드를 직접 매핑한 동적 컬럼 구조 (67+ 컬럼). 주요 필드:

| 컬럼 | 타입 | 에어테이블 필드 |
|------|------|---------------|
| id | SERIAL PK | PostgreSQL 자동증가 |
| airtable_id | VARCHAR(20) UNIQUE | 에어테이블 원본 레코드 ID (recXXX) |
| record_id | VARCHAR UNIQUE | Propsheet 고유 레코드 ID (recXXX, record_id_service 자동생성) |
| 지번 주소 | TEXT | 지번 주소 |
| 도로명주소 | TEXT | 도로명주소 |
| 매가(만원) | NUMERIC | 매가(만원) |
| 보증금(만원) | NUMERIC | 보증금(만원) |
| 월세(만원) | NUMERIC | 월세(만원) |
| 토지면적(㎡) | NUMERIC | 토지면적(㎡) |
| 연면적(㎡) | NUMERIC | 연면적(㎡) |
| 건폐율(%) | NUMERIC | 건폐율(%) |
| 용적률(%) | NUMERIC | 용적률(%) |
| 높이(m) | NUMERIC | 높이(m) |
| 용도지역 | TEXT | 용도지역 |
| 주용도 | TEXT | 주용도 |
| 층수 | TEXT | 층수 |
| 사용승인일 | DATE/TEXT | 사용승인일 |
| 현황 | TEXT | 현황 (Multiple Select) |
| 소유주연락처 | VARCHAR(100) | 소유주연락처 |
| fields_hash | VARCHAR(32) | 동기화 변경 감지용 MD5 해시 |
| synced_at | TIMESTAMP | 마지막 동기화 시각 |
| created_at | TIMESTAMP | - |
| updated_at | TIMESTAMP | - |

**인덱스**: `idx_sales_building_fields_hash`, `idx_sales_building_synced_at`

#### database_shares (2026-03-05 추가)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| database_id | INTEGER FK | databases.id 참조 (CASCADE) |
| share_token | VARCHAR(64) UNIQUE | 공유 토큰 (secrets.token_urlsafe) |
| created_by | INTEGER FK | web_users.id 참조 |
| expires_at | TIMESTAMP | 만료일 (기본 7일) |
| is_active | BOOLEAN | 활성 상태 |
| clone_count | INTEGER | 복제 횟수 추적 |
| created_at | TIMESTAMP | 생성일 |

**트리거**:
- `format_ad_text()` — 단일부동산 광고(자동완성) 자동 생성 (홍보문구+매매금액+임대내역+건물현황+면적+층수+주차+승강기+방향+주용도+용도지역+위반건축물+사용승인일)
- `format_ad_text_partial()` — 부분부동산 광고(자동완성) 자동 생성 (임대 전용: 홍보문구+물건종류+임대종류+보증금/월세+관리비+전용면적+방/화+방향+위반건축물+입주가능일)
- `format_ad_text_multi()` — 집합부동산 광고(자동완성) 자동 생성 (매매/전세/월세 분기, 관리비, 전용/공급/대지면적, 총세대수, 주차, 승강기, 사용승인일, 용도지역, 공시가격, 방/화, 방향, 입주가능일)
- `update_map_link()` — 지도 링크 자동 생성 (지번 주소 → 카카오맵 URL)
- `calculate_property_values()` — INSERT/UPDATE 시 수식 필드 자동 계산 (수익률, 실투자금, 126% 등)

---

## 5. 에어테이블 연동

### 5.1 에어테이블 설정

| 항목 | 값 |
|------|-----|
| Base ID | appGSg5QfDNKgFf73 |
| Table ID | tblnR438TK52Gr0HB |
| 총 레코드 수 | 408개 (2026-03-03 기준) |
| 뷰 수 | 4개 (all, reconstruction, high_yield, low_cost) |

### 5.2 에어테이블 필드 구조 (67개 필드)

**텍스트 필드**: 지번 주소, 도로명주소, 건물명, 주구조, 지붕, 주용도, 기타용도, 층수, 세대/가구/호, 인접역, 건물구성, 주인세대, 주인거주, 위반건축물, 사진필요, SH가능, 현황

**숫자 필드**: 매가(만원), 보증금(만원), 월세(만원), 토지면적(㎡), 연면적(㎡), 건축면적(㎡), 용적률산정용연면적(㎡), 건폐율(%), 용적률(%), 높이(m), 거리(m), 주차대수, 승강기수, 감정가(만원), 감정가율(%), 공시지가(원/㎡), 대지면적(㎡), 실투자금

**날짜 필드**: 사용승인일, 생성일자, 레코드생성일자

**수식 필드**: 126%, 매가(만원), 실투자금, 융자제외수익률(%), 융자포함수익률, 거리(m), Disco광고, 상세설명(자동생성), 홍보문구(상단/하단)

**첨부파일**: 대표사진, 건축물대장

**Single Select**: 용도지역, 현관가능여부

**Multiple Select**: 현황 (비공개, 공개중, 계약중, 등록대기 등)

**기타**: 전화번호, URL(지도, 디스코광고), Long text(상세설명, 비공개메모)

### 5.3 데이터 흐름

```
[Airtable API]
    │
    ▼ (매일 02:00 AM - airtable_backup.py)
[백업 JSON] ── backups/airtable/all_properties.json (408개 레코드)
    │
    ├──▶ (매일 03:00 AM - generate_map.py) → 지도 HTML 생성
    │
    └──▶ (매일 04:00 AM - airtable_to_propsheet_sync.py) → Propsheet DB (sales_building)
```

### 5.4 백업 프로세스

**스크립트**: `/home/webapp/goldenrabbit/backend/scripts/airtable_backup.py`

**실행 시간**: 매일 02:00 AM (cron)

**백업 디렉토리**: `/home/webapp/goldenrabbit/backups/airtable/`

**백업 파일 구조**:
```
backups/airtable/
├── all_properties.json          # 전체 매물 (408개)
├── reconstruction_properties.json  # 재건축용 토지
├── high_yield_properties.json    # 고수익률 건물
├── low_cost_properties.json      # 저가단독주택
├── coordinates.json              # 좌표 캐시
├── metadata.json                 # 백업 메타데이터
└── images/                       # 매물 이미지
    └── {record_id}/
        └── {filename}.jpg
```

**안전 백업 메커니즘**:
1. 기존 데이터 → `airtable_safe/` 복사 (롤백용)
2. 새 데이터 → `airtable_temp/` 다운로드
3. 검증 후 → `airtable/` 최종 반영
4. 실패 시 → `airtable_safe/`에서 자동 복원

**이미지 백업**: 증분 방식 (파일명+크기 비교, 변경분만 다운로드)

**알림**: 이메일 (성공/실패 모두 알림)

### 5.5 Propsheet 동기화

**스크립트**: `/home/webapp/goldenrabbit/backend/scripts/airtable_to_propsheet_sync.py`

**실행 시간**: 매일 04:00 AM (cron)

**동기화 방식**: 증분 동기화
- **키**: 에어테이블 레코드 ID (`airtable_id` 컬럼)
- **변경 감지**: 레코드 fields를 JSON 직렬화 → MD5 해시 → `fields_hash` 컬럼과 비교
- **동작**: 신규 → INSERT (record_id 자동 생성), 변경 → UPDATE, 삭제 → DELETE
- **record_id**: INSERT 시 `record_id_service.ensure_unique_record_id()` 호출하여 Propsheet 고유 ID 자동 부여
- **수식 필드**: DB 트리거가 자동 계산 (스크립트에서 스킵)

**필드 매핑**: 에어테이블 40+ 필드를 PostgreSQL 컬럼에 직접 매핑
- 숫자 필드: `_safe_float()` / `_safe_int()` 변환
- 날짜 필드: ISO 포맷 변환 (`_convert_to_iso_date()`)
- 첨부파일: URL만 저장

**마이그레이션 SQL**: `/home/webapp/goldenrabbit/backend/scripts/migration/add_sync_columns.sql`
- `fields_hash VARCHAR(32)` 컬럼 추가
- `synced_at TIMESTAMP` 컬럼 추가
- 관련 인덱스 생성

**초기 동기화 결과** (2026-03-03):
- 총 레코드: 275개 (백업 JSON 기준)
- 신규 추가: 3개
- 변경 업데이트: 271개
- 삭제: 10개
- 오류: 0개
- 2회차 실행: 274개 스킵 (변경 없음), 1개 업데이트 → 증분 동기화 정상 동작 확인

**알림**: 이메일 (성공/실패 요약)

**옵션**: `--dry-run` 모드 지원 (실제 DB 변경 없이 미리보기)

### 5.6 최근 백업 현황 (2026-03-03)

```json
{
  "last_backup_date": "2026-03-03",
  "last_backup_time": "2026-03-03T02:00:35",
  "backup_mode": "완전 새로고침",
  "total_records": 408,
  "views_processed": 4,
  "image_stats": {
    "new_images": 0,
    "updated_images": 6,
    "skipped_images": 269,
    "error_images": 0
  }
}
```

---

## 6. Propsheet 현재 기능

### 6.1 구현 완료 기능

**워크스페이스 관리** (`routes/propsheet.py`):
- 워크스페이스 CRUD (생성, 조회, 수정, 삭제)
- 데이터베이스 CRUD (생성, 조회, 수정, 삭제)
- **데이터베이스 복제** (테이블 구조 + 데이터 + 뷰 완전 복사) — 2026-03-05 추가
- Slug 기반 URL 라우팅 (`/propsheet/workspace/{slug}/database/{slug}`)
- 빈 테이블 생성 / 기존 테이블 복제
- 레거시 URL 리디렉션
- **멤버십 기반 워크스페이스 필터링** (관리자: 전체, 일반 사용자: 소속 워크스페이스만)

**스프레드시트 UI** (`templates/propsheet/database_list.html`):
- Alpine.js + HTMX 기반 인터랙티브 테이블
- 컬럼 관리 (표시/숨김, 드래그앤드롭 순서 변경)
- 필드 추가/설정 (⚙ 버튼)
- 레코드 추가/삭제
- 검색 (필드 선택 + 키워드)
- 고급 필터 (AND/OR 토글, 12개 연산자, Select 필드 체크박스 필터)
- 정렬 (오름차순/내림차순)
- 페이지네이션 (25/50/100개씩)
- CSV 내보내기
- 인라인 셀 편집 (기본 + Select 필드 드롭다운)
- 수식 필드 (PostgreSQL 계산 기반)
- **다중 뷰 시스템** (뷰 생성/저장/삭제/전환, 뷰별 필터/정렬/컬럼 설정 JSONB 저장)
- **Single/Multiple Select 필드** (드롭다운 UI, 색상 뱃지 렌더링, 10색 팔레트)
- **인라인 셀 편집** (클릭 편집, Tab/Enter/Escape 키보드 네비게이션, 수식 읽기전용)
- **레코드 상세 사이드패널** (▶ 버튼 클릭 시 오른쪽 슬라이드 패널 640px, 전체 필드 표시, 인라인 편집)
  - Select 필드 드롭다운 편집 지원
  - URL 값 자동 감지 → 클릭 시 외부 링크 오픈 (`target="_blank"`)
  - 긴 텍스트 자동 textarea 전환 (60자 이상 또는 줄바꿈 포함 시 자동 확장, Ctrl+Enter 저장)
  - 편집창 전체 너비 활용 (flex 레이아웃 최적화)
- **수식 엔진 강화** (에어테이블 수식 → PostgreSQL SQL 변환기, IF/텍스트 조합 지원)
- **날짜 필드 피커** (네이티브 date input, 한국어 포맷 표시)
- **URL 자동 링크** (그리드 셀에서도 https:// 값 자동 감지 → 클릭 가능한 링크 렌더링)
- **낙관적 잠금** (`updated_at` 기반 충돌 감지, 409 Conflict 응답) — 2026-03-05 추가
- **컬럼 너비 리사이즈** — 2026-03-05 추가:
  - 드래그 리사이즈 (기존) + 더블클릭 자동 맞춤 (autoFitColumn)
  - 뷰별 컬럼 너비 저장 (`column_config: {columns, widths}` JSONB)
  - 리사이즈 후 뷰 자동 저장
- **CSV 뷰별 내보내기** — 2026-03-05 추가:
  - 현재 뷰의 필터/정렬/컬럼 설정 반영하여 CSV 내보내기
  - `view_id` 파라미터 지원, 없으면 전체 내보내기 (하위 호환)
- **DB 공유 복제** — 2026-03-05 추가:
  - Owner가 공유 링크 생성 → 토큰 기반 URL (7일 만료)
  - 다른 사용자가 링크로 접속 → DB 미리보기 → 자신의 워크스페이스에 복제
  - 데이터+구조+뷰 복제, 권한은 제외 (복제자가 자동 owner)
  - `database_shares` 테이블 (토큰, 만료일, clone_count 추적)
- **이미지/첨부파일 시스템 Phase 1** — 2026-03-05 추가:
  - 에어테이블 백업 이미지를 Nginx로 직접 서빙 (`/uploads/airtable/`)
  - `formatCell`에서 이미지 첨부 자동 감지 → 셀 내 썸네일 표시 (32px)
  - 클릭 시 전체화면 오버레이 (`_openImageModal`)
  - PDF 첨부파일: 📄 아이콘 + 파일명 표시 (백업에 PDF 미포함으로 미리보기 불가)
  - `attachment` 필드 타입 정식 지원 (schema_service)
  - 디테일 패널에서 큰 썸네일 표시 (120px)
- **랜딩 페이지** — 2026-03-05 추가:
  - Propnet 회사 정보 footer (아이콘, 이메일, 저작권)

**사용자 관리 & 멤버 초대** — 2026-03-05 추가:
- 사용자 등록/인증 (`services/web_user_service.py`, bcrypt 해싱)
- 워크스페이스 멤버 초대 (이메일 + 역할 지정)
- 역할: owner (소유자), editor (편집자), viewer (열람자)
- 멤버 관리 모달 UI (멤버 목록, 초대, 역할 변경, 제거)
- 이메일로 초대 시 계정 미존재 시 자동 생성 (임시 비밀번호)
- 관리자(env var 인증)는 모든 워크스페이스 접근 가능

**데이터베이스 서비스** (`services/database_service.py`):
- PostgreSQL CRUD
- 동적 테이블 생성/복제
- 수식 필드 계산 (COALESCE 래핑으로 NULL 처리)
- field_definitions 테이블을 통한 필드 메타데이터 관리 (select_options, is_editable 포함)
- 고급 필터 (AND/OR 로직, 16개 연산자: equals, not_equals, contains, not_contains, gt, lt, gte, lte, is_before, is_after, is_on_or_before, is_on_or_after, is_empty, is_not_empty, is_any_of, is_none_of)
- 필드 타입별 필터 조건 분리: 텍스트/숫자/날짜/선택/체크박스/수식 각각 적절한 연산자만 표시 (2026-03-25)
- 수식(formula) 필드 결과값 필터링 지원: SQL 표현식을 WHERE 절에 삽입 (2026-03-25)

**뷰 서비스** (`services/view_service.py`) — 2026-03-04 추가:
- 뷰 CRUD (생성, 조회, 수정, 삭제)
- 뷰별 필터/정렬/컬럼 설정 JSONB 저장
- 기본 뷰 보호 (삭제 불가)
- slug 기반 조회
- **view_type 지원**: `grid` (스프레드시트) / `calendar` (캘린더) — 2026-03-24 추가

**Proptalk 연동 서비스** (`services/proptalk_service.py`) — 2026-03-24 추가:
- voiceroom DB 연결 (별도 psycopg2 커넥션, 같은 서버 localhost)
- `get_proptalk_rooms(email)` — 사용자의 Proptalk 채팅방 목록
- `create_proptalk_database_table()` — 통화요약 테이블 + field_definitions 자동 생성
- `import_all_audio_files()` — 최초 전체 가져오기 (voiceroom → goldenrabbit_db)
- `sync_new_audio_files()` — 새 오디오만 추가 (기존 데이터 보존, INSERT only)
- `check_matched_phones(phones)` — 전화번호 일괄 매칭 (숫자 정규화 후 비교)
- `get_audio_by_phone(phone)` — 특정 전화번호의 통화 요약 목록 조회

**캘린더 뷰** — 2026-03-24 추가:
- **URL**: `/propsheet/workspace/{slug}/database/{slug}/calendar`
- **4가지 뷰 모드**: 월간(monthly), 주간(weekly), 일간(daily), 연간(yearly)
- **일정/할일 관리**: 유형(일정/할일), 상태(예정/진행중/완료/취소), 우선순위, 중요도(★★★/★★/★)
- **담당자 지정**: agent/subagent 이름 드롭다운 (`/api/agent/assignees` API)
- **시간 필드**: `time` 필드 타입 — 시/분 2단계 드롭다운 (10분 단위)
- **종일 이벤트**: 체크 시 00:00~23:50 자동 설정
- **일정관리 DB 템플릿**: 워크스페이스에서 DB 생성 시 "일정관리" 선택 → 제목/시작일/종료일/시작시간/종료시간/종일/유형/상태/우선순위/중요도/카테고리/담당자/메모/비고 자동 생성
- **캘린더 API**: `GET /api/database/calendar?db=&year=&month=` (날짜 범위 기반 이벤트 조회)
- **뷰 전환 토글**: 스프레드시트 ↔ 캘린더 아이콘 (database_list.html 헤더)

**Proptalk 통화요약 연동** — 2026-03-24 추가, 2026-03-25 수정:
- **통화요약 DB 템플릿**: DB 생성 시 "통화요약" 선택 → Proptalk 채팅방 선택 → 해당 방의 음성 요약을 PropSheet 테이블로 가져오기
  - 필드: 녹음날짜, 이름, 전화번호, 요약, 통화내용, 길이(초), 파일명, Drive 링크, 상태, 업로더, 메모
  - agent/subagent 전용 (일반 user는 템플릿 미표시)
  - `databases.external_source='proptalk'`, `external_config={"room_id": N}` 저장
  - 스프레드시트 열 때 새 오디오 자동 동기화 (INSERT only, 기존 편집 보존)
  - `proptalk_audio_id` 컬럼으로 동기화 상태 추적 (중복 INSERT 방지)
- **전화번호-통화기록 연결**: 스프레드시트의 전화번호와 Proptalk 음성 파일 전화번호 자동 매칭
  - 숫자 정규화 매칭 (하이픈/공백/메모 포함 형식 모두 대응)
  - 매칭된 셀에 📞+건수 아이콘 표시
  - 클릭 시 사이드패널에 통화 기록 목록 (날짜, 이름, AI 요약, 길이, Drive 링크, 전문보기)
  - API: `POST /api/proptalk/check-phones` (일괄 매칭), `GET /api/proptalk/audio-by-phone` (통화 상세)
- **Nginx 캐시 개선**: propsheet static 경로 `expires 1h` → `ETag + no-cache, must-revalidate` (파일 수정 즉시 반영)
- **다크모드 지원**: 기존 CSS 변수 재활용
- **할일 사이드바**: 미완료 할일 목록 (시작일순 정렬, 체크박스 완료 토글)

**에어테이블 → Propsheet 동기화** (`scripts/airtable_to_propsheet_sync.py`):
- 매일 04:00 AM 자동 실행 (cron)
- 증분 동기화 (MD5 해시 기반 변경 감지)
- 에어테이블 백업 JSON → sales_building 테이블 반영
- 40+ 필드 매핑 (숫자/텍스트/날짜 자동 변환)
- 수식 필드는 DB 트리거가 자동 계산

### 6.2 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /propsheet/workspaces | 워크스페이스 목록 페이지 |
| GET | /propsheet/workspace/{slug} | 워크스페이스 상세 |
| GET | /propsheet/workspace/{ws}/database/{db} | 데이터베이스 뷰 |
| GET | /propsheet/api/workspaces | 워크스페이스 API |
| POST | /propsheet/api/workspace | 워크스페이스 생성 |
| PUT | /propsheet/api/workspace/{slug} | 워크스페이스 수정 |
| DELETE | /propsheet/api/workspace/{slug} | 워크스페이스 삭제 |
| POST | /propsheet/api/workspace/{slug}/database | DB 생성 |
| PUT | /propsheet/api/workspace/{ws}/database/{db} | DB 수정 |
| DELETE | /propsheet/api/workspace/{ws}/database/{db} | DB 삭제 |
| GET | /property-manager/api/database/views?database_id={id} | 뷰 목록 |
| POST | /property-manager/api/database/view | 뷰 생성 |
| PATCH | /property-manager/api/database/view/{id} | 뷰 수정 |
| DELETE | /property-manager/api/database/view/{id} | 뷰 삭제 |
| GET | /propsheet/api/workspace/{slug}/members | 멤버 목록 |
| POST | /propsheet/api/workspace/{slug}/members | 멤버 초대 (email + role) |
| DELETE | /propsheet/api/workspace/{slug}/members/{user_id} | 멤버 제거 |
| PATCH | /propsheet/api/workspace/{slug}/members/{user_id}/role | 역할 변경 |
| GET | /propsheet/ | 랜딩 페이지 (미인증 시) |
| GET | /propsheet/auth/google | Google OAuth 로그인 시작 |
| GET | /propsheet/auth/google/callback | Google OAuth 콜백 |
| GET | /propsheet/auth/logout | 로그아웃 |
| GET | /propsheet/auth/debug | 세션 상태 확인 (디버그) |
| POST | /propsheet/api/workspace/{ws}/database/{db}/share | DB 공유 링크 생성 (owner만) |
| GET | /propsheet/api/workspace/{ws}/database/{db}/shares | DB 공유 링크 목록 (owner만) |
| GET | /propsheet/share/{token} | DB 공유 미리보기 페이지 |
| POST | /propsheet/share/{token}/clone | DB 복제 실행 |
| DELETE | /propsheet/api/share/{share_id} | 공유 링크 비활성화 |

---

## 7. 크론 작업

```bash
# 에어테이블 백업 - 매일 02:00 AM
0 2 * * * /usr/bin/python3 /home/webapp/goldenrabbit/backend/scripts/airtable_backup.py

# 지도 생성 - 매일 03:00 AM
0 3 * * * /usr/bin/python3 /home/webapp/goldenrabbit/backend/scripts/generate_map.py

# Propsheet 동기화 - 매일 04:00 AM (활성)
0 4 * * * /home/webapp/goldenrabbit/backend/venv/bin/python3 /home/webapp/goldenrabbit/backend/scripts/airtable_to_propsheet_sync.py >> /home/webapp/goldenrabbit/logs/propsheet_sync.log 2>&1
```

---

## 8. 환경 변수

**파일**: `/home/webapp/goldenrabbit/backend/.env`

| 변수 | 용도 |
|------|------|
| AIRTABLE_API_KEY | 에어테이블 API 키 |
| AIRTABLE_BASE_ID | 에어테이블 Base ID |
| PUBLIC_API_KEY | 공공데이터포털 API 키 |
| VWORLD_APIKEY | VWorld API 키 |
| GOOGLE_SCRIPT_URL | 주소→코드 변환 Apps Script |
| FLASK_SECRET_KEY | Flask 세션 시크릿 |
| ADMIN_USERNAME | 관리자 아이디 |
| ADMIN_PASSWORD_HASH | 관리자 비밀번호 (SHA256) |
| GOOGLE_OAUTH_CLIENT_ID | Google OAuth 클라이언트 ID (Propsheet_Web) |
| GOOGLE_OAUTH_CLIENT_SECRET | Google OAuth 클라이언트 시크릿 |
| DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD | PostgreSQL 연결 |
| EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT | 이메일 알림 |
| ANTHROPIC_API_KEY | Claude API 키 |

---

## 9. 로그 파일

| 서비스 | 위치 |
|--------|------|
| API 서버 | `/home/webapp/goldenrabbit/logs/api/api_debug.log` |
| Property Manager | `/home/webapp/goldenrabbit/logs/property-manager/app.log` |
| Nginx | `/home/webapp/goldenrabbit/logs/nginx/access.log` |
| 에어테이블 백업 | `/home/webapp/goldenrabbit/logs/airtable_backup.log` |
| 맵 생성 | `/var/log/airtable_map.log` |
| Propsheet 동기화 | `/home/webapp/goldenrabbit/logs/propsheet_sync.log` (활성) |

---

## 10. 홈페이지 연동 (2026-03-25)

### 매물지도/검색/상세 DB 전환

기존 Airtable 백업 JSON/API 기반에서 PropSheet DB 실시간 조회로 전환 완료.

| 기능 | 변경 전 | 변경 후 |
|------|---------|---------|
| 매물 지도 | `airtable_map.html` (매일 새벽 크론 정적 HTML) | `map.html` (PropSheet DB 실시간 로드) |
| 매물 검색 | `POST /property-manager/api/search-map` (Airtable 백업 JSON) | `POST /propsheet/api/propsheet/search-map` (DB SQL 쿼리) |
| 매물 상세 | `GET /api/property-detail?id=` (Airtable API 직접 호출) | `GET /propsheet/api/propsheet/property-detail?id=` (PropSheet DB) |
| 공유 링크 | `/property/{recordId}` (별도 페이지) | `/?property={recordId}` (홈페이지 모달 자동 오픈) |

### 추가된 PropSheet API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/propsheet/map-data` | 지도 마커 데이터 (좌표 + 매물정보) |
| POST | `/api/propsheet/search-map` | 조건 검색 → 카카오맵 HTML 반환 |
| GET | `/api/propsheet/property-detail` | 단일 매물 상세 |

### 미완료 항목

- 추천매물 3개 카테고리 (재건축용 토지, 고수익률 건물, 저가단독주택): 아직 Airtable API 연결, DB 전환 필요
- map.html 상세 모달 → 부모 모달 통일: 현재 iframe 내 자체 모달 사용 중, `parent.postMessage`로 변경 예정
- 워크스페이스별 지도: 향후 워크스페이스가 늘어나면 각각의 map HTML 생성 구조 필요
