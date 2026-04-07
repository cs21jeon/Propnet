# PropNet 통합 인증 시스템 구현 보고서

**최초 작성일**: 2026-03-31
**최종 업데이트**: 2026-04-07
**구현 기간**: 2026-03-30 ~ 2026-04-07

---

## 인증 용어 정리

비개발자를 위한 핵심 용어 설명입니다.

### Auth (인증)
"이 사람이 누구인지 확인하는 과정". Google 로그인 버튼을 눌러 "이 사람이 cs21.jeon@gmail.com이 맞다"고 확인하는 것.

### 토큰 (Token)
"입장 팔찌". Google 로그인 성공 후 서버가 발급하는 인증 증표. 이후 모든 API 요청에 이 토큰을 함께 보내면 "인증된 사용자"로 처리됨.

### JWT (JSON Web Token)
"위조 방지 팔찌". 토큰의 구체적인 형태. 암호화된 문자열 안에 "누구인지, 언제 발급됐는지, 언제 만료되는지"가 담겨 있고 서버만 아는 비밀 키로 서명되어 위조 불가.
- **Access Token**: 24시간 유효. API 호출에 사용.
- **Refresh Token**: 30일 유효. Access Token 만료 시 새로 발급받는 교환권.

### 쿠키 (Cookie)
"브라우저가 자동으로 보내는 메모지". 웹 브라우저에 저장되는 작은 데이터. 같은 도메인에 요청할 때 자동으로 함께 전송됨.
- `propnet_token` 쿠키 (HttpOnly): 서버만 읽을 수 있는 JWT. 보안이 높음.
- `propnet_uid` 쿠키: JavaScript에서 "누가 로그인했는지" 확인하는 용도.
- `localStorage`: 쿠키와 달리 자동 전송이 안 되고, 코드에서 직접 꺼내서 보내야 함.

### SSO (Single Sign-On)
"한 번 로그인하면 모든 서비스에서 로그인된 상태". PropSheet에서 로그인하면 Propedia, Proptalk 웹에서도 재로그인 없이 사용 가능. propnet_token 쿠키가 propnet.kr 도메인 전체에 유효하기 때문에 가능.

### OAuth (Open Authorization)
"Google이 대신 인증해주는 방식". 사용자가 PropNet에 비밀번호를 직접 등록하지 않고, Google 계정으로 로그인. Google이 "이 사람이 맞다"고 PropNet에 알려줌.

### propnet_auth
PropNet이 만든 공유 인증 라이브러리. 4개 서비스(PropSheet, Propedia, Proptalk, Property Manager)가 모두 이 라이브러리를 import해서 동일한 방식으로 인증을 처리함.

### propnet_users (SSoT)
"회원 명부 원본". Single Source of Truth. 모든 서비스가 이 테이블의 역할(role), 소속(agent_id)을 참조함. 각 서비스의 로컬 유저 테이블(app_users, web_users, voiceroom.users)은 서비스별 추가 데이터만 보관.

---

## 시스템 구조도

```
사용자가 Google 로그인 클릭
        │
        ▼
   [Auth] 인증 과정
   Google에 "이 사람 맞아?" 확인
        │
        ▼
   서버가 [JWT] 토큰 발급
   "24시간짜리 입장 팔찌"
        │
        ├──→ 앱: 암호화 저장소에 보관
        │
        └──→ 웹: [쿠키]로 브라우저에 저장
             "propnet.kr 도메인 전체에 유효"
                    │
                    ▼
              [SSO] 다른 서비스 접속 시
              쿠키가 자동 전송 → 재로그인 불필요
```

### 서비스별 인증 흐름

```
┌─────────────────────────────────────────────────────────┐
│                    propnet_auth 라이브러리                │
│  JWT 발급/검증 · propnet_users 관리 · 동의 관리 · SSO 쿠키  │
└──────────┬──────────┬──────────┬──────────┬──────────────┘
           │          │          │          │
     ┌─────┴──┐ ┌─────┴──┐ ┌────┴───┐ ┌────┴────────┐
     │PropSheet│ │Propedia│ │Proptalk│ │PropertyMgr  │
     │ :5020  │ │ :5010  │ │ :5030  │ │   :5000     │
     │웹(HTMX)│ │앱+웹   │ │앱+웹   │ │ 홈페이지API  │
     └────────┘ └────────┘ └────────┘ └─────────────┘
```

---

## 현재 상태 (2026-04-07)

### 서비스별 인증 통합 현황

| 서비스 | 로그인 API | JWT 방식 | SSO 쿠키 | propnet_users 연동 | 상태 |
|--------|-----------|---------|----------|-------------------|------|
| **PropSheet** (웹) | `/propsheet/auth/google` | 통합 JWT | O | O | 완료 |
| **Propedia** (앱) | `/app/api/auth/google` | 통합 JWT | X (앱이라 불필요) | O | 완료 |
| **Propedia** (웹) | token-sync.js (SSO 수신만) | 통합 JWT | 수신만 가능 | O | 부분 완료 |
| **Proptalk** (앱) | `/voiceroom/api/auth/google` | 통합 JWT | X (앱이라 불필요) | O | 완료 |
| **Proptalk** (웹앱) | `/voiceroom/api/auth/google` | 통합 JWT | O | O | 완료 |
| **Proptalk** (billing) | `/proptalk/billing/login` | **통합 JWT** | O | O | **수정 완료 (04-07)** |
| **통합 회원가입** | `/register/callback` | 통합 JWT | O | O | 완료 |

### 2026-04-07 수정사항

#### 보안 수정 (6건)
| # | 수정 | 파일 | 심각도 |
|---|------|------|--------|
| 1 | PropSheet 탈퇴 시 propnet_users 비활성화 추가 | oauth.py | 심각 |
| 2 | Proptalk 탈퇴 시 propnet_users 비활성화 추가 | auth.py | 심각 |
| 3 | admin 이메일 하드코딩 fallback 제거 (SSoT 준수) | oauth.py | 중간 |
| 4 | OAuth nonce 세션 만료 시 검증 강화 | register.py | 중간 |
| 5 | /auth/debug admin 전용으로 보호 | oauth.py | 정보 |
| 6 | Proptalk 동의 병행 기록 TODO 주석 추가 | auth.py | 낮음 |

#### 도메인 전환 (3건)
| # | 수정 | 대상 |
|---|------|------|
| 1 | SSO 쿠키 도메인 `goldenrabbit.biz` → `propnet.kr` | propnet_auth/config.py |
| 2 | goldenrabbit.biz에서 /propsheet, /app/, /register → propnet.kr 301 리다이렉트 | goldenrabbit.conf |
| 3 | Propedia 앱 baseUrl → `https://propnet.kr` | api_client.dart |

#### Proptalk 웹/앱 통합 (2건)
| # | 수정 | 대상 |
|---|------|------|
| 1 | billing 로그인을 통합 JWT로 교체 (레거시 create_token → propnet_auth) | billing_web.py |
| 2 | billing 토큰 저장을 웹앱과 통일 (sessionStorage → localStorage) | billing/base.html, login.html |

#### Proptalk 웹 탈퇴 (2건)
| # | 수정 | 대상 |
|---|------|------|
| 1 | 웹앱 설정 패널에 회원탈퇴 버튼 추가 | templates/web/app.html, static/web/app.js |
| 2 | billing 페이지에 회원탈퇴 버튼 추가 | templates/billing/base.html |

---

## 1. 인프라부 (@infra-lead)

### 구현 내용

| 작업 | 상세 |
|------|------|
| **DB 테이블** | `propnet_users`, `service_user_links`, `propnet_consents`, `agent_requests`, `subagent_invitations` (goldenrabbit_db) |
| **기존 테이블 ALTER** | `app_users`에 `propnet_user_id` FK, `voiceroom.users`에 `propnet_user_id` + 인덱스 |
| **데이터 마이그레이션** | 3개 서비스 유저 60명 통합, service_user_links 67건 |
| **환경변수** | `PROPNET_JWT_SECRET` (64자 hex) → backend/.env + chat_stt/server/.env |
| **Nginx 라우팅** | `/legal/*` → 정적, `/admin/*` → 5010, `/register/*` → 5010 |
| **SSO 쿠키 도메인** | `propnet.kr` (2026-04-07 변경) |
| **goldenrabbit.biz 리다이렉트** | /propsheet, /app/, /register → propnet.kr 301 (API 프록시는 유지) |

### 검증 완료
- 4개 서비스 정상 기동
- propnet.kr에서 모든 서비스 200 응답
- goldenrabbit.biz → propnet.kr 301 리다이렉트 동작
- goldenrabbit.biz/app/api/, /voiceroom/api/ 프록시 유지 (구버전 앱 호환)

---

## 2. 개발부 (@dev-lead)

### propnet_auth 라이브러리

| 항목 | 상세 |
|------|------|
| **위치** | `/backend/shared/propnet_auth/` |
| **모듈** | 10개 Python 모듈, ~1,300줄 |
| **JWT** | 다중 secret fallback (PROPNET_JWT_SECRET → JWT_SECRET_KEY → JWT_SECRET) |
| **OAuth** | Google id_token 검증 (다중 Client ID) + 웹 code flow |
| **SSO** | set_propnet_cookie() / clear_propnet_cookie() |
| **동의 관리** | 역할별 동적 동의 항목, 버전 관리, IP/UA 기록 |

### 검증 완료
- JWT round-trip (생성→검증) PASS
- 다중 secret fallback PASS
- DB 연결 풀 정상
- Gmail 점 정규화 정상

---

## 3. Propedia (@propedia-dev)

### 구현 내용 (서버 + 앱)

| 작업 | 상세 | 상태 |
|------|------|------|
| app_auth.py 통합 | propnet_auth JWT, 동의 API, token_required | 완료 |
| Flutter 동의 화면 | consent_screen.dart (서버 기반 동적) | 완료 |
| Flutter 유저 타입 선택 | user_type_screen.dart | 완료 |
| Flutter Agent 가입 | agent_register_screen.dart | 완료 |
| **baseUrl 변경** | `goldenrabbit.biz` → `propnet.kr` | **완료 (04-07)** |
| **APK 빌드/배포** | - | **미완료** |
| **SSO 쿠키 설정** | 앱 로그인 시 set_propnet_cookie() 미호출 | **미완료** |

### 앱/웹 인증 상태
- 앱과 웹 모두 같은 `/app/api/auth/google` 엔드포인트 사용 → **인증 통합 완료**
- 데이터(즐겨찾기, 검색기록)도 같은 서버 API → **데이터 동기화 완료**
- SSO 쿠키는 미설정 → Propedia에서 로그인해도 다른 서비스에 SSO 전파 안 됨 (수신은 가능)

---

## 4. Proptalk (@proptalk-dev)

### 구현 내용 (서버 + 앱 + 웹)

| 작업 | 상세 | 상태 |
|------|------|------|
| auth.py 통합 | propnet_auth JWT, 동의 API, refresh token | 완료 |
| Flutter 동의 화면 | 서버 missing_consents 기반 동적 | 완료 |
| **billing 로그인 통합** | 레거시 JWT → propnet_auth 통합 JWT | **완료 (04-07)** |
| **토큰 저장 통일** | billing sessionStorage → localStorage 통일 | **완료 (04-07)** |
| **웹앱 탈퇴 버튼** | /proptalk/web/ 설정 패널에 추가 | **완료 (04-07)** |
| **billing 탈퇴 버튼** | billing base.html에 추가 | **완료 (04-07)** |

### 앱/웹 인증 상태
- 앱, 웹앱(/proptalk/web/), billing(/proptalk/billing/) 모두 **통합 인증 완료**
- 세 곳 모두 같은 JWT, 같은 DB(voiceroom), 같은 socket.io 서버
- 웹앱에서 로그인하면 billing에서도 자동 인증 (localStorage 공유)

---

## 5. PropSheet (@propsheet-dev)

### 구현 내용

| 작업 | 상세 | 상태 |
|------|------|------|
| oauth.py 통합 | propnet_auth JWT + SSO 쿠키 + 동의 리다이렉트 | 완료 |
| consent.html | Alpine.js 동의 화면 | 완료 |
| 동의 API 4개 | GET/POST consent, status, withdraw | 완료 |
| **admin 하드코딩 제거** | propnet_users.role SSoT 준수 | **완료 (04-07)** |
| **탈퇴 시 propnet_users 비활성화** | - | **완료 (04-07)** |

### 검증 완료
- admin 로그인 → 동의 4개 → 워크스페이스 PASS
- subagent 로그인 → 동의 5개 → 워크스페이스 PASS
- 동의 완료 유저 재로그인 → 동의 건너뛰기 PASS

---

## 6. 통합 회원가입 위자드 (/register/)

### 구현 내용

| 작업 | 상세 | 상태 |
|------|------|------|
| Step 1: 회원 유형 선택 | user / agent / subagent | 완료 |
| Step 2: Google OAuth | role을 state에 인코딩 | 완료 |
| Step 3: 역할별 동의 | get_required_consents() | 완료 |
| Step 4: Agent 등록 폼 | slug/등록증/주소 | 완료 |
| **nonce 검증 강화** | 세션 만료 시에도 거부 | **완료 (04-07)** |

---

## 회원 탈퇴 현황

| 서비스 | 앱 탈퇴 | 웹 탈퇴 | propnet_users 비활성화 |
|--------|--------|--------|----------------------|
| **PropSheet** | - (웹 전용) | **미구현** (향후) | **완료 (04-07)** |
| **Propedia** | O (profile) | O (profile.html) | O (기존 구현) |
| **Proptalk** | O (settings) | **O (04-07 추가)** | **완료 (04-07)** |

---

## 핵심 검증 체크리스트

### 완료

- [x] 서비스 기동 (4개 서비스 정상)
- [x] PropSheet admin/subagent 로그인 + 동의 (브라우저 자동화 테스트)
- [x] 법적 문서 5개 URL 200
- [x] Flutter analyze (Propedia, Proptalk 모두 No issues)
- [x] goldenrabbit.biz → propnet.kr 리다이렉트 동작
- [x] SSO 쿠키 도메인 propnet.kr 전환
- [x] Proptalk billing 인증 통합
- [x] 탈퇴 시 propnet_users 비활성화 (PropSheet, Proptalk)
- [x] /auth/debug admin 전용 보호
- [x] OAuth nonce 검증 강화
- [x] Propedia baseUrl → propnet.kr

### 미완료 (배포 전 필수)

- [ ] **Propedia APK 빌드**: `flutter build apk --release` 성공 + Play Store 배포
- [x] **가입 E2E 테스트**: Agent 가입 위자드 전체 흐름 (신청→승인→결제→활성화)
- [ ] **구버전 앱 호환**: 현재 Play Store 앱으로 API 호출 정상 확인

### 미완료 (배포 후)

- [ ] Propedia 앱 로그인 시 SSO 쿠키 설정 (set_propnet_cookie 추가)
- [ ] PropSheet 웹 탈퇴 UI 구현 (agent/subagent 데이터 처리 설계 필요)
- [ ] Subagent 초대 → 자동 연결 E2E
- [ ] 서버 메모리/DB 연결 수 모니터링
- [ ] Toss Payments 연동 테스트 (테스트 키 발급 후)

### 장기

- [ ] 법적 문서 전문가 검토
- [ ] 기존 JWT secret fallback 제거
- [ ] Proptalk 동의 이중 기록(voiceroom.user_consents) 제거
- [ ] goldenrabbit.biz API 프록시 제거 (구버전 앱 업데이트 확인 후, 6개월 예상)
- [ ] 구독 자동 갱신 크론 (billing_key 기반 월 정기결제)

---

## 2026-04-07 Agent 과금+인증 통합

### 구현 내용

| 작업 | 상세 | 상태 |
|------|------|------|
| DB 마이그레이션 | agent_requests +결제 컬럼, billing_plans +agent 플랜 3개, user_billing +propnet_user_id | 완료 |
| billing_check.py | PropSheet 접근 권한 확인 (admin/agent/subagent/user별) | 완료 |
| toss_payments.py | Toss 결제 공유 모듈 (confirm_payment, cancel_payment) | 완료 |
| Agent 가입 결제 흐름 | 신청→심사→approved_pending_payment→결제→활성화 | 완료 |
| 결제 페이지 | /register/agent/payment (3개 플랜 선택 + Toss SDK) | 완료 |
| Admin 대시보드 | 유저+과금 통합 뷰, 강제 완료, 결제 안내 이메일 | 완료 |
| PropSheet 접근 제어 | require_agent_access에 billing_check 추가 + billing_required 페이지 | 완료 |
| Agent 데이터 격리 수정 | _get_agent_room_ids SSoT 전환 (web_users→propnet_users) | 완료 |
| room_ids 방어 코딩 | 빈 리스트 시 전체 노출 방지 (if room_ids is not None) | 완료 |
| Proptalk SSO 자동 로그인 | propnet_token 쿠키 → localStorage 동기화 + 계정 불일치 재로그인 | 완료 |
| 환영 메일 개선 | 4개 서비스 카드 + PC/모바일 링크 분리 + Play Store ID 수정 | 완료 |
| 승인 메일 개선 | 요금제 박스형 카드 3개 + 모바일 친화 + Gmail 호환 버튼 | 완료 |
| 방 이름 | "상담방" → "업무방" | 완료 |
| 파비콘 | register 전체 + billing_required → propnet 아이콘 통일 | 완료 |
| Subagent 과금 | PropSheet=agent 구독 포함, Proptalk=독립 과금, 초대 시 구독 체크 | 완료 |

### Agent 가입 흐름

```
1. /register/ → agent 선택 → Google OAuth → 동의 5개
2. /register/agent → 사업자 정보 + 등록증/로고 업로드 → agent_requests (pending)
3. Admin /admin/agent-requests → 심사 승인 → approved_pending_payment + 결제 안내 메일
4. /register/agent/payment → 3개 플랜 선택 → Toss 결제 (또는 Admin 강제 완료)
5. 결제 성공 → role=agent + agents 테이블 + PropSheet/PropMap/Proptalk 자동 생성 + 환영 메일

### 검증 완료

- [x] Agent 가입 신청 → Admin 승인 → 강제 완료 → PropSheet/PropMap/Proptalk 생성
- [x] SSO 쿠키로 PropSheet 자동 로그인
- [x] Proptalk SSO 쿠키 자동 로그인
- [x] Agent 데이터 격리 (전화번호 조회 시 본인 room만)
- [x] PropSheet billing 체크 (미구독 시 billing_required 페이지)
- [x] 승인 메일 발송 (요금제 카드 + 결제 링크)
- [x] 환영 메일 발송 (4개 서비스 PC/모바일 링크)
```
