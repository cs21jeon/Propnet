# PropNet 통합 개발 진행 기록

> 최종 업데이트: 2026-04-16
> 크로스 서비스 변경 및 인프라/공통 작업을 기록합니다.

## 2026-04-16: 동별 클러스터링 + 부속지번 수렴 (Week 2~4 + 샘플 워크스페이스)

- [PropMap/PropSheet/Propedia] 대단지(파크리오 등) 매물 표시가 지번 1점에 뭉치던 문제 해결
  - "지번 중심" → "건물 중심" 좌표 체계로 전환
  - VWorld `LT_C_BLDGINFO` (GIS건물통합 WFS) 기반 동별 폴리곤·좌표 확보
  - 부속지번(신천동 20-6 등) → 본번(신천동 17/20) 자동 리다이렉트
- [PropSheet DB] 신규 공용 캐시 테이블 `building_dong_geometry`
  - `bd_mgt_sn`(건물관리번호 25자 PK) + `pnu/dong_nm` UNIQUE + GIN geometry
  - 실제 공공 데이터 기반 **15,096건 동 캐시** 축적
- [PropSheet DB] 운영 8개 + 샘플 3개 = **11개 agent 매물 테이블** 스키마 정합화
  - `bd_mgt_sn` 컬럼 + partial index (CONCURRENTLY, 무중단)
  - `coordinates_lat_orig` / `coordinates_lon_orig` 백업 컬럼 (C안)
  - 480건 기존 좌표 `_orig`에 백업 후 건물 중심으로 덮어쓰기
- [PropSheet/공통] UI 내부 시스템 필드 5개 숨김 처리
  - `schema_service.py`의 SSoT NOT IN 확장: `bd_mgt_sn`, `coordinates_lat/lon`, `coordinates_lat_orig/lon_orig`
  - PropSheet/Propedia/PropNet 모든 agent + 샘플 워크스페이스에 적용
- [PropSheet] 새 공유 서비스 `ldareg_service.py` (NSDI 대지권등록정보 래퍼, 15056691)
- [PropSheet] 새 확장 `cadastral_service_dong_ext.py`
  - `get_building_by_coord`, `get_buildings_by_pnu`, `cache_building_geometry`, `resolve_to_main_pnu`
  - VWorld WFS Filter XML 제거 → `LP_PA_CBND_BUBUN` attrFilter + BBOX 400m 후처리
- [PropSheet] 새 라우트 `/api/propsheet/map/dong-coords` (property-manager + propsheet Blueprint 양쪽 등록)
- [PropSheet] `propsheet_save_service.py` 매물 저장 시 동 필드 폴백 강화
- [PropMap] 동 단위 클러스터 공통 모듈 `propmap/js/dong-cluster-renderer.js`
  - 카카오맵 `zoom_changed` + `idle` 리스너, level<=3에서 동별 렌더
  - 매물 있음 파랑 마커(카운트+동명) / 매물 없음 회색 점선 윤곽
  - 중복 요청 방지 캐시, 기존 `createClusterPopup` 재사용
- [PropMap] `propmap/map.html` `createClusterPopup` 확장 — 대표 이미지 + "동별 보기" 버튼 + 매물 동 배지
- [PropMap] 3곳 동기 (map.html 메인 + index.html iframe 검색결과 + agent별 dir)
- [Propedia 웹] `frontend/public/app/result.html` — 집합부동산 저장 시 `동` 빈 값 경고 표시
- [스크립트] `scripts/warm_building_cache.py` — 캐시 워밍 + 배치 재좌표화
  - `--dry-run/--agent/--rate-limit/--fallback-ldareg` 옵션
  - 정교화된 매칭 로직 `_normalize_dong` + `_match_dong`
- [스크립트] `scripts/_week4_5_template_migrate.sh` + `_template_dryrun.py` — 샘플 워크스페이스 전용 원샷 마이그레이션
- [PropMap] 매칭률: 3.6% → 5.5% (전체 477건 기준, 상대 +53%)
  - goldenrabbit 집합: 18.3% 유지 + 좌표 정확도 향상 (24건 덮어쓰기, 평균 22.3m)
  - 큰 좌표 이동(100m+) 2건: 사당동 1157 (197m), 사당동 301-3 (260m) — 수동 검토 대상
- [운영] 기능 플래그 `ENABLE_DONG_CLUSTERING=true` — 실사용자 공개 운영 중
- 선행 조사 문서: `docs/research-dong-coordinates-2026-04-16.md`, `docs/vworld-16-api-final-proposal-2026-04-16.md`
- 설계 문서: `docs/prd-propmap-dong-clustering.md`, `docs/tech-design-dong-clustering.md`, `docs/infra-dong-clustering-schema.md`, `docs/design-dong-clustering-ux.md`
- 배포/QA 문서: `docs/deploy-log-dong-clustering-week2.md`, `docs/week3-deployment-guide.md`, `docs/week3-wfs-test-results.md`, `docs/week3-qa-report.md`, `docs/week4-final-qa-report.md`, `docs/week4-5-final-consolidated-report.md`
- 증거 스크린샷: `propmap-initial.png`, `propmap-dong-clusters-final.png`, `propmap-zoom-out.png` (Playwright E2E)
- Week 5 이관 과제: 매물등록 UI 동 필수화, `complex_master` 테이블(K-apt 연동) 기반 단지 통합, BLD_DIFF 케이스 분석

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
