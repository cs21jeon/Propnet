-- ============================================================
-- Week 5 — 공동주택 단지 마스터 스키마
-- 무중단 ALTER: 모든 CREATE TABLE은 IF NOT EXISTS
-- 2026-04-17
-- ============================================================
BEGIN;

-- 확장 기능 활성화 (없으면 수행)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ------------------------------------------------------------
-- 2-1-1. complex_master — 단지 마스터
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS complex_master (
    complex_pk            VARCHAR(14)  PRIMARY KEY,
    kapt_code             VARCHAR(11)  NULL,
    name                  VARCHAR(200) NOT NULL,
    complex_type_code     SMALLINT     NOT NULL,
    address_jibun         VARCHAR(300) NOT NULL,
    address_road          VARCHAR(300) NULL,
    representative_pnu    VARCHAR(19)  NOT NULL,
    dong_count            SMALLINT     NULL,
    household_count       INTEGER      NULL,
    completion_date       DATE         NULL,
    center_lat            NUMERIC(10, 7) NULL,
    center_lon            NUMERIC(10, 7) NULL,
    boundary              JSONB        NULL,
    source                VARCHAR(30)  NOT NULL DEFAULT 'reb_csv_20250918',
    confidence            NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    raw_row               JSONB        NULL,
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
    alias_type    VARCHAR(10)  NOT NULL,
    name          VARCHAR(200) NOT NULL,
    year          SMALLINT     NULL,
    source        VARCHAR(30)  NOT NULL DEFAULT 'reb_csv_20250918',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_alias_type CHECK (alias_type IN ('gongsi','bldreg','road','past','user'))
);

-- year IS NULL 케이스 포함 유니크 (COALESCE 기반 partial index)
CREATE UNIQUE INDEX IF NOT EXISTS uq_complex_alias
    ON complex_aliases (complex_pk, alias_type, name, (COALESCE(year, 0)));

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
    is_primary    BOOLEAN      NOT NULL DEFAULT FALSE,
    jibun         VARCHAR(100) NULL,
    source        VARCHAR(30)  NOT NULL DEFAULT 'reb_csv_20250918',
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
    dong_name      VARCHAR(50)  NOT NULL,
    dong_alias_bldreg VARCHAR(50) NULL,
    dong_alias_road   VARCHAR(50) NULL,
    floor_above    SMALLINT     NULL,
    source         VARCHAR(30)  NOT NULL DEFAULT 'reb_csv_dong_20250918',
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_complex_dong UNIQUE (complex_pk, dong_name)
);

CREATE INDEX IF NOT EXISTS idx_complex_dong_complex
    ON complex_dong (complex_pk);
CREATE INDEX IF NOT EXISTS idx_complex_dong_name
    ON complex_dong (dong_name);

COMMIT;

-- ============================================================
-- 검증 쿼리
-- ============================================================
\dt complex_*
\d complex_master
