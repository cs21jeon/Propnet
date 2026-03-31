# propnet.kr 도메인 마이그레이션 계획

> 작성일: 2026-03-25
> 상태: 계획 수립 완료, Phase 0 일부 진행 (propnet.conf 작성, 도메인 연결 완료)

## Context

goldenrabbit.biz에서 운영 중인 서비스들을 propnet.kr로 이전하면서, 멀티테넌트(agent_slug) URL 구조를 도입한다. goldenrabbit.biz는 금토끼부동산 전용 홈페이지로 축소하고, propnet.kr을 플랫폼 도메인으로 사용한다.

## URL 매핑 요약

| 현재 (goldenrabbit.biz) | 신규 (propnet.kr) | 비고 |
|---|---|---|
| `/` (매물지도) | `/propmap/goldenrabbit` | 멀티테넌트 |
| `/propsheet/*` | `/propsheet/goldenrabbit/*` | 멀티테넌트 |
| `/app/` (PWA) | `/proppedia/` | PWA 앱 |
| `/proppedia/` (랜딩) | `/proppedia/landing/` | 마케팅 페이지 |
| `/app/api/*` | `/proppedia/api/*` | 앱 API |
| `/app/dashboard` | `/proppedia/dashboard` | 관리자 |
| `/proptalk/` (랜딩) | `/proptalk/home` | 마케팅 페이지 |
| `/proptalk/admin/*` | `/proptalk/dashboard/*` | 관리자 |
| `/proptalk/billing/*` | `/proptalk/billing/*` | 변경 없음 |
| `/voiceroom/*` | `/voiceroom/*` | 변경 없음 (앱 의존) |
| `/api/*` | `/api/*` | PropNet API 유지 |

## 마이그레이션 순서

서버사이드만 수정하면 되는 서비스 먼저, Flutter 앱 의존 서비스는 나중에.

---

### Phase 0: 인프라 준비

**상태**: 진행 중 (propnet.conf 작성 완료, 도메인 연결 완료)

1. ~~카페24에서 propnet.kr 도메인 연결~~ (완료)
2. ~~propnet.conf 작성~~ (완료, `/home/webapp/goldenrabbit/config/nginx/propnet.conf`)
3. Nginx symlink + certbot SSL 발급
   ```bash
   sudo ln -sf /home/webapp/goldenrabbit/config/nginx/propnet.conf /etc/nginx/sites-enabled/propnet
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d propnet.kr -d www.propnet.kr
   ```
4. `.env`에 `PROPNET_DOMAIN=propnet.kr` 추가

---

### Phase 1: PropMap 멀티테넌트

**이유**: 정적 HTML이라 가장 간단. 디렉토리 이동 + Nginx만 수정.

**작업**:
1. 서버에 디렉토리 생성: `/home/webapp/goldenrabbit/frontend/public/propmap/goldenrabbit/`
2. 현재 root의 index.html 및 관련 파일을 해당 디렉토리로 복사
3. HTML/JS에서 상대경로 확인 및 수정
4. `propnet.conf`에 location 블록 추가:
   ```nginx
   location ~ ^/propmap/([a-zA-Z0-9_-]+)(/.*)?$ {
       alias /home/webapp/goldenrabbit/frontend/public/propmap/$1/;
       try_files $uri $uri/ /propmap/$1/index.html;
       expires 1h;
   }
   ```
5. propnet.kr 루트(`/`)는 현재 goldenrabbit.biz/propnet 페이지를 그대로 사용
   - `/home/webapp/goldenrabbit/frontend/public/propnet/` 디렉토리의 기존 파일 활용
   ```nginx
   location / {
       alias /home/webapp/goldenrabbit/frontend/public/propnet/;
       try_files $uri $uri/ /index.html;
   }
   ```

**수정 파일**:
- `/home/webapp/goldenrabbit/config/nginx/propnet.conf`
- `/home/webapp/goldenrabbit/frontend/public/` → `/propmap/goldenrabbit/`로 파일 이동

---

### Phase 2: PropSheet 멀티테넌트

**이유**: 서버 렌더링(HTMX)이라 모바일 앱 의존 없음.

**작업**:
1. `agents` 테이블 생성 (slug → agent_id 매핑)
   ```sql
   CREATE TABLE IF NOT EXISTS agents (
       id SERIAL PRIMARY KEY,
       slug VARCHAR(100) UNIQUE NOT NULL,
       name VARCHAR(200) NOT NULL,
       created_at TIMESTAMP DEFAULT NOW()
   );
   INSERT INTO agents (slug, name) VALUES ('goldenrabbit', '금토끼부동산');
   ```
2. `routes/propsheet.py`에 `/<agent_slug>/` 프리픽스 라우트 추가
   - `/<agent_slug>/workspaces` → agent별 워크스페이스 목록
   - `/<agent_slug>/workspace/<ws_slug>/database/<db_slug>` → DB 뷰
3. agent_slug로 agent_id 조회 후 세션에 저장, 기존 `_get_filtered_workspaces()` 필터 활용
4. 기존 `/propsheet/workspaces` 라우트는 호환성을 위해 유지

**수정 파일**:
- `/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py` - agent_slug 라우트 추가
- DB: `agents` 테이블 생성

---

### Phase 3: Proppedia URL 변경

**이유**: Flutter PWA + 모바일 앱 URL 변경 필요. 가장 복잡.

**작업**:
1. **Nginx (propnet.conf)**: `/app/*` 블록을 `/proppedia/*`로 변경
   ```nginx
   # Proppedia API
   location /proppedia/api/ {
       proxy_pass http://127.0.0.1:5010/api/;
       ...
   }
   # Proppedia Dashboard
   location /proppedia/dashboard {
       proxy_pass http://127.0.0.1:5010/dashboard;
       ...
   }
   # Proppedia Landing (정적)
   location /proppedia/landing/ {
       alias /home/webapp/goldenrabbit/frontend/public/proppedia/;
       try_files $uri $uri/ /proppedia/landing/index.html;
   }
   # Proppedia PWA (Flutter web)
   location /proppedia/ {
       alias /home/webapp/goldenrabbit/frontend/public/app/;
       try_files $uri $uri/ /proppedia/index.html;
   }
   ```
2. **Flask (port 5010)**: AppPrefixMiddleware에서 `/proppedia`도 지원
3. **Flutter Web**: `flutter build web --base-href /proppedia/`로 리빌드
4. **Flutter App (Android)**: 4개 파일 URL 변경
   - `propedia/lib/core/network/api_client.dart` → baseUrl을 `https://propnet.kr`로
   - `propedia/lib/presentation/widgets/property/property_image.dart` → 이미지 URL
   - `propedia/lib/presentation/screens/property/property_detail_screen.dart` → 공유 URL
   - `propedia/lib/presentation/widgets/common/app_drawer.dart` → 링크 URL

**중요**: goldenrabbit.biz의 `/app/api/*` 프록시는 **삭제하지 않고 유지** (구버전 앱 호환)

---

### Phase 4: Proptalk URL 변경

**작업**:
1. **Flask 라우트 변경**:
   - `/proptalk/` (랜딩) → `/proptalk/home`
   - `/proptalk/admin/*` → `/proptalk/dashboard/*`
2. **Flutter App**: 5개 파일 URL 변경
   - `proptalk/flutter/lib/services/api_service.dart` → baseUrl
   - `proptalk/flutter/lib/services/socket_service.dart` → 소켓 URL
   - `proptalk/flutter/lib/services/billing_service.dart` → 결제 URL
   - `proptalk/flutter/lib/constants/terms.dart` → 약관 URL
   - `proptalk/flutter/lib/screens/settings_screen.dart` → 관리자 URL
3. `/voiceroom/*` 경로는 양쪽 도메인 모두 유지 (변경 없음)

---

### Phase 5: 리다이렉트 및 정리

goldenrabbit.biz의 `goldenrabbit.conf`를 리다이렉트 중심으로 전환:

```nginx
# 웹 사용자 리다이렉트
location = / { return 301 https://propnet.kr/propmap/goldenrabbit; }
location /propsheet/ { return 301 https://propnet.kr/propsheet/goldenrabbit$request_uri; }
location /proppedia/ { return 301 https://propnet.kr/proppedia/landing/; }
location /proptalk/ { return 301 https://propnet.kr/proptalk/home; }

# 구버전 앱 API는 유지 (301은 POST에 불안정)
location /app/api/ { proxy_pass http://127.0.0.1:5010; ... }
location /voiceroom/ { proxy_pass http://127.0.0.1:5030; ... }
```

**정적 리소스** (`/airtable_backup/`, `/uploads/`) 도 양쪽에서 계속 서빙.

---

## 검증 방법

각 Phase 완료 후:
1. `sudo nginx -t` → Nginx 문법 검증
2. `curl -I https://propnet.kr/<path>` → HTTP 상태 확인
3. 브라우저에서 실제 접속 테스트
4. goldenrabbit.biz 구 URL → 301 리다이렉트 확인
5. Flutter 앱 API 호출 테스트 (구/신 도메인 모두)

## 주의사항

- **구버전 Flutter 앱**: goldenrabbit.biz의 API 프록시(`/app/api/`, `/voiceroom/`)는 최소 6개월 유지
- **세션 쿠키**: propnet.kr용 SESSION_COOKIE_DOMAIN 설정 필요
- **OG 메타태그/SEO**: 각 랜딩 페이지의 canonical URL, og:url 업데이트
- **서버 RAM 956MB**: 새 서비스 추가 아닌 라우팅 변경이므로 부하 없음
