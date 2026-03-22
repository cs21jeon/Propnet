"""
채팅방 API 라우트
"""
import string
import random
import logging
from flask import request, jsonify, g
from auth import login_required
from models import Room, Message, User, query_one
from drive_service import add_folder_permission, remove_folder_permission

logger = logging.getLogger(__name__)


def generate_invite_code(length=8):
    """초대 코드 생성"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


def register_room_routes(app):
    
    @app.route('/api/rooms', methods=['GET'])
    @login_required
    def list_rooms():
        """내가 참여한 채팅방 목록"""
        rooms = Room.list_for_user(g.user_id)
        return jsonify({'rooms': rooms})
    
    
    @app.route('/api/rooms', methods=['POST'])
    @login_required
    def create_room():
        """
        채팅방 생성
        
        Request:
            { "name": "부동산 상담방", "description": "..." }
        """
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'error': '채팅방 이름이 필요합니다'}), 400
        
        description = data.get('description', '')
        invite_code = generate_invite_code()
        
        enable_drive_backup = data.get('enable_drive_backup', True)
        enable_sheets_logging = data.get('enable_sheets_logging', True)

        # 채팅방 생성
        room = Room.create(name, description, g.user_id, invite_code,
                           enable_drive_backup=enable_drive_backup,
                           enable_sheets_logging=enable_sheets_logging)
        
        # 생성자를 admin으로 추가
        Room.add_member(room['id'], g.user_id, role='admin')
        
        # 시스템 메시지
        Message.create(room['id'], g.user_id, 'system', 
                       f'{g.user["name"]}님이 채팅방을 만들었습니다.')
        
        logger.info(f"채팅방 생성: {name} (by {g.user['email']})")
        
        return jsonify({
            'room': room,
            'invite_code': invite_code,
        }), 201
    
    
    @app.route('/api/rooms/<int:room_id>', methods=['GET'])
    @login_required
    def get_room(room_id):
        """채팅방 상세 정보"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403
        
        room = Room.find_by_id(room_id)
        if not room:
            return jsonify({'error': '채팅방을 찾을 수 없습니다'}), 404
        
        members = Room.get_members(room_id)
        
        return jsonify({
            'room': room,
            'members': members,
        })
    
    
    @app.route('/api/rooms/join', methods=['POST'])
    @login_required
    def join_room():
        """
        초대 코드로 채팅방 참여
        
        Request:
            { "invite_code": "ABC12345" }
        """
        data = request.get_json()
        code = data.get('invite_code', '').strip().upper()
        
        if not code:
            return jsonify({'error': '초대 코드가 필요합니다'}), 400
        
        room = Room.find_by_invite_code(code)
        if not room:
            return jsonify({'error': '유효하지 않은 초대 코드입니다'}), 404
        
        # 이미 멤버인지 확인
        if Room.is_member(room['id'], g.user_id):
            return jsonify({'room': room, 'message': '이미 참여한 채팅방입니다'})
        
        # 참여
        Room.add_member(room['id'], g.user_id, role='member')

        # Drive 폴더 권한 추가 (폴더가 있는 경우만)
        folder_id = Room.get_drive_folder_id(room['id'])
        if folder_id:
            try:
                owner = Room.get_owner(room['id'])
                if owner:
                    owner_tokens = User.get_google_tokens(owner['id'])
                    if owner_tokens:
                        perm_id = add_folder_permission(
                            owner_tokens, folder_id, g.user['email']
                        )
                        if perm_id:
                            Room.update_drive_permission(
                                room['id'], g.user_id, perm_id
                            )
            except Exception as e:
                logger.warning(f"Drive 권한 추가 실패 (참여는 정상): {e}")

        # 시스템 메시지
        Message.create(room['id'], g.user_id, 'system',
                       f'{g.user["name"]}님이 참여했습니다.')

        logger.info(f"채팅방 참여: room={room['id']} user={g.user['email']}")

        return jsonify({'room': room})
    
    
    def _remove_member_drive_permission(room_id, user_id):
        """멤버의 Drive 폴더 권한 제거 (내부 헬퍼)"""
        try:
            member = query_one(
                "SELECT drive_permission_id FROM room_members WHERE room_id = %s AND user_id = %s",
                (room_id, user_id)
            )
            if not member or not member.get('drive_permission_id'):
                return

            folder_id = Room.get_drive_folder_id(room_id)
            if not folder_id:
                return

            owner = Room.get_owner(room_id)
            if not owner:
                return

            owner_tokens = User.get_google_tokens(owner['id'])
            if owner_tokens:
                remove_folder_permission(
                    owner_tokens, folder_id, member['drive_permission_id']
                )
        except Exception as e:
            logger.warning(f"Drive 권한 삭제 실패: {e}")

    @app.route('/api/rooms/<int:room_id>/leave', methods=['POST'])
    @login_required
    def leave_room(room_id):
        """채팅방 나가기 (관리자는 나갈 수 없음)"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '채팅방 멤버가 아닙니다'}), 404

        member = query_one(
            "SELECT role FROM room_members WHERE room_id = %s AND user_id = %s",
            (room_id, g.user_id)
        )
        if member and member['role'] == 'admin':
            return jsonify({'error': '방장은 채팅방을 나갈 수 없습니다'}), 400

        # Drive 권한 제거
        _remove_member_drive_permission(room_id, g.user_id)

        # 멤버 제거
        Room.remove_member(room_id, g.user_id)

        # 시스템 메시지
        Message.create(room_id, g.user_id, 'system',
                       f'{g.user["name"]}님이 나갔습니다.')

        logger.info(f"채팅방 퇴장: room={room_id} user={g.user['email']}")
        return jsonify({'ok': True})

    @app.route('/api/rooms/<int:room_id>/members/<int:user_id>', methods=['DELETE'])
    @login_required
    def kick_member(room_id, user_id):
        """멤버 강퇴 (관리자 전용)"""
        # 관리자 확인
        admin = query_one(
            "SELECT role FROM room_members WHERE room_id = %s AND user_id = %s",
            (room_id, g.user_id)
        )
        if not admin or admin['role'] != 'admin':
            return jsonify({'error': '관리자만 강퇴할 수 있습니다'}), 403

        # 자기 자신은 강퇴 불가
        if user_id == g.user_id:
            return jsonify({'error': '자기 자신은 강퇴할 수 없습니다'}), 400

        if not Room.is_member(room_id, user_id):
            return jsonify({'error': '해당 멤버를 찾을 수 없습니다'}), 404

        # 강퇴 대상 정보
        target = User.find_by_id(user_id)

        # Drive 권한 제거
        _remove_member_drive_permission(room_id, user_id)

        # 멤버 제거
        Room.remove_member(room_id, user_id)

        # 시스템 메시지
        target_name = target['name'] if target else '알 수 없는 사용자'
        Message.create(room_id, g.user_id, 'system',
                       f'{target_name}님이 내보내졌습니다.')

        logger.info(f"멤버 강퇴: room={room_id} target={user_id}")
        return jsonify({'ok': True})

    @app.route('/api/rooms/<int:room_id>', methods=['PATCH'])
    @login_required
    def rename_room(room_id):
        """채팅방 이름 변경 (admin 전용)"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        member = query_one(
            "SELECT role FROM room_members WHERE room_id = %s AND user_id = %s",
            (room_id, g.user_id)
        )
        if not member or member['role'] != 'admin':
            return jsonify({'error': '관리자만 이름을 변경할 수 있습니다'}), 403

        data = request.get_json()
        new_name = data.get('name', '').strip()
        if not new_name:
            return jsonify({'error': '새 이름이 필요합니다'}), 400

        room = Room.rename(room_id, new_name)
        if not room:
            return jsonify({'error': '채팅방을 찾을 수 없습니다'}), 404

        Message.create(room_id, g.user_id, 'system',
                       f'채팅방 이름이 "{new_name}"(으)로 변경되었습니다.')

        logger.info(f"채팅방 이름 변경: room={room_id}, new_name={new_name}")
        return jsonify({'room': room})

    @app.route('/api/rooms/<int:room_id>/settings', methods=['PATCH'])
    @login_required
    def update_room_settings(room_id):
        """채팅방 설정 변경 (admin 전용)"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        # admin 확인
        from models import query_one
        member = query_one(
            "SELECT role FROM room_members WHERE room_id = %s AND user_id = %s",
            (room_id, g.user_id)
        )
        if not member or member['role'] != 'admin':
            return jsonify({'error': '관리자만 설정을 변경할 수 있습니다'}), 403

        data = request.get_json()
        room = Room.update_settings(
            room_id,
            enable_drive_backup=data.get('enable_drive_backup'),
            enable_sheets_logging=data.get('enable_sheets_logging'),
        )
        return jsonify({'room': room})

    @app.route('/api/rooms/<int:room_id>/members', methods=['GET'])
    @login_required
    def get_room_members(room_id):
        """채팅방 멤버 목록"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        members = Room.get_members(room_id)
        return jsonify({'members': members})

    @app.route('/api/rooms/<int:room_id>', methods=['DELETE'])
    @login_required
    def delete_room(room_id):
        """채팅방 삭제 (admin 전용)"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        member = query_one(
            "SELECT role FROM room_members WHERE room_id = %s AND user_id = %s",
            (room_id, g.user_id)
        )
        if not member or member['role'] != 'admin':
            return jsonify({'error': '관리자만 삭제할 수 있습니다'}), 403

        room = Room.find_by_id(room_id)
        if not room:
            return jsonify({'error': '채팅방을 찾을 수 없습니다'}), 404

        Room.delete(room_id)
        logger.info(f"채팅방 삭제: room={room_id} (by {g.user['email']})")

        return jsonify({'message': '채팅방이 삭제되었습니다.'}), 200
