# PropMap 업데이트 내역

## 2026-04-01: 집합/부분부동산 지도 표시 + 검색 기능 추가

### 배경
기존 매물지도는 단일부동산(매매)만 표시. 집합부동산과 부분부동산도 지도에 표시하고, 유형별 필터링 및 검색 기능 추가.

### 변경 파일 (서버)

| 파일 | 변경 내용 |
|------|----------|
| `frontend/public/map.html` | 전체 재작성 — 3유형 색상 마커, 우측 필터 패널, 팝업 유형 뱃지 |
| `frontend/public/index.html` | 검색 폼에 단일/집합/부분 탭 추가, 상세 모달 3유형 지원 |
| `backend/property-manager/routes/propsheet.py` | map-data/search-map/property-detail 3개 API 확장 |
| `backend/property-manager/routes/propnet_api.py` | 기존 문법 에러 수정 (email_pattern) |

### 기능 상세

**1. 지도 마커 (map.html)**
- 부동산유형별 색상 계열: 단일=파랑, 집합=초록, 부분=주황
- 거래유형별 명도 차이: 매매(진), 전세(중), 월세(연)
- 가격 표시 형식: 매매5억 / 전세2.5억 / 월세2000만/100

**2. 필터 패널 (map.html 우측)**
- 부동산유형 토글: 단일/집합/부분 (각 매물 수 표시)
- 거래유형 토글: 매매/전세/월세
- 조합 필터링 지원

**3. 검색 폼 (index.html)**
- 단일/집합/부분 탭으로 유형 선택
- 유형별 동적 검색 필드:
  - 단일: 매가/실투자금/수익률/토지면적
  - 집합: 매가/보증금/월세/전용면적/방수
  - 부분: 보증금/월세/전용면적/물건종류/방수

**4. 상세 모달 (index.html + map.html)**
- 유형 뱃지 (부분 월세, 집합 매매 등)
- 거래유형별 가격 표시 (보증금/월세 vs 매매가)
- 집합/부분은 상세정보(광고자동완성)에 중복되는 필드 제거

**5. 검색결과 지도 (_generate_search_map_html)**
- 매물지도와 동일한 색상 체계 적용
- 상세보기 postMessage에 dbId 포함

**6. API 확장 (propsheet.py)**
- `map-data`: types/txn 파라미터로 3개 테이블 합산 조회
- `search-map`: property_type별 다른 조건 필드 + 다른 테이블 쿼리
- `property-detail`: db_id 파라미터로 3개 테이블(39/38/43) 조회

### DB 구조

| 유형 | DB ID | 테이블명 | 거래유형 |
|------|-------|----------|----------|
| 단일부동산 | 39 | goldenrabbit01_sales_building | 매매 |
| 집합부동산 | 38 | goldenrabbit01_sales_multi_unit | 매매/전세/월세 |
| 부분부동산 | 43 | sales_building_copy | 매매/전세/월세 |

### 마커 색상 체계

| 유형 | 매매 | 전세 | 월세 |
|------|------|------|------|
| 단일 | #1D4ED8 | #3B82F6 | #93C5FD |
| 집합 | #15803D | #22C55E | #86EFAC |
| 부분 | #C2410C | #EA580C | #FB923C |

### 동기화 규칙
map.html, index.html(검색+상세), _generate_search_map_html 3곳은 마커 색상/상세보기/가격 표시 변경 시 반드시 함께 수정.
