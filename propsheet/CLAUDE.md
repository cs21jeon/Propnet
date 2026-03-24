# PropSheet - 스프레드시트 서비스

## 개요

PropSheet은 Airtable 대안 스프레드시트 SaaS입니다. 부동산 데이터 관리에 특화된 웹 기반 스프레드시트로, 워크스페이스/데이터베이스 구조를 갖습니다.

- **URL**: `https://goldenrabbit.biz/propsheet/`
- **포트**: 5020
- **코드 위치**: 서버 `/home/webapp/goldenrabbit/backend/property-manager/` (로컬에 소스 없음)
- **파일 접근**: MCP(goldenrabbit-server) 사용

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
- `routes/propsheet.py` — 워크스페이스/DB CRUD, 복제, 권한
- `routes/database.py` — DB 레코드 CRUD (낙관적 잠금)
- `routes/oauth.py` — Google OAuth 블루프린트
- `routes/workspace_members.py` — 멤버 관리 API

### Services
- `services/workspace_service.py` — 워크스페이스 관리 + DB 뷰 복제
- `services/database_service.py` — PostgreSQL 동적 CRUD
- `services/formula_service.py` — Airtable 수식 → SQL 변환
- `services/schema_service.py` — 필드 정의/스키마 관리
- `services/view_service.py` — 뷰 CRUD (grid/calendar)
- `services/permission_service.py` — 권한 데코레이터 (owner/editor/viewer)
- `services/google_auth_service.py` — Google OAuth 플로우
- `services/share_service.py` — DB 공유 토큰 CRUD

### Templates
`templates/propsheet/` 디렉토리:
- `database_list.html` — 메인 스프레드시트 UI (필터/정렬/인라인 편집)
- `calendar.html` — 캘린더 뷰 (월/주/일/년 4모드)
- `workspaces.html` — 워크스페이스 목록
- `share.html` — DB 공유 미리보기/복제
- `landing.html` — 랜딩 페이지

### Static
- `static/js/propsheet/` — Alpine.js 컴포넌트
- `static/css/propsheet/` — 스타일시트

## 필드 타입

text, number, date, time, single-select, multi-select, checkbox, formula, long-text, attachment, url, system_generated_value (12종)

## 뷰 타입

- **Grid** — 스프레드시트 테이블 뷰
- **Calendar** — 캘린더 뷰 (날짜/시간 필드 기반)

## 권한 체계

`owner` > `editor` > `viewer` (3단계)

## 배포

```bash
# 서비스 재시작
sudo systemctl restart propsheet

# 로그 확인
journalctl -u propsheet -f

# 공유 가상환경
source /home/webapp/goldenrabbit/backend/venv/bin/activate
```

## 주의사항

1. Property Manager(`/backend/property-manager/`)와 같은 Flask 앱 — Blueprint 구조
2. 공유 venv 사용: `/home/webapp/goldenrabbit/backend/venv/`
3. 환경변수: `/home/webapp/goldenrabbit/backend/.env`
4. Airtable 동기화: 매일 04:00 AM 자동 실행 (`scripts/airtable_to_propsheet_sync.py`)
