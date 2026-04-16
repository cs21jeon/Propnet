# VWorld 건물 관련 16개 API 최종 조합 제안서 — 파크리오 이슈 해결 통합본

> 작성일: 2026-04-16
> 작성자: @propnet-coo
> 지시: 오너 (CEO) — "vworld api 건물 관련 리스트인데, 이 부분을 적용해서 최선을 찾아봐줘. 다른 정보가 있으면 추가해도 되고, 이전에 지번/도로명과 지도상에 위치를 클릭했을 때 나타나는 부분이 달라서 문제가 되었던 경험이 있는데, 이것도 함께 해결이 되면 좋을 것 같아. (잠실 파크리오 관련)"
> 상태: 조사/분석 완료, 의사결정 대기 (코드 수정 금지)
> 선행 문서: `docs/research-dong-coordinates-2026-04-16.md` (동별 좌표 확정 검증), `propedia/docs/plan-building-footprint-lookup.md` (신천동 17↔20 부속지번 이슈)

---

## 한 줄 결론

**16개 API는 3계층으로 정리되며, 그중 "동별 좌표 + 동식별자 + 주소일치"를 한 번에 해결하는 조합은 `LT_C_BLDGINFO`(공간, GIS건물통합 WFS) + NSDI `LdaregService`(속성, 대지권등록 5종)의 2-레그 구조 하나뿐이다.** 파크리오 지번/도로명 ↔ 지도클릭 불일치는 현재 Propedia가 두 경로에서 **서로 다른 좌표 소스**(PNU 매칭 성공 → 필지 중심 / PNU 실패 → 카카오 키워드)를 쓰기 때문이며, 본 제안서의 `building_dong_geometry` 캐시를 중간 허브로 두면 두 경로가 **동일한 `bd_mgt_sn` 한 개로 수렴**하게 된다.

---

## Part A. VWorld 건물 관련 16개 API 전수 분석

### A-1. 3계층 분류 (이해를 위한 재구성)

오너가 제시한 16개 API는 VWorld 공식 문서 구조상 **3개 계층의 이종(異種) 서비스**가 섞여 있다. 이를 혼동 없이 쓰려면 계층부터 분리해야 한다.

| 계층 | 엔드포인트 | 번호 | 특징 | 좌표 제공 | 동 식별자 | 적합 용도 |
|---|---|---|---|---|---|---|
| **L1. GIS 공간데이터** (2D데이터 API 2.0) | `https://api.vworld.kr/req/data` (data=`LT_C_BLDGINFO` 등), `/req/wfs` (typename=`lt_c_bldginfo` 등) | 1~6 | 건물 **폴리곤** + 속성 동시 | ✅ MultiPolygon(EPSG:4326) | ✅ `dong_nm`, `bd_mgt_sn` | **동별 좌표 확정** |
| **L2. NED 속성데이터** (용도별건물, 건축물연령) | `https://api.vworld.kr/ned/data/{메소드명}` | 7~9, 11 | **PNU 입력 → 속성만** 반환(JSON/XML), 좌표 없음 | ❌ | 부분적 | 용도/연령 보강 |
| **L3. NSDI LdaregService** (대지권등록정보 5종, 공공데이터포털 15056691) | `http://apis.data.go.kr/1611000/nsdi/eios/LdaregService/{오퍼레이션}` | 12~16 | **PNU/건물일련번호 입력 → 정식 동/호 식별자**, 좌표 없음 | ❌ | ✅ **정식 체계** | 동/호 공식 식별자 |
| **보너스**: 도로명주소건물 (10번) | 2D데이터 API 2.0 중 `LT_C_SPBD_*` 계열(데이터 카탈로그 "도로명주소 건물" 항목) | 10 | 도로명주소-건물 매핑 | ✅ 제한적 | ✅ | 도로명↔지번↔건물 삼중 매칭 |

> L1은 엔드포인트가 `/req/data`(REST JSON)와 `/req/wfs`(WFS 1.1 GetFeature) 두 가지로 **동일 데이터셋**을 둘 다 제공한다. 오너 리스트의 "GIS건물통합조회"와 "GIS건물통합WFS조회"는 **같은 원본의 다른 인터페이스**이다. "WMS"는 타일 이미지이므로 좌표/속성 용도로는 부적합 (시각용).

### A-2. 16개 API 상세 표

| # | 한글명 | 엔드포인트 / service ID | 핵심 입력 | 핵심 출력 | 좌표 | 동 식별 | 실무 평가 |
|---|---|---|---|---|---|---|---|
| 1 | GIS건물통합조회 | `/req/data` + `data=LT_C_BLDGINFO` | `geomFilter`(POINT/BOX/POLYGON) 또는 `attrFilter`(`pnu:=:...`) | `bld_nm`, `dong_nm`, `pnu`, `bd_mgt_sn`, `bldrgst_pk`, `useapr_day`, `grnd_flr/ugrnd_flr`, `archarea/totalarea/platarea`, `height`, `strct_cd`, `usability`, `bc_rat/vl_rat`, `geoidn`, `ag_geom` | ✅ | ✅ | ⭐ **최우선** — 속성+도형 한 번에 |
| 2 | GIS건물통합WFS조회 | `/req/wfs` + `typename=lt_c_bldginfo` | `bbox`, `cql_filter` | 1번과 동일 (GeoJSON FeatureCollection) | ✅ | ✅ | 1번과 동일 원본, 지도 렌더용 |
| 3 | GIS건물일반정보WMS조회 | `/req/wms` + `layers=lt_c_bldgen_info` | `bbox`, `srs`, `width/height` | PNG 타일 | — | — | 배경지도 오버레이용, API 조회 부적합 |
| 4 | GIS건물일반정보WFS조회 | `/req/wfs` + `typename=lt_c_bldgen_info` | 2번과 동일 패턴 | **일반건물(비집합)** 속성+도형: 단독주택/상가/공장 등 | ✅ | ⚠️ 일반건물에는 `dong_nm` 제한적 | 단독·상가 전용 |
| 5 | GIS건물집합정보WMS조회 | `/req/wms` + `layers=lt_c_bldginfo_ap` | `bbox` | PNG 타일 | — | — | 집합건물 시각화 전용 |
| 6 | GIS건물집합정보WFS조회 | `/req/wfs` + `typename=lt_c_bldginfo_ap` | 2번과 동일 패턴 | **집합건물 전용** 속성+도형 | ✅ | ✅ 강함 | 아파트/오피스텔 전용 — 파크리오 16개 동 식별 검증된 계열(1/2번과 원본 공유) |
| 7 | 용도별건물속성조회 | `/ned/data/getBuildingUse` | `pnu`, `numOfRows`, `key`, `format=json` | 22개 필드: `ldCodeNm`(법정동명), `mnnmSlno`(지번), `agbldgSeCodeNm`(일반/집합 구분), `buldKndCodeNm`(건물종류: 아파트/다세대/연립/단독/상가...), `buldNm`, `useaprDay`, `gnflrCnt/bsmtflrCnt`, `mainAtchGbCdNm`, `bylotCnt` 등 | ❌ | 부분 | 단지 내 **용도별 분류** 확인, pnu 1개 → 건물 N개 |
| 8 | 용도별건물WMS조회 | `/req/wms` + `layers=lt_c_useupisuq153` | `bbox` | PNG 타일 | — | — | 시각용 |
| 9 | 용도별건물WFS조회 | `/req/wfs` + `typename=lt_c_useupisuq153` | `bbox` | 용도별 건물 도형+속성 | ✅ | 부분 | 지도에서 "상업용 건물만" 등 필터 렌더 |
| 10 | 도로명주소 건물 | `/req/data` + `data=LT_C_SPBD` 계열 (데이터카탈로그 "도로명주소건물") | `geomFilter`(POINT) 또는 `attrFilter`(`bdMgtSn:=:...`) | 도로명주소 + `bd_mgt_sn` + 건물 도형 | ✅ | ✅ | **도로명↔지번↔건물 삼중 매칭의 열쇠** (파크리오 이슈 핵심) |
| 11 | 건축물연령속성조회 | `/ned/data/getBuildingAge` (또는 유사) | `pnu`, `stdrYear` | 연도별/5년·10년 단위 건축물 연령 구분 | ❌ | ❌ | 구축 아파트 식별 (fallback 기준) |
| 12 | 건물층수조회 | `LdaregService/getBuldFlrOulnList` | `pnu`(19) + `buldSn`(건물일련번호) | 층별 용도, 층수, 구조코드 | ❌ | ❌ | 층별 구분 (전유부 보강) |
| 13 | 건물동명조회 | `LdaregService/getBuldDongNmList` | `pnu`(19) | 해당 필지의 **공식 동명 리스트**("파크리오 101동" ...) + 각 동의 `buldSn` | ❌ | ⭐ **정식 소스** | 건축물대장 `dongNm`과 교차검증, VWorld `dong_nm` 매칭의 정답지 |
| 14 | 건물실명조회 | `LdaregService/getBuldRlnmList` | `pnu` + `buldSn` | 건물 실명/표시명 (예: "파크리오 상가B동") | ❌ | ✅ | 상가동/부속동 식별 |
| 15 | 건물일련번호조회 | `LdaregService/getBuldSnList` | `pnu`(19) | 필지 내 **건물일련번호 전체 리스트** (아파트 단지 16개 동의 각 buldSn) | ❌ | ✅ | 단지 내 전체 동 enumerate |
| 16 | 건물호수조회 | `LdaregService/getBuldHoNmList` | `pnu` + `buldSn` | 특정 동의 호수(101호, 102호 ...) + 전유면적, 대지권지분 | ❌ | ❌ | 전유부 호수 열거 |

> 서비스 ID/오퍼레이션명은 VWorld 공식 2D데이터 API 2.0 레퍼런스, 공공데이터포털 15056691/15123970/15140363/15140366 카탈로그, `GitHub WooilJeong/PublicDataReader`, `qquack.org VBA 샘플`에서 교차 확인함. 정확한 대소문자·엔드포인트 구조는 서버 구현 시 공식 명세서 다운로드로 확정 필요.

### A-3. 관점별 최적 조합 (오너 요청 표)

| 용도 | 1순위 API | 2순위 API | 비고 |
|---|---|---|---|
| **동별 좌표 확보 (집합건물)** | **1/2번 `LT_C_BLDGINFO`** (`lt_c_bldginfo` WFS) | 6번 `lt_c_bldginfo_ap` | 1/2/6은 동일 원본 — WFS 인터페이스 하나로 충분. 파크리오 16개 동 좌표 실측 완료 (research-dong-coordinates L84-124) |
| **일반건물 좌표 확보 (단독·상가)** | **1번 `LT_C_BLDGINFO`** (통합) | 4번 `lt_c_bldgen_info` (일반) | 통합이 일반도 포함. 일반 전용은 `dong_nm`이 종종 null이므로 오히려 단점 |
| **동명 정식 식별** | **13번 `getBuldDongNmList`** | 1번 `LT_C_BLDGINFO.dong_nm` | 13번은 NSDI 원본, 1번은 시움터 파생. 불일치 시 13번 정답 |
| **구축 아파트 동명 fallback** | **13번 `getBuldDongNmList`** + 11번 `getBuildingAge` | 건축물대장 `getBrTitleInfo` (현재 Propedia가 이미 사용 중) | 11번으로 연도 스크리닝 후 13번으로 정식 동명 획득 |
| **여러 필지 대형 건물 식별** | **1번 `LT_C_BLDGINFO`** (bbox WFS) | 7번 `getBuildingUse` (pnu 단일) | 1번의 `bd_mgt_sn`은 건물 단위 — 필지 경계 무관, 대형상가 1동이 여러 PNU에 걸쳐 있어도 1개 feature |
| **도로명주소 ↔ 지번 ↔ 건물 삼중 매칭** | **10번 `LT_C_SPBD`** | 1번 `LT_C_BLDGINFO` + juso.go.kr | **파크리오 이슈 해결의 결정적 API** (본 문서 Part B 참고) |
| **전유부 호수 정밀 확정** | **16번 `getBuldHoNmList`** + 건축물대장 `getBrExposPubuseAreaInfo` | 15번 `getBuldSnList` | 기존 Propedia `dong_ho_dict`에 16번 병합하면 정확도 ↑ |

### A-4. "GIS건물통합 vs 일반 vs 집합" 3종 상세 비교

오너 관점 1번 질문에 대한 답:

| 구분 | 1번 통합 (`LT_C_BLDGINFO`) | 4번 일반 (`LT_C_BLDGEN_INFO`) | 6번 집합 (`LT_C_BLDGINFO_AP`) |
|---|---|---|---|
| 포함 범위 | **일반 + 집합 모두** | 단독주택/상가/공장 등 비집합만 | 아파트/오피스텔 등 집합만 |
| `dong_nm` | 집합은 동명, 일반은 보통 null | 대부분 null | 항상 동명 |
| 좌표 | MultiPolygon 풍부 | MultiPolygon | MultiPolygon |
| 레코드 수 | 최다 | 약 50% | 약 50% |
| **단독주택·상가 적합** | ✅ | ✅ (전용) | ❌ 미수록 |
| **아파트 적합** | ✅ | ❌ | ✅ (전용) |
| 쿼터 소비 | 1회 | 1회 | 1회 |

**권장**: 분기 없이 **1번 통합 하나로 통일**. 이유 — (a) 같은 원본을 분리한 것이므로 정확도 차이 없음 (b) 1번에 일반+집합이 모두 있어 "단독주택인지 아파트인지" 먼저 모를 때도 안전 (c) 코드 단순화. 4번/6번은 시각화 레이어 구분 시에만 별도 활용.

---

## Part B. 잠실 파크리오 "지번/도로명 ↔ 지도 클릭" 불일치 원인 + 해결

### B-1. 현재 두 경로의 실제 구현 (코드 근거)

#### 경로 ①: 주소 검색 (지번/도로명 입력)

```
[Propedia 앱 home_screen.dart L253]
  context.push('/search/jibun')
    → SearchJibunScreen (bjdong_code, bun, ji 입력)
    → POST /app/api/search/jibun
      body: {bjdong_code, bun, ji, land_type}
    → 서버 proppedia :5010 → building_unified_service.py
    → 건축물대장 API (getBrTitleInfo 등) → has_data 판정
    → [좌표 결정] _resolve_coordinates(codes, address_info):
        1) VWorld 필지 WFS (lp_pa_cbnd_bubun, pnu 매칭) → 필지 중심 좌표 = "vworld_pnu"
        2) 실패 시 VWorld geocoding API (PNU 19자리) → "vworld_api_pnu"
        3) 실패 시 Kakao 키워드 검색(주소 문자열) → "kakao"
    → location.source에 출처 명시 반환
```

#### 경로 ②: 지도 클릭 (역지오코딩)

```
[Propedia 앱 map_provider.dart L74-104, map_api.dart L10-16]
  KakaoMap onTap(lat, lng)
    → POST /app/api/map/click-jibun  body: {lat, lng}
    → 서버 proppedia :5010 → cadastral_service.get_jibun_from_coords(lat, lng)
      내부: VWorld 연속지적도(lp_pa_cbnd_bubun) geomFilter=POINT(lng lat)
      반환: pnu, 지번주소, 도로명주소(juso.go.kr fallback)
    → 이어서 /app/api/map/parcel-boundary (pnu, lat, lng) → 필지 폴리곤
    → result.html로 리다이렉트 → 내부에서 다시 /app/api/search/jibun 호출
```

**두 경로 요약 비교**:

| 측면 | 경로 ① (지번/도로명 검색) | 경로 ② (지도 클릭) |
|---|---|---|
| 시작 정보 | bjdong_code + bun + ji (문자) | lat, lng (좌표) |
| 좌표 결정 로직 | VWorld PNU → VWorld geocoder → Kakao (3단계 fallback) | VWorld `lp_pa_cbnd_bubun` POINT geomFilter 1단계 |
| 건물명 결정 | 건축물대장 `getBrTitleInfo.bldNm` | `lp_pa_cbnd_bubun` 에는 건물명 없음 → 재조회 시 ①과 동일 경로 |
| **반환되는 PNU** | 건축물대장 조회 시 받은 PNU(본번 기준) | 지적도 필지 PNU (클릭 위치 필지 = 부속지번일 수 있음) |
| **반환되는 좌표** | PNU가 있으면 필지 중심, 없으면 주소 키워드 카카오 좌표 | 클릭 좌표 그대로 또는 클릭이 속한 필지 중심 |

### B-2. 파크리오에서 왜 달라지는가 (3가지 중첩 원인)

파크리오(송파구 신천동 17번지, 16개 동, 6864세대)는 아래 3가지가 동시에 발생하는 **동시발현 케이스**이다.

#### 원인 ①: **부속지번 vs 본번** 불일치 (선행문서 `plan-building-footprint-lookup.md` 확인 완료)

- 파크리오 본번: **신천동 17** (건축물대장 등록)
- 부속지번: **17-4, 20, 20-6 ...** (건축물대장 미등록, 토지만 존재)
- 지도에서 **건물이 차지하는 위치**는 본번 17 필지뿐 아니라 부속 20, 20-6 필지까지 걸쳐 있음
- **지도 클릭 위치에 따라 PNU가 달라짐** — 같은 파크리오 건물을 클릭해도 "신천동 17" 또는 "신천동 20"이 나옴
- 경로 ①(지번 "신천동 20" 입력)은 juso.go.kr에서 "20-4 올림피아아파트"로 오매칭 → 엉뚱한 도로명 노출 (실제 기록됨)
- 경로 ②(지도 클릭, 부속지번 위치)는 필지 PNU = 신천동 20, 건축물대장 없음 → has_data=False → 카카오 fallback → 또 다른 좌표

#### 원인 ②: **16개 동의 개별 좌표가 필지 좌표 1개로 뭉개짐**

- 경로 ①에서 **PNU 매칭 성공** 시 좌표 출처 = `vworld_pnu` = **필지(17번지) 중심 단일 좌표** (16개 동 모두 동일 좌표)
- 경로 ②에서 **지도 클릭 성공** 시 좌표 = 클릭 위치 (동별로 서로 다름)
- 즉 "경로 ①의 좌표"(필지 중심) ≠ "경로 ②의 좌표"(클릭한 동 위치). 같은 건물이라도 마커가 다르게 찍힘.
- **이것이 research-dong-coordinates 보고서의 핵심 문제와 동일한 뿌리** — PropSheet DB의 `goldenrabbit01_sales_multi_unit` 82건 중 28건은 경로 ①로 저장돼 16개 동이 같은 좌표를 공유

#### 원인 ③: **도로명주소 ↔ 지번 동 부여 규칙 차이**

- 파크리오 도로명주소: **"올림픽로 300"** (단지 대표) 또는 각 동마다 "송파대로 42길 XX" 등 개별 부여
- juso.go.kr의 주출입구 좌표(`entX/entY`): **단지 대표 출입구 1개**만 제공 → 16개 동에 대해 동일 좌표
- VWorld 필지 좌표: 본번 17 중심
- 카카오 키워드 검색: "파크리오" → 카카오맵에 등록된 POI (단지 대표)
- **세 좌표가 모두 다른 지점을 가리킴**. 경로 ①은 VWorld PNU, 경로 ②는 클릭 위치, result.html 안내는 juso.go.kr → 사용자에게 "동일 건물인데 위치가 매번 다르다"로 경험됨

### B-3. 해결 방안 — `bd_mgt_sn`(건물관리번호) 단일 키로 통합

**핵심 설계**: 두 경로가 서로 다른 소스에서 제각각 좌표를 만들어내던 것을, **`bd_mgt_sn`(24자리 건물관리번호)라는 건물 단위 고유 식별자로 수렴**시킨다.

```
                    ┌─────────────────────────────────┐
                    │  building_dong_geometry 캐시    │
                    │  PK: bd_mgt_sn (24자리)         │
                    │  fields: pnu, dong_nm,          │
                    │    center_lat, center_lon,      │
                    │    polygon_geojson,             │
                    │    road_address, bun, ji,       │
                    │    nsdi_bld_sn (NSDI 건물일련번호)│
                    │    use_apr_day, usability 등    │
                    └─────────────────────────────────┘
                             ▲              ▲
        ┌────────────────────┘              └────────────────────┐
        │ ①주소 검색 경로                         ②지도 클릭 경로 │
        │                                                       │
 bjdong+bun+ji 입력                                lat/lng 클릭
        │                                                       │
        ▼                                                       ▼
 건축물대장 getBrTitleInfo → dongNm 리스트              LT_C_BLDGINFO WFS
        │                                                  geomFilter=POINT(lng lat)
        │ (선택된 동명으로)                                       │
        ▼                                                       ▼
 LT_C_BLDGINFO WFS                                  → bd_mgt_sn 즉시 획득
 attrFilter=pnu:=:1171010200100170000                     │
 → dong_nm='파크리오 101동' 필터                         │
 → bd_mgt_sn 획득                                        │
        │                                                       │
        └──────────────► 같은 bd_mgt_sn ◄────────────────────────┘
                    → 같은 레코드 → 같은 좌표 → 같은 건물
```

**부속지번 문제 동시 해결**:
- 경로 ② 클릭 위치가 부속지번(20)이어도 `LT_C_BLDGINFO`는 건물 단위이므로 `bd_mgt_sn`으로 본번(17)의 건축물대장을 역조회 가능
- 경로 ① 지번 입력이 "신천동 20"이어도 서버에서 `LT_C_BLDGINFO` bbox 조회 → 인근 건물의 `bd_mgt_sn`이 본번 17로 등록되어 있음을 확인 → 본번 리다이렉트

**도로명주소 일치**:
- `bd_mgt_sn` 기반 10번 "도로명주소 건물" API (`LT_C_SPBD`)를 부가 조회하면 해당 건물의 공식 도로명주소 획득 — juso.go.kr 오매칭 우회

### B-4. 16개 API 중 통일 API 선정

| 목적 | 선정 API | 근거 |
|---|---|---|
| 경로 ①/② 좌표 통일 | **1번 `LT_C_BLDGINFO`** (geomFilter=POINT 또는 attrFilter=pnu) | 공간 질의와 속성 질의 **모두 수용** — 양 경로 입력 형식 차이 흡수 |
| 부속지번→본번 변환 | **1번 `LT_C_BLDGINFO`** (bbox로 인근 건물 enumerate) | 건물 단위 feature이므로 부속지번 무관 |
| 동 정식 식별 (검증) | **13번 `getBuldDongNmList`** | 1번 `dong_nm`과 교차 확인 — 불일치 시 13번 우선 |
| 도로명↔지번 매칭 | **10번 `LT_C_SPBD`** | 공식 도로명주소건물 DB |
| 전유부 | 건축물대장 + **16번 `getBuldHoNmList`** | 현재 `dong_ho_dict` 보강 |

**운영 체감용 1줄 요약**: "첫 번째 줄(1번 통합)만 제대로 쓰면 90%는 해결된다. 13번은 수년 구축 아파트 검증용, 10번은 도로명주소 혼동 방지용 보험."

---

## Part C. Propedia / PropSheet / PropMap 3개 서비스 작업 범위

### C-1. 작업 범위 매트릭스

| 서비스 | 신규/변경 | 난이도 | 담당 | 우선순위 |
|---|---|---|---|---|
| **Propedia 앱 + HTML 웹** | 매물등록 플로우에 "동 좌표 확보" 단계 추가, 부속지번 본번 리다이렉트 안내 UI | 중 | @propedia-dev | P1 |
| **서버 (공유 property-manager)** | `cadastral_service.py` 확장 4개 메소드, 신규 라우트 2개, `building_dong_geometry` 테이블 | 중상 | @dev-lead + @infra-lead | P0 |
| **PropSheet DB + UI** | 신규 테이블, 기존 82건 재좌표화 배치, 관리자 교정 UI | 중 | @propsheet-dev | P1 |
| **PropMap (정적 HTML)** | 동별 마커 렌더링, 클러스터링, 역매칭 | 중 | @propmap-dev | P2 |

### C-2. Propedia 확장 범위

**파일별 수정안 (구현 미착수)**:

| 파일 (서버) | 수정 내용 |
|---|---|
| `backend/property-manager/services/cadastral_service.py` | 4개 메소드 신규: (a) `get_building_integration(pnu=None, bbox=None)` — 1번 `LT_C_BLDGINFO` 호출 (b) `get_dong_geometry(pnu, dong_nm)` — 1번 + 캐시 (c) `get_building_info_from_coords(lat, lng)` — 부속→본번 변환 (d) `get_road_name_building(bd_mgt_sn)` — 10번 `LT_C_SPBD` |
| `backend/property-manager/services/ldareg_service.py` (신규) | NSDI `LdaregService` 래퍼: `get_buld_sn_list(pnu)`, `get_buld_dong_nm_list(pnu)`, `get_buld_ho_nm_list(pnu, buldSn)` |
| `backend/property-manager/routes/app_api.py` | (a) `search_by_jibun`에 부속→본번 fallback 추가 (b) `/map/click-jibun`에 본번 정보 병합 (c) `/map/dong-coords` 신규 라우트 |
| `backend/property-manager/services/building_unified_service.py` | `_resolve_coordinates()` 4단계로 확장: 1번 → 기존 필지 PNU → geocoder → 카카오 (1번이 성공하면 `source: vworld_bldginfo`) |

**Flutter 앱**: `lib/presentation/providers/map_provider.dart`의 `searchByCoordinate()`에서 `jibunInfo.main_bun/main_ji` 있으면 "부속지번 → 본번 리다이렉트" 토스트 + result_screen 자동 재조회.

### C-3. PropSheet DB 스키마 확정안

```sql
CREATE TABLE building_dong_geometry (
    bd_mgt_sn           VARCHAR(24) PRIMARY KEY,          -- VWorld 건물관리번호 (24자리)
    pnu                 VARCHAR(19) NOT NULL,             -- 본번 기준 PNU
    dong_nm             VARCHAR(100),                     -- VWorld dong_nm
    nsdi_buld_sn        VARCHAR(5),                       -- NSDI 건물일련번호 (15번 API)
    nsdi_dong_nm        VARCHAR(100),                     -- NSDI 정식 동명 (13번 API 검증용)
    center_lat          DECIMAL(10,8) NOT NULL,
    center_lon          DECIMAL(11,8) NOT NULL,
    polygon_geojson     JSONB,                            -- MultiPolygon EPSG:4326
    road_address        VARCHAR(200),                     -- 10번 API 결과
    jibun_address       VARCHAR(200),                     -- "신천동 17"
    use_apr_day         VARCHAR(8),                       -- 사용승인일
    usability           VARCHAR(10),                      -- 용도코드
    grnd_flr            SMALLINT,
    ugrnd_flr           SMALLINT,
    arch_area           DECIMAL(12,2),
    total_area          DECIMAL(14,2),
    plat_area           DECIMAL(14,2),
    height              DECIMAL(8,2),
    source              VARCHAR(30) NOT NULL,             -- 'vworld_bldginfo' | 'nsdi_ldareg' | ...
    is_manual_corrected BOOLEAN DEFAULT FALSE,            -- agent 수동 교정 여부
    corrected_by        INTEGER REFERENCES propnet_users(id),
    corrected_at        TIMESTAMP,
    cached_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bdgeo_pnu ON building_dong_geometry(pnu);
CREATE INDEX idx_bdgeo_dong ON building_dong_geometry(pnu, dong_nm);
CREATE INDEX idx_bdgeo_geohash ON building_dong_geometry USING GIST (ST_MakePoint(center_lon, center_lat));
```

**82건 재좌표화 배치 설계** (`scripts/backfill_multi_unit_dong_coords.py`):

1. `goldenrabbit01_sales_multi_unit`에서 `(지번주소, 동)` 유니크 페어 추출 (~30페어 예상)
2. 각 지번의 PNU 산출 → 1번 `LT_C_BLDGINFO` attrFilter=pnu 호출 → features 전수 캐시
3. `dong_nm` 정규화 매칭 ("파크리오 101동" ≈ "101동" ≈ "101"): 아래 3단계
   - 완전 일치
   - 숫자만 추출한 일치 (101 == 101)
   - 레코드의 건물명(단지명) + 동번호 결합 후 일치
4. 매칭 시 해당 record에 `coordinates_lat/lon` = `center_lat/lon` 업데이트
5. 실행 전후 동일 record 샘플 10건 카카오맵 육안 검증 (@qa-lead)

**PropSheet UI에서의 교정 기능**:
- `propsheet/templates/record_detail.html`에 "이 동 좌표 수정" 토글 — agent가 카카오맵에서 드래그해서 좌표 재설정 시 `is_manual_corrected=TRUE` 기록
- 수동 교정된 건 재좌표화 배치에서 제외

### C-4. PropMap 렌더링

**현재 map.html**의 마커는 `/propsheet/api/propsheet/map-data` 응답을 그대로 찍는 구조. 이관 사항:

| 파일 | 수정 |
|---|---|
| `propmap/map.html` + `propmap/index.html` + 홈페이지 `map.html` (3곳 항상 동기) | (a) `building_dong_geometry` 조인한 map-data 사용 (b) 같은 `(pnu)` 내 복수 마커 클러스터링 (c) 줌 레벨 ≥ 17일 때 각 동별 전개 |
| `backend/property-manager/routes/propsheet.py` `map-data` 엔드포인트 | multi_unit 테이블에 `building_dong_geometry` LEFT JOIN. `center_lat/lon` 있으면 그걸, 없으면 레코드의 `coordinates_lat/lon` 사용 |
| 지도 클릭 → PropSheet 역매칭 | `/map/click-jibun` 결과의 `bd_mgt_sn`으로 `building_dong_geometry` 조회 → 해당 건물의 PropSheet 레코드 있으면 매물 상세 모달 오픈 |

### C-5. 구현 일정 (제안)

| 단계 | 담당 | 기간 | 선행 |
|---|---|---|---|
| ① 오너 의사결정 (본 제안서 수락) | CEO | 즉시 | — |
| ② PRD 확정 — 구현 범위/쿼터/UX | @pm-lead | 2일 | ① |
| ③ `building_dong_geometry` 스키마 + 라우트 설계 | @dev-lead + @infra-lead | 3일 | ② |
| ④ `cadastral_service` 4개 메소드 + `ldareg_service` | @dev-lead | 4일 | ③ |
| ⑤ Propedia 앱 + HTML 웹 동시 수정 | @propedia-dev | 5일 | ④ 병렬 |
| ⑥ PropSheet 82건 재좌표화 배치 + 교정 UI | @propsheet-dev | 3일 | ④ 병렬 |
| ⑦ PropMap 3곳 동기 수정 | @propmap-dev | 4일 | ⑥ 완료 후 |
| ⑧ QA — 파크리오/롯데캐슬/사당자이 + 17 테스트 케이스 | @qa-lead | 3일 | ⑤⑥⑦ |
| ⑨ 배포 + 재시작 | @infra-lead | 1일 | ⑧ |

**총 소요**: 약 3주 (병렬 가정).

---

## 이전 research-dong-coordinates 보고서의 5개 미결정 사항 — 갱신/추가

| # | 이전 상태 | 본 제안서 후 갱신 |
|---|---|---|
| 1. VWorld 쿼터/비용 | 무료 키 1만/일, fallback 정책 미정 | **갱신**: `building_dong_geometry` 캐시로 질의 ≈ 단지 수 × 1회 (평생). 평균 5건/일 예상. 쿼터 걱정 소멸. 단, NED(7,11) + NSDI(12~16)는 별도 쿼터 — NSDI는 각 오퍼레이션 10,000건/일 무료 확인 필요 |
| 2. sales_building(단일) 처리 | 필지 좌표로 충분한가 미정 | **갱신**: 단일건물도 1번 `LT_C_BLDGINFO`로 통일 — 필지 좌표보다 **건물 중심점**이 정확 (필지 좌표는 넓은 필지에서 건물과 멀 수 있음). 단일 테이블도 `building_dong_geometry` 조인 권장 |
| 3. PropMap 클러스터링 UX | 대단지 수십 개 마커 — UX 미정 | **갱신**: 줌 ≤ 16은 단지 단위 1개(단지명 + "N세대"), 줌 ≥ 17은 동별 전개. `.filter-btn` 기존 단일/집합/부분 색상 체계(파랑/녹색/주황) 재사용. 상세 시각 design-lead 확정 필요 |
| 4. `dong_nm`=null 구축 건물 | 대응 방침 미정 | **갱신**: 13번 `getBuldDongNmList` 교차 조회로 정식 동명 획득 시도 → 실패 시 "동 미등록" 배지 + 필지 중심 fallback. 이 경우 agent가 PropSheet에서 수동 교정 가능 (`is_manual_corrected`) |
| 5. 파일럿 agent 범위 | 미정 | **갱신**: goldenrabbit 단독 파일럿 → 파크리오 포함 송파구 10단지 검증 → 전 agent 확대. 파일럿 중 `building_dong_geometry` 테이블 품질 확인 |

**추가 미결정 사항 (본 제안에서 신규 발생)**:

6. **10번 도로명주소건물(`LT_C_SPBD`) 도입 범위**: Part B 원인 ③ 해결용이지만 비용 대비 효용이 애매 (juso.go.kr 개선으로도 상당 부분 해결 가능). 파일럿에서 juso 오매칭 발생률 측정 후 결정 권고
7. **NSDI LdaregService 서버 IP 화이트리스트 등록**: `apis.data.go.kr/1611000/nsdi/eios/LdaregService`는 일부 구간 서버 IP 화이트리스트 필요할 수 있음 — @infra-lead가 발급 단계에서 현재 서버 IP(175.119.224.71) 등록 필요
8. **PropSheet 수동 교정 권한 범위**: agent는 본인 매물만 교정 가능한지, 중개사 전체 매물까지 가능한지 정책 확정 필요 (Agent 데이터 격리 원칙 관련)

---

## 산출물 요약

### 오너 결정이 필요한 3가지 큰 축

1. **1번 `LT_C_BLDGINFO`를 정식 메인 API로 채택** — Propedia 4단계 좌표 fallback의 최우선 단계로 등록 (즉시 효과: 파크리오 부속지번 오매칭 + 동별 좌표 미분리 + 두 경로 좌표 불일치 **3문제 동시 해결**)
2. **`building_dong_geometry` 테이블 신설 + 3주 구현 일정 승인** — Propedia/PropSheet/PropMap 공통 허브
3. **13번 `getBuldDongNmList` + 10번 `LT_C_SPBD`는 보강용 옵션** — 파일럿 후 본격 도입 판단

### 코드 수정 금지 원칙 준수 확인

본 제안서 작성 과정에서 어떤 소스 파일도 수정하지 않음. WebFetch/WebSearch로 VWorld 공식 문서, 공공데이터포털, WooilJeong PublicDataReader GitHub, qquack.org VBA 샘플만 조회. Grep/Read로 현 코드베이스의 엔드포인트와 기존 조사 문서만 교차 확인.

---

## 참고 근거

### 공식 문서
- [VWorld 2D데이터 API 2.0 레퍼런스](https://www.vworld.kr/dev/v4dv_2ddataguide2_s001.do)
- [VWorld WMS/WFS API 2.0 레퍼런스](https://www.vworld.kr/dev/v4dv_wmsguide2_s001.do)
- [VWorld 광역시도 샘플 명세(LT_C_ADSIDO_INFO)](https://www.vworld.kr/dev/v4dv_2ddataguide2_s002.do?svcIde=adsido) — 공통 파라미터 체계 확인
- [국토교통부_GIS건물통합정보(WMS/WFS) (data.go.kr 15123970)](https://www.data.go.kr/data/15123970/openapi.do)
- [국토교통부_대지권등록정보조회서비스 (data.go.kr 15056691)](https://www.data.go.kr/data/15056691/openapi.do) — Ldareg 5종
- [국토교통부_건물일련번호조회 (data.go.kr 15140363)](https://www.data.go.kr/data/15140363/openapi.do)
- [국토교통부_건물호수조회 (data.go.kr 15140366)](https://www.data.go.kr/data/15140366/openapi.do)
- [VWorld 용도별건물 API 활용사례](https://qquack.org/excel/openapi-buildinginfo/) — `/ned/data/getBuildingUse` 22개 출력 필드
- [WooilJeong PublicDataReader - VworldData](https://github.com/WooilJeong/PublicDataReader/blob/main/assets/docs/vworld/VworldData.md)
- [VWorld 공식 교육 샘플](https://github.com/V-world/V-world_API_sample)

### 본 프로젝트 선행 문서
- `docs/research-dong-coordinates-2026-04-16.md` (동별 좌표 확정 실증)
- `propedia/docs/plan-building-footprint-lookup.md` (부속지번→본번 변환 기획)
- `propedia/docs/test-case-review-guide.md` (17개 테스트 케이스, `location.source` 필드 정의)
- `propedia/docs/service-architecture.md` (API 엔드포인트 구조)
- `propmap/docs/progress.md` (PropMap 동기화 규칙)

### 코드 근거 (로컬 실측)
- `propedia/lib/data/datasources/remote/map_api.dart` L10-46 — `/map/click-jibun`, `/map/geocode`
- `propedia/lib/presentation/providers/map_provider.dart` L74-123 — 지도 클릭 플로우
- `propedia/lib/presentation/screens/search/search_map_screen.dart` — SearchMap 화면

### 실호출 검증 (선행 보고서에서 수행)
- VWorld WFS `lt_c_bldginfo` 잠실 파크리오 BBOX 조회 → 파크리오 16개 동 개별 식별 (`research-dong-coordinates` L84-124)
- PropSheet DB `goldenrabbit01_sales_multi_unit` 82건 중 동별 좌표 구분 부재 실증 (`research-dong-coordinates` L47-57)
