"""
메시지 / 음성파일 API 라우트
핵심: 음성 업로드 → STT 변환 → Claude 요약 → 자동 댓글
"""
import os
import uuid
import time
import shutil
import logging
import threading
from urllib.parse import quote as url_quote
from datetime import datetime, date
from flask import request, jsonify, g, send_file
from werkzeug.utils import secure_filename
from auth import login_required
from models import Room, Message, AudioFile, FileAttachment, query_one, query_all
from config import Config


def _serialize(obj):
    """딕셔너리 내 datetime 객체를 ISO 문자열로 변환"""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize(v) for v in obj]
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj

logger = logging.getLogger(__name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def register_message_routes(app, socketio):
    
    # ============================================================
    # 텍스트 메시지
    # ============================================================
    @app.route('/api/rooms/<int:room_id>/messages', methods=['GET'])
    @login_required
    def get_messages(room_id):
        """채팅방 메시지 목록 (페이지네이션)"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403
        
        before_id = request.args.get('before_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        
        messages = Message.list_for_room(room_id, limit=limit, before_id=before_id)
        return jsonify({'messages': messages})
    
    
    @app.route('/api/rooms/<int:room_id>/messages', methods=['POST'])
    @login_required
    def send_message(room_id):
        """
        텍스트 메시지 전송
        
        Request:
            { "content": "메시지 내용", "parent_id": null }
        """
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403
        
        data = request.get_json()
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        
        if not content:
            return jsonify({'error': '메시지 내용이 필요합니다'}), 400
        
        msg = Message.create(room_id, g.user_id, 'text', content, parent_id)

        # 발신자는 자기가 보낸 메시지까지 읽은 것으로 처리
        Room.mark_read(room_id, g.user_id, msg['id'])

        # WebSocket으로 실시간 전송
        socketio.emit('new_message', {
            'message': _serialize({
                **msg,
                'user_name': g.user['name'],
                'user_avatar': g.user.get('avatar_url'),
            })
        }, room=f'room_{room_id}')

        # FCM 푸시 알림
        from notification_service import notify_new_message
        notify_new_message(room_id, g.user['name'], content,
                           msg_type='text', sender_user_id=g.user_id)

        return jsonify({'message': msg}), 201
    
    
    # ============================================================
    # 음성 파일 업로드 + 자동 STT
    # ============================================================
    @app.route('/api/rooms/<int:room_id>/audio', methods=['POST'])
    @login_required
    def upload_audio(room_id):
        """
        음성 파일 업로드 → 자동 STT 변환 → 자동 댓글
        
        Request: multipart/form-data
            - file: 음성 파일
            - language: 언어코드 (기본: ko)
        """
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        # 과금: 방장(room owner)에게 부과
        room = Room.find_by_id(room_id)
        owner_id = room['created_by']
        from billing_service import check_can_transcribe, ensure_user_billing, get_audio_duration_fast
        ensure_user_billing(owner_id)
        can_use, reason = check_can_transcribe(owner_id)
        if not can_use:
            return jsonify({'error': reason, 'code': 'INSUFFICIENT_BALANCE'}), 402

        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다'}), 400

        file = request.files['file']
        if not file.filename or not allowed_file(file.filename):
            return jsonify({'error': '허용되지 않는 파일 형식입니다'}), 400

        language = request.form.get('language', 'ko')
        original_filename = file.filename

        # 1) 파일 저장
        file_id = str(uuid.uuid4())
        ext = original_filename.rsplit('.', 1)[1].lower()
        saved_filename = f"{file_id}.{ext}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, saved_filename)

        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)
        file_size = os.path.getsize(filepath)

        # 과금: 파일 길이 vs 방장 잔여 시간 비교 (2차 — 부족 시 차단)
        audio_duration = get_audio_duration_fast(filepath)
        if audio_duration:
            can_use, reason = check_can_transcribe(owner_id, audio_duration_seconds=audio_duration)
            if not can_use:
                os.remove(filepath)
                return jsonify({'error': reason, 'code': 'INSUFFICIENT_BALANCE'}), 402

        # 2) 음성 메시지 생성 (채팅에 표시)
        msg = Message.create(
            room_id, g.user_id, 'audio',
            f'🎙️ {original_filename}'
        )

        # 발신자는 자기가 보낸 메시지까지 읽은 것으로 처리
        Room.mark_read(room_id, g.user_id, msg['id'])

        # 3) audio_files 레코드 생성
        audio = AudioFile.create(
            msg['id'], room_id, g.user_id, original_filename, file_size
        )
        
        # 4) WebSocket으로 음성 메시지 전송
        socketio.emit('new_message', {
            'message': _serialize({
                **msg,
                'user_name': g.user['name'],
                'user_avatar': g.user.get('avatar_url'),
                'audio_id': audio['id'],
                'audio_status': 'uploading',
            })
        }, room=f'room_{room_id}')

        # 음성 업로드 시에는 알림 보내지 않음 (요약 완료 시 알림)

        # 5) 백그라운드에서 STT + Drive 업로드 처리
        room_drive_enabled = room.get('enable_drive_backup', True)
        room_sheets_enabled = room.get('enable_sheets_logging', True)

        # 방장 Google 토큰 조회 (Drive 업로드용)
        owner_tokens = None
        room_drive_folder_id = room.get('drive_folder_id')
        room_name = room.get('name', 'Unknown')
        if Config.ENABLE_GOOGLE_DRIVE_BACKUP and room_drive_enabled:
            from models import User
            owner = User.find_by_id(room['created_by'])
            if owner and owner.get('google_tokens'):
                owner_tokens = owner['google_tokens']

        thread = threading.Thread(
            target=process_audio_background,
            args=(app, socketio,
                  filepath, audio['id'], msg['id'], room_id,
                  g.user_id, g.user['name'], original_filename, language,
                  owner_id, room_drive_enabled, room_sheets_enabled,
                  owner_tokens, room_name, room_drive_folder_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': msg,
            'audio': audio,
            'status': '변환을 시작합니다...'
        }), 201
    
    
    # ============================================================
    # 일반 파일 업로드 → Google Drive → 링크 공유
    # ============================================================
    def _allowed_file_upload(filename):
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in Config.ALLOWED_FILE_EXTENSIONS

    def _get_file_type(filename):
        ext = filename.rsplit('.', 1)[1].lower()
        if ext in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'):
            return 'image'
        elif ext in ('pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'):
            return 'document'
        elif ext in ('txt', 'csv', 'json'):
            return 'text'
        elif ext == 'zip':
            return 'archive'
        return 'other'

    def _get_file_icon(file_type):
        icons = {
            'image': '\U0001f5bc\ufe0f',
            'document': '\U0001f4c4',
            'text': '\U0001f4dd',
            'archive': '\U0001f4e6',
        }
        return icons.get(file_type, '\U0001f4ce')

    def _format_file_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"

    @app.route('/api/rooms/<int:room_id>/files', methods=['POST'])
    @login_required
    def upload_file(room_id):
        """일반 파일 업로드 → Drive 저장 → 링크 공유"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다'}), 400

        file = request.files['file']
        if not file.filename or not _allowed_file_upload(file.filename):
            return jsonify({'error': '허용되지 않는 파일 형식입니다'}), 400

        original_filename = file.filename
        file_type = _get_file_type(original_filename)
        icon = _get_file_icon(file_type)

        # 1) 임시 저장
        file_uuid = str(uuid.uuid4())
        ext = original_filename.rsplit('.', 1)[1].lower()
        saved_filename = f"{file_uuid}.{ext}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, saved_filename)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)
        file_size = os.path.getsize(filepath)

        if file_size > Config.MAX_FILE_SIZE:
            os.remove(filepath)
            return jsonify({'error': f'파일 크기 제한 초과 ({_format_file_size(Config.MAX_FILE_SIZE)})'}), 400

        # 1-b) 이미지 썸네일 생성
        thumbnail_path = None
        if file_type == 'image':
            try:
                from PIL import Image as PILImage
                thumb_dir = Config.THUMBNAIL_FOLDER
                os.makedirs(thumb_dir, exist_ok=True)
                thumb_filename = f"thumb_{file_uuid}.jpg"
                thumb_full_path = os.path.join(thumb_dir, thumb_filename)

                with PILImage.open(filepath) as img:
                    img.thumbnail(Config.THUMBNAIL_MAX_SIZE)
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    img.save(thumb_full_path, 'JPEG', quality=75)

                thumbnail_path = thumb_filename
                logger.info(f"[File] 썸네일 생성: {thumb_filename}")
            except Exception as e:
                logger.warning(f"[File] 썸네일 생성 실패: {e}")

        # 2) 메시지 생성
        size_str = _format_file_size(file_size)
        msg = Message.create(
            room_id, g.user_id, 'file',
            f'{icon} {original_filename} ({size_str})'
        )

        # 발신자는 자기가 보낸 메시지까지 읽은 것으로 처리
        Room.mark_read(room_id, g.user_id, msg['id'])

        # 3) file_attachments 레코드 생성
        mime_type = file.content_type
        attachment = FileAttachment.create(
            msg['id'], room_id, g.user_id,
            original_filename, file_size, file_type, mime_type,
            saved_filename=saved_filename, thumbnail_path=thumbnail_path
        )

        # 4) WebSocket 전송
        thumbnail_url = f"/api/files/{attachment['id']}/thumbnail" if thumbnail_path else None
        socketio.emit('new_message', {
            'message': _serialize({
                **msg,
                'user_name': g.user['name'],
                'user_avatar': g.user.get('avatar_url'),
                'file_id': attachment['id'],
                'file_name': original_filename,
                'file_size': file_size,
                'file_type': file_type,
                'file_drive_url': None,
                'file_status': 'uploading',
                'file_thumbnail_path': thumbnail_path,
            })
        }, room=f'room_{room_id}')

        # FCM 푸시 알림
        from notification_service import notify_new_message
        notify_new_message(room_id, g.user['name'], original_filename,
                           msg_type='file', sender_user_id=g.user_id)

        # 5) 백그라운드 Drive 업로드
        room = Room.find_by_id(room_id)
        room_drive_enabled = room.get('enable_drive_backup', True)
        owner_tokens = None
        room_drive_folder_id = room.get('drive_folder_id')
        room_name = room.get('name', 'Unknown')

        if Config.ENABLE_GOOGLE_DRIVE_BACKUP and room_drive_enabled:
            from models import User
            owner = User.find_by_id(room['created_by'])
            if owner and owner.get('google_tokens'):
                owner_tokens = owner['google_tokens']

        thread = threading.Thread(
            target=_process_file_upload,
            args=(app, socketio, filepath, attachment['id'], msg['id'],
                  room_id, g.user_id, original_filename,
                  owner_tokens, room_name, room_drive_folder_id)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'message': msg,
            'attachment': attachment,
        }), 201


    def _process_file_upload(app, socketio, filepath, attachment_id, message_id,
                             room_id, user_id, original_filename,
                             owner_tokens, room_name, room_folder_id):
        """백그라운드: 파일 → Drive 업로드 → 링크 공유"""
        with app.app_context():
            try:
                drive_url = None

                if owner_tokens:
                    from drive_service import upload_to_drive
                    from models import User

                    result = upload_to_drive(
                        owner_tokens, filepath, room_name,
                        room_folder_id=room_folder_id,
                        upload_filename=original_filename
                    )

                    drive_url = result.get('web_link')
                    FileAttachment.update_drive(
                        attachment_id, result['file_id'], drive_url
                    )

                    # 토큰 갱신 시 저장
                    if result.get('updated_tokens'):
                        room = Room.find_by_id(room_id)
                        User.update_google_tokens(room['created_by'], result['updated_tokens'])

                    # 폴더 ID 캐시 + 최초 생성 시 멤버 권한 설정
                    if result.get('folder_id') and not room_folder_id:
                        from models import execute
                        new_folder_id = result['folder_id']
                        execute("UPDATE rooms SET drive_folder_id = %s WHERE id = %s",
                                (new_folder_id, room_id))
                        # 기존 멤버들에게 폴더 읽기 권한 부여
                        try:
                            from drive_service import sync_folder_permissions
                            members = Room.get_members(room_id)
                            member_emails = [
                                m['email'] for m in members
                                if m['id'] != room['created_by']
                            ]
                            if member_emails:
                                perm_results = sync_folder_permissions(
                                    owner_tokens, new_folder_id, member_emails
                                )
                                for m in members:
                                    if m['email'] in perm_results:
                                        Room.update_drive_permission(
                                            room_id, m['id'],
                                            perm_results[m['email']]
                                        )
                        except Exception as pe:
                            logger.warning(f"[Drive] 초기 폴더 권한 설정 실패: {pe}")

                    logger.info(f"[File] Drive 업로드 완료: {original_filename}")
                else:
                    FileAttachment.update_status(attachment_id, 'completed')
                    logger.info(f"[File] Drive 미설정, 로컬 저장만: {original_filename}")

                # WebSocket으로 완료 알림
                socketio.emit('file_status', {
                    'message_id': message_id,
                    'attachment_id': attachment_id,
                    'status': 'completed',
                    'drive_url': drive_url,
                }, room=f'room_{room_id}')

            except Exception as e:
                logger.error(f"[File] 업로드 실패: {e}")
                FileAttachment.update_status(attachment_id, 'failed', str(e)[:200])

                socketio.emit('file_status', {
                    'message_id': message_id,
                    'attachment_id': attachment_id,
                    'status': 'failed',
                    'error': str(e)[:100],
                }, room=f'room_{room_id}')
            finally:
                # 임시 파일을 보관 폴더로 이동 (7일간 보관)
                if os.path.exists(filepath):
                    try:
                        import shutil
                        file_folder = Config.FILE_FOLDER
                        os.makedirs(file_folder, exist_ok=True)
                        dest_path = os.path.join(file_folder, os.path.basename(filepath))
                        shutil.move(filepath, dest_path)
                        logger.info(f"[File] 보관 폴더로 이동: {dest_path}")
                    except Exception as move_err:
                        logger.warning(f"[File] 보관 이동 실패, 삭제: {move_err}")
                        os.remove(filepath)
                        logger.info(f"[File] 임시 파일 삭제: {filepath}")


    # ============================================================
    # 메시지 검색 (내용 + 파일명 + 변환 텍스트)
    # ============================================================
    @app.route('/api/rooms/<int:room_id>/messages/search', methods=['GET'])
    @login_required
    def search_messages(room_id):
        """메시지 검색 (내용/파일명/요약 텍스트)"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403
        q = request.args.get('q', '').strip()
        if not q:
            return jsonify({'messages': []})
        messages = Message.search(room_id, q)
        return jsonify({'messages': messages})

    # ============================================================
    # 음성 파일 검색
    # ============================================================
    @app.route('/api/rooms/<int:room_id>/audio/search', methods=['GET'])
    @login_required
    def search_audio(room_id):
        """
        음성 파일 검색 (전화번호, 날짜)
        
        Query params:
            - phone: 전화번호 (부분 일치)
            - date_from: 시작일 (YYYY-MM-DD)
            - date_to: 종료일 (YYYY-MM-DD)
        """
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403
        
        phone = request.args.get('phone')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        results = AudioFile.search(
            room_id=room_id,
            phone_number=phone,
            date_from=date_from,
            date_to=date_to
        )
        
        return jsonify({'audio_files': results})
    
    
    # ============================================================
    # 음성 파일 상세
    # ============================================================
    @app.route('/api/audio/<int:audio_id>', methods=['GET'])
    @login_required
    def get_audio_detail(audio_id):
        """음성 파일 상세 정보 (변환 결과 포함)"""
        audio = AudioFile.find_by_id(audio_id)
        if not audio:
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404

        if not Room.is_member(audio['room_id'], g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        return jsonify({'audio': audio})

    # ============================================================
    # 음성 파일 다운로드 (서버 프록시 — CORS 회피)
    # ============================================================
    @app.route('/api/audio/<int:audio_id>/download', methods=['GET'])
    @login_required
    def download_audio(audio_id):
        """
        음성 파일 다운로드
        1) 로컬 파일이 있으면 직접 서빙
        2) 없으면 Drive API로 서버가 다운로드하여 클라이언트에 스트리밍
           (Drive URL 302 리다이렉트 시 CORS 에러 발생하므로 프록시 필수)
        """
        audio = AudioFile.find_by_id(audio_id)
        if not audio:
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404

        if not Room.is_member(audio['room_id'], g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        original_filename = audio['original_filename']
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'mp3'
        filepath = os.path.join(Config.AUDIO_FOLDER, f"{audio_id}.{ext}")

        # 1) 로컬 파일 우선
        if os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=original_filename
            )

        # 2) Drive 파일이 있으면 서버가 프록시로 다운로드
        drive_file_id = audio.get('drive_file_id')
        if drive_file_id:
            try:
                from models import Room as RoomModel, User
                room = RoomModel.find_by_id(audio['room_id'])
                if not room:
                    return jsonify({'error': '방 정보를 찾을 수 없습니다'}), 404

                owner = User.find_by_id(room['created_by'])
                if not owner or not owner.get('google_tokens'):
                    return jsonify({'error': 'Drive 인증 정보가 없습니다'}), 403

                from drive_service import download_from_drive
                file_bytes, updated_tokens = download_from_drive(
                    owner['google_tokens'], drive_file_id
                )

                # 토큰이 갱신되었으면 DB 업데이트
                if updated_tokens:
                    User.update_google_tokens(owner['id'], updated_tokens)

                # MIME 타입 결정
                mime_map = {
                    'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'm4a': 'audio/mp4',
                    'ogg': 'audio/ogg', 'flac': 'audio/flac', 'webm': 'audio/webm',
                    'aac': 'audio/aac', 'amr': 'audio/amr', '3gp': 'audio/3gpp',
                }
                mime_type = mime_map.get(ext, 'application/octet-stream')

                from flask import Response
                return Response(
                    file_bytes,
                    mimetype=mime_type,
                    headers={
                        'Content-Disposition': "attachment; filename=\"audio.{}\"; filename*=UTF-8''{}".format(ext, url_quote(original_filename)),
                        'Content-Length': str(len(file_bytes)),
                    }
                )
            except Exception as e:
                logger.error(f"[Download] Drive 프록시 실패: audio_id={audio_id}, error={e}")
                return jsonify({'error': '파일 다운로드에 실패했습니다'}), 500

        return jsonify({'error': '파일이 만료되었거나 존재하지 않습니다'}), 404


    # ============================================================
    # 파일 썸네일 서빙
    # ============================================================
    @app.route('/api/files/<int:attachment_id>/thumbnail', methods=['GET'])
    @login_required
    def get_file_thumbnail(attachment_id):
        """이미지 파일 썸네일 서빙"""
        attachment = FileAttachment.find_by_id(attachment_id)
        if not attachment:
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
        if not Room.is_member(attachment['room_id'], g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        thumb = attachment.get('thumbnail_path')
        if thumb:
            full_path = os.path.join(Config.THUMBNAIL_FOLDER, thumb)
            if os.path.exists(full_path):
                return send_file(full_path, mimetype='image/jpeg')

        return jsonify({'error': '썸네일이 없습니다'}), 404

    # ============================================================
    # 파일 다운로드 (로컬 → Drive 프록시 fallback)
    # ============================================================
    @app.route('/api/files/<int:attachment_id>/download', methods=['GET'])
    @login_required
    def download_file(attachment_id):
        """첨부 파일 다운로드"""
        attachment = FileAttachment.find_by_id(attachment_id)
        if not attachment:
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
        if not Room.is_member(attachment['room_id'], g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        original_filename = attachment['original_filename']
        # inline=1 이면 브라우저에서 바로 보기 (이미지 풀스크린용)
        inline = request.args.get('inline') == '1'

        # 1) 로컬 파일 우선 (UPLOAD_FOLDER → FILE_FOLDER 순서)
        saved = attachment.get('saved_filename')
        if saved:
            for folder in [Config.UPLOAD_FOLDER, Config.FILE_FOLDER]:
                filepath = os.path.join(folder, saved)
                if os.path.exists(filepath):
                    return send_file(filepath, as_attachment=not inline,
                                     download_name=original_filename)

        # 2) Drive 프록시
        drive_file_id = attachment.get('drive_file_id')
        if drive_file_id:
            try:
                from models import User
                room = Room.find_by_id(attachment['room_id'])
                if not room:
                    return jsonify({'error': '방 정보를 찾을 수 없습니다'}), 404

                owner = User.find_by_id(room['created_by'])
                if not owner or not owner.get('google_tokens'):
                    return jsonify({'error': 'Drive 인증 정보가 없습니다'}), 403

                from drive_service import download_from_drive
                file_bytes, updated_tokens = download_from_drive(
                    owner['google_tokens'], drive_file_id
                )

                if updated_tokens:
                    User.update_google_tokens(owner['id'], updated_tokens)

                mime_type = attachment.get('mime_type', 'application/octet-stream')

                from flask import Response
                return Response(
                    file_bytes,
                    mimetype=mime_type,
                    headers={
                        'Content-Disposition': "{}; filename*=UTF-8''{}".format(
                            'inline' if inline else 'attachment',
                            url_quote(original_filename)),
                        'Content-Length': str(len(file_bytes)),
                    }
                )
            except Exception as e:
                logger.error(f"[Download] Drive 프록시 실패: attachment_id={attachment_id}, error={e}")
                return jsonify({'error': '파일 다운로드에 실패했습니다'}), 500

        return jsonify({'error': '파일이 만료되었거나 존재하지 않습니다'}), 404

    # ============================================================
    # 메시지 삭제 (본인 or 방장)
    # ============================================================
    @app.route('/api/messages/<int:message_id>', methods=['DELETE'])
    @login_required
    def delete_message(message_id):
        """
        메시지 삭제 — DB, Google Drive, Google Sheets, 로컬 파일 모두 정리
        권한: 본인 메시지 OR 방 admin
        """
        msg = Message.find_by_id(message_id)
        if not msg:
            return jsonify({'error': '메시지를 찾을 수 없습니다'}), 404

        room_id = msg['room_id']
        role = Room.get_member_role(room_id, g.user_id)
        if not role:
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        is_owner = msg['user_id'] == g.user_id
        is_admin = role == 'admin'
        if not is_owner and not is_admin:
            return jsonify({'error': '삭제 권한이 없습니다'}), 403

        room = Room.find_by_id(room_id)
        msg_type = msg['type']
        deleted_ids = [message_id]

        # --- 1. 음성 파일 정리 ---
        if msg_type == 'audio':
            audio = query_one(
                "SELECT * FROM audio_files WHERE message_id = %s", (message_id,)
            )
            if audio:
                # Google Drive 삭제
                if audio.get('drive_file_id'):
                    try:
                        owner = Room.get_owner(room_id)
                        if owner and owner.get('google_tokens'):
                            from drive_service import delete_from_drive
                            delete_from_drive(owner['google_tokens'], audio['drive_file_id'])
                            logger.info(f"[Delete] Drive 파일 삭제: {audio['drive_file_id']}")

                            # Google Sheets 행 삭제
                            if room.get('enable_sheets_logging') and room.get('drive_folder_id'):
                                try:
                                    from sheets_service import delete_record
                                    delete_record(
                                        owner['google_tokens'],
                                        room['drive_folder_id'],
                                        room['name'],
                                        audio['original_filename']
                                    )
                                except Exception as e:
                                    logger.warning(f"[Delete] Sheets 행 삭제 실패: {e}")
                    except Exception as e:
                        logger.warning(f"[Delete] Drive 삭제 실패: {e}")

                # 로컬 파일 삭제
                ext = audio['original_filename'].rsplit('.', 1)[1].lower() if '.' in (audio['original_filename'] or '') else 'mp3'
                local_path = os.path.join(Config.AUDIO_FOLDER, f"{audio['id']}.{ext}")
                if os.path.exists(local_path):
                    os.remove(local_path)
                    logger.info(f"[Delete] 로컬 파일 삭제: {local_path}")

                # usage_logs 정리
                from models import execute as db_execute
                db_execute("DELETE FROM usage_logs WHERE audio_file_id = %s", (audio['id'],))

        # --- 2. 첨부 파일 정리 ---
        if msg_type == 'file':
            attachment = query_one(
                "SELECT * FROM file_attachments WHERE message_id = %s", (message_id,)
            )
            if attachment and attachment.get('drive_file_id'):
                try:
                    owner = Room.get_owner(room_id)
                    if owner and owner.get('google_tokens'):
                        from drive_service import delete_from_drive
                        delete_from_drive(owner['google_tokens'], attachment['drive_file_id'])
                        logger.info(f"[Delete] Drive 첨부파일 삭제: {attachment['drive_file_id']}")
                except Exception as e:
                    logger.warning(f"[Delete] 첨부파일 Drive 삭제 실패: {e}")

        # --- 3. 자식 메시지(replies) ID 수집 ---
        replies = query_all(
            "SELECT id FROM messages WHERE parent_id = %s", (message_id,)
        )
        deleted_ids.extend([r['id'] for r in replies])

        # --- 4. DB 삭제 (CASCADE: audio_files, file_attachments, replies, reactions) ---
        # replies의 parent_id가 SET NULL이므로 명시적 삭제
        from models import execute as db_execute
        if replies:
            placeholders = ','.join(['%s'] * len(replies))
            db_execute(
                f"DELETE FROM messages WHERE id IN ({placeholders})",
                tuple(r['id'] for r in replies)
            )
        db_execute("DELETE FROM messages WHERE id = %s", (message_id,))

        logger.info(f"[Delete] 메시지 삭제 완료: msg_id={message_id}, type={msg_type}")

        # --- 5. WebSocket 알림 ---
        socketio.emit('message_deleted', {
            'message_id': message_id,
            'deleted_ids': deleted_ids,
            'room_id': room_id,
        }, room=f'room_{room_id}')

        return jsonify({'success': True, 'deleted_ids': deleted_ids})


    # ============================================================
    # 이모지 리액션 토글
    # ============================================================
    @app.route('/api/messages/<int:message_id>/reactions', methods=['POST'])
    @login_required
    def toggle_reaction(message_id):
        """
        리액션 토글 (있으면 제거, 없으면 추가)
        Request: { "emoji": "👍" }
        """
        from models import Reaction

        msg = Message.find_by_id(message_id)
        if not msg:
            return jsonify({'error': '메시지를 찾을 수 없습니다'}), 404

        if not Room.is_member(msg['room_id'], g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        data = request.get_json()
        emoji = data.get('emoji', '').strip()
        if emoji not in Reaction.ALLOWED_EMOJIS:
            return jsonify({'error': '허용되지 않는 이모지입니다'}), 400

        action, reactions = Reaction.toggle(message_id, g.user_id, emoji)

        # WebSocket 알림
        socketio.emit('reaction_updated', {
            'message_id': message_id,
            'room_id': msg['room_id'],
            'reactions': _serialize(reactions),
        }, room=f'room_{msg["room_id"]}')

        return jsonify({
            'action': action,
            'reactions': _serialize(reactions),
        })


# ============================================================
# 백그라운드 STT 처리
# ============================================================
def process_audio_background(app, socketio, filepath, audio_id, message_id,
                              room_id, user_id, user_name, original_filename, language,
                              owner_id=None, room_drive_enabled=True, room_sheets_enabled=True,
                              owner_tokens=None, room_name='Unknown', room_drive_folder_id=None):
    """
    백그라운드에서 음성 파일 처리:
    1. 파일명에서 전화번호/날짜 파싱
    2. Whisper로 STT 변환
    3. Claude API로 핵심 요약
    4. 요약 + 다운로드 안내를 자동 댓글로 달기
    5. 파일을 24시간 보관 폴더로 이동
    6. (선택) Google Drive에 백업 저장
    """
    with app.app_context():
        try:
            logger.info(f"[STT] 처리 시작: audio_id={audio_id}, file={original_filename}")

            # --- 1단계: 파일명 AI 파싱 ---
            from filename_parser import parse_filename
            parsed = parse_filename(original_filename)

            AudioFile.update_parsed(
                audio_id,
                phone_number=parsed.get('phone_number'),
                record_date=parsed.get('record_date'),
                parsed_name=parsed.get('name'),
                parsed_memo=parsed.get('memo')
            )

            # 파싱 결과 알림
            parsed_info = []
            if parsed.get('phone_number'):
                phone = parsed['phone_number']
                if len(phone) == 11:
                    phone = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                parsed_info.append(f"📞 {phone}")
            if parsed.get('record_date'):
                parsed_info.append(f"📅 {parsed['record_date']}")
            if parsed.get('name'):
                parsed_info.append(f"👤 {parsed['name']}")

            if parsed_info:
                info_text = '\n'.join(parsed_info)
                info_msg = Message.create(
                    room_id, user_id, 'system',
                    f"파일정보\n{info_text}",
                    parent_id=message_id
                )
                socketio.emit('new_message', {
                    'message': _serialize({**info_msg, 'user_name': '시스템'})
                }, room=f'room_{room_id}')

            # --- 2단계: STT 변환 (OpenAI Whisper API) ---
            AudioFile.update_status(audio_id, 'transcribing')
            socketio.emit('audio_status', {
                'audio_id': audio_id,
                'message_id': message_id,
                'status': 'transcribing',
            }, room=f'room_{room_id}')

            from whisper_service import transcribe_audio
            start_time = time.time()

            result = transcribe_audio(filepath, language=language if language != 'auto' else 'ko')

            elapsed = time.time() - start_time
            transcript_text = result['text'].strip()

            # 세그먼트 정리
            segments = result.get('segments', [])

            # 음성 길이(초) 추출 + duration_seconds DB 기록
            from billing_service import extract_audio_duration, deduct_usage
            duration_seconds = extract_audio_duration(segments)
            if duration_seconds > 0:
                from models import execute as db_execute
                db_execute(
                    "UPDATE audio_files SET duration_seconds = %s WHERE id = %s",
                    (duration_seconds, audio_id)
                )

            logger.info(f"[STT] 변환 완료: {elapsed:.1f}초, {len(transcript_text)}자, 음성길이={duration_seconds:.1f}초")

            # 과금: 방장(owner)에게 사용량 차감
            billing_user_id = owner_id or user_id
            if duration_seconds > 0:
                deduct_result = deduct_usage(billing_user_id, audio_id, duration_seconds)
                if deduct_result:
                    logger.info(f"[Billing] 차감 완료: 잔여 {deduct_result['seconds_after']:.0f}초")

            # --- 3단계: Claude API 요약 ---
            summary_text = None
            try:
                from claude_service import summarize_transcript
                socketio.emit('audio_status', {
                    'audio_id': audio_id,
                    'message_id': message_id,
                    'status': 'summarizing',
                }, room=f'room_{room_id}')

                summary_text = summarize_transcript(transcript_text, language)
                if summary_text:
                    logger.info(f"[Claude] 요약 완료: {len(summary_text)}자")
            except Exception as e:
                logger.error(f"[Claude] 요약 실패 (STT는 완료됨): {e}")

            # DB 업데이트
            AudioFile.update_transcript(audio_id, transcript_text,
                                        transcript_summary=summary_text,
                                        transcript_segments=segments)

            # --- 4단계: 파일을 보관 폴더로 이동 ---
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'mp3'
            audio_folder = Config.AUDIO_FOLDER
            os.makedirs(audio_folder, exist_ok=True)
            permanent_path = os.path.join(audio_folder, f"{audio_id}.{ext}")

            shutil.move(filepath, permanent_path)
            logger.info(f"[파일] 보관 폴더로 이동: {permanent_path}")

            # --- 5단계: (선택) Google Drive 업로드 ---
            drive_uploaded = False
            if Config.ENABLE_GOOGLE_DRIVE_BACKUP and room_drive_enabled and owner_tokens:
                try:
                    from drive_service import upload_to_drive

                    drive_result = upload_to_drive(
                        owner_tokens, permanent_path, room_name,
                        room_folder_id=room_drive_folder_id,
                        upload_filename=original_filename
                    )

                    if drive_result:
                        AudioFile.update_drive(
                            audio_id,
                            drive_result['file_id'],
                            drive_result.get('web_link', '')
                        )
                        drive_uploaded = True
                        logger.info(f"[Drive] 업로드 성공: {drive_result['file_id']}")

                        if drive_result.get('updated_tokens'):
                            from models import User
                            User.update_google_tokens(owner_id, drive_result['updated_tokens'])

                        # 폴더 최초 생성 시 멤버 권한 설정
                        if drive_result.get('folder_id') and not room_drive_folder_id:
                            from models import execute as db_execute
                            new_fid = drive_result['folder_id']
                            db_execute("UPDATE rooms SET drive_folder_id = %s WHERE id = %s",
                                       (new_fid, room_id))
                            try:
                                from drive_service import sync_folder_permissions
                                members = Room.get_members(room_id)
                                emails = [m['email'] for m in members if m['id'] != owner_id]
                                if emails:
                                    perm_results = sync_folder_permissions(owner_tokens, new_fid, emails)
                                    for m in members:
                                        if m['email'] in perm_results:
                                            Room.update_drive_permission(room_id, m['id'], perm_results[m['email']])
                            except Exception as pe:
                                logger.warning(f"[Drive] 초기 폴더 권한 설정 실패: {pe}")

                except Exception as e:
                    logger.error(f"[Drive] 업로드 실패: {e}")

            # --- 6단계: 자동 댓글 (요약 + Drive/삭제 안내) ---
            if drive_uploaded:
                if summary_text:
                    reply_content = f"{summary_text}\n\n---\n\n☁️ **Google Drive에 저장되었습니다.**"
                else:
                    reply_content = "📝 음성 변환 완료\n\n요약을 생성하지 못했습니다.\n\n---\n\n☁️ **Google Drive에 저장되었습니다.**"
            else:
                if summary_text:
                    reply_content = f"{summary_text}\n\n---\n\n⚠️ **{Config.AUDIO_RETENTION_HOURS}시간 후 파일이 삭제됩니다.** 저장이 필요하면 다운로드하세요."
                else:
                    reply_content = f"📝 음성 변환 완료\n\n요약을 생성하지 못했습니다.\n\n---\n\n⚠️ **{Config.AUDIO_RETENTION_HOURS}시간 후 파일이 삭제됩니다.** 저장이 필요하면 다운로드하세요."

            reply_msg = Message.create(
                room_id, user_id, 'transcript',
                reply_content,
                parent_id=message_id
            )

            socketio.emit('new_message', {
                'message': _serialize({
                    **reply_msg,
                    'user_name': '🤖 자동 변환',
                    'audio_id': audio_id,
                    'can_download': True,
                })
            }, room=f'room_{room_id}')

            # FCM 푸시 알림: 요약 완료/실패 시 전송
            from notification_service import notify_new_message
            if summary_text:
                notify_body = summary_text[:100] + ('...' if len(summary_text) > 100 else '')
            else:
                notify_body = f"{user_name}: 음성 요약에 실패했습니다. 원본 텍스트를 확인하세요."
            notify_new_message(room_id, user_name, notify_body,
                               msg_type='text', sender_user_id=user_id)

            _audio_status_data = {
                'audio_id': audio_id,
                'message_id': message_id,
                'status': 'completed',
                'transcript_preview': transcript_text[:100],
                'has_summary': summary_text is not None,
                'drive_uploaded': drive_uploaded,
            }
            # 과금 정보 포함 (앱에서 잔여시간 자동 갱신)
            if deduct_result:
                _audio_status_data['billing'] = {
                    'remaining_seconds': deduct_result['seconds_after'],
                    'seconds_used': deduct_result['seconds_used'],
                }
            socketio.emit('audio_status', _audio_status_data, room=f'room_{room_id}')

            # --- 7단계: (선택) Google Sheets 로깅 ---
            if drive_uploaded and room_sheets_enabled and owner_tokens:
                try:
                    from sheets_service import append_record
                    record = {
                        '날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        '파일명': original_filename,
                        '전화번호': parsed.get('phone_number', ''),
                        '이름': parsed.get('name', ''),
                        '길이(초)': f'{duration_seconds:.0f}' if duration_seconds > 0 else '',
                        '업로더': user_name,
                        '방이름': room_name,
                        '처리시간': f'{elapsed:.1f}초',
                        'Drive링크': drive_result.get('web_link', '') if drive_result else '',
                        '원본텍스트': (transcript_text[:500] if transcript_text else ''),
                        '요약': (summary_text[:500] if summary_text else ''),
                    }
                    folder_id = room_drive_folder_id or (drive_result.get('folder_id') if drive_result else None)
                    if folder_id:
                        append_record(owner_tokens, folder_id, room_name, record)
                except Exception as e:
                    logger.warning(f'[Sheets] 로깅 실패 (Drive는 정상): {e}')

            # Drive 저장 완료 시 서버 파일 삭제
            if drive_uploaded:
                try:
                    os.remove(permanent_path)
                    logger.info(f"[파일] 서버 삭제 (Drive 저장됨): {permanent_path}")
                except Exception as e:
                    logger.warning(f"[파일] 서버 삭제 실패: {e}")

            logger.info(f"[STT] 전체 처리 완료: audio_id={audio_id}")

        except Exception as e:
            logger.error(f"[STT] 처리 실패: {e}", exc_info=True)
            AudioFile.update_status(audio_id, 'failed', str(e))

            socketio.emit('audio_status', {
                'audio_id': audio_id,
                'message_id': message_id,
                'status': 'failed',
                'error': str(e),
            }, room=f'room_{room_id}')

            Message.create(
                room_id, user_id, 'system',
                f'⚠️ 음성 변환 실패: {str(e)[:100]}',
                parent_id=message_id
            )

            # FCM 푸시 알림: 변환 실패 알림
            try:
                from notification_service import notify_new_message
                notify_new_message(room_id, user_name,
                                   f"{user_name}: 음성 변환에 실패했습니다.",
                                   msg_type='text', sender_user_id=user_id)
            except Exception:
                pass

            # 실패 시에도 임시 파일 정리
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"임시 파일 삭제: {filepath}")
