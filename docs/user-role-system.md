# PropNet 유저 역할 시스템

> 작성일: 2026-03-19

---

## 1. 역할 구조

| 역할 | 설명 | 비고 |
|------|------|------|
| **admin** | 시스템 관리자. 모든 기능 접근 + 대시보드 | agent_id로 중개소 정보 연결 가능 |
| **agent** | 중개사 (사무소 대표). 영문 slug 보유 | agents 테이블에 중개소 정보 저장 |
| **subagent** | 보조중개사. agent가 승인해야 자격 획득 | agent당 2명 제한 (설정 변경 가능) |
| **user** | 일반 사용자 | 기본 역할 |

---

## 2. 서비스별 접근 권한

| 서비스 | admin | agent | subagent | user |
|--------|-------|-------|----------|------|
| **Proppedia** | O (전체) | O (중개사 기능 + 저장) | O (보조 기능 + 저장) | O (무료, 조회만) |
| **Propsheet** | O (전체) | O (owner 수준) | O (agent와 동일, 향후 조정) | X (중개사 전용) |
| **Proptalk** | O | O (Agent 요금제 3단계) | O (agent 요금제에 포함) | O (User 요금제 5단계) |

---

## 3. 요금제

### 일반 User (Proptalk, 현재 5단계)

| code | 이름 | 가격 | 시간 | 타입 |
|------|------|------|------|------|
| free | 무료 체험 | 0원 | 10분 | free |
| pack_1h | 1시간 팩 | 4,900원 | 60분 | time_pack |
| pack_10h | 10시간 팩 | 19,900원 | 600분 | time_pack |
| basic_30h | Basic 30시간 | 29,900원/월 | 1800분 | subscription |
| pro_90h | Pro 90시간 | 79,900원/월 | 5400분 | subscription |

### Agent (Proptalk + Propsheet 번들)

| code | 이름 | 가격 | 시간 | Propsheet |
|------|------|------|------|-----------|
| agent_regular | Agent Regular | 9,900원/월 | Basic 기본 | 포함 |
| agent_basic | Agent Basic | 29,900원/월 | 30시간 | 포함 |
| agent_pro | Agent Pro | 79,900원/월 | 90시간 | 포함 |

- regular 제외 동일 가격에 Propsheet 무료 제공
- billing_plans 테이블에 user_type ('user'/'agent') + includes_propsheet 컬럼
- billing 페이지에서 일반 사용자/중개사 탭 전환

---

## 4. DB 스키마

### agents 테이블 (goldenrabbit_db)

```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255),
    name VARCHAR(100),                    -- 대표자명
    agency_name VARCHAR(200),             -- 사무소명
    slug VARCHAR(50) UNIQUE,              -- 영문 이름 (URL용)
    phone VARCHAR(20),
    address TEXT,
    license_no VARCHAR(50),               -- 등록번호
    license_file TEXT,                    -- 등록증 파일 경로
    avatar_url TEXT,
    max_subagents INTEGER DEFAULT 2,
    remaining_subagent_slots INTEGER DEFAULT 2,
    status VARCHAR(20) DEFAULT 'pending', -- pending/approved/rejected
    approved_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### subagent_requests 테이블

```sql
CREATE TABLE subagent_requests (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES app_users(id),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending', -- pending/approved/rejected
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    UNIQUE(agent_id, email)
);
```

### app_users 변경

```sql
ALTER TABLE app_users ADD COLUMN agent_id INTEGER REFERENCES agents(id);
```

- `role`: user / agent / subagent / admin
- `agent_id`: agent/subagent가 속한 중개소 ID (agents.id 참조)
- admin도 agent_id를 가질 수 있음 (admin + 중개소 연결)

### billing_plans 변경 (voiceroom DB)

```sql
ALTER TABLE billing_plans ADD COLUMN user_type VARCHAR(20) DEFAULT 'user';
ALTER TABLE billing_plans ADD COLUMN includes_propsheet BOOLEAN DEFAULT FALSE;
```

---

## 5. 등록 흐름

### Agent 등록

```
1. Google 로그인 (user로 가입)
2. Agent 가입 신청 폼:
   - 사무소명, 영문 slug, 대표자명, 전화번호, 주소, 등록번호
   - 중개사 등록증 파일 업로드 (필수)
3. 관리자(admin) 승인 대기
   - admin 대시보드에서 등록증 확인 후 role → agent로 변경
4. 승인 후:
   - agent 역할 부여 + agent_id 연결
   - Propsheet 워크스페이스 자동 생성
   - subagent 권한 2장 부여
```

### Subagent 등록

```
1. Google 로그인
2. Agent의 slug로 subagent 신청
3. Agent에게 동의 요청
4. Agent 승인 시:
   - subagent_requests.status → 'approved'
   - app_users.role → 'subagent'
   - app_users.agent_id → 해당 agent.id
   - agent.remaining_subagent_slots -= 1
5. 2장 소진 후 추가 승인 불가
```

---

## 6. 구현 현황

### 완료

- [x] agents 테이블 생성
- [x] subagent_requests 테이블 생성
- [x] app_users에 agent_id 컬럼 추가
- [x] cs21.jeon@gmail.com → admin + agent_id=1 (goldenrabbit) 등록
- [x] admin 대시보드 role 드롭다운 확장 (user/agent/subagent/admin)
- [x] role 변경 시 agents 테이블 자동 연동
- [x] role별 색상 스타일 (agent: 파란색, subagent: 노란색)
- [x] app_user_service에 agent_id 포함
- [x] auth 응답에 agent_id 포함
- [x] Proppedia 저장 버튼 role 조건 확장 (admin/editor/agent/subagent)
- [x] billing_plans에 agent 요금제 3개 추가
- [x] billing 페이지 일반/중개사 탭 전환
- [x] Proptalk 메인 페이지 요금제 업데이트

### 미완료

- [ ] Agent 가입 신청 폼 + API
- [ ] 등록증 파일 업로드
- [ ] Subagent 신청/승인 API
- [ ] Agent 대시보드 (subagent 관리)
- [ ] role_required 데코레이터 에어테이블 저장 라우트에 적용
- [ ] Propsheet 헤더 중개소 정보 DB에서 동적 표시
- [ ] Propsheet 접근 시 agent/subagent 확인

---

## 7. 핵심 파일

| 파일 | 역할 |
|------|------|
| `routes/admin_dashboard.py` | role 변경 API, agent 승인 |
| `services/admin_dashboard_service.py` | role 업데이트 + agents 연동 |
| `templates/admin_dashboard.html` | role 드롭다운 UI |
| `routes/app_auth.py` | role_required 데코레이터, auth 응답 |
| `services/app_user_service.py` | user 조회 (agent_id 포함) |
| `routes/airtable.py` | 에어테이블 저장 (role_required 적용 예정) |
| `frontend/public/app/result.html` | 저장 버튼 role 체크 |
| `chat_stt/server/routes_billing.py` | billing API (user_type 필터) |
| `chat_stt/server/templates/billing/plans.html` | 요금제 UI (탭 전환) |
