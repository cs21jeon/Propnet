"""
채팅방 API 라우트
"""
import string
import random
import logging
from flask import request, jsonify, g
from auth import login_required
from models import Room, Message

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
        
        # 채팅방 생성
        room = Room.create(name, description, g.user_id, invite_code)
        
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
        
        # 시스템 메시지
        Message.create(room['id'], g.user_id, 'system',
                       f'{g.user["name"]}님이 참여했습니다.')
        
        logger.info(f"채팅방 참여: room={room['id']} user={g.user['email']}")
        
        return jsonify({'room': room})
    
    
    @app.route('/api/rooms/<int:room_id>/members', methods=['GET'])
    @login_required
    def get_room_members(room_id):
        """채팅방 멤버 목록"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403
        
        members = Room.get_members(room_id)
        return jsonify({'members': members})
