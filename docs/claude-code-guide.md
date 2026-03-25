# Claude Code 지침 시스템 가이드

Claude Code에서 사용하는 지침/설정/메모리 시스템을 정리한 문서입니다.

---

## 1. CLAUDE.md — Claude에게 주는 지시서

매 세션 시작 시 자동으로 로드됩니다. **팀과 공유 가능**(git 커밋).

| 위치 | 범위 | 공유 |
|------|------|------|
| `./CLAUDE.md` 또는 `./.claude/CLAUDE.md` | 이 프로젝트 | O (git) |
| `~/.claude/CLAUDE.md` | 모든 프로젝트 | X (개인) |
| 서브디렉토리의 `CLAUDE.md` | 해당 디렉토리 작업 시만 | O |

**넣을 것:** 코딩 규칙, 아키텍처 규칙, 빌드 명령어, 배포 절차, 보안 규칙 등

규칙이 많아지면 `.claude/rules/` 폴더로 분리 가능:

```
.claude/rules/
├── security.md      # 보안 규칙
├── code-style.md    # 코드 스타일
└── deploy.md        # 배포 규칙
```

파일별로 적용 대상을 지정할 수도 있음 (frontmatter 사용):

```markdown
---
paths:
  - "src/**/*.ts"
  - "lib/**/*.dart"
---

# 코드 스타일 규칙
- 2 space 들여쓰기
```

---

## 2. Memory (메모리) — Claude가 스스로 기억하는 노트

대화에서 배운 것을 **다음 세션에도 기억**하기 위한 시스템.

### 저장 위치

```
~/.claude/projects/<프로젝트>/memory/
```

현재 PropNet 프로젝트:
`C:\Users\ant19\.claude\projects\C--Users-ant19-projects-Propnet\memory\`

### 구조

```
memory/
├── MEMORY.md           # 인덱스 (처음 200줄만 자동 로드)
├── user_role.md        # 사용자 정보
├── feedback_testing.md # 작업 방식 피드백
└── project_goals.md    # 프로젝트 맥락
```

### 메모리 유형 4가지

| 유형 | 용도 | 예시 |
|------|------|------|
| `user` | 사용자 역할/선호도 | "부동산 스타트업 1인 개발자" |
| `feedback` | 작업 방식 지침 | "커밋 전 보안 점검 필수" |
| `project` | 진행 중인 작업 맥락 | "PropMap 신규 서비스 개발 중" |
| `reference` | 외부 리소스 위치 | "버그 트래킹은 Linear에서" |

### 메모리 파일 형식

```markdown
---
name: 메모리 이름
description: 한 줄 설명 (다음 세션에서 관련성 판단에 사용)
type: user | feedback | project | reference
---

메모리 내용
```

### 메모리에 넣지 말아야 할 것

- 코드 패턴, 아키텍처, 파일 경로 (코드에서 파악 가능)
- Git 히스토리 (git log로 확인 가능)
- 디버깅 해결책 (코드와 커밋 메시지에 있음)
- CLAUDE.md에 이미 있는 내용
- 현재 대화에서만 쓰이는 임시 정보

---

## 3. CLAUDE.md vs Memory — 언제 뭘 쓰나?

| | CLAUDE.md | Memory |
|---|---|---|
| **누가 작성** | 사용자가 직접 | Claude가 대화 중 자동 |
| **공유 가능** | O (git 커밋) | X (로컬 전용) |
| **로드 시점** | 항상 전체 로드 | 인덱스 200줄만 로드 |
| **적합한 내용** | 코딩 규칙, 아키텍처, 빌드 명령 | 사용자 선호도, 피드백, 프로젝트 맥락 |
| **예시** | "Whisper 로컬 모델 금지" | "이 사용자는 간결한 응답 선호" |

**핵심 원칙:** 코드에서 파악할 수 없는 **규칙**은 CLAUDE.md, 코드에서 파악할 수 없는 **맥락**은 Memory

---

## 4. Settings — 권한과 자동화 설정

### 파일 위치와 우선순위

| 파일 | 위치 | 용도 | 공유 | 우선순위 |
|------|------|------|------|----------|
| Managed | 시스템 디렉토리 | 조직 전체 정책 | O | 1 (최고) |
| User | `~/.claude/settings.json` | 모든 프로젝트 공통 | X | 2 |
| Project | `.claude/settings.json` | 팀 공유 설정 | O | 3 |
| Local | `.claude/settings.local.json` | 개인 오버라이드 | X | 4 |

### 설정 가능한 항목

- **permissions**: 도구 사용 허용/차단 규칙
- **env**: 환경변수
- **hooks**: 자동 실행 훅
- **MCP 서버**: 외부 도구 연동

### 예시

```json
{
  "permissions": {
    "allow": ["Bash(npm test)", "Bash(flutter build)"],
    "deny": ["Bash(rm -rf *)", "Read(.env*)"]
  },
  "env": {
    "DEBUG": "true"
  }
}
```

---

## 5. Hooks — 자동 실행되는 강제 규칙

CLAUDE.md는 "가이드"(Claude가 무시할 수도 있음), Hook은 **강제 실행**됩니다.
Settings 파일에 설정합니다.

### 주요 이벤트

| 이벤트 | 시점 | 활용 예 |
|--------|------|---------|
| `PreToolUse` | 도구 실행 전 | 위험한 명령 차단 |
| `PostToolUse` | 도구 실행 후 | 코드 자동 포맷팅 |
| `UserPromptSubmit` | 프롬프트 제출 전 | 컨텍스트 자동 주입 |
| `SessionStart` | 세션 시작 시 | 초기 설정 |
| `Stop` | Claude 응답 완료 시 | 결과 검증 |

### Hook 타입

| 타입 | 설명 |
|------|------|
| `command` | 셸 스크립트 실행 (exit 0: 허용, exit 2: 차단) |
| `http` | HTTP POST 요청 |
| `prompt` | Claude API 호출로 판단 |
| `agent` | 서브에이전트로 검증 |

### 예시: 파일 편집 후 자동 포맷팅

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

---

## 6. 전체 디렉토리 맵

### 프로젝트 내 (Propnet/)

```
Propnet/
├── CLAUDE.md                          # 프로젝트 공통 규칙
├── .claude/
│   ├── settings.json                  # 팀 공유 설정
│   ├── settings.local.json            # 개인 설정 (gitignore)
│   ├── rules/                         # 주제별 규칙 분리
│   │   ├── security.md
│   │   └── deploy.md
│   ├── agents/                        # 프로젝트 서브에이전트
│   └── skills/                        # 프로젝트 스킬
├── propedia/CLAUDE.md                 # Propedia 전용 규칙
└── proptalk/CLAUDE.md                 # Proptalk 전용 규칙
```

### 사용자 홈 (~/.claude/)

```
~/.claude/
├── CLAUDE.md                          # 모든 프로젝트 공통 개인 규칙
├── settings.json                      # 모든 프로젝트 공통 설정
├── agents/                            # 사용자 서브에이전트
├── skills/                            # 사용자 스킬
└── projects/<프로젝트>/memory/        # Claude 메모리 저장소
    ├── MEMORY.md                      # 메모리 인덱스 (200줄 제한)
    └── *.md                           # 개별 메모리 파일
```

---

## 7. 세션 실행 흐름

```
세션 시작
  ↓
CLAUDE.md 로드 + Memory 인덱스(MEMORY.md 200줄) 로드
  ↓
SessionStart 훅 실행
  ↓
사용자 프롬프트 입력
  ↓
UserPromptSubmit 훅 실행
  ↓
PreToolUse 훅 → 도구 실행 → PostToolUse 훅
  ↓
Claude 응답 완료 → Stop 훅
  ↓
세션 종료 → Memory 저장 → SessionEnd 훅
```

---

## 8. 실전 활용 팁

### 보안 규칙을 CLAUDE.md에 추가하기

```markdown
## 보안 규칙
- 커밋 전 `.env`, API 키, 시크릿 포함 여부 반드시 확인
- 하드코딩된 비밀번호/토큰 검사
- `.gitignore` 누락 파일 점검
```

### 위험한 명령 차단 (Hook)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "echo $CLAUDE_TOOL_INPUT | grep -qE 'rm -rf|git push --force' && exit 2 || exit 0"
        }]
      }
    ]
  }
}
```

### 사용자 정보 메모리에 저장하기

"내 역할은 OOO이다" 같은 정보를 대화에서 알려주면 Claude가 자동으로 메모리에 저장합니다.
또는 직접 "OOO를 기억해줘"라고 요청할 수도 있습니다.
