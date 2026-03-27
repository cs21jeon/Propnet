# GoldenRabbit 서비스 아키텍처

> 최종 업데이트: 2026-03-27 (Propedia Blueprint 분리, 서비스 포트 역할 명확화)

## 전체 구조

```
[사용자 브라우저]
      │
      ▼
[Nginx (443/80)]
      │
      ├── /                          → frontend/public/ (정적 파일)
      ├── /property-manager/*        → Port 5000 (Property Manager)
      ├── /property/{id}             → Port 5000 (SNS 메타태그)
      ├── /propsheet/*               → Port 5020 (PropSheet 웹 UI)
      ├── /app/*                     → Port 5010 (Propedia 앱 API + 대시보드)
      ├── /uploads/propsheet/*       → /uploads/propsheet/ (정적 파일)
      └── /api/*                     → Port 8000 (API Server, 레거시)

[PostgreSQL - goldenrabbit_db]
      │
      ├── goldenrabbit01_sales_building (단일부동산, db_id=39)
      ├── goldenrabbit01_sales_multi_unit (집합부동산, db_id=38)
      ├── file_attachments (모든 첨부파일 메타데이터)
      └── ... (40+ 테이블)
```

## 서비스 목록

| 서비스 | Port | systemd | Nginx prefix | 역할 | app.py 위치 |
|--------|------|---------|-------------|------|-------------|
| Property Manager | 5000 | `property-manager` | `/property-manager`, `/property/*` | 홈페이지 매물 API, SNS 공유 | `/backend/property-manager/app.py` |
| Propedia | 5010 | `proppedia` | `/app/*` | Propedia 앱 API, 관리자 대시보드 | `/backend/proppedia/app.py` |
| PropSheet | 5020 | `propsheet` | `/propsheet/*` | PropSheet 스프레드시트 UI + 가이드 | `/backend/propsheet/app.py` |
| Proptalk | 5030 | `proptalk` | `/proptalk/*` | 음성 채팅/녹음/요약 | `/chat_stt/server/` |
| API Server | 8000 | `goldenrabbit-api` | `/api` (레거시) | VWorld 프록시 등 | `/backend/api/app.py` |

> **코드 공유 구조**: 5010(Propedia), 5020(PropSheet) 모두 `/backend/property-manager/`의 routes/services/templates를 `sys.path`로 임포트.
> 실제 코드는 property-manager에 있고, 각 서비스의 app.py에서 **필요한 Blueprint만 선택 등록**함.
> Blueprint 추가/수정 시 해당 서비스의 app.py에만 등록하면 됨 (다른 서비스에 중복 등록하지 않음).

## 데이터 흐름

### 홈페이지 (goldenrabbit.biz)

```
index.html
  ├── [지도탭]     map.html (iframe)
  │                  └── fetch('/propsheet/api/propsheet/map-data')      → DB
  │
  ├── [카테고리탭]  재건축(70), 고수익(71), 저가(72)
  │                  └── fetch('/propsheet/api/propsheet/category-properties') → DB
  │
  ├── [검색탭]      조건검색 폼
  │                  └── fetch('/propsheet/api/propsheet/search-map')    → DB
  │
  ├── [매물 클릭]   상세 모달
  │                  └── fetch('/propsheet/api/propsheet/property-detail') → DB
  │
  └── [링크 복사]   /property/{record_id}
                     └── SNS 크롤러용 OG 메타태그 (DB 조회) → /?property={id} 리다이렉트
```

### 이미지 서빙

```
DB 대표사진 필드: "파일명.jpg (/uploads/propsheet/39/1069/파일명.jpg)"
  │
  ├── propsheet.py: regex로 (/uploads/...) 추출 → photo_url
  ├── 프론트엔드: <img src="/uploads/propsheet/39/1069/파일명.jpg">
  └── Nginx: /uploads/propsheet/ → /home/webapp/goldenrabbit/uploads/propsheet/ (정적 서빙)
```

### 파일 업로드/삭제 (PropSheet)

```
업로드:
  PropSheet UI → POST /database/{db_id}/upload
    → 파일 저장: /uploads/propsheet/{db_id}/{record_id}/{safe_filename}
    → INSERT INTO file_attachments
    → _rebuild_cell_value(): 대표사진 필드 자동 업데이트

삭제:
  PropSheet UI → DELETE /database/{db_id}/file/{file_id}
    → 물리 파일 삭제
    → DELETE FROM file_attachments
    → _rebuild_cell_value(): 필드 재구성 (남은 파일 or NULL)
```

### SNS 공유 (카카오톡 등)

```
공유 URL: https://goldenrabbit.biz/property/recXXX
  │
  ├── Nginx → Port 5000 (propnet_api.py)
  ├── PropSheet DB에서 지번주소, 광고, 대표사진 조회
  ├── OG 메타태그 생성 (og:title, og:image, og:description)
  └── /?property=recXXX 로 리다이렉트
        └── index.html에서 모달로 상세 표시
```

## 디렉토리 구조

```
/home/webapp/goldenrabbit/
├── backend/
│   ├── .env                          # 공용 환경변수
│   ├── venv/                         # 공용 가상환경
│   ├── api/
│   │   └── app.py                    # API Server (port 8000)
│   ├── property-manager/
│   │   ├── app.py                    # Property Manager (port 5000)
│   │   ├── routes/
│   │   │   ├── propsheet.py          # 매물 API (카테고리, 상세, 지도, 검색)
│   │   │   ├── propnet_api.py        # SNS 공유, 블로그 등
│   │   │   ├── database.py           # DB CRUD + 파일 업로드/삭제
│   │   │   └── ...
│   │   └── services/
│   │       ├── database_service.py   # DB 연결 관리
│   │       ├── building_unified_service.py
│   │       └── ...
│   ├── scripts/
│   │   ├── deprecated/               # 사용 중지된 스크립트 (Airtable 관련)
│   │   ├── update_bjdong_codes_v2.py # 법정동코드 업데이트 (cron)
│   │   └── ...
│   └── shorts_automation/            # Shorts 영상 자동화
│
├── frontend/
│   └── public/
│       ├── index.html                # 메인 홈페이지
│       ├── map.html                  # 매물 지도 (iframe)
│       ├── about.html                # 회사소개
│       ├── inquiry.html              # 상담문의
│       └── app/                      # 모바일 앱 (PWA)
│
├── uploads/
│   └── propsheet/                    # 첨부파일 저장소
│       ├── 39/                       # 단일부동산 (db_id=39)
│       │   ├── {record_id}/
│       │   │   ├── 대표사진.jpg
│       │   │   └── 건축물대장.pdf
│       │   └── ...
│       └── ...
│
├── config/
│   ├── nginx/
│   │   ├── goldenrabbit.conf         # 메인 Nginx config
│   │   └── propnet.conf              # PropNet Nginx config
│   └── systemd/                      # systemd 서비스 파일
│
├── logs/
│   ├── api/
│   ├── property-manager/
│   └── nginx/
│
├── backups/
│   └── propsheet_coordinates.json    # 좌표 캐시
│
└── docs/                             # 문서
```

## DB 스키마 (주요 테이블)

### goldenrabbit01_sales_building (단일부동산)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | integer | PK (내부 ID) |
| record_id | varchar | 고유 레코드 ID (recXXX) |
| 지번 주소 | text | 주소 |
| 매가(만원) | numeric | 매매가 |
| 토지면적(㎡) | numeric | 토지면적 |
| 대표사진 | text | `"파일명 (/uploads/propsheet/39/{id}/파일명)"` |
| 건축물대장 | text | 동일 형식 |
| coordinates_lat | numeric | 위도 |
| coordinates_lon | numeric | 경도 |
| 현황 | varchar | 등록/네이버/디스코/당근/비공개 |

### file_attachments

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | integer | PK |
| database_id | integer | DB ID (단일부동산=39) |
| record_id | integer | 레코드 내부 ID (정수) |
| field_name | varchar | 필드명 (대표사진, 건축물대장 등) |
| filename | varchar | 저장 파일명 |
| original_filename | varchar | 원본 파일명 |
| file_size | integer | 파일 크기 (bytes) |
| mime_type | varchar | MIME 타입 |
| file_path | text | `/uploads/propsheet/{db_id}/{record_id}/파일명` |

## Cron Jobs (활성)

```bash
# 법정동 코드 일일 업데이트 (매일 새벽 2시 30분)
30 2 * * * update_bjdong_codes_v2.py --fill-mappings

# 추천 이미지 다운로드 (매일 새벽 3시)
0 3 * * * fetch_recomm_images.py

# 블로그 썸네일 (매일 새벽 3시)
0 3 * * * save_blog_thumbnails.py

# Threads 토큰 갱신 (매월 1일, 15일)
0 3 1,15 * * token_manager.py

# SSL 인증서 갱신 (매월 1일 새벽 4시)
0 4 1 * * certbot renew

# 부동산 뉴스레터 (매일 오전 7-11시)
0 7 * * * main.py collect
0 7-11 * * * publish_scheduled.py
```

**중지된 Cron (2026-03-26):**
- `airtable_backup.py` — Airtable → JSON 백업 (DISABLED)
- `generate_map.py` — JSON → 지도 HTML 생성 (DISABLED)

## 주의사항

### psycopg2 % 이스케이프
PropSheet DB 필드명에 `%` 포함: `건폐율(%)`, `용적률(%)`, `융자제외수익률(%)` 등.
`cur.execute(query, params)` 사용 시 SQL 내 리터럴 `%`는 `%%`로 이스케이프 필수.
미준수 시 `IndexError: tuple index out of range` 발생.

### Nginx config 동기화
`config/nginx/goldenrabbit.conf` 수정 시 반드시:
```bash
sudo cp config/nginx/goldenrabbit.conf /etc/nginx/sites-enabled/goldenrabbit
sudo nginx -t && sudo systemctl reload nginx
```

### Airtable 완전 제거됨 (2026-03-26)
- 모든 매물 데이터, 이미지, 건축물대장이 PropSheet DB + 로컬 파일로 전환됨
- Airtable API 키는 `.env`에 남아있으나 사용하지 않음
- `backend/scripts/deprecated/` 폴더: 참조 전용, 호출 금지
- 새 코드에서 Airtable 관련 코드 작성 금지

### 파일 업로드 경로 규칙
- 표준 경로: `/uploads/propsheet/{db_id}/{record_id}/파일명`
- Nginx 서빙: `/uploads/propsheet/` → 물리 경로
- DB 필드 값: `"원본파일명 (/uploads/propsheet/...)"` 형식
- `file_attachments` 테이블에 메타데이터 필수 등록

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-03-26 | Airtable 완전 제거. 모든 데이터 PropSheet DB + 로컬 파일로 전환 |
| 2026-03-26 | SNS 공유 엔드포인트 DB 전환, property-detail.html 삭제 |
| 2026-03-26 | 홈페이지(index.html) backup 의존 코드 제거 |
| 2026-03-26 | 대표사진/건축물대장 Airtable → /uploads/propsheet/ 마이그레이션 완료 |
| 2026-03-27 | Propedia Blueprint를 property-manager(5000)에서 제거, proppedia(5010)로 통일 |
| 2026-03-27 | 서비스 포트별 역할 명확화 (5000=홈페이지/SNS, 5010=Propedia, 5020=PropSheet) |
| 2026-02-11 | 초기 문서 작성 |
