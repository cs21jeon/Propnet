"""
FCM 푸시 알림 서비스 (firebase-admin)
"""
import logging
import threading
from config import Config

logger = logging.getLogger(__name__)

# Firebase Admin SDK 초기화 (lazy)
_firebase_app = None
_init_lock = threading.Lock()


def _get_firebase_app():
    """Firebase Admin SDK lazy 초기화"""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    with _init_lock:
        if _firebase_app is not None:
            return _firebase_app

        try:
            import firebase_admin
            from firebase_admin import credentials

            cred_path = Config.FCM_SERVICE_ACCOUNT_FILE
            if not cred_path:
                logger.warning("FCM_SERVICE_ACCOUNT_FILE 미설정 — 푸시 알림 비활성화")
                return None

            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK 초기화 완료")
            return _firebase_app
        except Exception as e:
            logger.error(f"Firebase Admin SDK 초기화 실패: {e}")
            return None


def send_push_to_users(user_ids, title, body, data=None, exclude_user_id=None):
    """
    특정 사용자들에게 FCM 푸시 알림 전송 (백그라운드 스레드)

    Args:
        user_ids: 알림 대상 user_id 목록
        title: 알림 제목
        body: 알림 본문
        data: 추가 데이터 (딥링크 등)
        exclude_user_id: 제외할 user_id (메시지 발신자)
    """
    thread = threading.Thread(
        target=_send_push_sync,
        args=(user_ids, title, body, data, exclude_user_id),
        daemon=True,
    )
    thread.start()


def _send_push_sync(user_ids, title, body, data, exclude_user_id):
    """실제 FCM 전송 (동기)"""
    app = _get_firebase_app()
    if app is None:
        return

    try:
        from firebase_admin import messaging
        from models import DeviceToken

        # 발신자 제외
        target_ids = [uid for uid in user_ids if uid != exclude_user_id]
        if not target_ids:
            return

        tokens_rows = DeviceToken.get_tokens_for_users(target_ids)
        if not tokens_rows:
            return

        fcm_tokens = [row['fcm_token'] for row in tokens_rows]

        # 데이터 페이로드 (문자열만 허용)
        str_data = {}
        if data:
            str_data = {k: str(v) for k, v in data.items()}

        # 멀티캐스트 전송 (최대 500개씩)
        for i in range(0, len(fcm_tokens), 500):
            batch = fcm_tokens[i:i + 500]
            message = messaging.MulticastMessage(
                tokens=batch,
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=str_data,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='proptalk_messages',
                        click_action='FLUTTER_NOTIFICATION_CLICK',
                    ),
                ),
            )

            response = messaging.send_each_for_multicast(message, app=app)
            logger.info(
                f"FCM 전송: 성공={response.success_count}, "
                f"실패={response.failure_count}"
            )

            # 유효하지 않은 토큰 정리
            for idx, send_resp in enumerate(response.responses):
                if send_resp.exception is not None:
                    error_code = getattr(send_resp.exception, 'code', '')
                    if error_code in (
                        'NOT_FOUND', 'UNREGISTERED', 'INVALID_ARGUMENT'
                    ):
                        DeviceToken.delete_by_token(batch[idx])
                        logger.info(f"유효하지 않은 FCM 토큰 삭제: {batch[idx][:20]}...")

    except Exception as e:
        logger.error(f"FCM 전송 오류: {e}")


# ============================================================
# 과금 알림
# ============================================================

def notify_low_balance(user_id, remaining_seconds):
    """잔여 시간 부족 알림 (5분 이하 진입 시 1회)"""
    mins = max(0, int(remaining_seconds / 60))
    send_push_to_users(
        user_ids=[user_id],
        title='Proptalk 잔여 시간 알림',
        body=f'잔여 시간이 {mins}분 남았습니다. 충전 후 이용해주세요.',
        data={'type': 'billing_low_balance', 'remaining_seconds': str(int(remaining_seconds))},
    )
    logger.info(f"[Billing] 잔여시간 부족 알림: user={user_id}, remaining={remaining_seconds:.0f}s")


def notify_time_exhausted(user_id):
    """이용 시간 소진 알림"""
    send_push_to_users(
        user_ids=[user_id],
        title='Proptalk 이용 시간 소진',
        body='이용 시간이 모두 소진되었습니다. 충전 후 이용해주세요.',
        data={'type': 'billing_exhausted'},
    )
    logger.info(f"[Billing] 시간 소진 알림: user={user_id}")


def notify_subscription_expiring(user_id, days_remaining):
    """구독 만료 임박 알림 (3일 전)"""
    send_push_to_users(
        user_ids=[user_id],
        title='Proptalk 구독 만료 예정',
        body=f'{days_remaining}일 후 구독이 만료됩니다. 갱신하시려면 결제 수단을 확인해주세요.',
        data={'type': 'billing_expiring', 'days': str(days_remaining)},
    )
    logger.info(f"[Billing] 구독 만료 임박 알림: user={user_id}, days={days_remaining}")


def notify_renewal_failed(user_id):
    """자동결제 실패 알림"""
    send_push_to_users(
        user_ids=[user_id],
        title='Proptalk 자동결제 실패',
        body='구독 갱신 결제에 실패했습니다. 결제 수단을 확인해주세요.',
        data={'type': 'billing_renewal_failed'},
    )
    logger.info(f"[Billing] 갱신 실패 알림: user={user_id}")


# ============================================================
# 채팅 알림
# ============================================================

def notify_new_message(room_id, sender_name, content, msg_type='text',
                       sender_user_id=None):
    """
    톡방 새 메시지 알림 전송

    Args:
        room_id: 채팅방 ID
        sender_name: 발신자 이름
        content: 메시지 내용
        msg_type: 메시지 타입 (text/audio/file)
        sender_user_id: 발신자 user_id (알림 제외 대상)
    """
    from models import Room

    # 방 멤버 목록 조회
    members = Room.get_members(room_id)
    member_ids = [m['id'] for m in members]

    room = Room.find_by_id(room_id)
    room_name = room['name'] if room else '톡방'

    # 알림 본문 구성
    if msg_type == 'audio':
        body = f"{sender_name}: 음성 파일을 업로드했습니다"
    elif msg_type == 'file':
        body = f"{sender_name}: 파일을 공유했습니다"
    else:
        # 텍스트: 최대 100자
        preview = content[:100] + ('...' if len(content) > 100 else '')
        body = f"{sender_name}: {preview}"

    send_push_to_users(
        user_ids=member_ids,
        title=room_name,
        body=body,
        data={
            'type': 'new_message',
            'room_id': room_id,
            'room_name': room_name,
        },
        exclude_user_id=sender_user_id,
    )
