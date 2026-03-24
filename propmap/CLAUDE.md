# PropMap - 매물지도 서비스

## 개요

PropMap은 공인중개사(agent)별 매물지도 서비스입니다. 현재 개발 초기 단계로, 랜딩페이지만 운영 중입니다.

- **URL**: `https://goldenrabbit.biz/propnet/`
- **코드 위치**: 서버 `/home/webapp/goldenrabbit/frontend/public/propnet/`
- **파일 접근**: MCP(goldenrabbit-server) 사용

## 기술 스택

| 계층 | 기술 |
|------|------|
| Frontend | 순수 HTML5 + Vanilla JS + CSS3 (빌드 없음) |
| Backend API | Flask property-manager (포트 5000) |
| 웹 서버 | Nginx (정적 파일 직접 서빙) |

## 핵심 파일 (서버 경로)

### Frontend
- `/home/webapp/goldenrabbit/frontend/public/propnet/index.html` — 메인 랜딩페이지
- `/home/webapp/goldenrabbit/frontend/public/js/ai-property-search.js` — AI 매물 검색
- `/home/webapp/goldenrabbit/frontend/public/js/navigation.js` — 네비게이션
- `/home/webapp/goldenrabbit/frontend/public/manifest.json` — PWA 매니페스트

### Backend API
- `/home/webapp/goldenrabbit/backend/property-manager/routes/propnet_api.py` — PropMap API

## API 연동

```
POST /api/property-search
Body: { ai_location, price_range, investment, expected_yield }
```

## Git 보안
- **절대 커밋 금지**: `.env`, API 키, DB 비밀번호, OAuth 시크릿 파일
- 커밋 전 `git diff --cached`로 민감 정보 노출 여부 반드시 확인
- 서버 `.env` 값을 코드/문서에 하드코딩 금지

## 배포

정적 파일이므로 빌드 과정 없음:
1. 서버의 `/frontend/public/propnet/`에 파일 복사
2. Nginx가 자동 서빙 (서비스 재시작 불필요)
3. Backend API 변경 시만: `sudo systemctl restart property-manager`

## 향후 계획

- `/propmap/{agent_slug}` 형태의 agent별 매물지도 페이지
- `propnet.kr` 도메인 추가
- `goldenrabbit.biz/` → `/propmap/goldenrabbit/` 301 리다이렉트
