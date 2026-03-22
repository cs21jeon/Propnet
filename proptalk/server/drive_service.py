"""
Google Drive Service - 방장의 Google Drive에 파일 저장
사용자 OAuth 토큰 기반, 자동 토큰 갱신 포함
"""
import os
import io
import re
import logging
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from config import Config

logger = logging.getLogger(__name__)


def _get_valid_credentials(user_tokens):
    """
    사용자 토큰으로 Credentials 생성, 만료 시 자동 갱신
    Returns: (credentials, updated_tokens or None)
    """
    credentials = Credentials(
        token=user_tokens.get('access_token'),
        refresh_token=user_tokens.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )

    updated_tokens = None

    # 토큰 만료 확인 및 갱신
    expires_at = user_tokens.get('expires_at', 0)
    now = datetime.now(timezone.utc).timestamp()

    if now >= expires_at - 300:  # 5분 전부터 갱신
        if credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            updated_tokens = {
                **user_tokens,
                'access_token': credentials.token,
                'expires_at': now + 3600,
            }
            logger.info("[Drive] 토큰 자동 갱신 완료")

    return credentials, updated_tokens


def _sanitize_folder_name(name):
    """폴더명에서 특수문자 제거"""
    sanitized = re.sub(r'[\\/:*?"<>|]', '_', name)
    return sanitized.strip() or 'Unnamed'


def get_drive_service(user_tokens):
    """사용자 토큰으로 Drive 서비스 생성"""
    credentials, updated_tokens = _get_valid_credentials(user_tokens)
    service = build('drive', 'v3', credentials=credentials)
    return service, updated_tokens


def get_or_create_folder(service, folder_name, parent_id=None):
    """폴더가 없으면 생성, 있으면 ID 반환"""
    safe_name = _sanitize_folder_name(folder_name)
    query = f"name='{safe_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])

    if files:
        return files[0]['id']

    # 폴더 생성
    file_metadata = {
        'name': safe_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    folder = service.files().create(body=file_metadata, fields='id').execute()
    logger.info(f"[Drive] 폴더 생성: {safe_name} ({folder.get('id')})")
    return folder.get('id')


def ensure_room_folder(user_tokens, room_name):
    """
    Proptalk/{room_name} 폴더 확보 (없으면 생성)
    Returns: (folder_id, updated_tokens)
    """
    service, updated_tokens = get_drive_service(user_tokens)

    proptalk_folder_id = get_or_create_folder(service, 'Proptalk')
    room_folder_id = get_or_create_folder(service, room_name, proptalk_folder_id)

    return room_folder_id, updated_tokens


def upload_to_drive(user_tokens, file_path, room_name, room_folder_id=None, upload_filename=None):
    """
    방장의 Google Drive에 파일 업로드
    폴더 구조: Proptalk/{room_name}/{file}

    Returns:
        {'file_id': str, 'web_link': str, 'updated_tokens': dict or None, 'folder_id': str}
    """
    try:
        service, updated_tokens = get_drive_service(user_tokens)

        # 폴더 ID가 캐시되어 있으면 사용, 없으면 생성
        if not room_folder_id:
            proptalk_folder_id = get_or_create_folder(service, 'Proptalk')
            room_folder_id = get_or_create_folder(service, room_name, proptalk_folder_id)

        # 파일 업로드
        file_name = upload_filename or os.path.basename(file_path)
        file_metadata = {
            'name': file_name,
            'parents': [room_folder_id]
        }

        # MIME 타입 결정
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            # Audio
            '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg', '.flac': 'audio/flac', '.webm': 'audio/webm',
            '.aac': 'audio/aac', '.amr': 'audio/amr', '.3gp': 'audio/3gpp',
            # Image
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp',
            # Document
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            # Text
            '.txt': 'text/plain', '.csv': 'text/csv', '.json': 'application/json',
            # Archive
            '.zip': 'application/zip',
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()

        logger.info(f"[Drive] 업로드 완료: {file_name} → {file.get('id')}")

        # 파일은 폴더 권한을 상속하므로 개별 권한 설정 불필요

        return {
            'file_id': file.get('id'),
            'web_link': file.get('webViewLink'),
            'download_link': file.get('webContentLink'),
            'updated_tokens': updated_tokens,
            'folder_id': room_folder_id,
        }
    except Exception as e:
        logger.error(f"[Drive] 업로드 실패: {e}")
        raise


def download_from_drive(user_tokens, file_id):
    """
    Google Drive에서 파일 다운로드 (서버 프록시용)
    Returns: (파일 바이트, updated_tokens)
    """
    try:
        service, updated_tokens = get_drive_service(user_tokens)

        request = service.files().get_media(fileId=file_id)
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        return file_data.getvalue(), updated_tokens
    except Exception as e:
        logger.error(f"[Drive] 다운로드 실패: {e}")
        raise


def add_folder_permission(user_tokens, folder_id, email):
    """
    Drive 폴더에 특정 사용자 읽기 권한 추가
    Returns: permission_id (str) or None
    """
    try:
        service, _ = get_drive_service(user_tokens)
        perm = service.permissions().create(
            fileId=folder_id,
            body={
                'type': 'user',
                'role': 'reader',
                'emailAddress': email,
            },
            sendNotificationEmail=False,
            fields='id',
        ).execute()
        perm_id = perm.get('id')
        logger.info(f"[Drive] 폴더 권한 추가: {email} → {perm_id}")
        return perm_id
    except Exception as e:
        logger.warning(f"[Drive] 폴더 권한 추가 실패 ({email}): {e}")
        return None


def remove_folder_permission(user_tokens, folder_id, permission_id):
    """
    Drive 폴더에서 특정 사용자 권한 제거
    """
    try:
        service, _ = get_drive_service(user_tokens)
        service.permissions().delete(
            fileId=folder_id,
            permissionId=permission_id,
        ).execute()
        logger.info(f"[Drive] 폴더 권한 삭제: {permission_id}")
        return True
    except Exception as e:
        logger.warning(f"[Drive] 폴더 권한 삭제 실패 ({permission_id}): {e}")
        return False


def sync_folder_permissions(user_tokens, folder_id, member_emails):
    """
    Drive 폴더에 멤버 목록의 읽기 권한을 일괄 설정
    Returns: dict { email: permission_id }
    """
    results = {}
    for email in member_emails:
        perm_id = add_folder_permission(user_tokens, folder_id, email)
        if perm_id:
            results[email] = perm_id
    return results


def remove_anyone_permission(user_tokens, folder_id):
    """
    폴더의 'anyone' 권한 제거 (기존 공개 링크 비활성화)
    """
    try:
        service, _ = get_drive_service(user_tokens)
        perms = service.permissions().list(
            fileId=folder_id, fields='permissions(id, type)'
        ).execute()
        for perm in perms.get('permissions', []):
            if perm.get('type') == 'anyone':
                service.permissions().delete(
                    fileId=folder_id, permissionId=perm['id']
                ).execute()
                logger.info(f"[Drive] anyone 권한 삭제: {folder_id}")
        return True
    except Exception as e:
        logger.warning(f"[Drive] anyone 권한 삭제 실패: {e}")
        return False


def delete_from_drive(user_tokens, file_id):
    """Google Drive에서 파일 삭제"""
    try:
        service, _ = get_drive_service(user_tokens)
        service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        logger.error(f"[Drive] 삭제 실패: {e}")
        return False
