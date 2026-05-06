# PropValue - 재개발/재건축 정비구역 지도

## 개요

PropValue는 수도권(서울/경기/인천) 재개발/재건축 정비구역 현황을 카카오맵 위에 표시하는 공개 서비스입니다.

- **URL**: `propnet.kr/propvalue/`
- **서버 경로**: `/home/webapp/goldenrabbit/frontend/public/propvalue/`
- **데이터**: PostgreSQL `redevelopment_zones` 테이블
- **API**: property-manager :5000 (`/api/propvalue/*`)

## 기술 스택

| 계층 | 기술 |
|------|------|
| Frontend | 단일 HTML + Vanilla JS (빌드 없음) |
| Backend API | Flask property-manager (:5000) Blueprint |
| 지도 | 카카오맵 SDK v2 (CustomOverlay) |
| DB | PostgreSQL `goldenrabbit_db` |
| 웹 서버 | Nginx 정적 서빙 |

## 데이터 소스

- **서울시**: 정비사업 정보몽땅 (cleanup.seoul.go.kr) 크롤링
- **경기/인천**: 공공데이터포털 도시정비사업 API (향후)
- **Geocoding**: VWorld API (VWORLD_APIKEY)

## 수집 스크립트

```
backend/scripts/propvalue/
├── collect_seoul_zones.py    # 서울시 정보몽땅 → DB
├── collect_molit_zones.py    # 경기/인천 (향후)
└── geocode_zones.py          # 좌표 보정 (향후)
```

## API

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/propvalue/zones` | 목록 (필터: city, district, stage, project_type, bounds, q) |
| GET | `/api/propvalue/zones/<id>` | 상세 |
| GET | `/api/propvalue/stats` | 통계 |

## 배포

정적 파일이므로 빌드 없음. Backend API 변경 시만 서비스 재시작 필요.
