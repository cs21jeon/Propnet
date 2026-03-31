# PropNet - 통합 프로젝트

## 개요

PropNet은 부동산 정보 관리 및 조회를 위한 통합 플랫폼입니다.
단일 서버(`175.119.224.71`, 도메인 `goldenrabbit.biz`)에서 운영됩니다.

> **Airtable 완전 제거 완료 (2026-03-26)**: 모든 매물 데이터, 이미지, 건축물대장이 PropSheet DB + 로컬 파일 시스템으로 전환됨. Airtable API, backup 스크립트, backup 디렉토리는 더 이상 사용하지 않음. 새 코드에서 Airtable 관련 코드 작성 금지.

## 서비스 구성

| 서비스 | 로컬 경로 | 플랫폼 | 서버 포트 | systemd 서비스명 | 서버 경로 | Nginx 경로 |
|--------|-----------|--------|-----------|------------------|-----------|------------|
| **Property Manager** | (서버만) | API | 5000 | `property-manager` | `/backend/property-manager/` | `/property-manager`, `/property/*`, `/services` |
| **Propedia** | `propedia/` | Flutter 앱 + 웹(PWA) | 5010 | `proppedia` | `/backend/proppedia/` | `/app/*` |
| **PropSheet** | `propsheet/` | 웹 (HTMX/Alpine.js) | 5020 | `propsheet` | `/backend/propsheet/` | `/propsheet/*` |
| **Proptalk** | `proptalk/` | Flutter 앱 | 5030 | `proptalk` | `/chat_stt/server/` | `/proptalk/*` |
| **PropMap** | `propmap/` | 웹 (정적 HTML) | - | - | `frontend/public/` | `/propmap/*` |

### 서비스별 역할 (포트 구조)

| 포트 | 역할 | Blueprint 등록 위치 |
|------|------|---------------------|
| **5000** (property-manager) | 홈페이지 매물 API, SNS 공유, PropSheet CRUD API | `/backend/property-manager/app.py` |
| **5010** (proppedia) | Propedia 앱 API, 관리자 대시보드 | `/backend/proppedia/app.py` |
| **5020** (propsheet) | PropSheet 웹 UI (사용자 접속) | `/backend/propsheet/app.py` |
| **5030** (proptalk) | Proptalk 음성 채팅 서비스 | `/chat_stt/server/` |

> **코드 공유 구조**: 5010, 5020 모두 `/backend/property-manager/`의 routes/services/templates를 `sys.path`로 임포트하여 재사용. 실제 코드는 property-manager에 있고, 각 서비스의 `app.py`에서 필요한 Blueprint만 선택 등록함.

> 각 서비스의 상세 규칙은 서비스별 CLAUDE.md를 참조:
> - `propedia/CLAUDE.md` - Flutter 빌드, Clean Architecture, 릴리즈 워크플로우
> - `proptalk/CLAUDE.md` - Whisper API 필수 사용, PM2 배포, 결제 시스템
> - `propsheet/CLAUDE.md` - HTMX/Alpine.js, Flask Blueprint, 스프레드시트 SaaS
> - `propmap/CLAUDE.md` - 정적 HTML, 매물지도, Nginx 서빙

## 조직 구조 (AI 에이전트)

```
                 👤 오너 (CEO)
                      │
              🤖 @propnet-coo (COO)
                      │
  ┌────────┬────────┬──┴───┬────────┬────────┬────────┐
  │        │        │      │        │        │        │
개발부   기획부   디자인부  QA부   그로스부  인프라부  CS부
@dev-lead @pm-lead @design @qa-lead @growth  @infra   @cs-lead
  │                        -lead            -lead    -lead
  ├─ @propedia-dev
  ├─ @proptalk-dev
  ├─ @propsheet-dev
  └─ @propmap-dev
```

### 부서별 에이전트

| 부서 | 에이전트 | 역할 |
|------|---------|------|
| **총괄** | `@propnet-coo` | 업무 분배, 부서 간 조율, 진행 추적 |
| **개발부** | `@dev-lead` | 기술 방향, 코드 리뷰, 아키텍처 |
| │ | `@propedia-dev` | Propedia Flutter + 웹 개발 |
| │ | `@proptalk-dev` | Proptalk 음성 채팅 개발 |
| │ | `@propsheet-dev` | PropSheet 스프레드시트 개발 |
| │ | `@propmap-dev` | PropMap 매물지도 개발 |
| **제품기획부** | `@pm-lead` | PRD, 로드맵, 우선순위 |
| **디자인부** | `@design-lead` | UI/UX, 디자인 시스템 |
| **품질관리부** | `@qa-lead` | 테스트, 모니터링, 릴리즈 승인 |
| **그로스부** | `@growth-lead` | 마케팅, SEO, 블로그 |
| **인프라부** | `@infra-lead` | 서버, 배포, DB, Nginx |
| **CS/운영부** | `@cs-lead` | 고객 대응, 가이드, 피드백 수집 |

### 업무 요청 가이드

- **새 기능**: @pm-lead → @design-lead → @dev-lead → @qa-lead → @infra-lead
- **버그/장애**: @qa-lead → @infra-lead → @dev-lead → @qa-lead → @infra-lead
- **블로그/마케팅**: @growth-lead → @design-lead → @growth-lead
- **서버/배포**: @infra-lead 직접 처리

> 각 에이전트의 상세 역할은 `.claude/agents/에이전트명.md` 참조

## 서비스별 작업 규칙

서비스 수정 요청을 받으면 **반드시** 해당 서비스의 CLAUDE.md를 먼저 읽고 작업을 시작하세요:
- `propedia/` 작업 → `propedia/CLAUDE.md` 읽기
- `proptalk/` 작업 → `proptalk/CLAUDE.md` 읽기
- `propsheet/` 작업 → `propsheet/CLAUDE.md` 읽기
- `propmap/` 작업 → `propmap/CLAUDE.md` 읽기

서버 파일 접근은 MCP(goldenrabbit-server)를 통해 수행합니다.

## 서버 정보

- **호스트**: `root@175.119.224.71` (Cafe24)
- **도메인**: `https://goldenrabbit.biz`
- **SSH**: `ssh root@175.119.224.71`
- **MCP**: `.mcp.json`으로 서버 파일시스템 접근

### 서비스 관리

```bash
# 서비스 재시작
sudo systemctl restart goldenrabbit-api  # API Server (:8000)
sudo systemctl restart property-manager  # Property Manager (:5000)
sudo systemctl restart proppedia         # Proppedia (:5010)
sudo systemctl restart propsheet         # PropSheet (:5020)
sudo systemctl restart proptalk          # Proptalk (:5030)

# 로그 확인
journalctl -u goldenrabbit-api -f
journalctl -u property-manager -f
journalctl -u proppedia -f
journalctl -u propsheet -f
journalctl -u proptalk -f
```

### 공유 리소스

- **가상환경**: `/home/webapp/goldenrabbit/backend/venv/` (PropNet, Proppedia, PropSheet 공유)
- **Proptalk 전용 venv**: `/home/webapp/goldenrabbit/chat_stt/server/venv/`
- **환경변수**: `/home/webapp/goldenrabbit/backend/.env`
- **DB**: PostgreSQL `goldenrabbit_db` (공유) + `voiceroom` (Proptalk 전용)
- **Nginx 설정**: `/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf`

## CRITICAL 규칙

1. **Proptalk Whisper**: 반드시 OpenAI Whisper API 사용. 로컬 whisper 모델 절대 금지 (서버 RAM 956MB)
2. **서버 배포 후 반드시 서비스 재시작**: `systemctl restart <서비스명>`
3. **Nginx 수정 후**: `sudo nginx -t && sudo systemctl reload nginx`
4. **Nginx config 동기화**: `config/nginx/goldenrabbit.conf` 수정 시 반드시 `/etc/nginx/sites-enabled/goldenrabbit`에도 반영
5. **Airtable 완전 제거됨**: 새 코드에서 Airtable 관련 코드 작성 금지. `backend/scripts/deprecated/`는 참조 전용, 호출 금지
6. **psycopg2 % 이스케이프**: PropSheet DB 필드명에 `%` 포함 (`건폐율(%)`, `용적률(%)` 등). SQL 내 리터럴 `%`는 `%%`로 이스케이프 필수 (미준수 시 `IndexError` 발생)
7. **파일 업로드 경로 규칙**: `/uploads/propsheet/{db_id}/{record_id}/파일명` 형식. `file_attachments` 테이블에 메타데이터 필수 등록
8. **Git 커밋/푸시 시 보안 필수 확인**:
   - 절대 커밋 금지 파일: `.env`, `key.properties`, `*.jks`, `*.keystore`, OAuth 토큰/시크릿 파일
   - 커밋 전 `git diff --cached`로 API 키, 비밀번호, 토큰이 포함되지 않았는지 반드시 확인
   - **신규 파일(A)도 반드시 검사**: `git diff --cached --diff-filter=A`로 새로 추가되는 파일 내용도 확인
   - 서버 경로의 `.env` 내용(API 키, DB 비밀번호 등)을 코드나 문서에 하드코딩 금지
   - 각 서비스 `.gitignore`에 민감 파일 패턴이 포함되어 있는지 주기적 확인
   - 서버 리포(`goldenrabbit`)에 pre-commit hook 설치됨 — 하드코딩 비밀번호/API 키 자동 차단
9. **비밀번호/API 키는 반드시 환경변수로**: DB 접속, 외부 API 키 등은 `os.environ.get()` 사용. 절대 소스코드에 직접 작성 금지. `.env` 파일에서 로드
10. **ID 체계 매핑 주의**: `app_users.id` ≠ `propnet_users.id` ≠ `voiceroom.users.id`. JWT의 user_id를 다른 테이블의 ID로 직접 사용 금지. 반드시 `service_user_links`를 통해 변환
11. **서버 코드 수정 전 변수명 확인 필수**: Blueprint, 함수명, 클래스명 등을 grep으로 반드시 확인 후 사용. 추정하여 코드 작성 금지
12. **Propedia 웹 = 정적 HTML**: Propedia 웹페이지는 `/app/*.html` 정적 파일. `flutter build web` 사용 금지. 앱 수정 시 HTML 웹도 함께 수정
13. **서비스 수정 후 기동 검증 필수**: 재시작 후 `journalctl -u <서비스명> -n 20`으로 에러 확인 + `curl`로 HTTP 응답 코드 확인. 에러 있으면 즉시 롤백
14. **탈퇴/비활성 유저 재가입 고려**: 회원탈퇴(is_active=FALSE) 후 동일 계정 재로그인 시 재활성화 + 동의 초기화 로직 필수
15. **Google OAuth 유저 특수 케이스**: Google 로그인 유저는 비밀번호가 없음. 비밀번호 요구 로직에 provider 체크 필수

## Git 구조

```
Propnet/.git/              ← 이 리포 (통합 설정/문서 관리)
Propnet/propedia/.git/     ← 독립 GitHub 리포 (cs21jeon/propedia)
Propnet/proptalk/.git/     ← 독립 GitHub 리포 (cs21jeon/Proptalk)
```

- Propnet 루트 git: 공유 설정/문서만 관리 (propedia/, proptalk/은 .gitignore로 제외)
- 서비스별 코드 변경: 각 서비스 디렉토리에서 독립적으로 commit/push

## 데이터 흐름 (홈페이지)

```
index.html → /propsheet/api/propsheet/category-properties → PropSheet DB
index.html → /propsheet/api/propsheet/property-detail → PropSheet DB
index.html → /propsheet/api/propsheet/search-map → PropSheet DB
map.html   → /propsheet/api/propsheet/map-data → PropSheet DB
```

### SNS 공유 (카카오톡 등)
```
https://goldenrabbit.biz/property/recXXX
  → Nginx → Port 5000 (propnet_api.py)
  → PropSheet DB에서 지번주소, 광고, 대표사진 조회
  → OG 메타태그 생성 → /?property=recXXX 리다이렉트
```

## 향후 계획

- **PropMap**: `/propmap/{agent_slug}` 형태의 agent별 매물지도 서비스 구축
- **도메인 마이그레이션**: `propnet.kr` 도메인 추가 예정
- **URL 변경**: `goldenrabbit.biz/` → `/propmap/goldenrabbit/` (301 리다이렉트 필요)

## 블로그

- **네이버 블로그**: blog.naver.com/propnet
- **문체 가이드**: `propedia/blog_sample/my-writing-style.md`
- **발행 도구**: Playwright MCP
