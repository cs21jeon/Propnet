# PropMap - 매물지도 서비스

## 개요

PropMap은 공인중개사(agent)별 매물지도 서비스입니다. 현재는 `goldenrabbit.biz/propnet/`에 랜딩페이지가 운영 중이며, **현재 홈페이지(`goldenrabbit.biz/`)의 매물지도 기능을 PropMap으로 이관할 계획**입니다.

> **Airtable 완전 제거 완료 (2026-03-26)**: 홈페이지의 모든 매물 데이터가 PropSheet DB로 전환됨. 지도, 카테고리, 검색, 상세 모두 PropSheet DB에서 실시간 조회.

- **PropMap 랜딩**: `https://goldenrabbit.biz/propnet/`
- **현재 홈페이지 (이관 대상)**: `https://goldenrabbit.biz/` (매물지도, 카테고리, 검색, 상세)
- **코드 위치**:
  - 랜딩: 서버 `/home/webapp/goldenrabbit/frontend/public/propnet/`
  - 홈페이지: 서버 `/home/webapp/goldenrabbit/frontend/public/` (index.html, map.html 등)
- **파일 접근**: MCP(goldenrabbit-server) 사용

## 기술 스택

| 계층 | 기술 |
|------|------|
| Frontend | 순수 HTML5 + Vanilla JS + CSS3 (빌드 없음) |
| Backend API | Flask property-manager (포트 5000) + PropSheet API |
| 웹 서버 | Nginx (정적 파일 직접 서빙) |
| 지도 | 카카오맵 SDK |
| 데이터 | PropSheet DB (PostgreSQL `goldenrabbit_db`) |

## 핵심 파일 (서버 경로)

### Frontend — 현재 홈페이지 (이관 대상)
- `/home/webapp/goldenrabbit/frontend/public/index.html` — 메인 홈페이지 (지도, 카테고리, 검색, 상세 모달)
- `/home/webapp/goldenrabbit/frontend/public/map.html` — 매물 지도 (iframe, 카카오맵)
- `/home/webapp/goldenrabbit/frontend/public/about.html` — 회사소개
- `/home/webapp/goldenrabbit/frontend/public/inquiry.html` — 상담문의

### Frontend — PropMap 랜딩
- `/home/webapp/goldenrabbit/frontend/public/propnet/index.html` — 메인 랜딩페이지
- `/home/webapp/goldenrabbit/frontend/public/js/ai-property-search.js` — AI 매물 검색
- `/home/webapp/goldenrabbit/frontend/public/js/navigation.js` — 네비게이션
- `/home/webapp/goldenrabbit/frontend/public/manifest.json` — PWA 매니페스트

### Backend API
- `/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py` — 매물 API (지도, 카테고리, 검색, 상세)
- `/home/webapp/goldenrabbit/backend/property-manager/routes/propnet_api.py` — SNS 공유 OG 메타태그

## 데이터 흐름 (현재 홈페이지)

```
index.html
  ├── [지도탭]     map.html (iframe)
  │                  └── fetch('/propsheet/api/propsheet/map-data')      → PropSheet DB
  │
  ├── [카테고리탭]  재건축(70), 고수익(71), 저가(72)
  │                  └── fetch('/propsheet/api/propsheet/category-properties') → PropSheet DB
  │
  ├── [검색탭]      조건검색 폼
  │                  └── fetch('/propsheet/api/propsheet/search-map')    → PropSheet DB
  │
  ├── [매물 클릭]   상세 모달
  │                  └── fetch('/propsheet/api/propsheet/property-detail') → PropSheet DB
  │
  └── [링크 복사]   /property/{record_id}
                     └── SNS 크롤러용 OG 메타태그 (DB 조회) → /?property={id} 리다이렉트
```

### 이미지 서빙
```
DB 대표사진 필드: "파일명.jpg (/uploads/propsheet/39/1069/파일명.jpg)"
  → propsheet.py: regex로 (/uploads/...) 추출 → photo_url
  → 프론트엔드: <img src="/uploads/propsheet/39/1069/파일명.jpg">
  → Nginx: /uploads/propsheet/ → 물리 경로 정적 서빙
```

### SNS 공유 (카카오톡 등)
```
https://goldenrabbit.biz/property/recXXX
  → Nginx → Port 5000 (propnet_api.py)
  → PropSheet DB에서 지번주소, 광고, 대표사진 조회
  → OG 메타태그 생성 → /?property=recXXX 리다이렉트
```

## API 엔드포인트

### 매물 API (PropSheet DB)
```
GET  /propsheet/api/propsheet/map-data              → 지도 마커 데이터
GET  /propsheet/api/propsheet/category-properties    → 카테고리별 매물
GET  /propsheet/api/propsheet/property-detail?id=    → 매물 상세
POST /propsheet/api/propsheet/search-map             → 조건 검색
```

### AI 매물 검색
```
POST /api/property-search
Body: { ai_location, price_range, investment, expected_yield }
```

## 배포

정적 파일이므로 빌드 과정 없음:
1. 서버의 `/frontend/public/`에 파일 복사
2. Nginx가 자동 서빙 (서비스 재시작 불필요)
3. Backend API 변경 시만: `sudo systemctl restart property-manager`

## 향후 계획: propnet.kr 마이그레이션 (Phase 1)

현재 홈페이지를 PropMap 멀티테넌트 구조로 이관:

### URL 구조
```
propnet.kr/                           → PropNet 랜딩 (현재 /propnet/)
propnet.kr/propmap/goldenrabbit/      → 금토끼부동산 매물지도 (현재 홈페이지 이관)
propnet.kr/propmap/{agent_slug}/      → 개별 agent 매물지도
```

### 작업 계획
1. 서버에 디렉토리 생성: `/frontend/public/propmap/goldenrabbit/`
2. 현재 홈페이지(index.html, map.html 등) 해당 디렉토리로 복사
3. HTML/JS에서 상대경로 확인 및 수정
4. `propnet.conf`에 location 블록 추가:
   ```nginx
   location ~ ^/propmap/([a-zA-Z0-9_-]+)(/.*)?$ {
       alias /home/webapp/goldenrabbit/frontend/public/propmap/$1/;
       try_files $uri $uri/ /propmap/$1/index.html;
   }
   ```
5. 기존 `goldenrabbit.biz/` → `/propmap/goldenrabbit/` 301 리다이렉트

### 리다이렉트 (Phase 5)
```nginx
location = / { return 301 https://propnet.kr/propmap/goldenrabbit; }
```

## Git 보안
- **절대 커밋 금지**: `.env`, API 키, DB 비밀번호, OAuth 시크릿 파일
- 커밋 전 `git diff --cached`로 민감 정보 노출 여부 반드시 확인
- 서버 `.env` 값을 코드/문서에 하드코딩 금지
