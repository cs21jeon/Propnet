"""
WebSocket 실시간 메시지 (Flask-SocketIO)
"""
import logging
from flask_socketio import join_room, leave_room, emit
from auth import decode_token, verify_token
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

        user_id = _resolve_user_id(token)

        if not user_id:
            logger.warning("WebSocket 인증 실패: 유효하지 않은 토큰")
            return False

        user = User.find_by_id(user_id)
        if not user:
            logger.warning(f"WebSocket 인증 실패: user_id={user_id} 없음")
            return False

        # 개인 room에 자동 join (채팅방 밖에서도 read_update 수신용)
        personal_room = f'user_{user_id}'
        join_room(personal_room)

        logger.info(f"WebSocket 연결: {user['name']} ({user['email']}), personal_room={personal_room}")
        return True
    
    
    def _resolve_user_id(token):
        """토큰에서 proptalk local user_id 추출 (propnet_auth 우선 → 레거시 fallback)"""
        # 1차: propnet_auth JWT → service_user_links로 local_user_id 변환
        payload = verify_token(token, expected_type='access')
        if payload:
            propnet_uid = payload.get('sub')
            if propnet_uid:
                try:
                    from propnet_auth.user_service import get_service_link
                    link = get_service_link(propnet_uid, 'proptalk')
                    if link:
                        return link['local_user_id']
                except Exception as e:
                    logger.warning(f"WebSocket _resolve_user_id service_link 실패: {e}")

        # 2차: propnet_auth verify_token (type 무시) → service_user_links 변환
        payload = verify_token(token)
        if payload:
            propnet_uid = payload.get('sub')
            if propnet_uid:
                try:
                    from propnet_auth.user_service import get_service_link
                    link = get_service_link(propnet_uid, 'proptalk')
                    if link:
                        return link['local_user_id']
                except Exception:
                    pass
            # sub가 없으면 기존 JWT의 user_id (local_user_id)
            uid = payload.get('user_id')
            if uid:
                return uid

        # 3차: 기존 Proptalk JWT (레거시)
        payload = decode_token(token)
        if payload:
            return payload.get('user_id')
        return None

    @socketio.on('join_room')
    def handle_join_room(data):
        """채팅방 입장"""
        token = data.get('token')
        room_id = data.get('room_id')

        if not token or not room_id:
            return

        user_id = _resolve_user_id(token)
        if not user_id:
            return
        
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


    @socketio.on('mark_read')
    def handle_mark_read(data):
        """읽음 처리 + 상대방에게 실시간 전파"""
        token = data.get('token')
        room_id = data.get('room_id')
        message_id = data.get('message_id')
        logger.info(f"[mark_read] 수신: room_id={room_id}, message_id={message_id}")

        if not token or not room_id:
            logger.warning(f"[mark_read] 토큰 또는 room_id 없음")
            return

        user_id = _resolve_user_id(token)
        if not user_id:
            logger.warning(f"[mark_read] user_id 해석 실패")
            return

        logger.info(f"[mark_read] user_id={user_id}, room_id={room_id}")

        if not Room.is_member(room_id, user_id):
            logger.warning(f"[mark_read] user_id={user_id}는 room_id={room_id}의 멤버가 아님")
            return

        # DB 업데이트
        if message_id:
            Room.mark_read(room_id, user_id, message_id)
        else:
            from models import query_one
            latest = query_one(
                "SELECT id FROM messages WHERE room_id = %s ORDER BY id DESC LIMIT 1",
                (room_id,)
            )
            message_id = latest['id'] if latest else 0
            Room.mark_read(room_id, user_id, message_id)

        # 채팅방 멤버 전원의 개인 room으로 읽음 상태 전파
        # (상대가 채팅방 밖(목록 화면 등)에 있어도 수신 가능)
        members = Room.get_members(room_id)
        read_payload = {
            'user_id': user_id,
            'room_id': room_id,
            'last_read_message_id': message_id,
        }
        for member in members:
            if member['id'] != user_id:
                emit('read_update', read_payload, room=f'user_{member["id"]}')


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
