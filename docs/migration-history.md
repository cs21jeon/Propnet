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
└── :8000  레거시 Threads (제거 예정)      → /backend/api/
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
