"""
음성파일 요약 조회 API 라우트
"""
import logging
from flask import request, jsonify, g
from auth import login_required
from models import Room, AudioFile, query_one, query_all

logger = logging.getLogger(__name__)


def register_audio_routes(app):

    @app.route('/api/audio/summaries', methods=['GET'])
    @login_required
    def list_audio_summaries():
        """사용자가 속한 모든 방의 음성파일 요약 목록 (페이지네이션, 필터)"""
        room_id = request.args.get('room_id', type=int)
        phone = request.args.get('phone')
        name = request.args.get('name')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        q = request.args.get('q')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 30, type=int)

        # 최대 100건 제한
        per_page = min(per_page, 100)

        result = AudioFile.list_summaries_for_user(
            user_id=g.user_id,
            room_id=room_id,
            phone_number=phone,
            parsed_name=name,
            date_from=date_from,
            date_to=date_to,
            query=q,
            page=page,
            per_page=per_page,
        )

        return jsonify(result)

    @app.route('/api/rooms/<int:room_id>/drive-folder', methods=['GET'])
    @login_required
    def get_room_drive_folder(room_id):
        """채팅방의 Google Drive 폴더 URL 반환"""
        # 멤버 확인
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '채팅방 멤버가 아닙니다'}), 403

        folder_id = Room.get_drive_folder_id(room_id)
        if not folder_id:
            return jsonify({'error': 'Drive 폴더가 설정되지 않았습니다'}), 404

        return jsonify({
            'drive_folder_id': folder_id,
            'drive_folder_url': f'https://drive.google.com/drive/folders/{folder_id}',
        })
