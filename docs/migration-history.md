# PropNet 마이그레이션 이력

## 1차 마이그레이션: 로컬 폴더 통합 (2026-03-22)

### 배경
- 기존: `C:\Users\ant19\projects\` 하위에 5개 독립 폴더로 운영
  - `Propnet/`, `propedia/`, `Proptalk/`, `Propsheet/`, `Propmap/`
- 각 폴더에서 별도로 Claude Code를 실행하여 개발
- 서비스 간 통합 관리 필요성 대두

### 변경 내용

#### Phase 1: 폴더 이동
| 원본 경로 | 이동 경로 | 비고 |
|-----------|-----------|------|
| `projects/propedia/` | `Propnet/propedia/` | .git 포함 이동, GitHub 리포 유지 (cs21jeon/Proppedia) |
| `projects/Proptalk/` | `Propnet/proptalk/` | .git 포함 이동, GitHub 리포 유지 (cs21jeon/Proptalk) |
| `projects/Propsheet/` | `Propnet/propsheet/` | git 없음, temp/tmp 216개 스크립트 그대로 유지 |
| `projects/Propmap/` | `Propnet/propmap/` | 로고 이미지 3개만 존재 |
| `projects/Propnet/` | (루트로 유지) | assets/, docs/, 사업자 서류 유지 |

- Shorts 서비스는 제외 (서버에만 존재)
- 각 서비스의 `.mcp.json`, `.claude/` 제거 (루트 통합본 사용)

#### Phase 2: 통합 설정 파일 생성
| 파일 | 내용 |
|------|------|
| `.mcp.json` | SSH(goldenrabbit-server) + Playwright + GitHub MCP |
| `.claude/settings.local.json` | Flutter, SSH, 기타 permissions 통합 |
| `CLAUDE.md` | 전체 서비스 아키텍처 가이드 |
| `.gitignore` | propedia/, proptalk/ 독립 git 제외, 시크릿 파일 제외, .mcp.json 제외 |

#### Phase 3: Git 초기화
- `Propnet/` 루트에 새 git 초기화
- 초기 커밋: 279 files, 26434 insertions
- GitHub 리포 생성 예정 (cs21jeon/Propnet, private)
- Git 구조:
  - `Propnet/.git/` → 통합 설정/문서 관리
  - `Propnet/propedia/.git/` → 독립 (cs21jeon/Proppedia)
  - `Propnet/proptalk/.git/` → 독립 (cs21jeon/Proptalk)

### 서버 상태 (변경 없음)
이번 마이그레이션은 로컬만 변경. 서버 구조는 그대로 유지:

```
175.119.224.71 (goldenrabbit.biz)
├── :5000  PropNet API + Property Manager  → /backend/property-manager/
├── :5010  Proppedia 앱 API               → /backend/proppedia/
├── :5020  PropSheet                      → /backend/propsheet/
├── :5030  Proptalk / VoiceRoom           → /chat_stt/server/
├── :5040  Shorts                         → /backend/shorts_automation/
└── :8000  API Server (VWorld, 블로그, SNS) → /backend/api/
```

### Nginx URL 라우팅 (현재 상태, 변경 없음)
```
/                          → 정적 파일 (frontend/public/index.html) = 금토끼부동산
/app/*                     → 정적 파일 (frontend/public/app/) = Proppedia PWA
/app/api/*                 → :5010 Proppedia API
/proppedia/                → 정적 파일 (frontend/public/proppedia/) = Proppedia 랜딩
/propsheet/*               → :5020 PropSheet
/proptalk/*                → :5030 Proptalk
/voiceroom/*               → :5030 Proptalk WebSocket/API
/api/*                     → :5000 PropNet API
/shorts/*                  → :5040 Shorts
```

---

## 1.5차 마이그레이션: 홈페이지 Airtable → PropSheet DB 전환 (2026-03-25)

### 배경
- 기존 홈페이지 매물 기능이 Airtable 백업 JSON 및 Airtable API에 의존
- 매물 지도: 매일 새벽 크론으로 Airtable 백업 JSON → 정적 HTML 생성
- 매물 검색/상세: Airtable 백업 JSON 파일 스캔 또는 Airtable API 직접 호출
- PropSheet DB가 안정화되어 실시간 DB 조회로 전환

### 변경 내용

| 기능 | 변경 전 | 변경 후 |
|------|---------|---------|
| 매물 지도 | `airtable_map.html` (크론 정적 HTML) | `map.html` (PropSheet DB 실시간, 카카오맵 SDK) |
| 매물 검색 | `POST /property-manager/api/search-map` | `POST /propsheet/api/propsheet/search-map` |
| 매물 상세 | `GET /api/property-detail?id=` (Airtable API) | `GET /propsheet/api/propsheet/property-detail?id=` (PropSheet DB) |
| 공유 링크 | `/property/{recordId}` (별도 페이지) | `/?property={recordId}` (홈페이지 모달) |

### 추가된 PropSheet API

- `GET /api/propsheet/map-data` — 지도 마커 데이터
- `POST /api/propsheet/search-map` — 조건 검색
- `GET /api/propsheet/property-detail` — 매물 상세

### 미완료

- [ ] map.html 상세 모달 → 부모 `index.html` 모달 통일 (`parent.postMessage`)
- [ ] 워크스페이스별 지도 구조

### 서버 상태
- PropSheet API 엔드포인트 추가 (`propsheet.py`)
- 프론트엔드 정적 파일만 변경 → Nginx/Flask 재시작 불필요
- 보안: `.gitignore` 보완 (`*.bak`, `uploads/`, `.openai_credit.json`, `*.pre-migration`)

---

## 1.7차 마이그레이션: Airtable 완전 제거 (2026-03-26)

### 배경
- 1.5차에서 홈페이지 DB 전환 후, 나머지 Airtable 의존성도 모두 제거
- SNS 공유, 이미지, 건축물대장 등 모든 기능이 PropSheet DB + 로컬 파일로 전환

### 변경 내용

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| SNS 공유 (`/property/{id}`) | Airtable API 조회 | PropSheet DB 조회 |
| 대표사진/건축물대장 | Airtable Attachment URL | `/uploads/propsheet/{db_id}/{record_id}/파일명` |
| 추천매물 카테고리 | Airtable 백업 JSON | PropSheet DB (재건축70, 고수익71, 저가72) |
| property-detail.html | 별도 상세 페이지 | 삭제 (index.html 모달로 통합) |
| backup 스크립트 | 활성 (cron) | `deprecated/`로 이동, cron 비활성화 |

### 중지된 Cron Jobs
- `airtable_backup.py` — Airtable → JSON 백업 (DISABLED)
- `generate_map.py` — JSON → 지도 HTML 생성 (DISABLED)

### 추가된 파일 시스템
- `/uploads/propsheet/` — 모든 첨부파일 저장소
- `file_attachments` 테이블 — 파일 메타데이터 관리

### 서버 상태
- `backend/scripts/deprecated/` — Airtable 관련 스크립트 격리 (참조 전용, 호출 금지)
- Airtable API 키는 `.env`에 남아있으나 사용하지 않음
- 서비스 재시작: `property-manager`, `goldenrabbit-api`

---

## 1.8차 마이그레이션: 상담신청 Airtable → PropSheet DB 전환 (2026-04-01)

### 배경
- 1.7차에서 매물 데이터는 모두 PropSheet DB로 전환 완료
- 그러나 상담신청(`/api/submit-inquiry`)만 여전히 Airtable API 사용 중이었음
- 이번에 상담 문의도 PropSheet DB로 전환하여 Airtable 의존성 완전 제거

### 변경 내용

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 상담 데이터 저장 | Airtable API POST | PropSheet DB INSERT (`inquiry` 테이블, db_id=11) |
| 이메일발송 상태 | Airtable API PATCH | PropSheet DB UPDATE |
| 이메일 발송 | Gmail SMTP (변경 없음) | Gmail SMTP (변경 없음) |
| 프론트엔드 | 변경 없음 | 변경 없음 |

### 수정 파일
- `/backend/property-manager/routes/propnet_api.py`
  - `submit_inquiry()`: Airtable API → `get_db_connection()` + `ensure_unique_record_id()` 사용한 DB INSERT
  - `send_email_and_update_airtable()` → `send_email_and_update_db()`: Airtable PATCH → DB UPDATE
  - `send_consultation_email()`: 변경 없음 (SMTP만 사용)

### DB 구조
- 워크스페이스: 금토끼부동산 (workspace_id=11, slug=goldenrabbit)
- 데이터베이스: 상담 문의 (db_id=11, slug=inquiry, table=inquiry)
- 기존 Airtable 데이터 3건 batch_import.py로 마이그레이션 완료

### 제거된 환경변수 의존성
- `AIRTABLE_INQUIRY_KEY` — 더 이상 사용하지 않음
- `AIRTABLE_INQUIRY_BASE_ID` — 더 이상 사용하지 않음
- `AIRTABLE_INQUIRY_TABLE_ID` — 더 이상 사용하지 않음

### 서버 상태
- `property-manager` 서비스 재시작 완료
- PropSheet UI에서 상담 문의 내역 조회/관리 가능

---

## 2차 마이그레이션 예정: PropMap + URL 변경

### 계획
- `goldenrabbit.biz/` → `goldenrabbit.biz/propmap/goldenrabbit/` 로 변경
- `goldenrabbit.biz/propmap/` → 통합 매물지도 (전체 agent)
- `goldenrabbit.biz/propmap/{agent_slug}` → 개별 agent 매물지도

### 필요 작업
- [ ] Propmap 정적 HTML 페이지 개발 (현재 index.html 48KB 기반)
- [ ] Nginx에 `/propmap/` 라우팅 추가
- [ ] 기존 `/` → `/propmap/goldenrabbit/` 301 리다이렉트 설정
- [ ] sitemap.xml, robots.txt 업데이트
- [ ] 네이버 서치어드바이저 URL 변경 등록
- [ ] 구글 서치콘솔 URL 변경 등록

---

## 3차 마이그레이션 예정: propnet.kr 도메인

### 계획
- `propnet.kr` 도메인 구매 후 적용
- `propnet.kr/propmap` → 전체 agent 통합 매물지도
- `propnet.kr/propmap/{agent_slug}` → 개별 agent 매물지도
- 기존 `goldenrabbit.biz`는 당분간 병행 운영 후 리다이렉트

### 필요 작업
- [ ] propnet.kr 도메인 구매 및 DNS 설정
- [ ] Nginx: `server_name`에 propnet.kr 추가 (멀티도메인)
- [ ] SSL: propnet.kr용 Let's Encrypt 인증서 발급
  ```bash
  sudo certbot --nginx -d propnet.kr -d www.propnet.kr
  ```
- [ ] Flutter 앱 `api_client.dart`: baseUrl 변경 또는 분기
  - 현재: `static const String baseUrl = 'https://goldenrabbit.biz';`
  - 변경: `https://propnet.kr` 또는 환경변수 분기
- [ ] Google OAuth: redirect URI에 propnet.kr 추가
  - Google Cloud Console → OAuth 2.0 Client IDs → Authorized redirect URIs
  - 현재 등록된 Client IDs:
    - serverClientId (모바일): `846392940969-a7k3...`
    - Web Client ID: `846392940969-sv29...`
    - Propsheet Web: `846392940969-h70f...`
- [ ] Google Play Console:
  - 개인정보처리방침 URL 변경
  - 앱 링크(App Links) 도메인 변경
- [ ] 네이버 블로그 프로필 URL 업데이트
- [ ] sitemap.xml, robots.txt 도메인 변경
- [ ] goldenrabbit.biz → propnet.kr 301 리다이렉트 설정 (SEO 보존)
- [ ] CORS 설정 업데이트 (Flask 서버들)

### 주의사항
- 도메인 변경 시 Google 인덱스 반영까지 수주 소요
- 네이버 검색 등록은 별도 신청 필요
- 앱 업데이트 없이 baseUrl 변경하려면 remote config 또는 서버 리다이렉트 활용
- OAuth redirect URI 변경 전에 새 도메인 SSL 인증 완료 필수

---

## 5차: PropSheet 관리비 필드 + Formula-Trigger 동기화 아키텍처 (2026-04-04)

### 배경
- 공인중개사법 시행령에 따라 관리비 세부내역 표시 의무 (2024.4.1 시행)
- PropSheet의 formula 필드와 PostgreSQL 트리거가 이중관리 → 불일치 문제

### 1. 관리비 관련 필드 추가

| DB | 추가 필드 | 타입 | 비고 |
|----|----------|------|------|
| 단일부동산(39) | `매물종류` | single-select | 주택/비주택/토지 (주용도 기반 자동분류) |
| 단일(39) | `관리비` | number | 주택 310건에 9만원 기본값 |
| 단일(39)/집합(38)/부분(43) | `부과방식` | single-select | 정액/확인불가/평균관리비 |
| 단일(39)/집합(38)/부분(43) | `포함항목` | multi-select | 공용/전기/가스/수도/난방/인터넷/TV/기타 |
| 단일(39)/집합(38)/부분(43) | `부과사유` | single-select | 5개 옵션 |

- 광고(자동완성) 트리거에 관리비 블록 추가 (두칸 들여쓰기)
- formula와 트리거 양쪽 동기화 완료

### 2. Formula-Trigger 동기화 아키텍처

**이전 구조 (문제)**:
- formula: SELECT 시에만 계산 (DB 미저장)
- trigger: INSERT/UPDATE 시 실제 컬럼에 저장
- 웹에서 formula 수정해도 trigger 변경 안 됨 → 불일치

**변경 후 구조 (Single Source of Truth)**:
```
웹에서 formula 수정 → 저장
  ① field_definitions.formula 저장
  ② formula_previous에 이전 값 보관 (Undo)
  ③ formula_history에 이력 기록
  ④ validate_formula()로 유효성 검증
  ⑤ regenerate_trigger()로 트리거 자동 재생성
  ⑥ recalculate_all_records()로 전체 레코드 재계산
```

**신규 파일/테이블**:
- `services/formula_trigger_service.py`: formula→trigger 변환/재생성/재계산 서비스
- `formula_history` 테이블: formula 변경 이력
- `field_definitions.formula_previous` 컬럼: 직전 수식 (Undo용)

**수정된 파일**:
- `routes/database.py`: update_field_definition() — formula 저장 시 트리거 동기화
- `services/schema_service.py`: formula_previous를 프론트엔드에 전달
- `templates/propsheet/database_list.html`: 되돌리기 버튼 추가
- `static/js/propsheet/database_list.js`: revertFormula() + 저장 결과 표시 + 컬럼 순서 뷰 DB 저장

**트리거 전환**:
| 이전 트리거 | 새 트리거 |
|-----------|----------|
| `format_ad_text()` | `trig_formula_39_광고_자동완성_` |
| `format_ad_text_multi()` | `trig_formula_38_광고_자동완성_` |
| `format_ad_text_partial()` | `trig_formula_43_광고_자동완성_` |

### 3. 중복 파일 첨부 정리
- DB 39 단일부동산에서 건축물대장/대표사진 중복 331건 삭제
- 159개 매물의 셀 값 재구성

### 4. 컬럼 순서 저장 버그 수정
- 이전: 드래그 순서가 localStorage에만 저장 → 새로고침 시 뷰 DB 순서로 원복
- 수정: saveColumnOrder()에서 뷰 DB에도 동시 저장

### 백업
- `/home/webapp/goldenrabbit/backend/backups/20260404/` 에 전체 백업 보관

---

## 6차: 데이터 보안 강화 + 자동 백업 체계 구축 (2026-04-04)

### 배경
- 매물 데이터에 소유주 개인정보(성명, 주소, 생년월일, 연락처) 포함
- 개인정보보호법상 생년월일·연락처는 암호화 저장 의무
- 서버 단일 구성으로 데이터 유실 리스크 존재
- 개인정보처리방침에 소유주 정보 수집·위탁 관계 미명시

### 1. 소유주 개인정보 필드 암호화

**암호화 대상 필드**:
| 필드 | 변경 전 타입 | 변경 후 |
|------|-------------|---------|
| `소유자생년월일` | BIGINT | TEXT (Fernet 암호화, `ENC:` 접두사) |
| `소유주연락처` | VARCHAR(30~100) | TEXT (Fernet 암호화, `ENC:` 접두사) |

**신규 파일**:
- `backend/property-manager/utils/encryption.py`: Fernet 암호화/복호화 모듈
- `backend/property-manager/utils/__init__.py`: 패키지 init
- `backend/scripts/migration/encrypt_existing_data.py`: 기존 데이터 마이그레이션 (롤백 지원)

**수정된 파일**:
- `services/database_service.py`: 저장 시 encrypt, 조회 시 decrypt
- `routes/database.py`: 인라인 수정, CSV 내보내기, 되돌리기에 암복호화 적용
- `services/propsheet_save_service.py`: INSERT/UPDATE 시 암호화
- `requirements.txt`: cryptography>=41.0.0 추가

**설계 결정**:
- Fernet (AES-CBC + HMAC-SHA256) 사용 — 간편하고 인증된 암호화
- `ENC:` 접두사로 암호화 여부 판별 → 마이그레이션 중 평문/암호문 공존 가능
- 암호화 키: `.env`의 `FIELD_ENCRYPTION_KEY`에 보관 (DB와 분리)
- audit_log에는 평문 저장 (사용성 우선)
- 홈페이지 공개 API는 개인정보 필드 미노출 → 복호화 불필요

### 2. 서버 자동 백업 체계

**매일 새벽 3시 cron 실행**:
1. `pg_dumpall` → `backups/daily/db_all_YYYYMMDD.sql.gz` (약 2.6MB)
2. `/uploads/` tar.gz → `backups/daily/uploads_YYYYMMDD.tar.gz` (약 832MB)
3. rclone으로 Google Drive `서버백업/YYYYMMDD/` 폴더에 전송
4. 서버 로컬 3일치, Google Drive 14일치 보관

**신규 파일**:
- `scripts/daily_backup.sh`: 일일 자동 백업 스크립트
- `scripts/setup_rclone_gdrive.sh`: rclone 설치/설정 안내
- `scripts/BACKUP_RESTORE_GUIDE.md`: 복원 가이드

**인프라 설정**:
- rclone 설치 + Google Drive 리모트(`gdrive`) 연동 완료
- crontab 등록: `0 3 * * * daily_backup.sh`
- `.env` EMAIL_PASSWORD 따옴표 추가 (source 시 공백 파싱 오류 수정)
- `pg_dumpall` → `sudo -u postgres pg_dumpall` (superuser 권한 필요)

### 3. 개인정보처리방침 / 이용약관 업데이트

**개인정보처리방침** (privacy-policy.html):
- 제1조: PropSheet 수집항목에 `매물 소유자 정보(성명, 주소, 생년월일, 연락처)` 추가
- 제7조 신설: 개인정보 처리 위탁 (중개사=수집주체, PropNet=수탁자)
- 제8조: 안전성 확보 조치 — AES-256 암호화, 감사 로그, 정기 백업 명시
- 시행일: 2026-04-04

**이용약관** (terms-of-service.html):
- 제4조: PropSheet 기능에 `매물 소유자 정보 관리` 추가
- 제8조: 중개사의 소유자 정보 적법 수집 책임 조항 신설
- 제9조: 회사의 소유자 정보 암호화 저장 의무 추가
- 시행일: 2026-04-04

### 서버 상태
- `property-manager`, `propsheet`, `proppedia` 재시작 완료
- 암호화 마이그레이션 완료 (backup 테이블: `encryption_migration_backup`)
- 롤백 명령: `python scripts/migration/encrypt_existing_data.py --rollback`
