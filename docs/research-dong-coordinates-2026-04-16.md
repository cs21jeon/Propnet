# 동별 좌표 조사 보고서 — Propedia / PropSheet / PropMap 통합

> 작성일: 2026-04-16
> 작성자: @propnet-coo
> 지시: 오너 (CEO)
> 상태: 조사 완료, 구현 미착수 (의사결정 대기)

---

## 0. 한 줄 결론

**동별 좌표는 VWorld `lt_c_bldginfo` WFS 하나로 충분히, 확정적으로 확보 가능.**
국토부 건축물대장 API는 좌표를 전혀 주지 않지만, VWorld WFS는 같은 단지 내 각 동(101동, 102동 …)을 **별도 MultiPolygon + 동명(`dong_nm`) + 건물관리번호(`bd_mgt_sn`)**로 구분해 반환한다. 파크리오 케이스로 실호출 검증 완료.

---

## 1. 문제 정의 (오너 지시사항)

1. Propedia에서 자동입력되는 매물의 "동, 호수"는 공공데이터 기준으로 들어오는데, 그 기준을 PropSheet/PropMap에서도 활용할 방법
2. 동별 좌표가 공공데이터에 실제로 나오는지 **확실한 근거** 필요
3. Propedia → PropSheet → PropMap 3개 서비스 동시 진행
4. 이 단계에서는 조사만, 구현 금지

---

## 2. 현재 상태 실측 (What we have now)

### 2-1. Propedia 자동입력 파이프라인

| 단계 | 소스 | 근거 |
|---|---|---|
| 주소 입력 | 도로명/지번/건물관리번호 검색 | `propedia/lib/data/datasources/remote/building_api.dart`, `service-architecture.md` |
| 건축물대장 조회 | 국토부 `apis.data.go.kr/1613000/BldRgstHubService` (`getBrRecapTitleInfo`, `getBrTitleInfo`, `getBrExposPubuseAreaInfo`) | 서버 `services/building_unified_service.py` |
| 동/호 선택 (집합건물) | `dong_ho_dict` (건축물대장 전유부에서 추출한 동→호 딕셔너리) | `propedia/lib/data/dto/building_dto.dart` L210, `result_screen.dart` L1413 |
| PropSheet 저장 | Propedia → `POST /app/api/propsheet/save/property` → `services/propsheet_save_service.py` | `propedia/lib/data/datasources/remote/propsheet_api.dart` |
| 좌표 변환 | 지번 주소 → VWorld 역지오코딩 → `coordinates_lat/lon` | `propsheet_save_service.py` L114-125 (`_geocode_record`) |

**핵심 사실**: 현재 저장되는 `coordinates_lat/lon`은 **지번(필지) 단위 1개 좌표**로, 같은 지번의 모든 동은 **동일 좌표**로 저장됨.

### 2-2. PropSheet DB 스키마 실측 (서버 psql)

| 테이블 | 동 필드 | 호수 필드 | 좌표 필드 | 용도 |
|---|---|---|---|---|
| `goldenrabbit01_sales_building` (단일) | 없음 | 없음 | `coordinates_lat`, `coordinates_lon` | 단일/부분 |
| `goldenrabbit01_sales_multi_unit` (집합) | `동` (text) | `호수` (text) | `coordinates_lat`, `coordinates_lon` | 집합건물 |

**사당/서초/분당 실데이터 샘플** (총 82건, 동 채워짐 28건=34%):

| 지번 | 건물명 | 동 | 호수 | lat | lon |
|---|---|---|---|---|---|
| 동작구 사당동 **1132** | 롯데캐슬 | **104동** | 201 | 37.49081145 | 126.97245500 |
| 동작구 사당동 **1132** | 롯데캐슬 | **106동** | 1203 | 37.49081145 | 126.97245500 |
| 동작구 사당동 1139 | 사당자이 | 104동 | 302호 | 37.48869601 | 126.96257068 |
| 동작구 사당동 1157 | 이수역리가 | 102동 | 1003 | 37.48938117 | 126.97393300 |
| 분당구 대장동 621 | 힐스테이트 엘포레 A3BL | 303동 | 301 | 37.36967792 | 127.06760624 |

→ 사당동 1132 롯데캐슬의 **104동과 106동이 동일 좌표**로 저장되어 있어, 동별 구분이 지도에서 불가능함을 실데이터로 확인.

### 2-3. 현재 Propedia가 이미 동명까지 가지고 있음

- `building_dto.dart`의 `BuildingInfo.dongHoDict` → 건축물대장 표제부에서 추출한 "동명 → [호명 리스트]" 매핑
- `result_screen.dart` L210: 유저가 `_selectedDong` / `_selectedHo` 선택 후 저장
- PropSheet 저장 payload (집합건물): `area.dong_nm`, `area.ho_nm` 전송 — 서버 `_build_multi_unit_record()`에서 `record['동']`, `record['호수']`에 기록
- 즉 **"동명" 식별자는 이미 공공데이터 기준으로 일관되게 흐르고 있음**. 문제는 **좌표만** 동별 구분이 없음.

---

## 3. 공공데이터 API별 "동별 좌표" 제공 여부 — 실측 검증

### 3-1. 국토교통부 건축물대장 API (data.go.kr) — ❌ 좌표 없음

| API | 응답 필드 중 위치 | 좌표 | 근거 |
|---|---|---|---|
| `getBrBasisOulnInfo` (기본개요) | `newPlatPlc`, `platPlc`, 동명칭 | ❌ | WooilJeong PublicDataReader 명세 |
| `getBrRecapTitleInfo` (총괄표제부) | `newPlatPlc`, `bldNm` | ❌ | 동일 |
| `getBrTitleInfo` (표제부) | `dongNm`, `bldNm`, `mainAtchGbCdNm` | ❌ | 동일 |
| `getBrFlrOulnInfo` (층별개요) | `dongNm`, `flrNoNm`, `flrGbCdNm` | ❌ | 동일 |
| `getBrExposPubuseAreaInfo` (전유공용면적) | `dongNm`, `hoNm`, `exposPubuseGbCdNm` | ❌ | 동일 |

**결론**: 국토부 건축물대장 API는 **위/경도를 전혀 제공하지 않음**. 문자 기반 주소(`platPlc`, `newPlatPlc`)와 동명(`dongNm`)만 제공.

### 3-2. VWorld 건물통합정보 WFS (`lt_c_bldginfo`) — ✅ **동별 폴리곤 + 동명 + 좌표 제공 확인**

**실호출 검증 (2026-04-16)**:

```
GET https://api.vworld.kr/req/wfs
  ?service=wfs&version=2.0.0&request=GetFeature
  &typename=lt_c_bldginfo&output=application/json&srsname=EPSG:4326
  &bbox=127.108,37.515,127.114,37.521
  &key={VWORLD_APIKEY}
```

**응답 필드(실측)**:

| 필드 | 의미 | 파크리오 301동 샘플 |
|---|---|---|
| `bld_nm` | 건물명 | "파크리오 301동" |
| `dong_nm` | 동명 | "파크리오 301동" |
| `pnu` | 19자리 지번코드 | `1171010200100200000` |
| `bd_mgt_sn` | **24자리 건물관리번호(동 단위 고유 ID)** | `1171010200100200005000007` |
| `bldrgst_pk` | 건축물대장 PK | `100225793` 등 |
| `useapr_day` | 사용승인일 | `20081001` |
| `grnd_flr` / `ugrnd_flr` | 지상/지하층수 | 18 / 4 |
| `archarea` / `totalarea` / `platarea` | 건축/연/대지면적 | 619 / 13509 / 1039 |
| `height` / `strct_cd` | 높이 / 구조코드 | 54 / 21 |
| `usability` | 용도코드 | 02000(공동주택) |
| `bc_rat` / `vl_rat` | 건폐율/용적률 | 59 / 962 |
| `geoidn` | Geo Identifier | `B00100000000XZZKU` |
| `geometry` | **MultiPolygon** (EPSG:4326) | 건물 윤곽선 |

**파크리오 케이스 (실측 16개 feature)**:

| bld_nm | dong_nm | bd_mgt_sn | 첫 좌표 (lon, lat) |
|---|---|---|---|
| 파크리오 201동 | 파크리오 201동 | 1171010200100200007000001 | 127.108649, 37.519609 |
| 파크리오 202동 | 파크리오 202동 | 1171010200100200007000002 | 127.109423, 37.519728 |
| 파크리오 203동 | 파크리오 203동 | 1171010200100200000000001 | 127.108578, 37.519907 |
| 파크리오 212동 | 파크리오 212동 | 1171010200100200000000007 | 127.109064, 37.520969 |
| 파크리오 301동 | 파크리오 301동 | 1171010200100200005000007 | 127.112133, 37.520944 |
| 파크리오 317동 | 파크리오 317동 | 1171010200100200005000014 | 127.113932, 37.520933 |
| 파크리오 상가B동 | 상가B동 | 1171010200100200006000001 | 127.112914, 37.520134 |

→ **단지 내 각 동이 서로 다른 좌표로 개별 제공됨이 실증적으로 확인됨**. 이는 조사의 결정적 근거.

### 3-3. 주소기반산업지원서비스 (business.juso.go.kr) — ⚠️ 제한적

- **실시간 상세주소정보 조회 API** (`data.go.kr/data/15096712`): 동/층/호 문자 정보 제공
- **주출입구 좌표** (`entX`, `entY`): 주소(도로명주소) 단위로 제공되며, **주된건물**의 대표 주출입구 1개만 제공 (아파트 단지의 경우 단지 출입구 1개)
- **공동주택 각 동별 엔트리 좌표는 제공되지 않음**. 도로명주소에 "동"이 부여된 경우(예: "올림픽로 300, 101동") 해당 레코드의 entX/entY는 **사용 가능 가능성** — 그러나 VWorld WFS보다 데이터 완전성/정확도가 떨어짐 (동이 도로명주소에 부여되지 않은 구축 아파트는 누락)

### 3-4. 카카오 로컬 API / 네이버 지도 API — ⚠️ 비공식, 불안정

- 카카오 키워드검색: `place_name`에 "파크리오 101동"이 등록되어 있으면 x/y 반환. 그러나 데이터 수록 여부가 **업체 등록에 의존** — 일부 아파트는 단지 1개만 등록되고 동별 POI 미등록
- 카카오의 `category_group_code` AP2(아파트)는 단지 단위. 동 단위 POI는 보장 없음
- 상용 지도 API 비용(쿼터 초과 시 유료)과 이용약관 제약 존재
- **Propedia 데이터 소스로 부적합**. 보조 검증용으로만 활용 가능

### 3-5. 공공 GIS 파일 데이터 (SHP) — 백업/초기 적재용

- `국토교통부_GIS건물통합정보` (data.go.kr/data/15083092) — 건물 단위 SHP 벡터. VWorld WFS와 동일 원본. 초기 전체 DB 적재 시 사용 가능
- `도로명주소 상세주소DB` (data.go.kr/data/15050425) — 동/층/호 문자 DB (좌표 제한적)

---

## 4. 근거 기반 권장 방안

### 4-1. 1순위: VWorld 건물통합정보 WFS (`lt_c_bldginfo`) — 확정 권장

**이유**:
1. **동별 폴리곤 + 동명 + 좌표를 공식 제공** (실호출 검증 완료)
2. 이미 Propedia 서버에 VWorld API 키 (`VWORLD_APIKEY`) 보유 및 사용 중 (`cadastral_service.py`)
3. `bd_mgt_sn` (건물관리번호 24자리)는 국토부 건축물대장 API와 **동일 체계** → Propedia 동명(`dongNm`)과 매칭 가능
4. 대단지 아파트 실케이스(파크리오) 검증 통과

**한계**:
- API 호출 쿼터 (VWorld는 무료 키 일 1만 건 제한) → **DB 캐시 전략 필수**
- WFS BBOX 조회 시 한 번에 여러 건물 반환 → 동별 매칭 로직 필요 (`dong_nm` 텍스트 정규화 — "파크리오 101동" vs "101동" vs "101")
- 간혹 `dong_nm`이 null인 건물 존재 (상가, 부속건축물)

### 4-2. 2순위 (보조): 서버 DB에 동별 좌표 캐시 테이블 구축

| 테이블 제안 | 용도 |
|---|---|
| `building_dong_geometry` | `pnu`, `bd_mgt_sn`, `dong_nm`, `center_lat`, `center_lon`, `polygon_geojson`, `cached_at` |

- Propedia가 처음 조회할 때 WFS → 캐시
- 이후 PropSheet 저장 / PropMap 렌더 시 캐시 재사용
- 1일 1만 쿼터 걱정 없음

### 4-3. 3순위 (대안): juso.go.kr 상세주소 API

- VWorld WFS 장애/쿼터 초과 시 fallback
- 단지 레벨 출입구 좌표만 제공되므로 동별 정밀도는 낮음

---

## 5. Propedia / PropSheet / PropMap 통합 시나리오 초안

### 5-1. 데이터 흐름 (제안)

```
[Propedia 앱]
  1. 주소 검색 → bjdong_code, bun, ji
  2. 건축물대장 조회 (국토부 API) → dongHoDict 획득
  3. 유저가 동/호 선택 → selectedDong, selectedHo
  4. [신규] 동별 좌표 조회: 서버에 "동 좌표 요청" API 호출
       ↓
  [서버: POST /app/api/building/dong-coords]
       → 캐시 확인 (building_dong_geometry 테이블)
       → 캐시 miss 시 VWorld WFS BBOX 조회
       → dong_nm 정규화 매칭 → center_lat/lon, polygon 캐시
       → 응답: { lat, lon, polygon }
  5. PropSheet 저장 payload에 area.dong_center_lat / dong_center_lon 추가 전송

[서버: /app/api/propsheet/save/property]
  → propsheet_save_service._build_multi_unit_record()
  → record['coordinates_lat'] = area.dong_center_lat  (있으면 동별 좌표, 없으면 필지 좌표 fallback)

[PropMap 지도]
  → /propsheet/api/propsheet/map-data 조회 시 집합건물 테이블도 포함
  → 동별 좌표로 마커 표시 (같은 지번이라도 동별로 다른 위치)
```

### 5-2. 서비스별 작업 범위 (구현 시점)

| 서비스 | 작업 | 파일 |
|---|---|---|
| **Propedia** | 1. 서버 API 호출(동 좌표 요청) 2. PropSheet 저장 payload에 `dong_center_lat/lon` 포함 3. 지도 화면에서 선택 동 하이라이트 | `lib/data/datasources/remote/`, `propsheet_provider.dart` |
| **서버 (공유)** | 1. `building_dong_geometry` 테이블 생성 2. `services/cadastral_service.py`에 `get_dong_geometry(pnu, dong_nm)` 추가 3. `/app/api/building/dong-coords` 라우트 4. `propsheet_save_service._build_multi_unit_record()`에 `coordinates_lat/lon` = 동 좌표 우선 | `backend/property-manager/services/`, `routes/app_api.py`, `routes/propsheet_save.py` |
| **PropSheet** | 1. `goldenrabbit01_sales_multi_unit`은 이미 `coordinates_lat/lon` 보유 → 스키마 변경 없음 2. 관리자 일괄 재좌표 배치(`reprocess_multi_unit_coords.py`) | `backend/property-manager/routes/propsheet.py` `map-data` |
| **PropMap** | 1. `map-data` API에 집합건물 병합 2. 같은 지번 내 복수 마커 클러스터링 규칙 3. 단지 명칭 + 동 번호 툴팁 | `frontend/public/map.html`, `frontend/public/js/` |

### 5-3. 캐시 & 쿼터 전략

- WFS 호출은 **bbox + bld_nm LIKE 단지명** 조건으로 1회 호출 → 단지 내 모든 동 일괄 수집 → 테이블에 적재
- 캐시 TTL: 1년 (건물 위치는 재건축 아니면 불변). 재건축/신축 시 수동 갱신
- 쿼터 모니터링: 현재 VWorld 호출은 `cadastral_service`, `vworld_service`에 분산. `VWORLD_DAILY_CALLS` 카운터 신설 권장 → QA 대시보드 노출

### 5-4. 기존 레코드(82건) 마이그레이션

- 일회성 배치 스크립트: `scripts/backfill_multi_unit_dong_coords.py`
- 사당동 1132 롯데캐슬의 104동/106동 좌표 분리 테스트 후 전체 실행
- QA는 실행 전/후 샘플 10건을 카카오맵에서 육안 검증

---

## 6. 미결정 사항 (오너 결정 필요)

1. **쿼터/비용**: VWorld 무료 키(일 1만 건) 한도 초과 시 유료 전환 or juso.go.kr fallback — 비용 정책 확정 필요
2. **단일부동산(sales_building) 처리**: 단일 건물은 지번=건물 1:1이라 기존 필지 좌표로 충분한가, 아니면 `lt_c_bldginfo` 건물 중심점으로 업그레이드할 것인가
3. **PropMap 클러스터링 UX**: 대단지 아파트에서 수십 개 마커가 겹쳐 보일 때 "단지 단위 요약 + 줌인 시 동별 전개"를 어느 수준까지 구현할 것인가 (기획 필요)
4. **구축 아파트 누락 대응**: `dong_nm`이 null인 구축 건물의 대응 방침 — 필지 좌표 fallback / "동 좌표 없음" 배지
5. **agent별 적용 범위**: goldenrabbit agent 먼저 파일럿 → 전 agent 확대 순서

---

## 7. 다음 단계 제안

| 단계 | 담당 | 기간 |
|---|---|---|
| ① 오너 의사결정 | CEO | 즉시 |
| ② PRD 확정 (@pm-lead) — 본 보고서 기반 구현 범위/UX/일정 확정 | @pm-lead | 2일 |
| ③ 서버 API 설계 (@dev-lead, @infra-lead) — `building_dong_geometry` 스키마 + 캐시 정책 | @dev-lead | 3일 |
| ④ Propedia 앱 수정 + PropSheet 저장 로직 + PropMap 렌더 (@propedia-dev, @propsheet-dev, @propmap-dev) | 각 서비스 | 1~2주 병렬 |
| ⑤ QA 검증 (@qa-lead) — 파크리오/롯데캐슬/사당자이 등 10단지 동별 마커 검증 | @qa-lead | 3일 |
| ⑥ 배포 (@infra-lead) — 배치 재좌표화 → propsheet/proppedia 서비스 재시작 | @infra-lead | 1일 |

---

## 8. 참고 근거

### 코드 근거 (로컬)
- `propedia/docs/plan-building-footprint-lookup.md` — VWorld WFS 건물 도형 조회 기존 기획 (부속지번→본번 매칭용). 본 건에서 확장 활용 가능
- `propedia/lib/data/dto/building_dto.dart` L202-216 — `dongHoDict` 구조
- `propedia/lib/presentation/providers/propsheet_provider.dart` L90-96 — `area.dong`, `area.ho` 저장 payload
- 서버 `/backend/property-manager/services/propsheet_save_service.py` L121-126 — `_geocode_record()` (현 필지 좌표 저장 로직)
- 서버 `/backend/property-manager/services/cadastral_service.py` L155-230 — VWorld WFS 기존 사용 패턴(`lp_pa_cbnd_bubun` 필지)

### 공공데이터 근거
- [국토교통부_건축HUB_건축물대장정보 서비스 (data.go.kr)](https://www.data.go.kr/data/15134735/openapi.do)
- [국토교통부_GIS건물통합정보(WMS/WFS) (data.go.kr)](https://www.data.go.kr/data/15123970/openapi.do)
- [국토교통부_GIS건물통합정보 파일데이터 (data.go.kr)](https://www.data.go.kr/data/15083092/fileData.do)
- [VWorld WMS/WFS API 2.0 레퍼런스](https://www.vworld.kr/dev/v4dv_wmsguide2_s001.do)
- [WooilJeong PublicDataReader - 건축물대장 응답 필드 명세](https://github.com/WooilJeong/PublicDataReader/blob/main/assets/docs/portal/BuildingLedger.md)
- [주소기반산업지원서비스 (business.juso.go.kr)](https://business.juso.go.kr/)
- [행정안전부_실시간 상세주소정보 조회 API (data.go.kr)](https://www.data.go.kr/data/15096712/openapi.do)
- [Kakao Developers - Local API](https://developers.kakao.com/docs/latest/ko/local/dev-guide)

### 실호출 검증 (본 조사에서 직접 수행)
- VWorld WFS `lt_c_bldginfo` 잠실 파크리오 BBOX 조회 → 314 feature 중 파크리오 16개 동 개별 식별 (bld_nm, dong_nm, bd_mgt_sn, 서로 다른 좌표) — 2026-04-16
- PropSheet DB `goldenrabbit01_sales_multi_unit` 사당동 1132 롯데캐슬 실데이터 2건이 동일 좌표 저장 확인 — 현 시스템 한계 실증
