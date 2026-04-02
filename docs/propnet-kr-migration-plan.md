# propnet.kr 도메인 마이그레이션 (v4)

> 최종 업데이트: 2026-04-02 — Phase 0~4 실행 완료, Phase 5 대기

## 진행 상태

| Phase | 상태 | 날짜 | 내용 |
|-------|------|------|------|
| Phase 0 | ✅ 완료 | 2026-04-02 | SSL 발급, propnet.conf v4, Kakao SDK, Google OAuth 3개 Web Client |
| Phase 1 | ✅ 완료 | 2026-04-02 | `/propmap/goldenrabbit/` Nginx alias, 루트(`/`) PropNet 랜딩 |
| Phase 2 | ✅ 완료 | 2026-04-02 | agents 테이블 slug 확인, propsheet.py agent_slug 라우트, OAuth 도메인 동적 처리 |
| Phase 3 | ✅ 완료 | 2026-04-02 | `/proppedia/` 정적 HTML, `/proppedia/landing/`, `/proppedia/api/*`, Flask 미들웨어 |
| Phase 4 | ✅ 완료 | 2026-04-02 | `/proptalk/landing`, Flutter 앱 URL 변경 (6파일), v1.0.5+8 AAB Play Store 업로드 |
| Phase 5 | ⏳ 대기 | - | goldenrabbit.biz 리다이렉트 (사용자 업데이트 확인 후) |

## 완료된 작업 상세

### Phase 0: 인프라 준비
- propnet.kr 도메인 연결 (카페24)
- Let's Encrypt SSL 발급 (만료: 2026-07-01, 자동 갱신)
- propnet.conf v4 전면 재작성 (통합 대시보드, 법적 문서, WebSocket timeout 반영)
- Kakao Maps JavaScript SDK 도메인 등록 (플랫폼 키 > JavaScript 키)
- Google Cloud Console: 3개 Web Client에 propnet.kr JavaScript 원본 + redirect URI 추가
  - Propsheet_Web, Proppedia Web, Proptalk Web

### Phase 1: PropMap 멀티테넌트
- `/propmap/goldenrabbit/` → Nginx alias로 기존 `/frontend/public/` 매핑
- HTML이 절대경로(`/images/`, `/js/`, `/propsheet/api/`) 사용 → 파일 복사 불필요
- `propnet.kr/` 루트 → `/frontend/public/propnet/index.html` (PropNet 랜딩)
- Proppedia 사이드메뉴 "금토끼부동산 매물정보" 링크 → `/propmap/goldenrabbit/` 수정

### Phase 2: PropSheet 멀티테넌트
- agents 테이블에 goldenrabbit slug 이미 존재 확인 (id=1, slug='goldenrabbit')
- propsheet.py에 agent_slug 라우트 추가 (3개):
  - `/<agent_slug>/` → 기본 WS DB 목록
  - `/<agent_slug>/<db_slug>` → 기본 WS 특정 DB
  - `/<agent_slug>/w/<ws_slug>/<db_slug>` → 추가 WS DB
- `_RESERVED_SLUGS`로 기존 라우트 충돌 방지
- google_auth_service.py: 도메인별 동적 redirect URI (`_get_redirect_uri(host)`)
- oauth.py: `request.host` 전달

### Phase 3: Proppedia URL 변경
- AppPrefixMiddleware: `/proppedia` 프리픽스 지원 추가 (기존 `/app` 호환 유지)
- Nginx: `/proppedia/api/*`, `/proppedia/landing/`, `/proppedia/` 라우트 추가
- `/proppedia/landing/` → 마케팅 랜딩 (기존 proppedia/ 디렉토리)
- `/proppedia/` → 정적 HTML 웹앱 (기존 app/ 디렉토리, **flutter build web 금지**)

### Phase 4: Proptalk URL 변경
- billing_web.py: `/proptalk/landing` 라우트 추가 (기존 `/proptalk/`도 유지)
- Flutter 앱 URL 변경 (6개 파일):
  - api_service.dart: baseUrl → `propnet.kr/voiceroom`
  - socket_service.dart: wsBaseUrl → `propnet.kr` (별도 변수)
  - billing_service.dart: billingWebUrl → `propnet.kr/proptalk/billing/`
  - terms.dart: 모든 URL 6개 → `propnet.kr`
  - settings_screen.dart: 관리자 → `propnet.kr/admin/`
- v1.0.5+8 AAB 빌드 → Play Store 업로드 완료

## 남은 작업 (TODO)

### 즉시 (이번 주)
- [ ] Proptalk 사용자 2-3명에게 업데이트 연락
- [ ] Proptalk 사용자 전원 업데이트 확인

### 단기 (2주 내)
- [ ] Proppedia Flutter 앱 URL 변경 (4파일: api_client.dart, property_image.dart, property_detail_screen.dart, app_drawer.dart)
- [ ] Proppedia v1.0.4 AAB 빌드 + Play Store 배포
- [ ] Proppedia 앱 내 공지 (`/app/api/notices`): "서비스 주소가 propnet.kr로 변경됩니다"
- [ ] Proppedia 웹페이지 마이그레이션 배너 추가

### 중기 (1개월 내)
- [ ] Phase 5: goldenrabbit.biz 웹페이지 301 리다이렉트 적용
  - `/propsheet/` → `propnet.kr/propsheet/goldenrabbit/`
  - `/proppedia/` → `propnet.kr/proppedia/landing/`
  - `/proptalk/` → `propnet.kr/proptalk/landing`
  - `/` → `propnet.kr/propmap/goldenrabbit`
  - **API 프록시는 유지**: `/app/api/*`, `/voiceroom/*`
- [ ] 강제 업데이트 알림 기능 구현 (Proppedia + Proptalk 공통)
- [ ] 네이버 블로그 도메인 변경 공지 포스팅
- [ ] SEO: canonical URL, sitemap.xml, robots.txt 업데이트

### 장기 (6개월 후)
- [ ] goldenrabbit.biz API 프록시 제거 (`/app/api/*`, `/voiceroom/*`)
- [ ] Google Cloud Console에서 goldenrabbit.biz redirect URI 제거
- [ ] Kakao SDK에서 goldenrabbit.biz 도메인 제거

## 발견된 주의사항

- **Kakao Maps API**: propnet.kr은 JavaScript SDK 도메인에 등록해야 함 (플랫폼 키 > JavaScript 키)
- **PropMap HTML 절대경로**: 파일 복사 대신 Nginx alias 방식이 적합
- **propnet.conf certbot 라인**: `managed by Certbot` 라인 수동 편집 시 보존 필수
- **Google OAuth 전파 시간**: redirect URI 변경 후 5분~수시간 소요
- **PropSheet 쿠키 도메인**: goldenrabbit.biz 쿠키는 propnet.kr에서 무효 → 도메인별 재로그인 필요
- **Proptalk wsBaseUrl**: API baseUrl과 별도 변수로 하드코딩 → 함께 수정 필수
- **Propedia 웹 = 정적 HTML**: `flutter build web` 사용 금지 (CLAUDE.md Rule 12)

## 서버 설정 파일

- Nginx (propnet.kr): `/home/webapp/goldenrabbit/config/nginx/propnet.conf`
- Nginx (goldenrabbit.biz): `/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf`
- PropSheet 라우트: `/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py`
- PropSheet OAuth: `/home/webapp/goldenrabbit/backend/property-manager/services/google_auth_service.py`
- Proppedia 미들웨어: `/home/webapp/goldenrabbit/backend/proppedia/app.py`
- Proptalk 랜딩: `/home/webapp/goldenrabbit/chat_stt/server/billing_web.py`
