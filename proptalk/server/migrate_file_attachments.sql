-- file_attachments 테이블 생성
CREATE TABLE IF NOT EXISTS file_attachments (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(id) ON DELETE CASCADE,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),

    original_filename VARCHAR(500) NOT NULL,
    file_size INTEGER DEFAULT 0,
    file_type VARCHAR(50) NOT NULL,   -- image, document, video, other
    mime_type VARCHAR(100),

    drive_file_id VARCHAR(200),
    drive_url TEXT,

    status VARCHAR(20) DEFAULT 'uploading',  -- uploading, completed, failed
    error_message TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_file_attachments_message ON file_attachments(message_id);
CREATE INDEX IF NOT EXISTS idx_file_attachments_room ON file_attachments(room_id);
