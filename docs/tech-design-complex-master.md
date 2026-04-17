# 기술 설계 — 공동주택 단지 마스터 (Complex Master) Week 5

> 작성일: 2026-04-16
> 작성 주체: @dev-lead + @infra-lead (@propnet-coo 발주)
> 상위 문서: `docs/prd-complex-master-week5.md`, `docs/week5-complex-master-csv-path.md`
> 버전: v1.0

---

## 1. 전체 아키텍처

```
┌─────────────────────────────┐
│ 공공데이터포털 15106861 CSV  │ 연 1회
└────────────┬────────────────┘
             │ curl POST
             ▼
┌─────────────────────────────┐
│ /data/complex_master/raw/   │ 서버 로컬 (gitignore)
│ apt_basic_info_YYYYMMDD.csv │
└────────────┬────────────────┘
             │ load_complex_master_from_csv.py
             ▼
┌─────────────────────────────────────────────────┐
│ PostgreSQL goldenrabbit_db                      │
│ ├─ complex_master      (307k 단지 마스터)       │
│ ├─ complex_aliases     (단지명 3종 + 이력)      │
│ ├─ complex_parcels     (단지 ↔ PNU N:M)         │
│ └─ complex_dong        (단지 ↔ 동)              │
└────────────┬────────────────┬───────────────────┘
             │                │
             │                └─ JOIN ─▶ building_dong_geometry (Week 3)
             ▼
┌─────────────────────────────┐
│ Flask routes/complex.py     │
│ /api/complex/lookup         │
│ /api/complex/search         │
│ /api/complex/{pk}/properties│
└────────────┬────────────────┘
             │ HTTP
             ▼
┌─────────────────────────────────────────────────┐
│ Frontend                                        │
│ ├─ PropMap dong-cluster-renderer.js (complex 레이어) │
│ ├─ index.html (단지 검색 UI)                    │
│ └─ Propedia 매물 등록 (단지 자동완성)           │
└─────────────────────────────────────────────────┘
```

---

## 2. DDL (무중단 적용)

### 2-1. 마이그레이션 파일
`migrations/20260417_create_complex_master.sql` (서버 경로)

```sql
-- ============================================================
-- Week 5 — 공동주택 단지 마스터 스키마
-- 무중단 ALTER: 모든 CREATE TABLE은 IF NOT EXISTS
-- 2026-04-17
-- ============================================================
BEGIN;

-- ------------------------------------------------------------
-- 2-1-1. complex_master — 단지 마스터
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS complex_master (
    complex_pk            VARCHAR(14)  PRIMARY KEY,  -- 한국부동산원 단지고유번호
    kapt_code             VARCHAR(11)  NULL,         -- K-apt 단지코드 (추후 보강)
    name                  VARCHAR(200) NOT NULL,     -- 단지명 (기본: 공시가격 기준)
    complex_type_code     SMALLINT     NOT NULL,     -- 1=아파트, 2=연립, 3=다세대
    address_jibun         VARCHAR(300) NOT NULL,     -- 지번 주소 (CSV 원본)
    address_road          VARCHAR(300) NULL,         -- 도로명주소 (사후 보강)
    representative_pnu    VARCHAR(19)  NOT NULL,     -- 대표 PNU (CSV 필지고유번호)
    dong_count            SMALLINT     NULL,         -- 동수
    household_count       INTEGER      NULL,         -- 세대수
    completion_date       DATE         NULL,         -- 사용승인일
    center_lat            NUMERIC(10, 7) NULL,       -- 대표 좌표 위도 (사후 보강)
    center_lon            NUMERIC(10, 7) NULL,       -- 대표 좌표 경도 (사후 보강)
    boundary              JSONB        NULL,         -- 단지 경계 폴리곤 (사후 보강)
    source                VARCHAR(30)  NOT NULL DEFAULT 'reb_csv_20250918',
    confidence            NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    raw_row               JSONB        NULL,         -- CSV 원본 1행 보관 (감사용)
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_complex_type CHECK (complex_type_code IN (1, 2, 3)),
    CONSTRAINT chk_confidence CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE INDEX IF NOT EXISTS idx_complex_master_name
    ON complex_master USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_complex_master_rep_pnu
    ON complex_master (representative_pnu);
CREATE INDEX IF NOT EXISTS idx_complex_master_geo
    ON complex_master (center_lat, center_lon)
    WHERE center_lat IS NOT NULL AND center_lon IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_complex_master_addr_jibun
    ON complex_master USING gin (address_jibun gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_complex_master_kapt
    ON complex_master (kapt_code)
    WHERE kapt_code IS NOT NULL;

-- updated_at 자동 갱신
CREATE OR REPLACE FUNCTION complex_master_update_ts() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_complex_master_update_ts ON complex_master;
CREATE TRIGGER trg_complex_master_update_ts
    BEFORE UPDATE ON complex_master
    FOR EACH ROW EXECUTE FUNCTION complex_master_update_ts();


-- ------------------------------------------------------------
-- 2-1-2. complex_aliases — 단지명 3종 + 이력 + 사용자 입력
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS complex_aliases (
    id            BIGSERIAL PRIMARY KEY,
    complex_pk    VARCHAR(14)  NOT NULL REFERENCES complex_master(complex_pk) ON DELETE CASCADE,
    alias_type    VARCHAR(10)  NOT NULL,  -- gongsi|bldreg|road|past|user
    name          VARCHAR(200) NOT NULL,
    year          SMALLINT     NULL,      -- past 타입에서만 사용 (변경년도)
    source        VARCHAR(30)  NOT NULL DEFAULT 'reb_csv_20250918',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_alias_type CHECK (alias_type IN ('gongsi','bldreg','road','past','user')),
    CONSTRAINT uq_complex_alias UNIQUE (complex_pk, alias_type, name, COALESCE(year, 0))
);

CREATE INDEX IF NOT EXISTS idx_complex_aliases_complex
    ON complex_aliases (complex_pk);
CREATE INDEX IF NOT EXISTS idx_complex_aliases_name_trgm
    ON complex_aliases USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_complex_aliases_name_btree
    ON complex_aliases (name);


-- ------------------------------------------------------------
-- 2-1-3. complex_parcels — 단지 ↔ 필지(PNU) N:M
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS complex_parcels (
    id            BIGSERIAL PRIMARY KEY,
    complex_pk    VARCHAR(14)  NOT NULL REFERENCES complex_master(complex_pk) ON DELETE CASCADE,
    pnu           VARCHAR(19)  NOT NULL,
    is_primary    BOOLEAN      NOT NULL DEFAULT FALSE,  -- CSV 대표 PNU 여부
    jibun         VARCHAR(100) NULL,                     -- 지번(17-4 등)
    source        VARCHAR(30)  NOT NULL DEFAULT 'reb_csv_20250918',
                -- reb_csv_YYYYMMDD | vworld_matched | kakao_fallback | nsdi_wfs | manual
    confidence    NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_complex_parcel UNIQUE (complex_pk, pnu),
    CONSTRAINT chk_parcel_confidence CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE INDEX IF NOT EXISTS idx_complex_parcels_pnu
    ON complex_parcels (pnu);
CREATE INDEX IF NOT EXISTS idx_complex_parcels_complex
    ON complex_parcels (complex_pk);
CREATE INDEX IF NOT EXISTS idx_complex_parcels_primary
    ON complex_parcels (complex_pk) WHERE is_primary = TRUE;


-- ------------------------------------------------------------
-- 2-1-4. complex_dong — 단지 ↔ 동
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS complex_dong (
    id             BIGSERIAL PRIMARY KEY,
    complex_pk     VARCHAR(14)  NOT NULL REFERENCES complex_master(complex_pk) ON DELETE CASCADE,
    dong_name      VARCHAR(50)  NOT NULL,   -- 대표 동명 (공시가격 기준)
    dong_alias_bldreg VARCHAR(50) NULL,     -- 건축물대장 동명
    dong_alias_road   VARCHAR(50) NULL,     -- 도로명주소 동명
    floor_above    SMALLINT     NULL,       -- 지상층수
    source         VARCHAR(30)  NOT NULL DEFAULT 'reb_csv_dong_20250918',
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_complex_dong UNIQUE (complex_pk, dong_name)
);

CREATE INDEX IF NOT EXISTS idx_complex_dong_complex
    ON complex_dong (complex_pk);
CREATE INDEX IF NOT EXISTS idx_complex_dong_name
    ON complex_dong (dong_name);


-- ------------------------------------------------------------
-- 2-1-5. 매물 테이블 FK 추가 (무중단)
-- ------------------------------------------------------------
-- {agent}_sales_building, {agent}_sales_multi_unit에 complex_pk 컬럼 추가는
-- 별도 마이그레이션 (20260417_add_complex_pk_to_sales.sql)로 분리
-- Week 3의 bd_mgt_sn 추가 패턴 재사용

-- ------------------------------------------------------------
-- 확장 기능 활성화 (없으면 수행)
-- ------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pg_trgm;

COMMIT;
```

### 2-2. 매물 테이블 FK 추가
`migrations/20260417_add_complex_pk_to_sales.sql`

```sql
DO $$
DECLARE
    agent_slug TEXT;
    tbl TEXT;
BEGIN
    FOR agent_slug IN SELECT slug FROM agents WHERE is_active = TRUE LOOP
        FOREACH tbl IN ARRAY ARRAY['_sales_building', '_sales_multi_unit'] LOOP
            EXECUTE format(
                'ALTER TABLE %I ADD COLUMN IF NOT EXISTS complex_pk VARCHAR(14) NULL',
                agent_slug || tbl
            );
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_%I_complex_pk ON %I (complex_pk) WHERE complex_pk IS NOT NULL',
                agent_slug || tbl, agent_slug || tbl
            );
        END LOOP;
    END LOOP;
END $$;
```

### 2-3. 무중단 보장
- 모든 CREATE TABLE은 `IF NOT EXISTS`
- 모든 CREATE INDEX는 `IF NOT EXISTS` (CONCURRENTLY는 초기 빈 테이블이므로 불필요)
- `ADD COLUMN ... NULL`은 PG 11+ 메타데이터 변경만, 테이블 rewrite 없음
- pg_trgm 확장은 `CREATE EXTENSION IF NOT EXISTS` — 기존 Week 3에서 이미 설치된 상태면 no-op

---

## 3. 적재 알고리즘

### 3-1. Phase A — CSV → complex_master + aliases (기본정보)

```
For each row in apt_basic_info_20250918.csv:
  1. 단지고유번호 → complex_pk (PK)
  2. 필지고유번호 → representative_pnu
  3. 주소 → address_jibun
  4. 3종 단지명 수집:
       - 단지명_공시가격 → name (기본)
       - 단지명_공시가격 → aliases (type=gongsi)
       - 단지명_건축물대장 → aliases (type=bldreg) [비어있지 않으면]
       - 단지명_도로명주소 → aliases (type=road)    [비어있지 않으면]
       - 중복 제거 (같은 name은 저장하지 않음)
       - 모두 비었으면 row skip + 로그
  5. 단지종류 → complex_type_code
  6. 동수/세대수/사용승인일 → dong_count/household_count/completion_date
  7. 대표 PNU → complex_parcels (is_primary=TRUE)
  8. raw_row → 전체 JSON 보관

UPSERT (ON CONFLICT DO UPDATE):
  - complex_master: name, 3종 메타, raw_row, source 갱신. created_at 유지
  - complex_aliases: (complex_pk, alias_type, name) UNIQUE → INSERT OR IGNORE
  - complex_parcels: (complex_pk, pnu) UNIQUE → INSERT OR IGNORE

배치 크기: 2000건/트랜잭션, 진행률 10000건마다 로그
실패 시: batch_failures 테이블에 기록, skip 후 계속
```

### 3-2. Phase B — 동정보 CSV → complex_dong

```
apt_dong_info_YYYYMMDD.csv (160,020 rows):
  컬럼: 단지고유번호, 동명_공시가격, 동명_건축물대장, 동명_도로명주소, 지상층수

For each row:
  - (complex_pk, dong_name=동명_공시가격) UPSERT
  - 건축물대장/도로명주소 동명이 다르면 dong_alias_bldreg, dong_alias_road로 저장
```

### 3-3. Phase C — 이력 CSV → complex_aliases (type=past)

```
apt_hist_info_YYYYMMDD.csv (8,905 rows):
  컬럼: 단지고유번호, 변경년도, 변경전단지명, 변경후단지명

For each row:
  - alias_type='past', name=변경전단지명, year=변경년도 INSERT
  - 변경후단지명이 현재 name과 다르면 alias(type=gongsi)로도 추가
  - (잠실주공1단지 → 잠실엘스 케이스 커버)
```

### 3-4. Phase D — VWorld/카카오로 세부 PNU 보강 (비동기)

```
전수 적재 완료 후 야간 배치:

For each complex in complex_master:
  1. address_jibun 기반 VWorld 검색 → 해당 단지 내 모든 PNU 수집
  2. building_dong_geometry 조인하여 실제 건물들의 PNU 매칭
  3. complex_parcels에 is_primary=FALSE로 INSERT (source=vworld_matched)
  4. 실패 시 카카오 Local fallback
  5. 모두 실패 시 complex_master.confidence -= 0.1

배치 호출 제한:
  - VWorld 40,000건/일 쿼터 내에서 30,000건/일만 사용 (다른 기능 보호)
  - 307k 단지 × 평균 3-5 PNU 보강 = 약 1M 호출 → 30일 분할
```

### 3-5. 매물 매칭 (on-the-fly)

```
매물 등록/조회 시:
  1. 매물의 pnu → complex_parcels.pnu 조회 → complex_pk 획득
  2. 매물 주소 → complex_master.address_jibun 퍼지 매칭 (trgm)
  3. 매물 단지명 → complex_aliases.name 퍼지 매칭
  4. 3개 중 우선순위: pnu > 주소 > 이름
  5. 매칭 성공 시 {agent}_sales_*.complex_pk 업데이트
```

---

## 4. API 설계

### 4-1. 라우트 등록
`/backend/property-manager/routes/complex.py` (신규)

```python
from flask import Blueprint, jsonify, request

complex_bp = Blueprint('complex', __name__, url_prefix='/api/complex')

@complex_bp.get('/lookup')
def lookup():
    complex_pk = request.args.get('complex_pk')
    pnu = request.args.get('pnu')
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius_m = request.args.get('radius_m', 500, type=int)
    # ...

@complex_bp.get('/search')
def search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []})
    # pg_trgm similarity 기반
    # SELECT ... FROM complex_master cm
    #   LEFT JOIN complex_aliases ca ON cm.complex_pk = ca.complex_pk
    #   WHERE cm.name % %s OR ca.name % %s
    #   ORDER BY GREATEST(similarity(cm.name, %s), similarity(ca.name, %s)) DESC
    #   LIMIT 10
    # ...

@complex_bp.get('/<complex_pk>/properties')
def properties(complex_pk):
    agent_slug = request.args.get('agent_slug', 'goldenrabbit01')
    # agent 격리 원칙 유지
    # SELECT ... FROM {agent}_sales_building WHERE complex_pk = %s
    # ...
```

### 4-2. Blueprint 등록
- `/backend/property-manager/app.py` (5000) — SNS/홈페이지에서 사용하므로 등록
- `/backend/propsheet/app.py` (5020) — PropSheet에서도 등록
- `/backend/proppedia/app.py` (5010) — Propedia 앱/웹에서도 등록

### 4-3. 응답 스펙

```json
// GET /api/complex/lookup?pnu=1171010200100170000
{
  "complex_pk": "11710120100792",
  "name": "파크리오",
  "aliases": [
    {"type": "gongsi", "name": "파크리오"},
    {"type": "bldreg", "name": "파크리오"},
    {"type": "road",   "name": "파크리오"}
  ],
  "complex_type_code": 2,
  "complex_type_name": "연립",
  "address_jibun": "서울특별시 송파구 신천동 17",
  "address_road": null,
  "dong_count": 66,
  "household_count": 6864,
  "completion_date": "2008-08-29",
  "representative_pnu": "1171010200100170000",
  "parcels": [
    {"pnu": "1171010200100170000", "is_primary": true,  "source": "reb_csv_20250918"},
    {"pnu": "1171010200100170004", "is_primary": false, "source": "vworld_matched"},
    {"pnu": "1171010200100170005", "is_primary": false, "source": "vworld_matched"}
  ],
  "center_lat": 37.5170,
  "center_lon": 127.1030,
  "boundary": null,
  "source": "reb_csv_20250918",
  "confidence": 1.0
}
```

```json
// GET /api/complex/search?q=파크리
{
  "results": [
    {
      "complex_pk": "11710120100792",
      "name": "파크리오",
      "match_alias": null,
      "address_jibun": "서울특별시 송파구 신천동 17",
      "household_count": 6864,
      "dong_count": 66,
      "similarity": 0.75
    },
    {
      "complex_pk": "11500320400242",
      "name": "리오파크빌",
      "match_alias": {"type": "bldreg", "name": "리오파크"},
      "address_jibun": "서울특별시 강서구 화곡동 1128-9",
      "household_count": 19,
      "dong_count": 1,
      "similarity": 0.55
    }
  ]
}
```

### 4-4. 캐시 정책
- `lookup`: `Cache-Control: public, max-age=3600, stale-while-revalidate=86400`
- `search`: 캐시 없음 (입력 가변)
- `properties`: agent별 private cache, max-age=60

---

## 5. 프론트엔드 설계

### 5-1. PropMap `dong-cluster-renderer.js` 확장

```javascript
// 줌 레벨 전환 규칙
//   level >= 6 : 광역 뷰 (현재 cluster 유지)
//   level = 4~5: complex 레이어 (단지 1개 = 마커 1개)
//   level = 3  : dong 레이어 (Week 3 기존)
//   level <= 2 : 개별 매물

var COMPLEX_ZOOM_THRESHOLD = { min: 4, max: 5 };
var DONG_ZOOM_THRESHOLD    = { min: 3, max: 3 };

function renderComplexLayer(properties, map) {
  // properties에서 unique complex_pk 추출
  var groups = {};
  properties.forEach(function(p) {
    var pk = p.complex_pk;
    if (!pk) return;
    if (!groups[pk]) groups[pk] = { complex_pk: pk, items: [], lat: 0, lon: 0 };
    groups[pk].items.push(p);
    groups[pk].lat += p.lat;
    groups[pk].lon += p.lon;
  });

  // 2차: complex_pk 없는 매물들은 /api/complex/lookup로 후속 매칭
  // ...

  Object.values(groups).forEach(function(g) {
    g.lat /= g.items.length;
    g.lon /= g.items.length;
    // /api/complex/lookup?complex_pk=xxx 호출 → center_lat/lon + name 사용
    // 마커 렌더링
  });
}
```

### 5-2. 3곳 지도 동기화
`CLAUDE.md` 규칙에 따라 아래 3개 파일 모두 수정:
- `propmap/map.html` (랜딩 매물지도)
- `propmap/index.html` + 서버 `frontend/public/propmap/index.html`
- `frontend/public/index.html` (현재 홈페이지 매물지도, 추후 PropMap으로 이관 대상)

### 5-3. Propedia 단지 자동완성
- **앱** (Flutter): `lib/widgets/complex_autocomplete.dart` 신규
- **웹** (정적 HTML): `propedia/app/*.html` 중 매물 등록 페이지에 동일 로직 추가
- 규칙: Propedia 웹 ≠ Flutter. 앱+HTML 각각 수정

```javascript
// Propedia 웹 (propedia/app/add-property.html 등)
var input = document.querySelector('#complex-name-input');
var dropdown = document.querySelector('#complex-suggestions');
var debounceTimer;
input.addEventListener('input', function(e) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(function() {
    var q = e.target.value.trim();
    if (q.length < 2) return;
    fetch('/api/complex/search?q=' + encodeURIComponent(q))
      .then(r => r.json())
      .then(renderSuggestions);
  }, 150);
});

function onSelect(complex) {
  // 주소·대표 PNU·동 목록 자동 채움
  document.querySelector('#address-jibun').value = complex.address_jibun;
  document.querySelector('#complex-pk').value = complex.complex_pk;
  loadDongOptions(complex.complex_pk);
}
```

---

## 6. 매칭 로직 상세

### 6-1. PNU → 단지 역매핑
```sql
SELECT cm.*, cp.is_primary, cp.source AS parcel_source
FROM complex_parcels cp
JOIN complex_master cm ON cp.complex_pk = cm.complex_pk
WHERE cp.pnu = %s
ORDER BY cp.is_primary DESC, cp.confidence DESC
LIMIT 1;
```

**엣지 케이스**: 장미2(complex_pk=A)와 장미3(complex_pk=B)가 같은 PNU 공유
- 위 쿼리는 is_primary 우선으로 정렬 → 대표로 등록된 단지 반환
- 매물의 건물명 텍스트 매칭을 secondary로 수행하여 정확한 단지 확정

### 6-2. 단지명 퍼지 매칭
```sql
SELECT
  cm.complex_pk, cm.name, cm.address_jibun, cm.household_count, cm.dong_count,
  NULL AS match_alias_type, NULL AS match_alias_name,
  similarity(cm.name, %s) AS sim
FROM complex_master cm
WHERE cm.name %% %s
UNION ALL
SELECT
  cm.complex_pk, cm.name, cm.address_jibun, cm.household_count, cm.dong_count,
  ca.alias_type, ca.name,
  similarity(ca.name, %s) AS sim
FROM complex_aliases ca
JOIN complex_master cm ON ca.complex_pk = cm.complex_pk
WHERE ca.name %% %s
ORDER BY sim DESC
LIMIT 10;
```

`%%` 는 psycopg2 이스케이프 (CRITICAL 규칙 6).

### 6-3. 좌표 반경 조회
```sql
SELECT cm.*,
       2 * 6371000 * asin(sqrt(
         sin(radians((cm.center_lat - %s) / 2)) ^ 2 +
         cos(radians(%s)) * cos(radians(cm.center_lat)) *
         sin(radians((cm.center_lon - %s) / 2)) ^ 2
       )) AS distance_m
FROM complex_master cm
WHERE cm.center_lat BETWEEN %s AND %s
  AND cm.center_lon BETWEEN %s AND %s
  AND cm.center_lat IS NOT NULL
ORDER BY distance_m
LIMIT 20;
```

---

## 7. 성능 분석

### 7-1. 스토리지
| 테이블 | 예상 레코드 | 평균 크기 | 총 용량 |
|---|---|---|---|
| complex_master | 307,407 | 500B (raw_row 포함 800B) | ~250MB |
| complex_aliases | 900,000 (3종 × 307k + 과거 8.9k) | 100B | ~90MB |
| complex_parcels | 1,500,000 (초기 307k + VWorld 보강 후) | 80B | ~120MB |
| complex_dong | 160,020 | 120B | ~20MB |
| **합계** | ~2.9M | — | **~480MB** (인덱스 포함 ~700MB) |

### 7-2. 적재 시간
- Phase A: 307k 레코드, 2000건/트랜잭션 → 약 25~30분
- Phase B: 160k 레코드 → 15분
- Phase C: 8.9k 레코드 → 2분
- Phase D (VWorld 보강): 야간 배치 30일 분할

### 7-3. 쿼리 성능 (목표)
| 쿼리 | 인덱스 | P95 |
|---|---|---|
| /api/complex/lookup?complex_pk | PK | < 20ms |
| /api/complex/lookup?pnu | idx_complex_parcels_pnu | < 30ms |
| /api/complex/lookup?lat&lon | idx_complex_master_geo | < 80ms |
| /api/complex/search?q | gin_trgm_ops | < 150ms |
| /api/complex/{pk}/properties | FK + {agent}_sales_* index | < 100ms |

---

## 8. 배포 시퀀스

```bash
# [S1] CSV 다운로드 (서버에서)
bash /home/webapp/goldenrabbit/backend/scripts/week5_complex_master/download_kreb_csv.sh

# [S2] DDL 적용 (무중단)
psql -U webapp -d goldenrabbit_db \
  -f /home/webapp/goldenrabbit/migrations/20260417_create_complex_master.sql
psql -U webapp -d goldenrabbit_db \
  -f /home/webapp/goldenrabbit/migrations/20260417_add_complex_pk_to_sales.sql

# [S3] 파일럿 적재 (송파/동작/관악)
python /home/webapp/goldenrabbit/backend/scripts/week5_complex_master/load_complex_master_from_csv.py \
  --csv /home/webapp/goldenrabbit/data/complex_master/raw/apt_basic_info_20250918.csv \
  --sigungu 11710,11590,11620 \
  --dry-run

# [S4] 파일럿 실제 실행
python ... --sigungu 11710,11590,11620

# [S5] 파크리오 검증
psql -U webapp -d goldenrabbit_db -c "
SELECT complex_pk, name, address_jibun, dong_count, household_count
FROM complex_master
WHERE name = '파크리오' AND address_jibun LIKE '서울%송파%신천동%';
"

# [S6] 서울 전역 적재
python ... --sido 11

# [S7] 전국 적재
python ...

# [S8] 3 서비스 재시작 (공유 코드)
sudo systemctl restart property-manager proppedia propsheet

# [S9] 헬스 체크
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:5000/api/complex/lookup?complex_pk=11710120100792
journalctl -u property-manager -n 30 --no-pager

# [S10] PropMap/Propedia 프론트 배포
# (정적 파일 rsync, Nginx 리로드는 필요 시)
```

---

## 9. 롤백

- **코드 롤백**: `git revert` + 3 서비스 재시작
- **스키마 롤백**: 불필요 (모든 신규 컬럼 NULL 허용, 신규 테이블은 기존 기능에 영향 없음)
- **긴급 비활성화**:
  - `.env`에 `ENABLE_COMPLEX_LAYER=false` 추가 → prop-map frontend에서 feature flag 체크
  - 프론트 3곳 `propmap/map.html`, `propmap/index.html`, `frontend/public/index.html` 동시 확인
- **데이터 롤백**:
  - `DELETE FROM complex_master WHERE source = 'reb_csv_20250918'` → CASCADE로 aliases/parcels/dong 동반 삭제
  - 재적재 시간 30분 → 롤포워드가 일반적으로 더 안전

---

## 10. 오픈 질문

- [ ] `complex_master.center_lat/lon`을 대표 PNU 좌표로 계산 vs 단지 내 모든 PNU 평균 중 어느 것이 시각적으로 적합?
- [ ] `complex_master`를 public schema에 두고 agent 테이블은 schema 분리하는 것이 향후 성장에 유리한지
- [ ] `raw_row` JSONB 보관을 유지할지, 감사 후 drop할지 (현 설계: 유지, 700MB 중 200MB 차지)
- [ ] Propedia 단지 자동완성 debounce 150ms가 적절한지 — QA 사용자 테스트 필요

---

**다음 작업: `scripts/week5_complex_master/` 디렉토리의 다운로드 + 적재 + 검증 스크립트 작성**
