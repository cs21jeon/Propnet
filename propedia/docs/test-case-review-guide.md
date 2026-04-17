# 부동산 정보 조회 앱 - 테스트 케이스 검토 가이드

---

## 1. 개요

웹앱, Flutter 크롬앱, Flutter 모바일앱의 **조회화면**과 **PDF 출력**의 일관성을 검증하는 프로세스입니다.

---

## 2. 핵심 동작 원칙

테스트 전 반드시 숙지해야 할 시스템 동작 원칙:

| 원칙 | 설명 |
|------|------|
| **도로명주소 = 건축물대장** | 도로명주소는 건물이 있을 때만 건축물대장(`new_plat_plc`)에서 제공. 건물 없는 토지는 도로명주소 표시 안 함 |
| **임야에도 건물 가능** | 산번지(land_type=2)라고 건물이 없는 것은 아님. 토지 유형과 무관하게 건물 유무로 판단 |
| **신규 행정구역 이중 코드** | 동탄구 등 신규 행정구역은 건축물대장=신 코드, VWorld 토지=구 코드. API마다 다른 코드 사용 |
| **공시지가 vs 공동주택가격** | 공시지가=토지 가격(㎡당), 공동주택가격=해당 호수의 주택 가격. 별도 API |
| **대지지분/공동주택가격 항상 표시** | 데이터 없으면 "-"로 표시. 칸 자체를 숨기지 않음 |

---

## 3. 테스트 케이스 목록

| # | 주소 | 케이스 유형 | 중점 확인 사항 |
|---|------|------------|---------------|
| 1 | 사당동 산 32-77 | 토지만 (임야) | 공시지가 정상 파싱 (xmltodict 리스트 처리), 도로명주소 미표시, 산 표시 |
| 2 | 사당동 318-107 | 토지만 (대지) | 건물 없을 때 도로명주소 미표시, 토지정보 상세표시 |
| 3 | 사당동 1044-23 | 일반건축물 | 주용도, 층별정보, 도로명주소(건축물대장) 표시 |
| 4 | 사당동 314-12 동없음 201호 | 공동주택 (동 없음) | 동 없는 공동주택 처리, 공동주택가격 표시 |
| 5 | 사당동 280-1 101동 201호 | 다필지 공동주택 (엘파라시오8차) | 9필지 합산, 도로명 검색 시 대표지번(280-1) 정확성, 지도 표시 |
| 6 | 사당동 1154 108동 206호 | 대규모 아파트 (480세대) | 해당동 정보, 전유부, 대지지분 |
| 7 | 사당동 105 101동 101호 | 초대규모 아파트 (4,613세대) | VWorld 대지지분, 부속지번, 39개동 |
| 8 | 사당동 147-29 이수자이동 101-1402호 | 복잡한 동/호명 | 특수 동명/호명 매칭 |
| 9 | 사당동 86-6 동없음 101호 | 비주거 건물 | 주택 아닌 multi_unit 처리 |
| 10 | 화성시동탄구 영천동 892 321동 301호 | 신규 행정구역 | 건축물대장 신 코드 폴백, 공시지가(구 코드), 공동주택가격 |
| 11 | 화성시동탄구 오산동 1089 103동 801호 | 신규 행정구역 대단지 (1,837세대) | DB 캐시 대지지분 |
| 12 | 화성시동탄구 여울동 971 101동 1001호 | 신규 행정구역 (동 이름 변경) | old_bjdong_code 매핑(여울동→오산동), VWorld PNU 구 코드 폴백 |
| 13 | 화성시동탄구 신동 898 2311동 1001호 | 신규 행정구역 + VWorld 미등재 | 건축물대장 신 코드 폴백, 공시지가 없음(정상), 통합검색 동명 중복 |
| 14 | 화성시동탄구 신동 822 4018동 201호 | 신규 행정구역 | 구 코드 매핑, 신축건물 |
| 15 | 달성군 옥포읍 기세리 969-22 | 읍/면+리, 법정동≠행정동 | bjdong_code: 2771026226, ri_name 표시 |
| 16 | 태안군 태안읍 남산리 151 | 읍/면+리, 토지만 | 건물 없으므로 도로명 미표시, 통합검색 리 주소 인식, 지도 정확도 |
| 17 | 포천시 소흘읍 이동교리 123 | 읍/면+리 주소 | 리 이름 표시, 지도 정확도 확인 |

---

## 4. 케이스별 상세 검증 가이드

### Case 1: 토지만 (임야) — 사당동 산 32-77

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"32","ji":"77","land_type":"2"}'
```

**중점 확인:**
- [ ] `land.public_land_price` > 0 (2025년 기준 348,200원/㎡)
- [ ] `land.price_year` = "2025"
- [ ] `building.has_data` = false
- [ ] `building.building_info.new_plat_plc` = null (**건물 없으므로 도로명 미표시**)
- [ ] 지번주소에 "산" 표시: "사당동 산 32-77"
- [ ] 토지정보 상세표시 (지목, 이용상황, 지형 등)

**과거 버그:** VWorld XML에 `<pblntfPclnd>` 태그 중복 → xmltodict가 리스트로 파싱 → `float([...])` TypeError → 공시지가 0원 표시. `_first()` 헬퍼로 수정 완료.

### Case 2: 토지만 (대지) — 사당동 318-107

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"318","ji":"107","land_type":"1"}'
```

**중점 확인:**
- [ ] `building.has_data` = false
- [ ] `building.building_info.new_plat_plc` = null (**건물 없으므로 도로명 미표시**)
- [ ] 토지정보 정상 표시

### Case 3: 일반건축물 — 사당동 1044-23

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"1044","ji":"23","land_type":"1"}'
```

**중점 확인:**
- [ ] `building.type` = "general"
- [ ] `building.building_info.new_plat_plc` 존재 (건축물대장에서 제공)
- [ ] 주용도, 층별정보 정상 표시
- [ ] 단독주택 공시가격 (`building_info.house_price`) 표시 여부

### Case 4: 공동주택 (동 없음) — 사당동 314-12

```bash
# 건물 조회
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"314","ji":"12","land_type":"1"}'

# 전유부 조회
curl -s -X POST "https://goldenrabbit.biz/app/api/area" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"314","ji":"12","dong_nm":"동 없음","ho_nm":"201호"}'
```

**중점 확인:**
- [ ] `building.type` = "multi_unit"
- [ ] 동 없는 경우 "동 없음"으로 표시
- [ ] 공동주택가격 행 항상 표시 (데이터 없으면 "-")
- [ ] 대지지분 행 항상 표시 (데이터 없으면 "-")
- [ ] VWorld 공동주택가격 API에서 `dongNm=''`(빈 동)일 때도 호수 매칭

### Case 5: 다필지 공동주택 — 사당동 280-1 (엘파라시오8차)

```bash
# 건물 조회
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"280","ji":"1","land_type":"1"}'

# 전유부 조회 (101동 201호)
curl -s -X POST "https://goldenrabbit.biz/app/api/area" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"280","ji":"1","dong_nm":"101동","ho_nm":"201호"}'
```

**중점 확인:**
- [ ] 필지수 표시: 9필지 (부속지번 8개 + 본번)
- [ ] 공동주택가격 정상 표시 (295,000,000원 / 2025년)
- [ ] 도로명 검색 "사당로14길 67" → 대표지번 **280-1** (280-4가 아님)
- [ ] 도로명 검색 결과 → result.html 이동 시 **지도 정상 표시**
- [ ] `/search/bdmgtsn` 응답에 `location` 필드 포함

**과거 버그:**
1. 도로명 검색 시 VWorld getCoord → handleMapClick 역지오코딩 → 280-4 매칭. juso.go.kr bdMgtSn 직접 반환으로 수정.
2. bdMgtSn 파라미터로 이동 시 지도 미표시 → `/search/bdmgtsn`에 `_resolve_coordinates` 추가.

### Case 6: 대규모 아파트 — 사당동 1154

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"1154","ji":"0","land_type":"1"}'
```

**중점 확인:**
- [ ] 480세대
- [ ] 해당동 정보, 전유부 정보 표시
- [ ] DB 캐시 대지지분

### Case 7: 초대규모 아파트 — 사당동 105 (극동아파트 4,613세대)

```bash
# 건물 조회
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"105","ji":"0","land_type":"1"}'

# 전유부 조회 (대지지분 VWorld API)
curl -s -X POST "https://goldenrabbit.biz/app/api/area" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"105","ji":"0","dong_nm":"101동","ho_nm":"101호"}'
```

**중점 확인:**
- [ ] 39개동 정상 표시
- [ ] VWorld 대지지분 조회
- [ ] 부속지번 표시

### Case 8: 복잡한 동/호명 — 사당동 147-29

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"147","ji":"29","land_type":"1"}'
```

**중점 확인:**
- [ ] "이수자이동" 동명 매칭
- [ ] "101-1402호" 호명 매칭

### Case 9: 비주거 건물 — 사당동 86-6

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"86","ji":"6","land_type":"1"}'
```

**중점 확인:**
- [ ] 주택 아닌 multi_unit 처리 (근생 등)

### Case 10: 신규 행정구역 — 영천동 892 (동탄파크자이)

```bash
# 지번 검색
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4159710600","bun":"892","ji":"0","land_type":"1"}'

# 전유부 조회 (321동 301호)
curl -s -X POST "https://goldenrabbit.biz/app/api/area" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4159710600","bun":"892","ji":"0","dong_nm":"321동","ho_nm":"301호"}'
```

**중점 확인:**
- [ ] `building.has_data` = true, `building.type` = "multi_unit"
- [ ] **건축물대장**: 구 코드(`41590/13100`) 실패 → 신 코드(`41597/10600`) 폴백 성공
- [ ] `codes.old_bjdong_code` = "4159013100"
- [ ] 공시지가 정상 표시 (구 PNU `4159013100...`로 VWorld 조회)
- [ ] 공동주택가격 정상 표시 (구 PNU로 VWorld 조회)
- [ ] 대지지분 정상 표시

**핵심 원칙:** 건축물대장 API는 구 코드/신 코드 이중 시도, VWorld 토지/가격 API는 구 코드(api_pnu) 사용.

### Case 11: 신규 행정구역 대단지 — 오산동 1089 (동탄역롯데캐슬)

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4159710400","bun":"1089","ji":"0","land_type":"1"}'

curl -s -X POST "https://goldenrabbit.biz/app/api/area" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4159710400","bun":"1089","ji":"0","dong_nm":"103동","ho_nm":"801호"}'
```

**중점 확인:**
- [ ] 건물명 "동탄역롯데캐슬", 1,837세대
- [ ] `codes.old_bjdong_code` = "4159012900"
- [ ] 전유부 조회: 전용면적 102.71㎡, 대지지분 22.58㎡

### Case 12: 신규 행정구역 (동 이름 변경) — 여울동 971

> 여울동은 오산동에서 이름이 변경된 법정동. `old_bjdong_code` 매핑 필수.

```bash
# 지번 검색
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4159711500","bun":"971","ji":"0","land_type":"1"}'

# 전유부 조회 (101동 1001호)
curl -s -X POST "https://goldenrabbit.biz/app/api/area" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4159711500","bun":"971","ji":"0","dong_nm":"101동","ho_nm":"1001호"}'
```

**중점 확인:**
- [ ] `codes.api_pnu` = "4159012900109710000" (오산동 구 코드)
- [ ] 공시지가: 8,961,000원/㎡ (2025년) — 구 PNU(`4159012900...`)로 조회
- [ ] 공동주택가격: 726,000,000원 (2025년) — 구 PNU로 VWorld 조회
- [ ] 건축물대장: 신 코드(`41597/11500`) 직접 성공 또는 폴백

**과거 버그:** `bjdong_codes` 테이블에 `old_bjdong_code` 매핑 누락 → VWorld 조회 불가 → DB에 `4159711500 → 4159012900` 매핑 추가.

### Case 13: 신규 행정구역 + VWorld 미등재 — 신동 898

```bash
# 통합검색 (동명 중복 테스트)
curl -s "https://goldenrabbit.biz/api/search/unified?q=신동+898"

# 지번 검색
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4159710800","bun":"898","ji":"0","land_type":"1"}'

# 전유부 조회 (2311동 1001호)
curl -s -X POST "https://goldenrabbit.biz/app/api/area" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4159710800","bun":"898","ji":"0","dong_nm":"2311동","ho_nm":"1001호"}'
```

**중점 확인:**
- [ ] **통합검색**: "신동 898" → 동탄구 신동이 목록에 포함 (전국 신동 전부 표시)
- [ ] 건축물대장: 신 코드(`41597/10800`) 폴백 성공, `has_data` = true
- [ ] 공시지가: "-" (VWorld 데이터 미등재 — **정상**)
- [ ] 대지지분: "-" (토지 데이터 없어 계산 불가 — **정상**)
- [ ] 공동주택가격: "-" (VWorld 데이터 미등재 — **정상**)
- [ ] **표시 원칙**: 데이터 없어도 행은 보이고 "-"로 표시

### Case 14: 신규 행정구역 — 신동 822

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4159710800","bun":"822","ji":"0","land_type":"1"}'
```

**중점 확인:**
- [ ] 건축물대장 신 코드 폴백 정상
- [ ] 구 코드 매핑 확인

### Case 15: 옥포읍 기세리 — 법정동≠행정동

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"2771026226","bun":"969","ji":"22","land_type":"1"}'
```

**중점 확인:**
- [ ] bjdong_code: `2771026226` (기세리)
- [ ] `address.ri_name` = "기세리"
- [ ] 도로명주소: 건축물대장에서 제공 (건물 있는 경우)
- [ ] `location.source`: kakao

### Case 16: 읍/면+리, 토지만 — 태안읍 남산리 151

```bash
# 통합검색
curl -s "https://goldenrabbit.biz/api/search/unified?q=태안읍+남산리+151"

# 지번 검색
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4482525024","bun":"151","ji":"0","land_type":"1"}'
```

**중점 확인:**
- [ ] **통합검색**: "태안읍 남산리 151" → "충청남도 태안군 태안읍 남산리 151" 첫 결과
- [ ] **통합검색**: "남산리 151" → 전국 남산리 전부 표시, prefix "태안읍" 필터링
- [ ] `building.has_data` = false
- [ ] **도로명주소 미표시** (건물 없으므로 `new_plat_plc` = null)
- [ ] `address.ri_name` = "남산리"
- [ ] 지도 마커: "태안읍 남산리 151" (ri_name 포함)
- [ ] `location.source`: kakao

**과거 버그:**
1. 통합검색 `RE_DONG_BUN`이 `*동`만 인식 → `*리|*가` 추가.
2. 도로명 조회 시 "태안읍 151"로 검색 → ri_name 누락 → "독샘로 151" 잘못 매칭 → 건물 없으면 도로명 조회 자체 제거.

### Case 17: 읍/면+리 — 소흘읍 이동교리 123

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"4165025022","bun":"123","ji":"0","land_type":"1"}'
```

**중점 확인:**
- [ ] `address.ri_name` = "이동교리"
- [ ] 지도 마커: "소흘읍 이동교리 123"
- [ ] `location.source`: kakao

---

## 5. 데이터 조회 방법

### 5.1 건물/토지 기본정보 조회 (jibun API)

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/search/jibun" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"86","ji":"6","land_type":"1"}'
```

**파라미터:**
- `bjdong_code`: 법정동코드 (사당동 = 1159010700)
- `bun`: 본번 (86)
- `ji`: 부번 (6)
- `land_type`: 토지구분 (1=대지, 2=임야)

**응답 구조:**
```json
{
  "success": true,
  "address": { "sido_name", "sigungu_name", "eupmyeondong_name", "ri_name", "full_address" },
  "codes": { "bjdong_code", "bun", "ji", "pnu", "api_pnu", "old_bjdong_code" },
  "land": { "land_area", "parcel_count", "public_land_price", "price_year", ... },
  "building": {
    "type": "general" | "multi_unit" | null,
    "has_data": true/false,
    "building_info": { "new_plat_plc": "도로명(건물있을때만)", "house_price": ..., ... },
    "recap_title_info": { ... },
    "dong_ho_dict": { "동명": [{ "ho_nm": "101호" }, ...] },
    "floor_info": [ ... ]
  },
  "location": { "lat": 37.483, "lng": 126.97, "source": "vworld_pnu" | "vworld_api_pnu" | "kakao" }
}
```

### 5.2 전유부 정보 조회 (area API)

```bash
curl -s -X POST "https://goldenrabbit.biz/app/api/area" \
  -H "Content-Type: application/json" \
  -d '{"bjdong_code":"1159010700","bun":"280","ji":"1","dong_nm":"101동","ho_nm":"201호"}'
```

**응답 구조:**
```json
{
  "success": true,
  "area_info": {
    "dong_nm": "101동",
    "ho_nm": "201호",
    "exclusive_area": 49.19,
    "supply_area": 58.75,
    "land_share": 25.5,
    "house_price": 295000000,
    "house_price_year": "2025",
    "house_price_month": "01",
    "dong_title_info": { ... }
  }
}
```

### 5.3 통합검색 (unified API)

```bash
curl -s "https://goldenrabbit.biz/api/search/unified?q=사당동+280"
```

**지원 패턴:**
- 지번: `신동 898`, `남산리 151`, `태안읍 남산리 151`
- 도로명: `사당로14길 67`
- 건물명: `파크리오`, `동탄파크자이`

---

## 6. 검토 대상 파일

### 6.1 웹앱 (goldenrabbit.biz/app)

| 파일 | 위치 | 용도 |
|------|------|------|
| index.html | `/home/webapp/goldenrabbit/frontend/public/app/index.html` | 검색화면 + 통합검색 |
| result.html | `/home/webapp/goldenrabbit/frontend/public/app/result.html` | 조회화면 + PDF 생성 |

### 6.2 백엔드 API

| 파일 | 위치 | 용도 |
|------|------|------|
| app_api.py | `/backend/property-manager/routes/app_api.py` | /search/jibun, /search/bdmgtsn, /area |
| search_unified.py | `/backend/property-manager/routes/search_unified.py` | /api/search/unified |
| vworld_service.py | `/backend/property-manager/services/vworld_service.py` | VWorld API (토지, 주택가격) |
| building_unified_service.py | `/backend/property-manager/services/building_unified_service.py` | 건축물대장 API |

### 6.3 Flutter 앱

| 파일 | 경로 | 용도 |
|------|------|------|
| result_screen.dart | `lib/presentation/screens/search/result_screen.dart` | 조회화면 |
| pdf_generator.dart | `lib/core/pdf/pdf_generator.dart` | PDF 생성 |

---

## 7. 검증 항목 체크리스트

### 7.1 기본정보 섹션

| 항목 | 웹앱 조회 | 웹앱 PDF | Flutter 조회 | Flutter PDF |
|------|----------|---------|--------------|-------------|
| 지번주소 (시도+리 포함) | ☐ | ☐ | ☐ | ☐ |
| 도로명주소 (건물 있을 때만) | ☐ | ☐ | ☐ | ☐ |
| 건물 없을 때 도로명 미표시 | ☐ | ☐ | ☐ | ☐ |
| 세대/가구/호 값 | ☐ | ☐ | ☐ | ☐ |
| 주용도 | ☐ | ☐ | ☐ | ☐ |

### 7.2 토지정보 섹션

| 항목 | 웹앱 조회 | 웹앱 PDF | Flutter 조회 | Flutter PDF |
|------|----------|---------|--------------|-------------|
| 토지면적 + 평 | ☐ | ☐ | ☐ | ☐ |
| 필지수 [n필지] | ☐ | ☐ | ☐ | ☐ |
| 공시지가 + 년도 (없으면 "-") | ☐ | ☐ | ☐ | ☐ |
| 건물없음: 상세표시 | ☐ | ☐ | ☐ | ☐ |

### 7.3 건물정보 섹션

| 항목 | 웹앱 조회 | 웹앱 PDF | Flutter 조회 | Flutter PDF |
|------|----------|---------|--------------|-------------|
| 대지면적 + 평 + 필지수 | ☐ | ☐ | ☐ | ☐ |
| 연면적 + 평 | ☐ | ☐ | ☐ | ☐ |
| 건축면적 + 평 | ☐ | ☐ | ☐ | ☐ |
| 층수 (모든 건물타입) | ☐ | ☐ | ☐ | ☐ |
| 높이 | ☐ | ☐ | ☐ | ☐ |
| 주차대수 + 대 | ☐ | ☐ | ☐ | ☐ |
| 승강기수 + 기 | ☐ | ☐ | ☐ | ☐ |

### 7.4 지도/위치 섹션

| 항목 | 웹앱 조회 | Flutter 조회 |
|------|----------|--------------|
| 지도 좌표 정확 (올바른 위치) | ☐ | ☐ |
| 지도 마커 레이블 (동+리+번지) | ☐ | ☐ |
| bdMgtSn 이동 시 지도 표시 | ☐ | ☐ |
| 읍/면+리 주소: 리 이름 포함 | ☐ | ☐ |

### 7.5 전유부정보 섹션 (공동주택)

| 항목 | 웹앱 조회 | 웹앱 PDF | Flutter 조회 | Flutter PDF |
|------|----------|---------|--------------|-------------|
| 동/호 | ☐ | ☐ | ☐ | ☐ |
| 전용면적 + 평 | ☐ | ☐ | ☐ | ☐ |
| 공급면적 + 평 | ☐ | ☐ | ☐ | ☐ |
| 대지지분 + 평 (없으면 "-") | ☐ | ☐ | ☐ | ☐ |
| 공동주택가격 + 년도 (없으면 "-") | ☐ | ☐ | ☐ | ☐ |

---

## 8. 주요 코드 위치

### 웹앱 (result.html)
```javascript
displayBasicInfo(data)              // 기본정보 표시
displayLandInfo(land, hasBuilding)  // 토지정보 표시
displayGeneralBuilding(building)    // 일반건축물 표시
displayMultiUnitBuilding(building, codes)  // 공동주택 표시
displayAreaInfo(areaInfo)           // 전유부정보 표시
displayMap(data)                    // 지도 표시 (location 필드 사용)
createPDFPreviewHTML()              // PDF 생성
```

### 웹앱 (index.html)
```javascript
UnifiedSearch.onSelect(item)        // 통합검색 결과 선택 시
// PNU 파싱: bjdong_code(0-10) + land_type(10-11) + bun(11-15) + ji(15-19)
```

### Flutter
```dart
// result_screen.dart
_buildBasicInfoCard()           // 기본정보 카드
_buildLandCard()                // 토지정보 카드
_buildBuildingInfoCard()        // 건물정보 카드
_buildDongTitleInfoSection()    // 해당동 정보
_buildExclusiveInfoSection()    // 전유부 정보

// pdf_generator.dart
_buildBasicInfoSection()        // PDF 기본정보
_buildLandSection()             // PDF 토지정보
_buildBuildingSection()         // PDF 건물정보
_buildAreaInfoSection()         // PDF 전유부정보
```

---

## 9. 발견된 주요 이슈 및 수정 이력

| 날짜 | 이슈 | 영향 범위 | 수정 내용 |
|------|------|----------|----------|
| 2026-02-11 | `fmly` 변수 미정의 버그 | 웹앱 | `fmly` → `family` |
| 2026-02-11 | 세대/가구/호 기본값 | 웹앱 | `-/-/-` → `0/0/0` |
| 2026-02-11 | 필지수 표시 형식 | 전체 | `(합계)` → `[n필지]` |
| 2026-02-11 | 층수/높이/승강기 누락 | Flutter 조회 | 항목 추가 |
| 2026-03-29 | 읍/면+리 검색 실패 | 서버 | ri_name 누락 수정 |
| 2026-03-29 | 지도 위치 오류 | 서버+PWA+앱 | 서버 좌표 해결 (location 필드) |
| 2026-03-29 | Case 15 bjdong_code 오류 | 가이드 | 2771025323 → 2771026226 |
| 2026-04-17 | 공시지가 0원 표시 (Case 1) | 서버 | xmltodict 리스트 파싱 → `_first()` 헬퍼 |
| 2026-04-17 | 도로명 검색 → 부속지번 매칭 (Case 5) | 서버+프론트 | juso.go.kr bdMgtSn 직접 반환, onSelect 우선순위 변경 |
| 2026-04-17 | bdMgtSn 이동 시 지도 미표시 | 서버 | `/search/bdmgtsn`에 `_resolve_coordinates` 추가 |
| 2026-04-17 | 건축물대장 신규 코드 미지원 (Case 10,13) | 서버 | 구 코드 → 신 코드 폴백 로직 (jibun, bdmgtsn, area 3곳) |
| 2026-04-17 | 여울동 old_bjdong_code 누락 (Case 12) | DB | `4159711500 → 4159012900` 매핑 추가 |
| 2026-04-17 | 공동주택가격 빈 동 매칭 실패 | 서버 | VWorld `dongNm=''`일 때 호수만으로 매칭 |
| 2026-04-17 | 공동주택가격 VWorld PNU 오류 (Case 12) | 서버 | `/area`에서 VWorld용 PNU를 api_codes(구 코드) 기반으로 생성 |
| 2026-04-17 | 대지지분/공동주택가격 칸 숨김 | 웹앱 | null일 때 "-" 표시, 칸 항상 노출 |
| 2026-04-17 | PNU 파싱 인덱스 오류 | 웹앱 | `substring(10,14)` → `substring(11,15)` (land_type 1자리 건너뛰기) |
| 2026-04-17 | 통합검색 동명 중복 (Case 13) | 서버 | DB 기반 복수 결과 반환 (VWorld 단일 → bjdong_codes 전체) |
| 2026-04-17 | 통합검색 리 주소 미인식 (Case 16) | 서버 | `RE_DONG_BUN` 패턴에 `리\|가` 추가, ri_name DB 검색 |
| 2026-04-17 | 건물 없는 토지에 잘못된 도로명 | 서버 | 건물 없으면 도로명주소 조회 로직 제거 (jibun, bdmgtsn 2곳) |

---

## 10. 참고 사항

- **서버 접속**: `ssh root@175.119.224.71`
- **서비스 재시작**: `sudo systemctl restart property-manager proppedia propsheet` (3개 공유)
- **법정동코드 (사당동)**: `1159010700`
- **신규 행정구역 코드 매핑 확인**:
  ```sql
  SELECT bjdong_code, old_bjdong_code, full_address
  FROM bjdong_codes
  WHERE bjdong_code LIKE '41597%'
  ORDER BY bjdong_code;
  ```
