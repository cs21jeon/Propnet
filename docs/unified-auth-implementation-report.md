# PropNet 통합 인증 시스템 구현 보고서

**작성일**: 2026-03-31
**플랜 승인일**: 2026-03-30
**구현 기간**: 2026-03-30 ~ 2026-03-31

---

## 1. 인프라부 (@infra-lead)

### 진행 내용

| 작업 | 상세 |
|------|------|
| **DB 테이블 생성** | `propnet_users`, `service_user_links`, `propnet_consents`, `agent_requests`, `subagent_invitations` (goldenrabbit_db) |
| **기존 테이블 ALTER** | `app_users`에 `propnet_user_id` 추가, `voiceroom.users`에 `propnet_user_id` + 인덱스 추가 |
| **데이터 마이그레이션** | 3개 서비스 유저 60명 통합, service_user_links 67건, Proptalk 동의 이력 6건 이관 |
| **환경변수 추가** | `PROPNET_JWT_SECRET` (64자 hex) → backend/.env + chat_stt/server/.env 양쪽 |
| **Nginx 라우팅** | `/legal/*` → 정적 파일, `/admin/*` → 5010 포트. 두 설정 파일 동기화 |
| **서비스 재시작** | property-manager, proppedia, propsheet, proptalk 4개 서비스 일괄 재시작 |
| **admin_settings 테이블** | 대시보드용 관리자 설정 테이블 생성 |

### 검증 완료 항목

- 4개 서비스 모두 정상 기동 (journalctl 로그에 에러 없음)
- `propnet_auth loaded successfully` 로그 출력 확인 (property-manager, propsheet)
- API 기본 응답: `/app/api/auth/me` → 401, `/propsheet/` → 200, `/proptalk/` → 200
- Nginx `/legal/*` 5개 URL 모두 HTTP 200
- Nginx `/admin/*` 라우팅 정상

### 우려 사항

| 우려 | 상세 | 중점 검증 |
|------|------|----------|
| **DB 연결 풀 부족** | propnet_auth가 자체 ThreadedConnectionPool(min=2, max=5)을 생성. 기존 각 서비스의 DB 연결과 합산하면 서버 RAM(956MB)에서 PostgreSQL 커넥션 수 초과 가능 | `SELECT count(*) FROM pg_stat_activity`로 현재 연결 수 모니터링. max_connections 설정 확인 |
| **voiceroom DB 환경변수 충돌** | Proptalk `.env`의 `DB_NAME=voiceroom`이 propnet_auth의 goldenrabbit_db 연결과 충돌. import 시 환경변수 임시 교체 패턴으로 해결했지만 불안정 | Proptalk 서비스 장시간 운영 후 DB 연결 정상 여부 확인 |
| **마이그레이션 누락** | `admin@goldenrabbit.co.kr` (web_users id=1)은 google_id 없이 등록됨. 이메일/비밀번호 전용 유저 4명도 google_id 없음 | 이들이 Google 로그인 시 정상 연동되는지 확인 |

---

## 2. 개발부 (@dev-lead)

### 진행 내용

| 작업 | 상세 |
|------|------|
| **propnet_auth 라이브러리** | 10개 Python 모듈, ~1,300줄. `/backend/shared/propnet_auth/` |
| **아키텍처 설계** | 공유 라이브러리 방식 (새 프로세스 없음), 각 서비스가 import하여 사용 |
| **JWT 통합 전략** | 다중 secret fallback (PROPNET_JWT_SECRET → JWT_SECRET_KEY → JWT_SECRET), sub/user_id 호환 |
| **OAuth 이중 플로우** | `verify_id_token()` (앱 id_token 검증) + `process_userinfo()` (웹 code flow) |

### 검증 완료 항목

- 모듈 import 테스트 PASSED
- JWT round-trip (생성→검증) PASSED
- DB 연결 (propnet_users 60행 조회) PASSED
- `get_all_secrets()` 2개 시크릿 확인
- `get_required_consents(services=["proptalk"])` 4개 항목 정상 반환

### 우려 사항

| 우려 | 상세 | 중점 검증 |
|------|------|----------|
| **다중 secret fallback 보안** | 기존 JWT_SECRET_KEY/JWT_SECRET도 계속 유효하므로, 이전 secret이 유출되었을 경우 위험 | 전환 기간 후 기존 secret fallback 제거 일정 수립 |
| **Lazy DB pool 초기화** | 첫 쿼리 시점에 커넥션 풀 생성. 서비스 시작 직후 첫 요청이 느릴 수 있음 | 서비스 재시작 후 첫 로그인 응답 시간 측정 |
| **voiceroom 별도 연결** | `ensure_service_account("proptalk")`에서만 voiceroom DB 직접 연결. 풀 미사용이라 매번 새 연결 생성 | Proptalk 가입이 빈번해지면 voiceroom 연결 풀 추가 필요 |

---

## 3. Propedia 개발 (@propedia-dev)

### 진행 내용

#### 백엔드 (서버)
| 작업 | 상세 |
|------|------|
| **app_auth.py 수정** | Google 로그인에 propnet_auth 통합, 통합 JWT(access 24h + refresh 30d) 발급 |
| **동의 API 3개 추가** | POST/GET `/app/api/auth/consent`, POST `/consent/withdraw` |
| **login_required 수정** | propnet_auth.verify_token() 사용 + 기존 JWT fallback |
| **응답 포맷 호환** | `access_token` + `token` 키 동시 반환 |

#### Flutter 앱
| 작업 | 상세 |
|------|------|
| **consent_screen.dart** | 신규 생성. 서버 missing_consents 기반 동적 동의 화면 |
| **user_type_screen.dart** | 신규 생성. 신규 유저 대상 일반/Agent 선택 |
| **agent_register_screen.dart** | 신규 생성. Agent 가입 신청 폼 (상호/slug/등록증) |
| **auth_provider.dart** | AuthStatus에 consentRequired, userTypeRequired 추가. submitConsent(), selectUserType(), completeAgentRequest() |
| **auth_api.dart** | loginWithGoogleRaw(), recordConsent(), checkSlug(), submitAgentRequest() 추가 |
| **auth_repository.dart** | LoginResult 클래스 (consentRequired, isNewUser 포함) |
| **app_router.dart** | /consent, /user-type, /agent-register 라우트 + 리다이렉트 로직 |

### 검증 완료 항목

- `dart analyze` → **No issues found**
- `flutter analyze` → **No issues found** (agent_register_screen.dart, app_router.dart)
- 서버 재시작 후 `/app/api/auth/me` → 401 정상 응답

### 우려 사항

| 우려 | 상세 | 중점 검증 |
|------|------|----------|
| **앱 빌드 미완료** | Flutter 코드 수정만 완료, APK/AAB 빌드 및 Play Store 배포 미진행. 현재 배포된 앱은 동의 화면이 없는 구버전 | `flutter build apk --release` 빌드 성공 여부, 실제 기기 테스트 |
| **기존 앱 사용자 호환** | 구버전 앱의 JWT(user_id payload)가 새 서버에서도 인증되는지 | 구버전 앱 설치 상태에서 기존 토큰으로 API 호출 테스트 |
| **Google 로그인 후 동의 플로우** | 로그인 → consent_required 응답 → 동의 화면 → 제출 → 홈 전체 플로우가 앱에서 끊김 없이 동작하는지 | 실기기에서 Google 로그인 → 동의 → 홈 도달 E2E 테스트 |
| **register_screen.dart 기존 동의** | 기존 이메일/비밀번호 회원가입의 체크박스 동의가 아직 남아있음. 이중 동의 UI 혼란 가능 | register_screen의 기존 동의 체크박스 제거 또는 통합 동의 화면으로 리다이렉트 |
| **refresh_token 미존재 → 존재 전환** | 기존 앱은 refresh_token을 받지 못했는데, 새 서버는 발급함. 기존 앱이 refresh_token을 무시하고 정상 동작하는지 | 구버전 앱의 AuthResponse DTO가 refresh_token을 optional로 처리하는지 확인 |
| **file_picker 파일 경로** | Android에서 file_picker로 선택한 파일의 경로가 multipart 업로드에 유효한지 | 실기기에서 등록증 이미지 선택 → 업로드 테스트 |

---

## 4. Proptalk 개발 (@proptalk-dev)

### 진행 내용

#### 백엔드 (서버)
| 작업 | 상세 |
|------|------|
| **auth.py 수정** | 330줄 → 547줄. propnet_auth 통합, 통합 JWT, consent API를 propnet_consents + user_consents 병행 기록 |
| **환경변수 추가** | DB_PASSWORD, VOICEROOM_DB_NAME/USER/PASSWORD 추가 |
| **refresh 엔드포인트** | POST `/api/auth/refresh` 추가 |

#### Flutter 앱
| 작업 | 상세 |
|------|------|
| **consent_screen.dart 리팩토링** | 하드코딩 3개 → 서버 missing_consents 기반 동적 구성 |
| **auth_service.dart** | refresh_token 저장 + access_token 키 지원 |
| **api_service.dart** | 401 시 refresh token 자동 갱신 + 재시도 |
| **terms.dart** | 버전 '2026-04-01' + 통합 URL + 동적 매핑 헬퍼 |

### 검증 완료 항목

- 서버 재시작 후 정상 기동 (gunicorn + eventlet)
- `/proptalk/` → 200 정상 응답
- 의존성 확인: PyJWT 2.11.0, psycopg2-binary 2.9.11, google-auth 2.48.0

### 우려 사항

| 우려 | 상세 | 중점 검증 |
|------|------|----------|
| **DB_NAME 환경변수 교체 패턴** | auth.py 상단에서 `DB_NAME=goldenrabbit_db`로 교체 후 propnet_auth import, 이후 원복. 모듈 로드 타이밍에 의존 | 서비스 재시작 후 propnet_auth.db 풀이 goldenrabbit_db에 연결되었는지 확인 |
| **user_consents 이중 기록** | 동의 시 propnet_consents + voiceroom.user_consents 양쪽에 기록. 한쪽 실패 시 불일치 가능 | 동의 기록 후 양쪽 테이블 레코드 수 비교 |
| **기존 ConsentScreen 폴백** | 서버 missing_consents가 비어있으면 기존 3개 항목으로 폴백. 서버 에러 시 의도치 않게 구버전 동의 항목 표시 가능 | 서버 에러 시나리오에서 동의 화면 동작 확인 |
| **앱 빌드 미완료** | Propedia와 동일하게 APK 빌드/배포 미진행 | `flutter build apk --release` 후 실기기 테스트 |
| **Drive 토큰 교환 영향** | auth.py에서 exchange_auth_code() 로직은 유지했지만, JWT 변경으로 인해 Drive 백업 기능에 영향 가능 | Proptalk 앱에서 음성 녹음 → Drive 백업 정상 동작 테스트 |

---

## 5. PropSheet 개발 (@propsheet-dev)

### 진행 내용

| 작업 | 상세 |
|------|------|
| **oauth.py 수정** | Google OAuth callback에 propnet_auth 통합, JWT 쿠키 설정, 동의 미완료 시 리다이렉트 |
| **permission_service.py 수정** | JWT 쿠키 인증 fallback 추가 (_try_jwt_auth) |
| **consent.html 신규** | Alpine.js 기반 동의 화면 (체크박스 + "내용 보기" + "동의하고 시작하기") |
| **동의 API 4개 추가** | GET/POST `/propsheet/auth/consent`, GET `/consent/status`, POST `/consent/withdraw` |
| **Admin 하드코딩 제거** | `cs21.jeon@gmail.com` 비교 → propnet_users.role == 'admin' (fallback 유지) |

### 검증 완료 항목 (브라우저 자동화 테스트)

- **admin 계정 테스트**: 로그인 → 동의 화면(4개 항목) → 전체 동의 → 워크스페이스 정상 이동 **PASS**
- **subagent 계정 테스트**: 로그인 → 동의 화면(5개 항목, subagent 전용 포함) → 전체 동의 → 워크스페이스 정상 이동 **PASS**
- **DB 동의 기록**: admin 4건, subagent 5건 propnet_consents에 정상 기록 확인
- **역할별 동의 항목 차이**: admin은 공통3+PropSheet1=4개, subagent는 +subagent전용1=5개 정상 표시

### 우려 사항

| 우려 | 상세 | 중점 검증 |
|------|------|----------|
| **propnet_auth 실패 시 fallback** | `PROPNET_AUTH_AVAILABLE = False`일 때 기존 로직으로 동작하지만, 동의 화면은 표시되지 않음 | propnet_auth import 실패 시나리오 시뮬레이션 |
| **JWT 쿠키 SSO** | PropSheet에서 로그인 후 Propedia PWA로 이동 시 propnet_token 쿠키로 자동 인증되는지 | PropSheet 로그인 → 브라우저에서 `/app/` 접속 → 인증 상태 확인 |
| **permission_service.py 공유** | property-manager(5000)과 propsheet(5020)이 같은 파일을 사용. JWT 쿠키 인증 추가가 property-manager에도 영향 | property-manager(5000)의 기존 API 정상 동작 확인 (매물 API, SNS 공유) |
| **동의 재요구 시나리오** | 이미 동의한 유저가 재로그인 시 동의 화면이 다시 뜨지 않는지 | admin 계정으로 로그아웃 → 재로그인 → 바로 워크스페이스로 가는지 확인 |
| **일반 유저(role=user) 접근** | role='user'인 유저가 PropSheet에 로그인하면 어떻게 되는지 (현재 플랜상 접근 불가) | 일반 유저 계정으로 PropSheet 로그인 시도 → 적절한 접근 제한 메시지 표시 여부 |

---

## 6. 제품기획부 (@pm-lead)

### 진행 내용

| 작업 | 상세 |
|------|------|
| **유저 플로우 설계** | 로그인 → 동의 → (신규) 유저 타입 선택 → 일반: 홈 / Agent: 신청 → 승인 대기 |
| **역할별 서비스 매핑** | user(Propedia+Proptalk), subagent(+PropSheet editor), agent(+PropSheet owner), admin(전체) |
| **Agent 가입 필수 항목** | 상호, 영문이름(slug), 대표자, 연락처, 주소, 공인중개사 등록증 |

### 검증 필요 항목

| 우려 | 상세 | 중점 검증 |
|------|------|----------|
| **유저 타입 선택 타이밍** | 신규 유저만 표시되어야 하는데, `is_new_user` 판별이 서버 응답에 의존 | 기존 유저 재로그인 시 유저 타입 화면이 뜨지 않는지 확인 |
| **Agent 승인 후 자동 설정** | role 변경 + agents 테이블 + PropSheet 워크스페이스 생성이 원자적으로 이루어지는지 | 대시보드에서 Agent 승인 → DB 확인 → PropSheet에서 워크스페이스 보이는지 E2E |
| **Subagent 초대 → 자동 감지** | 초대받은 이메일로 첫 로그인 시 자동 subagent 설정이 실제 동작하는지 | 새 이메일로 초대 → 해당 이메일 Google 로그인 → role=subagent 확인 |

---

## 7. CS/운영부 (@cs-lead)

### 진행 내용

| 작업 | 상세 |
|------|------|
| **법적 문서 5개** | 이용약관, 개인정보 처리방침, 국외 이전 고지, Proptalk 음성 동의, PropSheet 매물 동의 |
| **Nginx 라우팅** | `/legal/*` → 정적 파일 서빙 |
| **문서 URL** | `https://goldenrabbit.biz/legal/` 하위 5개 |

### 검증 완료 항목

- 5개 URL 모두 HTTP 200 확인
- PropSheet 동의 화면의 "내용 보기" 링크 정상 연결

### 우려 사항

| 우려 | 상세 | 중점 검증 |
|------|------|----------|
| **법적 문서 내용 검토** | AI가 작성한 약관/방침이 실제 법적 요건을 충족하는지 | 법률 전문가 검토 또는 최소한 개인정보보호위원회 가이드라인 대조 |
| **약관 버전 관리** | 현재 '2026-04-01' 버전. 내용 수정 시 버전 업데이트 + terms.py 동기화 필요 | 약관 수정 프로세스 문서화 |
| **기존 Proptalk 법적 문서** | `/proptalk/privacy-policy.html` 등 기존 문서가 아직 유효. 통합 문서와 내용 불일치 가능 | 기존 Proptalk 문서를 통합 문서로 리다이렉트 설정 |

---

## 8. 품질관리부 (@qa-lead)

### 검증 완료 항목

| 테스트 | 방법 | 결과 |
|--------|------|------|
| 서비스 기동 | systemctl + journalctl | 4개 서비스 정상 |
| API 기본 응답 | curl | 401/200 예상대로 |
| PropSheet admin 로그인 | 브라우저 자동화 | 동의 4개 → 워크스페이스 **PASS** |
| PropSheet subagent 로그인 | 브라우저 자동화 | 동의 5개(subagent 전용 포함) → 워크스페이스 **PASS** |
| DB 동의 기록 | SQL 직접 조회 | admin 4건, subagent 5건 정상 |
| 법적 문서 접근 | curl | 5개 URL 모두 200 |
| 대시보드 접근 | curl + 브라우저 | 7개 페이지 200 |
| Flutter analyze | dart analyze | No issues found |

### 미검증 항목 (반드시 수행 필요)

| 테스트 | 우선순위 | 방법 |
|--------|---------|------|
| **Propedia 앱 빌드** | 높음 | `flutter build apk --release` 성공 확인 |
| **Proptalk 앱 빌드** | 높음 | `flutter build apk --release` 성공 확인 |
| **구버전 앱 하위 호환** | 높음 | 현재 배포된 앱으로 로그인/API 호출 정상 확인 |
| **PropSheet 재로그인** | 중간 | 동의 완료 유저가 재로그인 시 동의 화면 건너뛰는지 |
| **JWT 쿠키 SSO** | 중간 | PropSheet → Propedia PWA 자동 인증 |
| **Agent 가입 신청 E2E** | 중간 | 앱에서 Agent 선택 → 폼 입력 → 등록증 첨부 → 제출 → 대시보드 승인 |
| **Subagent 초대 E2E** | 중간 | Agent가 이메일 초대 → 해당 이메일 로그인 → 자동 subagent |
| **홈페이지 매물 API** | 중간 | property-manager(5000)의 기존 API 영향 없는지 |
| **Proptalk Drive 백업** | 낮음 | 음성 녹음 후 Drive 백업 정상 |
| **서버 메모리 모니터링** | 낮음 | DB 풀 추가로 인한 메모리 사용량 변화 확인 (956MB 제약) |

---

## 9. 통합 관리자 대시보드 (@propnet-coo)

### 진행 내용

| 작업 | 상세 |
|------|------|
| **대시보드 7페이지** | 홈, 유저관리, Agent승인, 동의관리, 과금, AI사용량, 로그인 |
| **인증** | propnet_users.role == 'admin' (하드코딩 이메일 제거) |
| **Agent 승인 워크플로우** | 신청 조회 → 등록증 확인 → 승인(role변경+agents+워크스페이스) / 거절(사유 입력) |

### 우려 사항

| 우려 | 상세 | 중점 검증 |
|------|------|----------|
| **기존 Proptalk 대시보드 병행** | `/proptalk/admin/`이 아직 살아있음. 관리자가 혼란 가능 | 전환 기간 후 리다이렉트 설정, 기존 대시보드 deprecation 안내 |
| **Agent 승인 시 DB 트랜잭션** | role 변경, agents INSERT, 워크스페이스 생성이 원자적이지 않을 수 있음 | 승인 중간에 에러 발생 시 partial update 상태 확인 |
| **voiceroom DB 접근** | 과금/AI 사용량 페이지가 voiceroom DB를 직접 조회. 연결 실패 시 해당 페이지만 에러 | voiceroom DB 연결 불가 시 graceful error 표시 확인 |
| **OPENAI_ADMIN_KEY** | AI 사용량 페이지에 필요한 환경변수가 backend .env에 없을 수 있음 | 해당 환경변수 존재 확인, 없으면 추가 |

---

## 핵심 검증 체크리스트 (우선순위 순)

### 즉시 수행 (배포 전 필수)

- [ ] **구버전 앱 하위 호환**: 현재 Play Store 앱으로 로그인 → API 정상 동작
- [ ] **PropSheet 재로그인**: 동의 완료 유저 → 재로그인 → 동의 화면 없이 바로 워크스페이스
- [ ] **Propedia APK 빌드**: `flutter build apk --release` 성공
- [ ] **Proptalk APK 빌드**: `flutter build apk --release` 성공
- [ ] **홈페이지 매물 API**: `goldenrabbit.biz` 메인 페이지 정상 로드 (property-manager 5000)

### 배포 후 검증

- [ ] Propedia 앱 Google 로그인 → 동의 화면 → 완료 → 홈
- [ ] Proptalk 앱 Google 로그인 → 동의 화면 → 완료 → 채팅
- [ ] Agent 가입 신청 E2E (앱 → 대시보드 승인)
- [ ] Subagent 초대 E2E (초대 → 로그인 → 자동 연결)
- [ ] JWT 쿠키 SSO (PropSheet 웹 → Propedia PWA)
- [ ] 서버 메모리 사용량 모니터링 (free -m)
- [ ] DB 연결 수 모니터링 (pg_stat_activity)

### 장기 모니터링

- [ ] 약관 법적 검토
- [ ] 기존 Proptalk 대시보드 → 통합 대시보드 리다이렉트
- [ ] 기존 JWT secret fallback 제거 일정
- [ ] 기존 Proptalk 법적 문서 → 통합 문서 리다이렉트
