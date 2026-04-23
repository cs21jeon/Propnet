-- PropNet 매물 데이터 Enrichment Phase 1
-- 지하철역 마스터 + 학교 마스터 + 매물별 enrichment 캐시
-- 실행: psql -U goldenrabbit -d goldenrabbit_db -f enrichment_tables.sql

BEGIN;

-- 1) 지하철역 마스터
CREATE TABLE IF NOT EXISTS subway_stations (
    id SERIAL PRIMARY KEY,
    station_name VARCHAR(64) NOT NULL,
    line_name VARCHAR(32) NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    region VARCHAR(32),
    UNIQUE(station_name, line_name)
);

CREATE INDEX IF NOT EXISTS idx_subway_lat_lon
    ON subway_stations (lat, lon);

-- 2) 학교 마스터
CREATE TABLE IF NOT EXISTS schools (
    id SERIAL PRIMARY KEY,
    school_name VARCHAR(128) NOT NULL,
    school_type VARCHAR(16) NOT NULL,   -- 초등학교/중학교/고등학교/특수학교
    address TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    student_count INTEGER,
    teacher_count INTEGER,
    data_year INTEGER,
    UNIQUE(school_name, address)
);

CREATE INDEX IF NOT EXISTS idx_schools_lat_lon
    ON schools (lat, lon);
CREATE INDEX IF NOT EXISTS idx_schools_type
    ON schools (school_type);

-- 3) 매물별 enrichment 캐시
CREATE TABLE IF NOT EXISTS property_enrichment (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(64) NOT NULL,
    db_id INTEGER NOT NULL,
    nearest_subway JSONB,       -- [{name, line, distance_m, walk_min}]
    nearby_schools JSONB,       -- [{name, type, distance_m, student_count}]
    enriched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(record_id, db_id)
);

CREATE INDEX IF NOT EXISTS idx_pe_record
    ON property_enrichment (record_id, db_id);

COMMIT;
