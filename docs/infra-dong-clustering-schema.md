# 인프라 설계 — 동별 클러스터링 DB 스키마 + 배포 전략

> 작성일: 2026-04-16
> 작성 주체: @infra-lead (발주: @propnet-coo)
> 연관: `docs/prd-propmap-dong-clustering.md`, `docs/tech-design-dong-clustering.md`
> 버전: v1.0 (Week 1 초안, 실행 금지)

---

## 1. 공용 캐시 테이블 DDL — `building_dong_geometry`

### 1-1. CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS building_dong_geometry (
    bd_mgt_sn        VARCHAR(25)  PRIMARY KEY,
    pnu              VARCHAR(19)  NOT NULL,
    dong_nm          VARCHAR(50)  NULL,
    bld_nm           VARCHAR(200) NULL,
    center_lat       NUMERIC(10, 7) NOT NULL,
    center_lon       NUMERIC(10, 7) NOT NULL,
    geometry         JSONB        NULL,
    road_addr        VARCHAR(300) NULL,
    jibun_addr       VARCHAR(300) NULL,
    source           VARCHAR(20)  NOT NULL DEFAULT 'vworld_wfs',
    fetched_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    ttl_until        TIMESTAMPTZ  NOT NULL DEFAULT (NOW() + INTERVAL '365 days'),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_source CHECK (source IN ('vworld_wfs','vworld_data','nsdi_ldareg','manual','fallback'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_bdg_pnu_dong
    ON building_dong_geometry (pnu, COALESCE(dong_nm, ''));

CREATE INDEX IF NOT EXISTS idx_bdg_pnu       ON building_dong_geometry (pnu);
CREATE INDEX IF NOT EXISTS idx_bdg_road      ON building_dong_geometry (road_addr);
CREATE INDEX IF NOT EXISTS idx_bdg_ttl       ON building_dong_geometry (ttl_until) WHERE ttl_until < NOW();
CREATE INDEX IF NOT EXISTS idx_bdg_bld_nm    ON building_dong_geometry (bld_nm);

-- updated_at 자동 갱신
CREATE OR REPLACE FUNCTION bdg_update_ts() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_bdg_update_ts ON building_dong_geometry;
CREATE TRIGGER trg_bdg_update_ts
    BEFORE UPDATE ON building_dong_geometry
    FOR EACH ROW EXECUTE FUNCTION bdg_update_ts();
```

### 1-2. 설계 포인트

| 결정 | 이유 |
|---|---|
| `bd_mgt_sn` PK | NSDI/VWorld 모두 일관된 SSoT |
| `(pnu, dong_nm)` UNIQUE | 과거 매물 UPDATE 시 dong_nm으로 재조회 필요 |
| `geometry JSONB NULL` | 폴리곤 원본 보관, 필요 시 지도에 경계 표시 |
| `ttl_until` 파티셔닝 대신 인덱스 | 현재 예상 레코드 < 50만건, 인덱스로 충분 |
| `source` CHECK | 데이터 품질 감사 용이 |
| `COALESCE(dong_nm,'')` 유니크 | 단독주택(동명 null) 중복 방지 |

### 1-3. 예상 규모

- 서울·경기 건물 약 500만동 (전국 약 700만) 중 실제 매물 커버리지: 5~10만건 규모
- 테이블 크기 예상: 50MB (geometry 제외) / 300MB (geometry 포함)
- 월간 증가량: < 5000건

---

## 2. 매물 테이블 ALTER — 전체 agent

### 2-1. 대상 테이블 목록

```sql
-- agents 테이블에서 slug 수집 후 동적 생성
SELECT slug FROM agents WHERE is_active = TRUE;
-- 각 slug당 2개:
--   {slug}_sales_building
--   {slug}_sales_multi_unit
```

### 2-2. ALTER 문 (예: goldenrabbit01)

```sql
ALTER TABLE goldenrabbit01_sales_multi_unit
    ADD COLUMN IF NOT EXISTS bd_mgt_sn VARCHAR(25) NULL;

CREATE INDEX IF NOT EXISTS idx_goldenrabbit01_mu_bd_mgt_sn
    ON goldenrabbit01_sales_multi_unit (bd_mgt_sn)
    WHERE bd_mgt_sn IS NOT NULL;

ALTER TABLE goldenrabbit01_sales_building
    ADD COLUMN IF NOT EXISTS bd_mgt_sn VARCHAR(25) NULL;

CREATE INDEX IF NOT EXISTS idx_goldenrabbit01_bd_bd_mgt_sn
    ON goldenrabbit01_sales_building (bd_mgt_sn)
    WHERE bd_mgt_sn IS NOT NULL;
```

### 2-3. 동적 ALTER 스크립트

`migrations/20260420_add_bd_mgt_sn_all_agents.sql`:

```sql
DO $$
DECLARE
    agent_slug TEXT;
    tbl TEXT;
BEGIN
    FOR agent_slug IN SELECT slug FROM agents WHERE is_active = TRUE LOOP
        FOREACH tbl IN ARRAY ARRAY['_sales_building', '_sales_multi_unit'] LOOP
            EXECUTE format(
                'ALTER TABLE %I ADD COLUMN IF NOT EXISTS bd_mgt_sn VARCHAR(25) NULL',
                agent_slug || tbl
            );
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_%I_bd_mgt_sn ON %I (bd_mgt_sn) WHERE bd_mgt_sn IS NOT NULL',
                agent_slug || tbl, agent_slug || tbl
            );
        END LOOP;
    END LOOP;
END $$;
```

### 2-4. 무중단 적용 보장

- `ADD COLUMN ... NULL` → PostgreSQL은 즉시 (메타데이터만 변경, 테이블 rewrite 없음)
- `CREATE INDEX ... WHERE bd_mgt_sn IS NOT NULL` → 초기 데이터 없어 즉시 완료
- 따라서 무중단, 트래픽 영향 없음

---

## 3. 배치 실행 계획

### 3-1. 단계별 실행

| 단계 | 작업 | 예상 소요 | 실행 시간대 |
|---|---|---|---|
| S1 | 스키마 적용 (ALTER, CREATE TABLE) | < 30초 | 평일 오전 가능 |
| S2 | goldenrabbit multi_unit dry-run | 5분 | 오너 승인 후 즉시 |
| S3 | goldenrabbit multi_unit 실제 배치 | 30분 (28건) | 평일 낮 |
| S4 | goldenrabbit building 배치 | 1시간 (54건) | 평일 낮 |
| S5 | 전체 agent 일괄 배치 | 야간 02-05시 | 새벽 야간 슬롯 |

### 3-2. 체크포인트 테이블

```sql
CREATE TABLE IF NOT EXISTS batch_checkpoints (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    agent_slug VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    last_processed_id VARCHAR(100) NULL,
    processed_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running',  -- running|paused|done|failed
    started_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (job_name, agent_slug, category)
);

CREATE TABLE IF NOT EXISTS batch_failures (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    agent_slug VARCHAR(100) NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    reason TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3-3. 실패 복구

- `batch_failures` 조회 후 원인별 재처리
- VWorld 쿼터 복구 후 `--resume` 옵션으로 체크포인트 이어서
- 30% 초과 실패 시 자동 일시 정지 + 알림

---

## 4. NSDI/VWorld API 화이트리스트 확인

### 4-1. NSDI LdaregService

- 엔드포인트: `http://apis.data.go.kr/1611000/nsdi/eios/LdaregService/...`
- 공공데이터포털 15056691, 15123970, 15140363, 15140366
- **IP 화이트리스트 필요 여부**: 공공데이터포털 대부분 불필요 (키 기반). 단, 일부 NSDI 계열은 사전 신청 필요 — **확인 액션 필요**
- 액션: 공공데이터포털 마이페이지에서 키 상태 확인, 필요 시 `175.119.224.71` 등록

### 4-2. VWorld

- 엔드포인트: `https://api.vworld.kr/req/data`, `/req/wfs`
- **도메인 등록 필요**: 기존 키에 `goldenrabbit.biz`, `propnet.kr` 등록됨 추정 → 확인 필요
- 서버 측 호출(IP 기반)은 도메인 제약 없음. 단, 쿼터는 키 단위로 소비
- 일일 쿼터: 표준 키 40,000건/일 → 배치 야간 분할로 충분

### 4-3. 액션 아이템

- [ ] 현재 `.env`의 `BUILDING_REG_API_KEY`, `VWORLD_API_KEY` 쿼터 상태 확인
- [ ] NSDI LdaregService 키 별도 필요 여부 확인 (같은 키 공유 가능성)
- [ ] 필요 시 추가 키 발급 신청 (최대 2영업일)

---

## 5. 배포 & 재시작 전략

### 5-1. 무중단 배포 순서

```bash
# [S1] 코드 배포 (공유 services/* 변경)
cd /home/webapp/goldenrabbit
git pull origin main

# [S2] DB 마이그레이션 (무중단)
psql -U webapp -d goldenrabbit_db \
  -f /home/webapp/goldenrabbit/migrations/20260420_create_bdg.sql
psql -U webapp -d goldenrabbit_db \
  -f /home/webapp/goldenrabbit/migrations/20260420_add_bd_mgt_sn_all_agents.sql

# [S3] 3서비스 동시 재시작 (CRITICAL — 공유 코드)
sudo systemctl restart property-manager proppedia propsheet

# [S4] 헬스 체크
journalctl -u property-manager -n 30 --no-pager
journalctl -u proppedia      -n 30 --no-pager
journalctl -u propsheet      -n 30 --no-pager
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:5000/
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:5010/
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:5020/

# [S5] 기능 플래그 ON
# .env: ENABLE_DONG_CLUSTERING=true
sudo systemctl restart property-manager proppedia propsheet
```

### 5-2. 롤백 전략

- **코드 롤백**: `git revert` + 3서비스 재시작
- **스키마 롤백 불필요**: `bd_mgt_sn` 컬럼은 NULL 허용이므로 기존 로직에 영향 없음
- **기능 플래그 off**: `.env`에서 `ENABLE_DONG_CLUSTERING=false` 후 재시작

### 5-3. Nginx

- 신규 라우트 `/map/dong-coords`는 기존 `location /` → Port 5000 proxy_pass로 자동 커버
- Nginx 설정 변경 불필요 (확인 완료)

---

## 6. 모니터링

### 6-1. 로그 지표

| 지표 | 출처 | 알림 임계값 |
|---|---|---|
| 캐시 히트율 | `journalctl` grep `[cache_hit]` | < 80% 시 경고 |
| VWorld 5xx 비율 | grep `[vworld_error]` | > 5% 시 경고 |
| NSDI 5xx 비율 | grep `[nsdi_error]` | > 5% 시 경고 |
| 배치 실패율 | batch_failures COUNT | 10분당 > 30 건 시 중단 |
| `/map/dong-coords` P95 | access_log 분석 | > 500ms 시 경고 |

### 6-2. 일일 보고 통합

- 기존 `daily-report/` 시스템에 `dong_clustering` collector 추가
- 매일 아침 보고에 캐시 커버리지, 배치 진행률 포함

---

## 7. 보안 / 환경변수

```
# .env 추가
NSDI_LDAREG_KEY=<공공데이터포털 키>       # 또는 BUILDING_REG_API_KEY 공유
VWORLD_API_KEY=<기존 유지>
ENABLE_DONG_CLUSTERING=false             # 초기값, 검증 후 true
DONG_CACHE_TTL_DAYS=365
```

- 키는 `os.environ.get()`로만 접근, 하드코딩 절대 금지 (CRITICAL 규칙 8, 9 준수)
- pre-commit hook이 자동 검증

---

## 8. 용량 & 성능 예측

| 항목 | 예측 | 근거 |
|---|---|---|
| `building_dong_geometry` 초기 레코드 | 5만 | 현 매물 규모 |
| 디스크 사용 | +500MB (인덱스 포함) | JSONB 평균 5KB |
| VWorld 일일 호출 | < 5000 | 신규 매물 500건 × 10 |
| NSDI 일일 호출 | < 2000 | 신규 pnu당 2-3회 |
| `/map/dong-coords` 캐시 히트 시 | < 50ms | DB 인덱스 조회 |
| DB 커넥션 추가 | 0 | 기존 pool 재사용 |

---

## 9. 오픈 이슈 & 액션

- [ ] NSDI 키 IP 화이트리스트 확인 (owner: @infra-lead, due: Week 1)
- [ ] VWorld 쿼터 증설 필요 여부 판단 (owner: @infra-lead)
- [ ] 배치 야간 슬롯 03-05시 확정 (cron 등록 예정)
- [ ] PostgreSQL 버전 확인 — JSONB GIN 인덱스 필요 시 추가
- [ ] `batch_checkpoints` / `batch_failures` 테이블을 기존 백오피스 대시보드에 노출할지 @pm-lead와 협의
