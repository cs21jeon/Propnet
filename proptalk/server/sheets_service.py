"""
Google Sheets Service - 음성 파일 메타데이터 자동 기록
Proptalk/{방이름}/ 폴더에 스프레드시트 생성, 업로드마다 행 추가
"""
import logging
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from drive_service import get_or_create_folder, _sanitize_folder_name
from config import Config

logger = logging.getLogger(__name__)

SHEETS_SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets',
]


def _get_sheets_credentials(user_tokens):
    """Sheets + Drive 스코프로 Credentials 생성 (토큰 갱신 포함)"""
    credentials = Credentials(
        token=user_tokens.get('access_token'),
        refresh_token=user_tokens.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        scopes=SHEETS_SCOPES
    )

    updated_tokens = None
    expires_at = user_tokens.get('expires_at', 0)
    now = datetime.now(timezone.utc).timestamp()

    if now >= expires_at - 300:
        if credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            updated_tokens = {
                **user_tokens,
                'access_token': credentials.token,
                'expires_at': now + 3600,
            }
            logger.info('[Sheets] 토큰 자동 갱신 완료')

    return credentials, updated_tokens

# 헤더 컬럼 정의
SHEET_HEADERS = [
    '날짜', '파일명', '전화번호', '이름', '길이(초)',
    '업로더', '방이름', '처리시간', 'Drive링크', '원본텍스트', '요약'
]

# 방별 스프레드시트 ID 캐시 (메모리)
_spreadsheet_cache = {}


def _get_sheets_service(user_tokens):
    """사용자 토큰으로 Sheets 서비스 생성"""
    credentials, updated_tokens = _get_sheets_credentials(user_tokens)
    service = build('sheets', 'v4', credentials=credentials)
    return service, updated_tokens


def _find_spreadsheet_in_folder(drive_service, folder_id, sheet_name):
    """폴더 내에서 스프레드시트 검색"""
    query = (
        f"name='{sheet_name}' "
        f"and mimeType='application/vnd.google-apps.spreadsheet' "
        f"and trashed=false "
        f"and '{folder_id}' in parents"
    )
    results = drive_service.files().list(
        q=query, spaces='drive', fields='files(id, name)'
    ).execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None


def _create_spreadsheet(sheets_service, drive_service, folder_id, room_name):
    """스프레드시트 생성 + 헤더 행 추가 + 폴더로 이동"""
    safe_name = _sanitize_folder_name(room_name)
    title = f"{safe_name} - 기록"

    # Sheets API로 생성
    spreadsheet = sheets_service.spreadsheets().create(
        body={
            'properties': {'title': title},
            'sheets': [{
                'properties': {'title': safe_name}
            }]
        },
        fields='spreadsheetId'
    ).execute()
    spreadsheet_id = spreadsheet['spreadsheetId']

    # 헤더 행 추가
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{safe_name}'!A1",
        valueInputOption='RAW',
        body={'values': [SHEET_HEADERS]}
    ).execute()

    # 폴더로 이동 (기본 root에서 target 폴더로)
    drive_service.files().update(
        fileId=spreadsheet_id,
        addParents=folder_id,
        removeParents='root',
        fields='id, parents'
    ).execute()

    logger.info(f"[Sheets] 스프레드시트 생성: {title} ({spreadsheet_id})")
    return spreadsheet_id


def get_or_create_spreadsheet(user_tokens, folder_id, room_name):
    """
    방의 스프레드시트 ID 확보 (캐시 → Drive 검색 → 생성)
    Returns: (spreadsheet_id, updated_tokens)
    """
    cache_key = f"{folder_id}_{room_name}"

    # 메모리 캐시 확인
    if cache_key in _spreadsheet_cache:
        return _spreadsheet_cache[cache_key], None

    from drive_service import get_drive_service
    drive_svc, updated_tokens = get_drive_service(user_tokens)
    sheets_svc, _ = _get_sheets_service(user_tokens)

    safe_name = _sanitize_folder_name(room_name)
    sheet_title = f"{safe_name} - 기록"

    # Drive에서 검색
    spreadsheet_id = _find_spreadsheet_in_folder(drive_svc, folder_id, sheet_title)

    if not spreadsheet_id:
        # 생성
        spreadsheet_id = _create_spreadsheet(sheets_svc, drive_svc, folder_id, room_name)

    _spreadsheet_cache[cache_key] = spreadsheet_id
    return spreadsheet_id, updated_tokens


def append_record(user_tokens, folder_id, room_name, record_data):
    """
    스프레드시트에 레코드 1행 추가

    record_data: dict with keys matching SHEET_HEADERS
        - 날짜, 파일명, 전화번호, 이름, 길이(초),
        - 업로더, 방이름, 처리시간, Drive링크, 원본텍스트, 요약
    """
    try:
        spreadsheet_id, updated_tokens = get_or_create_spreadsheet(
            user_tokens, folder_id, room_name
        )
        sheets_svc, _ = _get_sheets_service(user_tokens)
        safe_name = _sanitize_folder_name(room_name)

        # 헤더 순서에 맞게 행 구성
        row = [str(record_data.get(h, '')) for h in SHEET_HEADERS]

        sheets_svc.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"'{safe_name}'!A:K",
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': [row]}
        ).execute()

        logger.info(f"[Sheets] 레코드 추가: {room_name} - {record_data.get('파일명', '?')}")
        return True

    except Exception as e:
        logger.error(f"[Sheets] 레코드 추가 실패: {e}")
        return False
