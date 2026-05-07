-- PropValue: 재개발/재건축 정비구역 테이블
-- 실행: psql -U goldenrabbit_user -d goldenrabbit_db -f propvalue_v1.sql

CREATE TABLE IF NOT EXISTS redevelopment_zones (
    id                  SERIAL PRIMARY KEY,
    zone_name           VARCHAR(100) NOT NULL,
    zone_code           VARCHAR(30) UNIQUE,
    city                VARCHAR(20) NOT NULL,
    district            VARCHAR(20) NOT NULL,
    dong                VARCHAR(20),
    project_type        VARCHAR(20) NOT NULL,
    stage               VARCHAR(20) NOT NULL,
    area_sqm            NUMERIC(12,2),
    households          INTEGER,
    floors_plan         VARCHAR(50),
    developer           VARCHAR(100),
    union_approved      DATE,
    biz_approved        DATE,
    mgmt_approved       DATE,
    construction_start  DATE,
    completion_date     DATE,
    geometry            JSONB,
    center_lat          NUMERIC(10,7),
    center_lon          NUMERIC(10,7),
    source              VARCHAR(30) DEFAULT 'seoul',
    raw_data            JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rz_city_district ON redevelopment_zones(city, district);
CREATE INDEX IF NOT EXISTS idx_rz_stage ON redevelopment_zones(stage);
CREATE INDEX IF NOT EXISTS idx_rz_project_type ON redevelopment_zones(project_type);
CREATE INDEX IF NOT EXISTS idx_rz_center ON redevelopment_zones(center_lat, center_lon);

COMMENT ON TABLE redevelopment_zones IS 'PropValue 정비구역(재개발/재건축) 정보. 공공데이터 기반.';
