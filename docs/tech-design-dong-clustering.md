# 기술 설계 — PropMap 동별 좌표 클러스터링 + 부속지번 수렴

> 작성일: 2026-04-16
> 작성 주체: @dev-lead (발주: @propnet-coo)
> 연관: `docs/prd-propmap-dong-clustering.md`, `docs/research-dong-coordinates-2026-04-16.md`, `docs/vworld-16-api-final-proposal-2026-04-16.md`
> 버전: v1.0 (Week 1 초안, 구현 금지)

---

## 0. 아키텍처 전체도

```
┌────────────────────────────────────────────────────────────────────┐
│                        클라이언트 (지도 3곳)                        │
│   propmap/map.html   propmap/index.html   frontend/.../map.html    │
│                 │                │                │                  │
│                 └────────┬───────┴────────┬──────┘                  │
└──────────────────────────┼────────────────┼─────────────────────────┘
                           │  (줌/bbox)     │
                           ▼                │
              ┌──────────────────────────┐  │
              │ GET /map/dong-coords     │  │
              │  ?bbox=&agent_slug=&zoom=│  │
              │  Port 5000 property-mgr  │  │
              └────────────┬─────────────┘  │
                           │                 │
                ┌──────────┴──────────┐     │
                ▼                      ▼     │
  ┌──────────────────────┐  ┌──────────────────────┐
  │ building_dong_geom   │  │ {agent}_sales_*      │
  │  (공용 캐시 테이블)   │  │  + bd_mgt_sn 컬럼    │
  │  TTL 1년             │  │                       │
  └──────────┬───────────┘  └───────────────────────┘
             │ cache miss
             ▼
  ┌──────────────────────────────────────────┐
  │ cadastral_service.py (확장)               │
  │   + ldareg_service.py (신규)              │
  │   - NSDI LdaregService 5종                │
  │   - VWorld LT_C_BLDGINFO WFS              │
  │   - VWorld LT_C_SPBD (도로명↔bd_mgt_sn)   │
  └──────────────────────────────────────────┘
             ▲
             │ 저장 시 호출
  ┌──────────┴────────────────────────────────┐
  │ Propedia _resolve_coordinates() 4단계     │
  │  (propsheet_save_service.py)              │
  └───────────────────────────────────────────┘
```

---

## 1. 공유 서비스 설계

### 1-1. `services/cadastral_service.py` 확장

위치: `/backend/property-manager/services/cadastral_service.py` (공유 코드 — 5000/5010/5020 동시 반영, 재시작 3서비스 모두)

신규/확장 함수:

```python
# 기존 함수 유지 + 아래 추가

def get_building_footprint_wfs(pnu: str = None, bbox: tuple = None, bd_mgt_sn: str = None) -> list[dict]:
    """
    VWorld LT_C_BLDGINFO WFS 조회.
    입력: pnu (cql_filter=pnu LIKE ...) OR bbox OR bd_mgt_sn
    출력: [{bd_mgt_sn, pnu, dong_nm, bld_nm, geometry(GeoJSON), center_lat, center_lon, ...}]
    """

def resolve_bd_mgt_sn_by_road(road_addr: str) -> str | None:
    """
    도로명주소 → VWorld LT_C_SPBD → bd_mgt_sn.
    파크리오 지번/도로명 불일치 해결의 핵심.
    """

def get_or_fetch_dong_geometry(pnu: str, dong_nm: str = None, bd_mgt_sn: str = None) -> dict | None:
    """
    1) building_dong_geometry 캐시 조회 (TTL 체크)
    2) miss 시 VWorld WFS 호출 → 캐시 저장
    3) 결과 반환
    """

def compute_polygon_centroid(geojson: dict) -> tuple[float, float]:
    """
    MultiPolygon GeoJSON → (lat, lon) 무게중심.
    Shapely 의존 (기존 venv에 있음). 없으면 간단 평균 fallback.
    """
```

### 1-2. `services/ldareg_service.py` 신규

위치: `/backend/property-manager/services/ldareg_service.py`

NSDI `LdaregService` 5종 래퍼:

```python
def list_buld_sn(pnu: str) -> list[dict]:
    """15번 getBuldSnList — 필지 내 건물일련번호 전체 enumerate."""

def list_buld_dong_nm(pnu: str) -> list[dict]:
    """13번 getBuldDongNmList — 필지의 공식 동명 리스트 + buldSn."""

def get_buld_rlnm(pnu: str, buld_sn: str) -> dict | None:
    """14번 getBuldRlnmList — 건물 실명/표시명 (상가B동 등)."""

def list_buld_ho_nm(pnu: str, buld_sn: str) -> list[dict]:
    """16번 getBuldHoNmList — 전유부 호수 + 전유면적."""

def list_buld_flr_ouln(pnu: str, buld_sn: str) -> list[dict]:
    """12번 getBuldFlrOulnList — 층별 용도."""
```

특이사항:
- 엔드포인트: `http://apis.data.go.kr/1611000/nsdi/eios/LdaregService/{operation}`
- 인증키: 기존 `BUILDING_REG_API_KEY` 재사용 또는 신규 `NSDI_LDAREG_KEY` (@infra-lead 확인)
- 타임아웃: 10초, 재시도 2회 (지수 백오프)

---

## 2. 신규 라우트 `/map/dong-coords`

### 2-1. 엔드포인트

```
GET /map/dong-coords
Query:
  - bbox: "minLon,minLat,maxLon,maxLat" (필수)
  - agent_slug: 예 "goldenrabbit" 또는 "all" (필수)
  - zoom: 정수 (선택, 기본 15)
  - category: "building" | "multi_unit" | "all" (선택, 기본 "all")
Response:
  {
    "level": "complex" | "dong",      # 줌에 따라 결정
    "clusters": [
      {
        "id": "<pnu>" 또는 "<bd_mgt_sn>",
        "center": {"lat": ..., "lon": ...},
        "name": "파크리오",            # complex일 때 단지명
        "dong_nm": "103동",            # dong일 때
        "count": 5,                     # 매물 개수
        "ids": ["recA", "recB", ...]   # 상세 조회용 record ID
      }, ...
    ]
  }
```

### 2-2. 서버 처리 흐름

```
1. zoom 판단: zoom < 15 → level=complex (pnu 기준 그룹핑)
              zoom >= 15 → level=dong (bd_mgt_sn 기준 그룹핑)
2. agent_slug="all"이면 agents-public 공개 대상 전체, 아니면 해당 agent 테이블만
3. bbox 내 매물 조회:
     SELECT id, coordinates_lat, coordinates_lon, bd_mgt_sn, pnu, ...
     FROM {agent}_sales_{category}
     WHERE coordinates_lat BETWEEN ? AND ?
       AND coordinates_lon BETWEEN ? AND ?
4. bd_mgt_sn 있는 레코드 → building_dong_geometry JOIN 해 정밀 좌표로 치환
5. level=complex: pnu로 GROUP BY → 단지 중심점 (center_lat 평균)
   level=dong: bd_mgt_sn로 GROUP BY → 동 중심점 (geometry 무게중심)
6. 반환
```

### 2-3. Blueprint 등록

- 파일: `/backend/property-manager/routes/map.py` (신규 또는 기존 확장)
- Blueprint: `map_bp`
- 등록 위치: `/backend/property-manager/app.py` (포트 5000만)
- PropMap 클라이언트는 5000 포트로 직접 호출 (Nginx proxy_pass 경유)

---

## 3. Propedia `_resolve_coordinates()` 4단계 확장

### 3-1. 현재 구현

위치: `/backend/property-manager/services/propsheet_save_service.py` L114-125 `_geocode_record()`
현재: 지번 주소 → VWorld 역지오코딩 → (lat, lon) 1개

### 3-2. 확장 설계

```python
def _resolve_coordinates(self, record: dict) -> tuple[float, float, str | None]:
    """
    집합건물/일반건물 모두 처리. 반환: (lat, lon, bd_mgt_sn_or_None)
    """
    pnu = record.get('pnu')
    dong_nm = record.get('동') or record.get('dong_nm')
    road_addr = record.get('도로명주소')

    # Stage 1: 캐시
    if pnu and dong_nm:
        cache = get_or_fetch_dong_geometry(pnu=pnu, dong_nm=dong_nm)
        if cache:
            return cache['center_lat'], cache['center_lon'], cache['bd_mgt_sn']

    # Stage 2: NSDI LdaregService (동명으로 bd_mgt_sn 찾기)
    if pnu and dong_nm:
        dong_list = list_buld_dong_nm(pnu)
        match = next((d for d in dong_list if d['dong_nm'] == dong_nm), None)
        if match:
            bd_mgt_sn = match['bd_mgt_sn']
            # Stage 2b: bd_mgt_sn으로 WFS 조회 → 캐시 저장
            geom = get_or_fetch_dong_geometry(bd_mgt_sn=bd_mgt_sn)
            if geom:
                return geom['center_lat'], geom['center_lon'], bd_mgt_sn

    # Stage 3: 도로명 경로 (집합건물 아니거나 동명 없음)
    if road_addr:
        bd_mgt_sn = resolve_bd_mgt_sn_by_road(road_addr)
        if bd_mgt_sn:
            geom = get_or_fetch_dong_geometry(bd_mgt_sn=bd_mgt_sn)
            if geom:
                return geom['center_lat'], geom['center_lon'], bd_mgt_sn

    # Stage 4: Fallback — 기존 지번 역지오코딩
    lat, lon = self._legacy_geocode(record)  # 현행 로직
    return lat, lon, None
```

호출부 수정:
- `propsheet_save_service.py`에서 `record['bd_mgt_sn'] = bd_mgt_sn`로 주입
- 저장 SQL에 `bd_mgt_sn` 컬럼 포함

---

## 4. PropSheet 배치 스크립트 설계

### 4-1. 파일 위치

`/backend/property-manager/scripts/batch_fill_bd_mgt_sn.py` (신규)

### 4-2. 실행 흐름

```
1. agents-public 전체 agent 순회 (agents 테이블 SELECT slug)
2. 각 agent당 2개 테이블 처리:
   - {slug}_sales_multi_unit (집합건물 우선)
   - {slug}_sales_building (일반건물)
3. bd_mgt_sn IS NULL 레코드만 배치 크기 100으로 SELECT
4. 각 레코드 → _resolve_coordinates() 호출 → UPDATE
5. 진행률 로깅 (10레코드마다), 실패 레코드는 별도 테이블 batch_failures에 기록
6. agent 단위 COMMIT, 중단 시 체크포인트 (batch_checkpoints 테이블)
```

### 4-3. CLI 옵션

```
python batch_fill_bd_mgt_sn.py \
  --agent <slug>|all \
  --category multi_unit|building|all \
  --limit 100 \
  --dry-run \
  --resume
```

### 4-4. 안전장치

- `--dry-run`: SELECT만 하고 UPDATE 안 함
- `--resume`: 체크포인트에서 재시작
- VWorld 쿼터 초과 시 자동 sleep + 재시도
- 실패율 > 30%면 자동 중단 후 알림

---

## 5. PropMap 3곳 렌더링 로직

### 5-1. 공통 JavaScript 모듈

위치: `propmap/js/dong-cluster-renderer.js` (신규, 3곳이 공유)

```javascript
// 줌 변화 이벤트에 훅
map.on('zoomend', async () => {
  const bbox = map.getBounds().toBBoxString();
  const zoom = map.getZoom();
  const data = await fetch(
    `/map/dong-coords?bbox=${bbox}&agent_slug=${AGENT_SLUG}&zoom=${zoom}`
  ).then(r => r.json());

  clearMarkers();
  if (data.level === 'complex') {
    data.clusters.forEach(c => addComplexMarker(c));  // 집계 마커
  } else {
    data.clusters.forEach(c => addDongMarker(c));     // 동별 마커
  }
});
```

### 5-2. 3곳 동기화 (CRITICAL 규칙)

- `propmap/map.html` — 통합 매물지도
- `propmap/index.html` — 검색 화면
- `frontend/public/.../map.html` — 홈페이지 검색결과 지도

3곳 모두 `dong-cluster-renderer.js` 임포트, 동일 API 호출. 수정 시 3곳 모두 변경 (메모리 `feedback_map_search_sync.md` 준수).

### 5-3. 마커 색상 팔레트

- 기존 9종 팔레트 유지 (@design-lead 확정 대기)
- 단지 마커: 단지 내 매물 수 많을수록 진한 색
- 동 마커: 동별 매물 수 기반

---

## 6. 의존성 & 재시작 규칙

### 6-1. 서비스 재시작 순서 (배포 시)

```bash
# 1. DB 스키마 적용 (무중단 — ADD COLUMN NULL)
psql ... -f migrations/20260420_add_bd_mgt_sn.sql

# 2. 공유 코드 반영 후 3서비스 재시작
sudo systemctl restart property-manager proppedia propsheet

# 3. 검증
journalctl -u property-manager -n 20
journalctl -u proppedia -n 20
journalctl -u propsheet -n 20
curl -sS http://localhost:5000/map/dong-coords?bbox=...&agent_slug=all
```

### 6-2. 영향받는 파일 (공유 코드 CRITICAL)

- `services/cadastral_service.py` ← 3서비스 공유
- `services/ldareg_service.py` ← 신규, 3서비스 공유
- `services/propsheet_save_service.py` ← 3서비스 공유
- `routes/map.py` ← 5000만 등록

### 6-3. 기능 플래그

```python
# .env
ENABLE_DONG_CLUSTERING = "false"  # 기본 off, 파일럿 검증 후 true
```

플래그 off 시: `_resolve_coordinates`는 Stage 4 fallback만, `/map/dong-coords`는 404 또는 레거시 모드.

---

## 7. 테스트 계획

### 7-1. 단위 테스트

- `test_cadastral_service.py`: WFS mock 응답으로 `compute_polygon_centroid` 검증
- `test_ldareg_service.py`: 파크리오 PNU로 16개 `bd_mgt_sn` 반환 확인

### 7-2. 통합 테스트

- `test_map_dong_coords.py`: 파크리오 bbox 쿼리 → 16개 클러스터 반환
- `test_batch_fill.py`: `--dry-run`으로 샘플 10건 처리

### 7-3. E2E (수동)

- 파크리오 매물 Propedia 앱에서 신규 등록 → PropMap 즉시 동별 분리 확인
- 신천동 17 주소 입력 → 17로 저장 (20으로 새지 않음) 확인

---

## 8. 오픈 이슈 (@pm-lead 측 PRD 9장과 대응)

1. NSDI IP 화이트리스트 → @infra-lead 스키마 문서에서
2. 단독주택 `bd_mgt_sn` 저장 → **저장하되 동명은 null 허용**, 건물 중심점 확보가 이득
3. 캐시 테이블 FK → soft FK (애플리케이션 레벨), DB 제약 걸지 않음 (batch 복구 용이성)
4. Shapely 의존 → 기존 venv에 없으면 `pip install shapely`, 또는 순수 파이썬 centroid 구현
