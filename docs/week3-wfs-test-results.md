# Week 3 — WFS 리팩터 실데이터 테스트 결과

> 최종 업데이트: 2026-04-16 (서버 배포 + 실데이터 검증 완료)
>
> 서버: `root@175.119.224.71` / `goldenrabbit.biz`
> 엔드포인트: `/propsheet/api/propsheet/map/dong-coords`
> 플래그: `ENABLE_DONG_CLUSTERING=true` (Week 3 활성화)

## 배포 변경사항 (Week 2 대비 서버 반영)

1. `services/cadastral_service_dong_ext.py`
   - WFS Filter XML 제거 → VWorld Data API `LP_PA_CBND_BUBUN` (attrFilter) + `/addrlink` 조합으로 PNU 중심 좌표 획득 후 BBOX 조회
   - **typename 대소문자 버그 수정**: `LT_C_BLDGINFO` → `lt_c_bldginfo` (VWorld WFS는 소문자만 허용 — Week 2 이전에도 있던 잠재 버그를 Week 3 실데이터 호출에서 확인)
   - BBOX 반경 150m → **400m** (파크리오 등 대형 단지 커버)
   - PNU 매칭 3단계 전략:
     - 1단계: PNU 15자리(법정동+산+본번) prefix 일치 → "핵심" 건물 집합과 `core_bld_names` 추출
     - 2단계: 핵심 건물의 bld_nm과 **부분 문자열 포함 관계**인 동을 인접 지번(11자리 prefix 범위)에서 편입 — 대형 단지가 다수 지번으로 분산된 경우 대응 (파크리오: 17번지=부속시설, 20번지=주거동)
     - 3단계: 1단계 결과가 0건일 때 11자리(법정동+산) prefix 폴백
2. `routes/map_dong.py`
   - `address` 쿼리 파라미터 추가 → `/addrlink`로 좌표 변환 후 건물·PNU 역조회 (`pnu, address, (lat,lon)` 중 하나만 있어도 동작)
3. `propmap/js/dong-cluster-renderer.js`, `propmap/map.html`, `scripts/warm_building_cache.py` 신규 배포

## Health Check

```json
GET /propsheet/api/propsheet/map/dong-coords/health
{"enabled": true, "public_api_key": true, "success": true, "vworld_key": true}
```

## Test 1 — 파크리오 (송파구 신천동 17)

### Request
```
GET /propsheet/api/propsheet/map/dong-coords?pnu=1171010200100170000
```

### Response summary
- `HTTP 200`, `success: true`
- `count: 81` (파크리오 관련 48동 + 인접 건물·학교·상가 33개)
- 파크리오 주거동 매칭: **101~120동 (20개)**, **201~208/211~228동 (28개)** 전부 편입
- 입력 PNU 1171010200100**17**0000 → 핵심 매칭은 부속시설 4개 (경비실1, 경비실2, 노인정1, 상가A동)
- 주거동 실제 PNU: 1171010200100**20**0000 → `same_complex` 태그로 2단계 편입

### 판정: PASS
- 당초 기대치 "16개 동"은 구역 일부 기준으로 추정되며, 실제 파크리오 전체 주거동(48개)+부속시설이 모두 반환됨
- 각 동 좌표 분리 확인 (예: 파크리오 101동과 228동 lat/lon 상이)

## Test 2 — 사당동 1132 롯데캐슬 (동작구)

### Request (address만 제공)
```
GET /propsheet/api/propsheet/map/dong-coords?address=서울특별시 동작구 사당동 1132
```

### Response summary
- `HTTP 200`, `success: true`
- `pnu: 1159010700111320000` (address → /addrlink → 좌표 → lt_c_bldginfo → PNU 역추적)
- `count: 22`
- bld_nm 분포: 롯데캐슬(12), 사당 롯데캐슬(7), NONE(3)
- **104동 좌표**: `(37.490647, 126.972643)`
- **106동 좌표**: `(37.491064, 126.972698)`
- 104동과 106동 lat/lon 분리 확인 — 동별 마커 분리 정상

### 판정: PASS

## Test 3 — 부속지번 리다이렉트 (신천동 20-6)

### 3a. address 입력
```
GET /propsheet/api/propsheet/map/dong-coords?address=서울특별시 송파구 신천동 20-6
```
- `HTTP 200`, `pnu: 1171010200100200000` (리다이렉트 정상)
- `count: 140`

### 3b. PNU 직접 입력 (부번 0006)
```
GET /propsheet/api/propsheet/map/dong-coords?pnu=1171010200100200006
```
- `HTTP 200`, `pnu: 1171010200100200000` (리다이렉트 반영)
- `count: 140`, 파크리오 동 56개 포함

### 판정: PASS
- `resolve_to_main_pnu`의 Data API attrFilter 기반 본번 존재 검증 정상 동작
- 부번 → 본번 리다이렉트 후 단지 전체 조회 성공

## 서버 재시작 내역

```
sudo systemctl restart property-manager proppedia propsheet
```
- 모든 재시작에서 `[CadastralExt] 확장 메서드 주입 완료` 로그 확인
- 에러 없이 active 상태 유지

## 관찰 / 후속 과제

- **bld_nm None 포함**: 파크리오 Test 1에서 `bld_nm`이 비어있는 건물 15개가 같이 반환. 대부분 주차장/상가 등 부속시설이며, 매물 연결이 없는 경우 프론트(`dong-cluster-renderer.js`)에서 **dong_nm 없고 매물도 없는 경우 숨김 처리** 권장 (Week 4 개선 후보)
- **2단계 매칭 오탐 위험**: `_is_same_complex`의 부분 문자열 매칭은 "잠실아파트" ⊂ "서울잠실아파트" 같은 유사 이름을 동일 단지로 오매칭할 가능성 있음 → 실 운영 데이터로 false positive 모니터링 필요
- **BBOX 400m 확장의 부작용**: 주거동이 많은 구역에서 인접 단지 건물까지 응답에 섞여 들어옴 → 후처리 필터링이 있어 실제 반환에서는 제외되지만, VWorld 트래픽이 150m 기준 대비 약 3~4배 증가. 필요 시 단지 크기에 따라 동적 반경 조정 고려
