-- 파일 첨부 테이블에 썸네일 관련 컬럼 추가
-- saved_filename: 서버에 저장된 UUID 기반 파일명 (다운로드/썸네일용)
-- thumbnail_path: 썸네일 파일 경로 (이미지 파일만)

ALTER TABLE file_attachments ADD COLUMN IF NOT EXISTS saved_filename VARCHAR(500);
ALTER TABLE file_attachments ADD COLUMN IF NOT EXISTS thumbnail_path VARCHAR(500);
