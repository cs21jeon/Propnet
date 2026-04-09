# PropNet 가이드 페이지 현황

> 최종 업데이트: 2026-04-09

## 가이드 URL 총괄

| 서비스 | URL (propnet.kr) | 페이지 수 | 스크린샷 | 완성도 |
|--------|------------------|----------|---------|--------|
| **Agent 통합** | `/guide/agent/` | 1 | 플레이스홀더 | 텍스트 완성, 이미지 미완 |
| **Propedia** | `/proppedia/guide/` | 1 | 다수 포함 | 완성 |
| **Proptalk** | `/proptalk/guide` | 1 | 17장 | 완성 |
| **PropSheet** | `/propsheet/guide/*` | 18 | - | 완성 |
| **PropMap** | - | 0 | - | 미제작 |

## 파일 위치

### Agent 통합 가이드
- **URL**: `https://propnet.kr/guide/agent/`
- **로컬**: `marketing/guide/agent/index.html`
- **서버**: `/home/webapp/goldenrabbit/frontend/public/guide/agent/index.html`
- **서빙**: Nginx 정적 (root 기본 서빙, 별도 location 블록 불필요)
- **내용**: 6개 섹션 (가입 → 승인 → PropSheet → PropMap → Propedia → Proptalk)
- **TODO**: 스크린샷 캡처 및 교체, 연락처(010-XXXX-XXXX) 실제 번호로 변경

### Propedia 가이드
- **URL**: `https://propnet.kr/proppedia/guide/`
- **로컬**: `propedia/marketing/proppedia/guide/index.html`
- **서버**: `/home/webapp/goldenrabbit/frontend/public/proppedia/guide/index.html`
- **서빙**: Nginx location `^~ /proppedia/guide/`
- **내용**: 10개 섹션 (시작 → 회원가입 → 검색 3종 → 결과 → 즐겨찾기 → 기록 → PDF → 프로필)

### Proptalk 가이드
- **URL**: `https://propnet.kr/proptalk/guide`
- **로컬**: `proptalk/marketing/proptalk/guide.html`
- **서버**: `/home/webapp/goldenrabbit/chat_stt/marketing/proptalk/guide.html`
- **서빙**: Flask `send_from_directory` (포트 5030, Nginx 프록시)
- **내용**: 6개 섹션 (시작 → 로그인 → 채팅방 → 음성업로드 → 데이터확인 → 프로필)

### PropSheet 가이드 (18페이지)
- **URL**: `https://propnet.kr/propsheet/guide/{페이지명}`
- **서버**: `/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/guide/`
- **서빙**: Flask Jinja2 템플릿 (포트 5020, Nginx 프록시)
- **페이지 목록**:

| # | 경로 | 내용 |
|---|------|------|
| - | `index.html` | 가이드 목차/인덱스 |
| - | `_base.html` | 공통 레이아웃 템플릿 |
| 1 | `getting-started` | 시작하기 (로그인, 워크스페이스) |
| 2 | `workspaces` | 워크스페이스 관리 |
| 3 | `databases` | 데이터베이스 관리 |
| 4 | `records` | 레코드 CRUD |
| 5 | `fields` | 필드 타입 |
| 6 | `views` | 뷰 (그리드/캘린더) |
| 7 | `filter-sort-search` | 필터, 정렬, 검색 |
| 8 | `formulas` | 수식 |
| 9 | `attachments` | 파일 첨부 |
| 10 | `sharing` | 공유 |
| 11 | `members` | 멤버 관리 |
| 12 | `calendar` | 캘린더 뷰 |
| 13 | `csv-export` | CSV 내보내기 |
| 14 | `history` | 변경 이력 |
| 15 | `property-types` | 부동산 유형 (단일/부분/집합) |
| 16 | `subagents` | 서브에이전트 |
| 17 | `proptalk` | Proptalk 연동 |
| 18 | `faq` | 자주 묻는 질문 |

### PropMap 가이드
- **상태**: 미제작
- **예상 URL**: `/propmap/guide/` 또는 `/guide/propmap/`

## 도메인 통일 현황

모든 가이드의 canonical URL, OG 태그, 내부 링크가 `propnet.kr`로 통일됨 (2026-04-09).

| 항목 | goldenrabbit.biz | propnet.kr |
|------|:---:|:---:|
| Agent 가이드 링크 | - | O |
| Propedia 가이드 canonical | - | O |
| Proptalk 가이드 canonical | - | O (수정완료) |
| PropSheet 가이드 | - | O (Flask 자동) |

## CSS 디자인 시스템

Agent/Propedia/Proptalk 가이드는 동일한 CSS 프레임워크 사용:
- **CSS Variables**: `--primary-color: #2196F3`, `--primary-dark: #1976D2`
- **폰트**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR'`
- **최대 너비**: `800px`
- **주요 클래스**: `.guide-section`, `.steps`, `.tip`, `.screenshot`, `.screenshot-row`, `.toc`, `.cta-banner`
- **반응형**: `@media (max-width: 600px)`

PropSheet 가이드는 `_base.html` Jinja2 템플릿 기반으로 별도 스타일 체계.

## 향후 작업

- [ ] Agent 가이드 스크린샷 캡처 및 교체
- [ ] Agent 가이드 연락처 실제 번호로 변경
- [ ] PropMap 가이드 제작
- [ ] 각 서비스 랜딩페이지에서 가이드 링크 추가
- [ ] Agent 가이드를 PropNet 랜딩(propnet.kr)에서 링크
