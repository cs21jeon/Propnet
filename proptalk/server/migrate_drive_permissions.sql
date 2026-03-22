-- Drive 폴더 권한 관리를 위한 마이그레이션
-- room_members에 drive_permission_id 컬럼 추가
ALTER TABLE room_members ADD COLUMN IF NOT EXISTS drive_permission_id VARCHAR(200);
