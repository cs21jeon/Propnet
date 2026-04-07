-- admin_settings 테이블 (OpenAI 크레딧 등 관리자 설정 저장)
CREATE TABLE IF NOT EXISTS admin_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- agent_requests 테이블에 reviewed_by, reject_reason 컬럼 확인/추가
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agent_requests' AND column_name = 'reviewed_at'
    ) THEN
        ALTER TABLE agent_requests ADD COLUMN reviewed_at TIMESTAMP;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agent_requests' AND column_name = 'reviewed_by'
    ) THEN
        ALTER TABLE agent_requests ADD COLUMN reviewed_by VARCHAR(255);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agent_requests' AND column_name = 'reject_reason'
    ) THEN
        ALTER TABLE agent_requests ADD COLUMN reject_reason TEXT;
    END IF;
END $$;
