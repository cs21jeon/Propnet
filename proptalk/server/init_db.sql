-- ============================================================
-- VoiceRoom - DB 초기화
-- PostgreSQL
-- ============================================================

-- 사용자
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    google_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 채팅방
CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    invite_code VARCHAR(20) UNIQUE,  -- 초대 코드
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 채팅방 멤버
CREATE TABLE IF NOT EXISTS room_members (
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member',  -- admin / member
    status VARCHAR(20) DEFAULT 'active',  -- active / pending
    is_favorite BOOLEAN DEFAULT false,
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (room_id, user_id)
);

-- 메시지
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(20) NOT NULL DEFAULT 'text',  -- text / audio / transcript / system
    content TEXT,
    parent_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,  -- 댓글 대상
    created_at TIMESTAMP DEFAULT NOW()
);

-- 음성 파일 기록
CREATE TABLE IF NOT EXISTS audio_files (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(id) ON DELETE CASCADE,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    
    -- 파일 정보
    original_filename VARCHAR(500),
    file_size INTEGER,
    duration_seconds FLOAT,
    
    -- Google Drive 저장
    drive_file_id VARCHAR(200),
    drive_url TEXT,
    
    -- AI 파싱 결과 (파일명에서 추출)
    phone_number VARCHAR(20),
    record_date DATE,
    parsed_name VARCHAR(100),       -- 파싱된 이름 (있으면)
    parsed_memo TEXT,               -- 파싱된 메모/설명
    
    -- STT 결과
    transcript_text TEXT,
    transcript_summary TEXT,        -- AI 요약
    transcript_segments JSONB,      -- 시간별 세그먼트
    
    -- 상태
    status VARCHAR(20) DEFAULT 'uploading',  -- uploading / transcribing / completed / failed
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_parent ON messages(parent_id);
CREATE INDEX IF NOT EXISTS idx_audio_room ON audio_files(room_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audio_phone ON audio_files(phone_number);
CREATE INDEX IF NOT EXISTS idx_audio_date ON audio_files(record_date);
CREATE INDEX IF NOT EXISTS idx_audio_status ON audio_files(status);
CREATE INDEX IF NOT EXISTS idx_room_members_user ON room_members(user_id);
CREATE INDEX IF NOT EXISTS idx_room_members_status ON room_members(room_id, status);
CREATE INDEX IF NOT EXISTS idx_rooms_invite ON rooms(invite_code);

-- 사용자 동의 이력
CREATE TABLE IF NOT EXISTS user_consents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    agreed BOOLEAN NOT NULL DEFAULT true,
    agreed_at TIMESTAMP DEFAULT NOW(),
    withdrawn_at TIMESTAMP,
    ip_address VARCHAR(50),
    user_agent TEXT
);

-- 접속기록 (감사 로그)
CREATE TABLE IF NOT EXISTS access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(30),
    resource_id INTEGER,
    ip_address VARCHAR(50),
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_consents_user ON user_consents(user_id);
CREATE INDEX IF NOT EXISTS idx_user_consents_type ON user_consents(user_id, consent_type);
CREATE INDEX IF NOT EXISTS idx_access_logs_user ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_created ON access_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_access_logs_action ON access_logs(action);

-- 업데이트 트리거
CREATE OR REPLACE FUNCTION update_room_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE rooms SET updated_at = NOW() WHERE id = NEW.room_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_message_update_room ON messages;
CREATE TRIGGER trg_message_update_room
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_room_timestamp();
