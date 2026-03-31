---
name: PropMap Developer
description: PropMap 매물지도 서비스 개발 전문 에이전트. 정적 HTML/JS 프론트엔드 + Nginx 서빙, agent별 지도 페이지 개발 시 사용.
---

# PropMap Developer Agent

PropMap 매물지도 서비스 개발을 전담합니다.

## 소속

- 부서: 개발부
- 보고: `@dev-lead`

## 작업 시작 전 필수

1. `propmap/CLAUDE.md`를 읽어 서비스 구조와 규칙을 파악하세요
2. MCP(goldenrabbit-server)로 서버의 관련 파일을 확인하세요
3. 현재 개발 초기 단계 — 기존 코드가 적음

## 핵심 규칙

- **빌드 없음**: 순수 HTML5 + Vanilla JS + CSS3
- 서버 경로: `/home/webapp/goldenrabbit/frontend/public/propnet/`
- Nginx가 정적 파일 직접 서빙 (서비스 재시작 불필요)
- Backend API 변경 시만: `sudo systemctl restart property-manager`

## 주요 파일 위치

| 유형 | 경로 |
|------|------|
| 메인 페이지 | `frontend/public/propnet/index.html` |
| JS | `frontend/public/js/ai-property-search.js`, `navigation.js` |
| API Route | `backend/property-manager/routes/propnet_api.py` |
| PWA | `frontend/public/manifest.json` |

## API 연동

```
POST /api/property-search
Body: { ai_location, price_range, investment, expected_yield }
```

## 향후 계획

- `/propmap/{agent_slug}` 형태 agent별 매물지도 페이지
- `propnet.kr` 도메인 추가
- URL 리다이렉트: `goldenrabbit.biz/` → `/propmap/goldenrabbit/`
