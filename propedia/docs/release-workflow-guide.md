# Propedia 릴리즈 워크플로우 가이드

Claude Code를 활용한 자동화된 업데이트/릴리즈 프로세스입니다.

---

## 1. 개요

### 워크플로우 흐름
```
1. 업데이트 요청 → 코드 수정
2. 테스트 실행 (/test)
3. 오류 있으면 → 수정 후 재테스트
4. 오류 없으면 → CHANGELOG 업데이트
5. 버전 업데이트 (pubspec.yaml)
6. APK/AAB 빌드 (/build)
7. 커밋 및 푸시
8. (필요시) 서버 배포 (/deploy)
```

### 사용 가능한 슬래시 명령어
| 명령어 | 용도 |
|--------|------|
| `/release` | 전체 릴리즈 워크플로우 |
| `/test` | 코드 분석 및 테스트 |
| `/build` | APK/AAB 빌드 |
| `/deploy` | 서버 배포 |

---

## 2. 설정 파일 구조

```
propedia/
├── .claude/
│   ├── commands/           # 슬래시 명령어 정의
│   │   ├── release.md      # /release 명령어
│   │   ├── test.md         # /test 명령어
│   │   ├── build.md        # /build 명령어
│   │   └── deploy.md       # /deploy 명령어
│   └── settings.local.json # 로컬 권한 설정
├── .mcp.json               # MCP 서버 연결 설정
├── CLAUDE.md               # 프로젝트 가이드
└── docs/
    ├── CHANGELOG.md        # 버전별 업데이트 이력
    └── release-workflow-guide.md  # 이 문서
```

---

## 3. 초기 설정

### 3.1 Claude Code 설치
```bash
npm install -g @anthropic-ai/claude-code
```

### 3.2 프로젝트 디렉토리에서 실행
```bash
cd C:\Users\ant19\projects\propedia
claude
```

### 3.3 명령어 인식 확인
새 명령어 파일 추가 후에는 **세션 재시작** 필요:
```bash
# Claude Code 종료
/exit  또는  Ctrl+C

# 다시 실행
claude
```

---

## 4. 사용 방법

### 4.1 전체 릴리즈 (/release)

Claude Code에서:
```
/release
```

자동으로 수행되는 작업:
1. `git status` - 변경 사항 확인
2. `flutter analyze` - 코드 분석
3. `flutter test` - 테스트 실행
4. 버전 업데이트 안내
5. `flutter build apk --release` - APK 빌드
6. `flutter build appbundle --release` - AAB 빌드
7. 커밋 메시지 생성

### 4.2 부동산 조회 테스트 (/test)

```
/test
```

실행 내용:
- `test-case-review-guide.md`의 9개 테스트 케이스 실행
- 각 주소별 API 호출 및 데이터 정상 반환 확인
- 오류 발견 시 → 수정 → 재테스트

테스트 케이스:
| # | 주소 | 케이스 유형 |
|---|------|-----------|
| 1 | 사당동 산 32-77 | 토지만 (임야) |
| 2 | 사당동 318-107 | 토지만 (대지) |
| 3 | 사당동 1044-23 | 일반건축물 |
| 4 | 사당동 314-12 | 공동주택 |
| 5 | 사당동 280-1 | 다필지 공동주택 |
| 6 | 사당동 1154 | 대규모 아파트 |
| 7 | 사당동 105 | 초대규모 아파트 |
| 8 | 사당동 147-29 | 복잡한 동/호명 |
| 9 | 사당동 86-6 | 비주거 건물 |

### 4.3 빌드만 실행 (/build)

```
/build
```

실행 내용:
- APK 빌드: `build/app/outputs/flutter-apk/app-release.apk`
- AAB 빌드: `build/app/outputs/bundle/release/app-release.aab`

### 4.4 서버 배포 (/deploy)

```
/deploy
```

MCP를 통해 서버 파일 수정 및 배포:
- 호스트: `root@175.119.224.71`
- 경로: `/home/webapp/goldenrabbit`

---

## 5. 버전 관리

### 5.1 버전 형식
```
X.Y.Z+N
```
- **X**: Major - 호환성 깨지는 변경
- **Y**: Minor - 기능 추가
- **Z**: Patch - 버그 수정
- **N**: Build Number - Play Store 업로드마다 증가

### 5.2 버전 업데이트 위치
`pubspec.yaml`:
```yaml
version: 1.0.2+3
```

### 5.3 CHANGELOG 작성
`docs/CHANGELOG.md`:
```markdown
## [1.0.3+4] - 2026-02-24

### 개선
- 기능 개선 내용

### 버그 수정
- 수정 내용
```

---

## 6. MCP 서버 설정

### 6.1 설정 파일
`.mcp.json`:
```json
{
  "mcpServers": {
    "goldenrabbit-server": {
      "command": "ssh",
      "args": [
        "-o", "LogLevel=ERROR",
        "-o", "StrictHostKeyChecking=no",
        "root@175.119.224.71",
        "npx -y @modelcontextprotocol/server-filesystem /home/webapp/goldenrabbit"
      ]
    }
  }
}
```

### 6.2 SSH 키 설정
서버 접속을 위해 SSH 키가 설정되어 있어야 합니다:
```bash
ssh-copy-id root@175.119.224.71
```

---

## 7. 빌드 서명 설정

### 7.1 키스토어 파일
- 위치: `android/upload-keystore.jks`
- 설정: `android/key.properties`

### 7.2 key.properties 내용
```properties
storePassword=비밀번호
keyPassword=비밀번호
keyAlias=upload
storeFile=../upload-keystore.jks
```

---

## 8. 문제 해결

### 슬래시 명령어가 인식되지 않음
→ Claude Code 세션 재시작 (`/exit` 후 다시 `claude`)

### 빌드 실패
```bash
flutter clean
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter build apk --release
```

### 서버 연결 실패
```bash
# SSH 연결 테스트
ssh root@175.119.224.71 "echo 'connected'"
```

---

## 9. 관련 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| 프로젝트 가이드 | `CLAUDE.md` | 프로젝트 구조, 명령어 |
| 업데이트 이력 | `docs/CHANGELOG.md` | 버전별 변경 사항 |
| 테스트 가이드 | `docs/test-case-review-guide.md` | 테스트 케이스 목록 |
| 마케팅 계획 | `docs/marketing-2week-plan.md` | 홍보 일정 |

---

*작성일: 2026-02-23*
