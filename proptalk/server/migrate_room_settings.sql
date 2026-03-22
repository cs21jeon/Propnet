-- 채팅방 Drive/Sheets 토글 컬럼 추가
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS enable_drive_backup BOOLEAN DEFAULT true;
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS enable_sheets_logging BOOLEAN DEFAULT true;
