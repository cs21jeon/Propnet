---
name: pushupdate
description: 진행기록(progress.md) 갱신 + 보안 검증 + 로컬/서버 Git 커밋/푸시 통합 스킬
---

# /pushupdate — 진행기록 갱신 + Git 커밋/푸시

사용자가 `/pushupdate`을 실행하면 아래 5단계를 순서대로 수행합니다.

---

## Phase 1: 변경 탐지

### 로컬 리포 (C:\Users\ant19\projects\Propnet\)
```bash
git status -s
git diff --stat
```

### 서버 리포 (/home/webapp/goldenrabbit/)
```bash
ssh root@175.119.224.71 "cd /home/webapp/goldenrabbit && git status -s && git diff --stat"
```

### 서비스별 분류
경로 prefix로 변경 파일을 분류하여 사용자에게 요약 제시:

| 경로 prefix | 서비스 |
|------------|--------|
| `propedia/` | Propedia |
| `proptalk/` | Proptalk |
| `propsheet/` | PropSheet |
| `propmap/` | PropMap |
| `docs/`, `scripts/`, 루트 파일 | 통합/인프라 |
| 서버: `chat_stt/` | Proptalk (서버) |
| 서버: `backend/property-manager/` | PropSheet/공통 (서버) |
| 서버: `frontend/public/` | PropMap (서버) |
| 서버: `config/nginx/` | 인프라 (서버) |

---

## Phase 2: 진행기록(progress.md) 갱신

### 대상 파일

| 서비스 | 파일 경로 |
|--------|----------|
| Propedia | `propedia/docs/progress.md` |
| Proptalk | `proptalk/docs/progress.md` |
| PropSheet | `propsheet/docs/progress.md` |
| PropMap | `propmap/docs/progress.md` |
| 통합/인프라 | `docs/progress.md` |

### 갱신 규칙
1. 변경이 감지된 서비스의 progress.md에 오늘 날짜 섹션 추가
2. 사용자에게 변경 요약 메시지를 질문하여 내용 작성
3. 이미 오늘 날짜 섹션이 있으면 항목을 추가
4. `> 최종 업데이트:` 줄을 오늘 날짜로 갱신

### 크로스 서비스 변경 기록 규칙
여러 서비스에 걸친 변경이 있을 때:
1. **주도 서비스** progress.md: 상세 기록 (수정 파일, 기술 내용)
2. **docs/progress.md** (통합): 크로스 서비스 관점 요약 (`[서비스명]` 태그 사용)
3. **연동 서비스** progress.md: 한 줄 참조 (예: `- → Proptalk XXX 연동 반영`)

### 형식
```markdown
## YYYY-MM-DD: 변경 요약 한 줄

- 변경 항목 1
- 변경 항목 2
  - 세부 내용 (수정 파일, 기술 상세 등)
```

### 범위 제외 (이 스킬에서 다루지 않음)
- 버전업 파일: `pubspec.yaml`, `CHANGELOG.json`, `app_version.json`
- 서비스 재시작

---

## Phase 3: 보안 검증 (CRITICAL — 반드시 실행)

커밋 전 스테이징된 파일에 대해 아래 검사를 모두 통과해야 함.

### 3-1. 파일명 검사 (금지 패턴)
스테이징된 파일 중 다음 패턴이 있으면 즉시 중단:
- `.env`, `key.properties`, `*.jks`, `*.keystore`, `*.pem`
- `google-services.json`, `*firebase-adminsdk*`
- `.mcp.json`, `ecosystem.config.js`

### 3-2. 내용 검사 (정규식 스캔)
`git diff --cached` 출력에서 다음 패턴 검사:
- API 키: `sk-`, `AIza`, `AKIA`, `ghp_`, `gho_`, `github_pat_`
- 비밀번호: `password\s*=\s*['"][^'"]+`, `DB_PASS`, `DB_PASSWORD`, `SECRET`
- 토큰: `Bearer\s+[A-Za-z0-9._-]{20,}`
- Private Key: `-----BEGIN.*PRIVATE KEY-----`
- DB 연결: `postgresql://.*:.*@`

### 3-3. 신규 파일 별도 검사
```bash
git diff --cached --diff-filter=A
```
새로 추가되는 파일의 전체 내용을 위 패턴으로 검사.

### 3-4. 위반 시 대응
- 즉시 중단
- 해당 파일 unstage (`git reset HEAD <file>`)
- 사용자에게 위반 내용 보고
- 수정 후 재실행 안내

### 3-5. 통과 시 출력
```
=== 보안 스캔 결과 ===
[PASS] 금지 파일 패턴 없음
[PASS] API 키/비밀번호/토큰 미검출
[PASS] 신규 파일 (N개) 검사 완료
스테이징 파일: N개
```

---

## Phase 4: 분류 커밋 + 푸시

### 로컬 (cs21jeon/Propnet)
1. 변경사항을 논리 그룹별로 분류하여 커밋
   - 동일 기능의 변경 = 하나의 커밋 (서비스 경계 무시 가능)
   - 서로 다른 기능이면 서비스별 분리
   - progress.md 갱신은 해당 기능 커밋에 포함
2. 커밋 메시지 형식:
   ```
   <type>: <한국어 설명>

   Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
   ```
   타입: `feat`, `fix`, `docs`, `security`, `refactor`, `chore`
3. `git push origin main`

### 서버 (cs21jeon/goldenrabbit)
1. SSH 접속: `ssh root@175.119.224.71`
2. 동일한 보안 검증 (Phase 3) 적용
3. 그룹별 커밋 → 푸시:
   ```bash
   cd /home/webapp/goldenrabbit
   git add <files>
   git commit -m "<message>"
   git push origin main
   ```

### 커밋 시 주의
- `git add .` 또는 `git add -A` 절대 사용 금지 — 파일을 명시적으로 지정
- 커밋 전 `git diff --cached`로 최종 확인

---

## Phase 5: 결과 요약

실행 완료 후 다음 정보 출력:
- 로컬: 커밋 N개, 변경 파일 N개, 푸시 결과
- 서버: 커밋 N개, 변경 파일 N개, 푸시 결과
- 갱신된 progress.md 파일 목록
