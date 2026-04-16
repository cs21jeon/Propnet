# PropNet 통합 개발 진행 기록

> 최종 업데이트: 2026-04-16
> 크로스 서비스 변경 및 인프라/공통 작업을 기록합니다.

## 2026-04-16: goldenrabbit.biz 금토끼부동산 홈페이지 전용화 + 네이버 검색 정리

- [통합/인프라] goldenrabbit.biz 역할 재정의 — 금토끼부동산 홈페이지 외 모든 서비스는 propnet.kr로 일원화
- [인프라] 서버 루트 favicon 교체: 금토끼(85KB) → PropNet 아이콘(6KB)
  - `frontend/public/favicon.ico`, `favicon.png` 교체, 기존 파일은 `favicon_backup_20260416.*`로 백업
  - 로컬: `assets/images/Propnet_icon_transparent_half size_512X512.png`를 Pillow로 ico/png 변환
  - 네이버 검색 결과의 propnet.kr 옆 아이콘이 PropNet 아이콘으로 갱신될 예정
- [인프라] Nginx `goldenrabbit.conf` 대규모 정리
  - 301 리다이렉트 추가: `/proptalk/`, `/proppedia/`, `/admin/`, `/property-manager`, `/services`, `/legal/`
  - location 블록 삭제: `/app/dashboard`, `/app/api/admin/` (백엔드 라우트 부재)
  - 유지: `/api/*`(홈페이지 의존), `/property/{id}`(SNS 공유), `/shorts`, `/(auth|webhook|deauth)/threads`, `/voiceroom/*`, `/app/api/`(구버전 앱 호환)
  - `/legal/`은 `^~` 수식어 사용으로 regex `\.html$` 블록보다 우선 매칭 처리
- [인프라] goldenrabbit.biz 전용 robots.txt + sitemap.xml 분리
  - Nginx `location = /robots.txt`에서 홈페이지만 Allow, 나머지 전부 Disallow
  - `frontend/public/sitemap_goldenrabbit.xml` 신규 — 홈페이지 1개 URL만 포함
  - 기존 propnet.kr용 `sitemap.xml`과 완전 분리 (도메인 불일치 방지)
- [PropSheet/공통] Property Manager (구 UI) 진입점을 Proppedia로 재지정
  - `backend/property-manager/app.py:126` — `redirect('/propsheet/')` → `redirect('/proppedia/')`
  - Property Manager의 후속 서비스는 Proppedia(건축물 정보 조회)이므로 역사적 연속성 유지
  - `property-manager`, `proppedia`, `propsheet` 3개 서비스 재시작
- [운영] 네이버 서치어드바이저 후속 작업 필요
  - goldenrabbit.biz: robots.txt 재수집, sitemap 재제출, 레거시 URL 10개 삭제 요청, 홈페이지 재수집
  - propnet.kr: 신규 URL 5개 수집 요청 (`/proptalk/guide`, `/proppedia/guide/`, `/guide/agent/`, `/propmap/`, `/proppedia/`)

## 2026-04-15: 법적 문서 통합 점검 + 약관/개인정보처리방침 업데이트

- [Propedia] 국외이전 동의서에서 "공공데이터 포털(한국)" 항목 삭제 (국내 API는 국외이전 대상 아님)
- [Propedia] terms.dart — OAuth 인증 토큰 수집항목 추가, VWorld API 제3자 제공 추가
- [Propedia] 랜딩 페이지 회사명 "금토끼부동산" → "PropNet (프롭넷)" 통일, datePublished 업데이트
- [Proptalk] 웹 약관/개인정보처리방침 HTML을 PropNet 통합 버전으로 전면 교체 (구버전 2026-03-01 → 통합 2026-04-04)
- [Proptalk] terms.dart — OAuth 인증 토큰 수집항목 추가, VWorld API 제3자 제공 추가
- [통합] scripts/legal/ 이용약관에 PropMap 서비스 정의 추가
- [통합] scripts/legal/ 개인정보처리방침에 OAuth 토큰 수집항목 + VWorld API 제3자 제공 추가
- 서버 6개 파일 배포 완료 (정적 파일, 재시작 불필요)

## 2026-04-13: 집합건물 전체 매도 저장 + PropMap 마커 개편 + 광고 면책 확인

- [Propedia] 집합건물 동/호 미선택 시 단일부동산 저장 분기 (앱+웹)
- [PropSheet] 현황→등록 변경 시 PropMap 광고 면책 확인 다이얼로그
- [PropMap] 마커 색상 9종 체계 (유형×거래 명도), 중복 매물 클러스터, 통합↔agent 네비게이션 버튼, 패널 레이아웃 정비
- 전 서비스(goldenrabbit.biz, propmap/, propmap/{agent_slug}/) 동일 반영

## 2026-04-13: 주간전략보고서 조치 — WebSocket 수정, 봇 차단, QA 개선, 보고 시스템 고도화

- [Proptalk] WebSocket 소켓 누수 수정 (Bad file descriptor 78회/주)
  - websocket.py: disconnect 핸들러에 room 정리 + sid↔user_id 추적 추가
  - models.py: DB 연결 풀 dead connection 자동 감지/교체
  - routes_messages.py: 백그라운드 emit 8곳에 _safe_emit() 안전장치 적용
  - app.py: ping_timeout 60→90초, ping_interval 25→30초 조정
- [인프라] IP 직접 접근 + 봇/스캐너 트래픽 차단
  - config/nginx/security-block.conf 신규 — HTTP/HTTPS default_server 444 반환
  - 차단 로그: logs/nginx/blocked_access.log
- [인프라] QA 모니터링 파이프라인 확장
  - qa_collector.py: journalctl 기반 service_errors(daily), service_error_trend_7d(weekly) 추가
  - 기존 billing_error_logs만 → 4개 서비스 에러 전체 추적으로 확장
- [인프라] 주간보고 조치 추적 시스템 구축
  - report_storage.py: propnet_report_actions 테이블 + save_actions/get_last_weekly_report 함수
  - aggregator.py: 주간보고 시 지난주 보고서+조치 결과를 COO 프롬프트에 자동 포함
  - prompts.py: COO 주간 프롬프트에 "지난주 조치 항목 추적" 섹션 추가 + 깨진 문자 수정
  - 이번 주(4/13) 조치 결과 7건 DB 저장 (resolved 4, deferred 3)

## 2026-04-12: AI 일간/주간 보고 시스템 구축

- [인프라] daily-report/ 신규 모듈 — 7개 부서 AI 에이전트 보고 시스템
  - 일간(08:00): infra, dev, qa, growth, cs → Claude haiku 분석 → COO sonnet 취합 → Gmail 발송
  - 주간(월 09:00): 전 7개 부서(+design, pm) → Claude sonnet 분석/취합 → Gmail 발송
  - 수집: DB 쿼리(propnet_users, agents, billing 등) + Nginx 로그 + systemd 상태 + git log
  - 저장: propnet_reports 테이블(JSONB) + JSON 파일 백업
  - 스케줄: systemd timer 2개 (propnet-daily-report, propnet-weekly-report)
- [인프라] 서버 배포 완료 — /home/webapp/goldenrabbit/backend/daily-report/
  - anthropic 0.34.0→0.94.0 업그레이드, markdown 라이브러리 활용
  - 이메일 마크다운→HTML 변환 (Gmail 인라인 스타일 표/볼드/리스트)
- [인프라] 헬스체크 경로 수정 (/ → 서비스별 실제 라우트), billing_daily_summary 컬럼명 수정

## 2026-04-11: 중개사 시작 가이드 전면 개편 + 파비콘/가이드 라우트 수정

- [통합] 중개사 가이드(/guide/agent/) 6개 섹션 실제 스크린샷 19장 반영
- [PropSheet] 가이드: 템플릿 DB 4종(매물장/상담신청/일정/채팅방) 설명, 매물장 입력방법 2가지, 서비스 간 연결
- [PropMap] 가이드: "나만의 매물 홈페이지" 강조, 개별/통합 지도 분리
- [Propedia] 가이드: PropSheet 자동입력 흐름, 활용 순서 재정리(검색기록→즐겨찾기→PDF→PropSheet)
- [PropSheet] guide.py trailing slash 라우트 추가 (로그인 시 /propsheet/guide/ 접근 불가 수정)
- [인프라] 루트 favicon.ico/png를 PropNet 아이콘으로 교체 (금토끼 로고 심볼릭 링크 제거)

## 2026-04-11: 승인 이메일 개선 + Proptalk PWA 설정 변경

- [통합] 승인 환영 이메일 PropSheet 링크 "PC/모바일 웹 열기" → "PC 웹 열기" 변경
- [Proptalk] manifest.json display: standalone → browser (웹앱 창 대신 브라우저 탭)
- [PropMap] map.html 로고 경로 변경 + 레거시 로고 파일 정리

## 2026-04-11: Agent 환경 셋업 복구 + 필드 정합성 + 문의 API 수정

- [PropSheet] 레코드생성일자 필드 통합 마이그레이션 (날짜↔레코드생성일자 불일치 해소)
- [PropSheet] 컬럼 show/hide 변경이 서버 view config에 자동 저장되도록 수정
- [PropSheet] 전체 워크스페이스 필드 정합성 감사 — 유령 필드/레거시 정리 (20건→0건)
- [PropMap] 통합지도 문의 API 엔드포인트 수정 (존재하지 않는 URL → /api/submit-inquiry)
- [PropMap] propnet agent 매물지도 페이지 생성
- [인프라] Agent 가입 강제완료 시 환경 셋업 타임아웃 분석 및 수동 복구 스크립트

## 2026-04-10: PropSheet ↔ Proppedia 양방향 연동

- [PropSheet] 부동산 DB에 "Proppedia 조회" 버튼 추가 (slug 기반, 모든 agent 공통)
- [Proppedia] 저장 성공 모달에 "PropSheet에서 보기" 바로가기 추가
- [인프라] Nginx /api/auth/ → 5010 라우팅 추가 (SSO session-sync 수정)

## 2026-04-10: 서비스 간 크로스 링크 네비게이션 추가

- [통합] propnet.kr 메인 → Proptalk 사용가이드 링크 추가 (서비스 카드 + 푸터)
- [Proptalk] 랜딩 페이지 헤더/푸터에 "PropNet 서비스 모두 보기" 버튼 추가
- [Proptalk] 가이드 페이지 헤더에 "PropNet 홈" 링크 추가
- [Propedia] 랜딩 페이지 헤더/푸터에 "PropNet 홈" 버튼 추가
- [Propedia] 가이드 페이지 헤더에 "PropNet 홈" 링크 추가
- [문서] CLAUDE.md에 정적 페이지 서버 경로 매핑 테이블 추가
  - propnet.kr 루트는 `frontend/public/propnet/index.html` (index.html 아님)
  - Nginx 설정 2개 분리: goldenrabbit.conf + propnet.conf

## 2026-04-10: Proptalk 사용 가이드 전면 리뉴얼

- [Proptalk] guide.html 6개→8개 섹션 개편, 최신 캡쳐 이미지 30장 교체
- [Proptalk] 중개사 전용 PropSheet 연동 섹션 신설

## 2026-04-09: 랜딩 페이지 네비게이션 개선 + Proptalk 계정 삭제 수정

- [통합] propnet.kr 랜딩 페이지에 중개사 시작 가이드 링크 추가 (헤더/CTA/푸터)
- [통합] PropMap 카드 "서비스 예정" → "운영 중" 전환, /propmap/ 링크 연결
- [통합] PropSheet 배지 "중개사 전용" 표기 추가
- [Proptalk] 요금제 Agent Regular "기본(1시간)" 표기, Propsheet+PropMap 포함 설명 추가
- [Proptalk] 가이드 페이지에 초대코드 참여 설명+스크린샷 추가
- [Proptalk] 계정 삭제 FK 위반 오류 수정: hard delete → soft delete 전환
  - voiceroom.users에 is_active 컬럼 추가, 탈퇴 시 개인정보 익명화
  - 재가입 시 is_active=TRUE 자동 재활성화

## 2026-04-09: Proptalk 음성 요약 검색 + 서버 백업 실패 알림

- [Proptalk] 음성 요약 검색 기능 추가 (웹+앱, 5개 필드 ILIKE 검색)
- [인프라] daily_backup.sh 실행 권한 수정 + 실패 시 이메일 알림 추가

## 2026-04-09: Proptalk 읽음 처리 개선 + PropSheet 채팅등록일시 + 문서 구조 개편

- [Proptalk] mark-read 전면 개선: 발신자 자동 읽음 처리, WebSocket 개인 room 전파
- [PropSheet] 채팅등록일시 system_generated_value 필드 추가 (Proptalk 동기화 연동)
- [PropSheet] 정렬 설정 자동 저장 (toggleSort → saveCurrentView)
- [관리자] 공지사항 CRUD + app_notice_service target_app 필터
- [인증] billing_check: admin도 agent owner로 PropSheet 접근 허용
- [회원가입] subagent 역할 직접 가입 차단 (초대 전용)
- [Nginx/SEO] sitemap, robots.txt, PropMap/Proptalk 랜딩 업데이트
- [통합] 문서 구조 개편: 오래된 docs 6개 삭제 → archive 이동
- [통합] pushupdate 스킬 추가 (.claude/skills/pushupdate/)

## 2026-04-08: PropMap 통합 매물지도 구축

- [PropMap] propnet.kr/propmap/ 통합 매물지도 서비스 신규 구축
- [PropSheet] agents-public API: center 좌표 동적화

## 2026-04-07: 통합 인증 체계 완성 + agent 온보딩

- [인증] propnet_users SSoT + SSO 쿠키(propnet.kr) + 보안 수정
- [PropSheet] agent_slug 기반 URL 구조 전환, require_agent_access 데코레이터
- [인증] agent 신청→심사→결제→활성화 흐름, billing 통합
- [Proptalk] 라이트/다크모드 배경-콘텐츠 색상 대비 개선

## 2026-04-04: 물건종류 필터 + propnet.kr 마이그레이션

- [PropSheet/PropMap] 매물지도 + 조건검색에 물건종류(세부유형) 필터 추가
- [인프라] propnet.kr 도메인 마이그레이션 Phase 0~4 + SSO 쿠키 전환

## 2026-03-26: Airtable 완전 제거

- [PropSheet] 모든 매물 데이터 → PropSheet DB + 로컬 파일 시스템 전환
- [전체] Airtable API, backup 스크립트, backup 디렉토리 제거 완료
