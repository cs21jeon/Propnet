"""
Google Drive 파일 업로드 서비스
Service Account 인증 사용
"""
import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import Config

logger = logging.getLogger(__name__)

# 스코프
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_drive_service():
    """Google Drive API 서비스 객체 생성"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            Config.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Drive 서비스 초기화 실패: {e}")
        return None


def upload_to_drive(filepath: str, filename: str, folder_id: str = None, 
                    subfolder: str = None) -> dict | None:
    """
    파일을 Google Drive에 업로드
    
    Args:
        filepath: 로컬 파일 경로
        filename: 저장할 파일명
        folder_id: Drive 폴더 ID (None이면 Config에서 가져옴)
        subfolder: 하위 폴더명 (예: '2025-02', 'room_1')
    
    Returns:
        {'file_id': '...', 'url': 'https://drive.google.com/file/d/...'} or None
    """
    service = get_drive_service()
    if not service:
        return None
    
    target_folder = folder_id or Config.GOOGLE_DRIVE_FOLDER_ID
    
    try:
        # 하위 폴더가 필요한 경우 생성/조회
        if subfolder and target_folder:
            target_folder = get_or_create_folder(service, subfolder, target_folder)
        
        # MIME 타입 매핑
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac',
            '.webm': 'audio/webm',
            '.mp4': 'video/mp4',
            '.aac': 'audio/aac',
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        # 메타데이터
        file_metadata = {'name': filename}
        if target_folder:
            file_metadata['parents'] = [target_folder]
        
        # 업로드
        media = MediaFileUpload(filepath, mimetype=mime_type, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        result = {
            'file_id': file.get('id'),
            'url': file.get('webViewLink', f"https://drive.google.com/file/d/{file.get('id')}")
        }
        
        logger.info(f"Drive 업로드 성공: {filename} → {result['file_id']}")
        return result
    
    except Exception as e:
        logger.error(f"Drive 업로드 실패: {e}")
        return None


def get_or_create_folder(service, folder_name: str, parent_id: str) -> str:
    """폴더 조회, 없으면 생성"""
    try:
        # 기존 폴더 검색
        query = (f"name = '{folder_name}' and "
                 f"'{parent_id}' in parents and "
                 f"mimeType = 'application/vnd.google-apps.folder' and "
                 f"trashed = false")
        
        results = service.files().list(
            q=query, fields='files(id)', pageSize=1
        ).execute()
        
        files = results.get('files', [])
        if files:
            return files[0]['id']
        
        # 폴더 생성
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = service.files().create(
            body=folder_metadata, fields='id'
        ).execute()
        
        logger.info(f"Drive 폴더 생성: {folder_name} → {folder['id']}")
        return folder['id']
    
    except Exception as e:
        logger.error(f"Drive 폴더 처리 실패: {e}")
        return parent_id
