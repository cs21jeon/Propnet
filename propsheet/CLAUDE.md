# PropSheet - 스프레드시트 서비스

## 개요

PropSheet은 Airtable 대안 스프레드시트 SaaS입니다. 부동산 데이터 관리에 특화된 웹 기반 스프레드시트로, 워크스페이스/데이터베이스 구조를 갖습니다.

> **Airtable 완전 제거 완료 (2026-03-26)**: 모든 매물 데이터, 이미지, 건축물대장이 PropSheet DB + 로컬 파일 시스템으로 전환됨. 홈페이지/SNS 공유 모두 PropSheet DB에서 직접 조회. 새 코드에서 Airtable 관련 코드 작성 금지.

- **URL**: `https://goldenrabbit.biz/propsheet/`
- **파일 접근**: MCP(goldenrabbit-server) 사용

### ⚠️ 포트 및 서비스 구조 (중요)

- **PropSheet 웹 UI** → 포트 **5020** (`propsheet` 서비스)
- **app.py 위치**: `/backend/propsheet/app.py`
- **Nginx**: `/propsheet` → `localhost:5020`
- **코드 공유**: `/backend/property-manager/`의 routes/services/templates를 `sys.path`로 임포트

**PropSheet 관련 Blueprint는 `/backend/propsheet/app.py`(5020)에만 등록하면 됨.**
property-manager(5000)는 홈페이지 API/SNS 공유/Propedia 앱용 서버이므로 PropSheet UI Blueprint와 무관.

```bash
# PropSheet 배포 시
sudo systemctl restart propsheet   # 5020만 재시작하면 됨
```

## 기술 스택

| 계층 | 기술 |
|------|------|
| Backend | Python Flask (Property Manager Blueprint) |
| Frontend | HTMX + Alpine.js |
| Database | PostgreSQL (`goldenrabbit_db` 공유) |
| 인증 | Google OAuth 2.0 |
| 프로세스 | systemd (`propsheet`) |

## 핵심 파일 (서버 경로)

모든 경로는 `/home/webapp/goldenrabbit/backend/property-manager/` 기준:

### Routes
- `routes/propsheet.py` — 워크스페이스/DB CRUD, 복제, 권한 + **홈페이지 매물 API** (map-data, category-properties, search-map, property-detail)
- `routes/database.py` — DB 레코드 CRUD (낙관적 잠금) + **파일 업로드/삭제**
- `routes/propnet_api.py` — **SNS 공유** (`/property/{id}` OG 메타태그, PropSheet DB 조회)
- `routes/oauth.py` — Google OAuth 블루프린트
- `routes/workspace_members.py` — 멤버 관리 API

### Services
- `services/workspace_service.py` — 워크스페이스 관리 + DB 뷰 복제
- `services/database_service.py` — PostgreSQL 동적 CRUD + DB 연결 관리 + `geocode_address()` (VWorld API)
- `services/propsheet_save_service.py` — Proppedia 앱 → PropSheet 저장 (좌표 자동 변환 포함)
- `services/formula_service.py` — 수식 → SQL 변환
- `services/schema_service.py` — 필드 정의/스키마 관리
- `services/view_service.py` — 뷰 CRUD (grid/calendar)
- `services/permission_service.py` — 권한 데코레이터 (owner/editor/viewer)
- `services/google_auth_service.py` — Google OAuth 플로우
- `services/share_service.py` — DB 공유 토큰 CRUD
- `services/building_unified_service.py` — 건축물대장 통합 조회

### Templates
`templates/propsheet/` 디렉토리:
- `database_list.html` — 메인 스프레드시트 UI (필터/정렬/인라인 편집)
- `calendar.html` — 캘린더 뷰 (월/주/일/년 4모드)
- `workspaces.html` — 워크스페이스 목록
- `share.html` — DB 공유 미리보기/복제
- `landing.html` — 랜딩 페이지
- `guide/_base.html` — 가이드 공통 레이아웃 (사이드바+콘텐츠)
- `guide/index.html` — 가이드 메인 목차
- `guide/*.html` — 17개 가이드 페이지 (getting-started ~ faq)

### Routes (추가)
- `routes/guide.py` — 가이드 페이지 Blueprint (공개, 인증 불필요)

### Static
- `static/js/propsheet/` — Alpine.js 컴포넌트
- `static/css/propsheet/` — 스타일시트
- `static/css/propsheet/guide.css` — 가이드 페이지 전용 스타일
- `static/images/guide/` — 가이드 스크린샷 디렉토리

## 필드 타입

text, number, date, time, single-select, multi-select, checkbox, formula, long-text, attachment, url, system_generated_value (12종)

## 뷰 타입

- **Grid** — 스프레드시트 테이블 뷰
- **Calendar** — 캘린더 뷰 (날짜/시간 필드 기반)

## 권한 체계

`owner` > `editor` > `viewer` (3단계)

## 배포

```bash
# PropSheet 재시작 (포트 5020)
sudo systemctl restart propsheet

# 로그 확인
journalctl -u propsheet -f

# 공유 가상환경
source /home/webapp/goldenrabbit/backend/venv/bin/activate
```

## 홈페이지 매물 API (PropSheet DB 직접 조회)

홈페이지(goldenrabbit.biz) + PropMap의 모든 매물 기능이 PropSheet DB를 직접 조회:

```
GET  /api/propsheet/map-data              → 지도 마커 데이터
GET  /api/propsheet/category-properties   → 카테고리별 매물 (재건축70, 고수익71, 저가72)
GET  /api/propsheet/property-detail?id=   → 매물 상세
POST /api/propsheet/search-map            → 조건 검색
```

> **property-detail API 응답 필드를 변경하면 PropMap의 모든 프론트엔드에 영향.**
> PropMap의 상세보기 UI는 8개 서버 파일에 복사되어 있음 — `propmap/CLAUDE.md`의 "동일 UI를 서빙하는 복수 경로" 표 참조.

### 이미지 서빙
```
DB 대표사진 필드: "파일명.jpg (/uploads/propsheet/39/1069/파일명.jpg)"
  → propsheet.py: regex로 (/uploads/...) 추출 → photo_url
  → 프론트엔드: <img src="/uploads/propsheet/39/1069/파일명.jpg">
  → Nginx: /uploads/propsheet/ → 물리 경로 정적 서빙
```

### 파일 업로드/삭제
```
업로드: POST /database/{db_id}/upload
  → 파일 저장: /uploads/propsheet/{db_id}/{record_id}/{safe_filename}
  → INSERT INTO file_attachments
  → _rebuild_cell_value(): 대표사진 필드 자동 업데이트
  → 용량 제한: 2GB/데이터베이스 (MAX_DB_SIZE in database.py)

삭제: DELETE /database/{db_id}/file/{file_id}
  → 물리 파일 삭제 + DELETE FROM file_attachments
  → _rebuild_cell_value(): 필드 재구성
```

### SNS 공유 (카카오톡 등)
```
https://goldenrabbit.biz/property/recXXX
  → Nginx → Port 5000 (propnet_api.py)
  → PropSheet DB에서 지번주소, 광고, 대표사진 조회
  → OG 메타태그 생성 → /?property=recXXX 리다이렉트
```

## 가이드 페이지

- **URL**: `/propsheet/guide` (메인 목차), `/propsheet/guide/{slug}` (개별 페이지)
- **공개 접근**: 비로그인 사용자도 접근 가능 (인증 데코레이터 없음)
- **17개 페이지**: getting-started, workspaces, databases, fields, records, views, filter-sort-search, formulas, attachments, sharing, members, calendar, csv-export, history, subagents, proptalk, faq
- **스크린샷**: `static/images/guide/` 디렉토리에 저장. 각 페이지에 placeholder로 필요한 스크린샷 위치와 캡처 조건 명시됨
- **다크모드 지원**: 기존 CSS 변수 체계 재활용

## DB 스키마 (주요)

### 단일부동산 (db_id=39, 테이블: `goldenrabbit01_sales_building`)
- `id` (integer): 내부 PK
- `record_id` (varchar): 고유 레코드 ID (recXXX)
- `대표사진`: `"파일명 (/uploads/propsheet/39/{id}/파일명)"` 형식
- `coordinates_lat`, `coordinates_lon`: 좌표 (Proppedia 저장 시 VWorld API로 자동 변환)

### file_attachments
- `database_id`, `record_id`, `field_name`, `file_path` 등 메타데이터

## 주의사항

1. Property Manager(`/backend/property-manager/`)와 같은 Flask 앱 — Blueprint 구조
2. 공유 venv 사용: `/home/webapp/goldenrabbit/backend/venv/`
3. 환경변수: `/home/webapp/goldenrabbit/backend/.env`
4. **psycopg2 % 이스케이프 필수**: DB 필드명에 `%` 포함 (`건폐율(%)`, `용적률(%)` 등). SQL 내 리터럴 `%`는 `%%`로 이스케이프. 미준수 시 `IndexError: tuple index out of range` 발생
5. **Airtable 관련 코드 작성 금지**: `backend/scripts/deprecated/`는 참조 전용, 호출 금지
6. **파일 업로드 경로**: `/uploads/propsheet/{db_id}/{record_id}/파일명` 형식 필수. `file_attachments` 테이블에 메타데이터 등록

## 향후 계획: 멀티테넌트

propnet.kr 마이그레이션 Phase 2에서 agent별 PropSheet 분리 예정:
- `agents` 테이블 생성 (slug → agent_id 매핑)
- `/<agent_slug>/workspaces` 라우트 추가
- 기존 `/propsheet/workspaces` 라우트는 호환성 유지

## Git 보안
- **절대 커밋 금지**: `.env`, DB 비밀번호, API 키, OAuth 시크릿 파일
- 커밋 전 `git diff --cached`로 민감 정보 노출 여부 반드시 확인
- 서버 `.env` 값을 코드/문서에 하드코딩 금지
