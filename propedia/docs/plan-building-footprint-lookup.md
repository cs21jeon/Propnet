# 부속지번 → 본번 자동 매칭 (건물 도형 기반)

> 상태: 미착수 (향후 진행 예정)
> 작성일: 2026-04-02

---

## 1. 문제

부속지번(예: 신천동 20)으로 검색하거나 지도에서 클릭하면 건축물대장이 없어 건물 정보가 표시되지 않음.
실제로는 본번(신천동 17, 파크리오)의 부속지번이므로 본번의 건물 정보가 나와야 함.

### 현재 동작

```
지번 검색 "신천동 20" → 건축물대장 조회(bun=0020) → has_data=False
  → juso.go.kr fallback → "신천동 20-4"(올림피아아파트, 올림픽로 393) 잘못 매칭
  → 건물 정보 없음, 엉뚱한 도로명 표시
```

### 원인

- 건축물대장은 본번(17)에만 등록, 부속지번(20)에는 미등록
- `getBrAtchJibunInfo` API는 본번→부속 방향만 지원 (역방향 불가)
- VWorld 토지 API에는 부속지번 관계 정보 없음 (토지/건물 별개 체계)

### 영향 범위

- 지번 검색 (`/app/api/search/jibun`)
- 지도 클릭 → 조회 (`/app/api/map/click-jibun` → result.html)
- Flutter 앱 지번 검색 + 지도 검색

---

## 2. 해결 방안: VWorld 건물통합정보 WFS

### 핵심 아이디어

필지(지적도) 대신 **건물 도형(건물 윤곽선)**으로 매칭.
건물 폴리곤은 여러 필지에 걸쳐 있어도 **등록 주소(본번)**를 속성으로 가지고 있음.

```
현재:  좌표 → 연속지적도(필지) → "신천동 20" → 건축물대장 없음
개선:  좌표 → 건물통합정보(건물) → "신천동 17" → 건축물대장 있음
```

### VWorld WFS 서비스

| 항목 | 값 |
|------|---|
| 서비스명 | 건물통합정보 |
| 서비스ID | `lt_c_bldginfo` |
| API URL | `https://api.vworld.kr/req/wfs` |
| API 키 | 기존 `VWORLD_APIKEY` 사용 가능 (활용 신청 필요할 수 있음) |
| 좌표계 | EPSG:4326 |
| 출력 | application/json (GeoJSON) |

### 예상 요청

```
GET https://api.vworld.kr/req/wfs
  ?service=wfs
  &version=2.0.0
  &request=GetFeature
  &typename=lt_c_bldginfo
  &output=application/json
  &srsname=EPSG:4326
  &bbox={lng-0.0001},{lat-0.0001},{lng+0.0001},{lat+0.0001}
  &key={VWORLD_APIKEY}
```

### 예상 응답 속성

| 필드 | 의미 |
|------|------|
| `pnu` | 건물 등록 PNU (본번 기준) |
| `addr` | 건물 주소 |
| `bld_nm` | 건물명 |
| `geometry` | 건물 윤곽선 (Polygon/MultiPolygon) |

---

## 3. 구현 플랜

### Phase 1: API 검증 (1일)

1. VWorld 건물통합정보 WFS 활용 신청 (필요 시)
2. 테스트 스크립트로 신천동 20 좌표에서 건물 도형 조회
3. 응답 필드 확인 — PNU, 주소, 건물명이 "신천동 17 파크리오"로 나오는지
4. 사당동 280-3 좌표에서도 동일 테스트

### Phase 2: 서버 로직 구현 (2일)

#### 2-1. cadastral_service.py에 건물 도형 조회 메서드 추가

```python
def get_building_info_from_coords(self, lat, lng):
    """좌표로 건물통합정보 조회 (건물 도형 기반)"""
    # VWorld WFS lt_c_bldginfo BBOX 조회
    # 건물 PNU → 본번 bun/ji 추출
    # 반환: { 'success': True, 'pnu': '...', 'bun': '0017', 'ji': '0000', 'bld_nm': '파크리오' }
```

#### 2-2. app_api.py의 search_by_jibun에 fallback 추가

```python
# 현재: has_data=False → juso.go.kr fallback (잘못된 매칭)
# 개선:
if not building_result.get('has_data'):
    # 1단계: 좌표 기반 건물 도형 조회
    location = _resolve_coordinates(codes, address_info)
    if location.get('lat'):
        bldg = cadastral_service.get_building_info_from_coords(location['lat'], location['lng'])
        if bldg.get('success') and bldg['bun'] != bun:
            # 본번이 다름 → 부속지번으로 판단
            # 본번으로 search_building 재실행
            main_bun, main_ji = bldg['bun'], bldg['ji']
            building_result = building_service.search_building(sigungu_cd, bjdong_cd, main_bun, main_ji)
            # 이하 기존 로직 계속...
```

#### 2-3. map_click_jibun에도 동일 로직 적용

```python
@bp.route('/map/click-jibun', methods=['POST'])
def map_click_jibun():
    # 기존: VWorld 역지오코딩 (필지 기반)
    result = cadastral_service.get_jibun_from_coords(lat, lng)

    # 추가: 건물 도형 기반 본번 확인
    bldg = cadastral_service.get_building_info_from_coords(lat, lng)
    if bldg.get('success'):
        result['jibun_info']['main_pnu'] = bldg['pnu']
        result['jibun_info']['main_bun'] = bldg['bun']
        result['jibun_info']['main_ji'] = bldg['ji']
```

### Phase 3: 클라이언트 대응 (1일)

- result.html: 본번 리다이렉트 시 "부속지번 → 본번" 안내 표시
- Flutter 앱: map_provider.dart에서 main_bun/main_ji 처리
- search-map.html: 지도 클릭 결과에 본번 정보 반영

### Phase 4: 테스트 (0.5일)

| 테스트 케이스 | 기대 결과 |
|-------------|----------|
| 신천동 20 지번 검색 | → 신천동 17 파크리오 건물 정보 |
| 신천동 20 지도 클릭 | → 신천동 17 파크리오 표시 |
| 사당동 280-3 지번 검색 | → 사당동 280-1 건물 정보 |
| 사당동 산 32-77 (임야) | → 건물 없음 (정상) |
| 사당동 318-107 (나대지) | → 건물 없음 (정상) |

---

## 4. Fallback 전략 (건물 도형 조회 실패 시)

건물통합정보에 데이터가 없는 경우를 대비:

```
1순위: 건물통합정보 WFS (좌표 → 건물 PNU)
2순위: 토지이용상황 기반 인근 탐색 (±5 범위)
         - land_use_situation이 주거용(아파트/다세대/연립)일 때만
         - 같은 본번 ji=0000 먼저, 그 다음 bun ±1~±5
         - getBrTitleInfo totalCount>0 확인 (경량)
         - 발견 시 부속지번 목록에 현재 지번 포함 여부 확인
3순위: 현재 동작 유지 (juso.go.kr fallback)
```

---

## 5. 조사 결과 요약 (2026-04-02)

### 확인된 사실

- `getBrAtchJibunInfo`: 본번→부속 방향만 조회 가능, 역방향 불가
- VWorld 연속지적도(`lp_pa_cbnd_bubun`): 필지별 독립 속성만 제공, 부속관계 없음
- VWorld 토지특성정보: `land_use_situation_name`으로 토지용도 확인 가능
- juso.go.kr: "신천동 20" 검색 시 "20-4"(올림피아아파트)가 1위 매칭 (오매칭)

### 테스트 데이터

| 지번 | 역할 | 건축물대장 | 비고 |
|------|------|-----------|------|
| 신천동 17 | 본번 | 있음 (파크리오) | 부속: 17-4, 20, 20-6 |
| 신천동 20 | 부속지번 | 없음 | 토지이용: 아파트 |
| 신천동 20-4 | 별도 건물 | 별도 (올림피아) | 올림픽로 393 |
| 사당동 280-1 | 본번 | 있음 (공동주택) | 9필지 합산 |
| 사당동 280-3 | 부속지번 | 없음 | 토지이용: 다세대 |

### 참고 사이트

- disco.re: 지도 클릭 시 건물 도형 기반으로 본번 표시 (지번 검색은 미지원)
- VWorld 건물통합정보: `lt_c_bldginfo` WFS 서비스

---

## 6. 수정 대상 파일

| 파일 | 위치 | 수정 내용 |
|------|------|----------|
| cadastral_service.py | 서버 `/backend/property-manager/services/` | 건물 도형 조회 메서드 추가 |
| app_api.py | 서버 `/backend/property-manager/routes/` | search_by_jibun, map_click_jibun fallback |
| search-map.html | 서버 `/frontend/public/app/` | 지도 클릭 결과에 본번 반영 |
| map_provider.dart | Flutter `lib/presentation/providers/` | main_bun/main_ji 처리 |
| result_screen.dart | Flutter `lib/presentation/screens/search/` | 부속지번 안내 표시 |
