# PropNet - 통합 프로젝트

## 개요

PropNet은 부동산 정보 관리 및 조회를 위한 통합 플랫폼입니다.
단일 서버(`175.119.224.71`, 도메인 `goldenrabbit.biz`)에서 운영됩니다.

## 서비스 구성

| 서비스 | 로컬 경로 | 플랫폼 | 서버 포트 | 서버 경로 |
|--------|-----------|--------|-----------|-----------|
| **Propedia** | `propedia/` | Flutter 앱 + 웹(PWA) | 5010 | `/backend/proppedia/` |
| **Proptalk** | `proptalk/` | Flutter 앱 | 5030 | `/chat_stt/server/` |
| **PropSheet** | `propsheet/` | 웹 (HTMX/Alpine.js) | 5020 | `/backend/propsheet/` |
| **PropMap** | `propmap/` | 웹 (정적 HTML) | - | `frontend/public/` |
| **PropNet API** | (서버만) | API | 5000 | `/backend/property-manager/` |

> 각 서비스의 상세 규칙은 서비스별 CLAUDE.md를 참조:
> - `propedia/CLAUDE.md` - Flutter 빌드, Clean Architecture, 릴리즈 워크플로우
> - `proptalk/CLAUDE.md` - Whisper API 필수 사용, PM2 배포, 결제 시스템
> - `propsheet/CLAUDE.md` - HTMX/Alpine.js, Flask Blueprint, 스프레드시트 SaaS
> - `propmap/CLAUDE.md` - 정적 HTML, 매물지도, Nginx 서빙

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
sudo systemctl restart property-manager  # PropNet API (:5000)
sudo systemctl restart proppedia         # Proppedia (:5010)
sudo systemctl restart propsheet         # PropSheet (:5020)
sudo systemctl restart proptalk          # Proptalk (:5030)

# 로그 확인
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
4. **Git 커밋/푸시 시 보안 필수 확인**:
   - 절대 커밋 금지 파일: `.env`, `key.properties`, `*.jks`, `*.keystore`, OAuth 토큰/시크릿 파일
   - 커밋 전 `git diff --cached`로 API 키, 비밀번호, 토큰이 포함되지 않았는지 반드시 확인
   - 서버 경로의 `.env` 내용(API 키, DB 비밀번호 등)을 코드나 문서에 하드코딩 금지
   - 각 서비스 `.gitignore`에 민감 파일 패턴이 포함되어 있는지 주기적 확인

## Git 구조

```
Propnet/.git/              ← 이 리포 (통합 설정/문서 관리)
Propnet/propedia/.git/     ← 독립 GitHub 리포 (cs21jeon/propedia)
Propnet/proptalk/.git/     ← 독립 GitHub 리포 (cs21jeon/Proptalk)
```

- Propnet 루트 git: 공유 설정/문서만 관리 (propedia/, proptalk/은 .gitignore로 제외)
- 서비스별 코드 변경: 각 서비스 디렉토리에서 독립적으로 commit/push

## 향후 계획

- **PropMap**: `/propmap/{agent_slug}` 형태의 agent별 매물지도 서비스 구축
- **도메인 마이그레이션**: `propnet.kr` 도메인 추가 예정
- **URL 변경**: `goldenrabbit.biz/` → `/propmap/goldenrabbit/` (301 리다이렉트 필요)

## 블로그

- **네이버 블로그**: blog.naver.com/propnet
- **문체 가이드**: `propedia/blog_sample/my-writing-style.md`
- **발행 도구**: Playwright MCP
