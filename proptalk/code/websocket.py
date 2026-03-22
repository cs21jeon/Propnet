"""
WebSocket 실시간 메시지 (Flask-SocketIO)
"""
import logging
from flask_socketio import join_room, leave_room, emit
from auth import decode_token
from models import User, Room

logger = logging.getLogger(__name__)


def register_websocket(socketio):
    
    @socketio.on('connect')
    def handle_connect(auth=None):
        """WebSocket 연결 시 인증"""
        token = None
        if auth and 'token' in auth:
            token = auth['token']
        
        if not token:
            logger.warning("WebSocket 인증 실패: 토큰 없음")
            return False
        
        payload = decode_token(token)
        if not payload:
            logger.warning("WebSocket 인증 실패: 유효하지 않은 토큰")
            return False
        
        user = User.find_by_id(payload['user_id'])
        if not user:
            return False
        
        logger.info(f"WebSocket 연결: {user['name']} ({user['email']})")
        return True
    
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """채팅방 입장"""
        token = data.get('token')
        room_id = data.get('room_id')
        
        if not token or not room_id:
            return
        
        payload = decode_token(token)
        if not payload:
            return
        
        user_id = payload['user_id']
        
        # 멤버 확인
        if not Room.is_member(room_id, user_id):
            emit('error', {'message': '접근 권한이 없습니다'})
            return
        
        room_key = f'room_{room_id}'
        join_room(room_key)
        
        user = User.find_by_id(user_id)
        logger.info(f"방 입장: room={room_id}, user={user['name']}")
        
        emit('user_joined', {
            'user_id': user_id,
            'user_name': user['name'],
            'room_id': room_id,
        }, room=room_key)
    
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """채팅방 퇴장"""
        room_id = data.get('room_id')
        if room_id:
            room_key = f'room_{room_id}'
            leave_room(room_key)
            logger.info(f"방 퇴장: room={room_id}")
    
    
    @socketio.on('typing')
    def handle_typing(data):
        """타이핑 표시"""
        room_id = data.get('room_id')
        user_name = data.get('user_name')
        is_typing = data.get('is_typing', True)
        
        if room_id:
            emit('user_typing', {
                'user_name': user_name,
                'is_typing': is_typing,
            }, room=f'room_{room_id}', include_self=False)
    
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("WebSocket 연결 해제")
