"""
토스페이먼츠 API 래퍼
https://docs.tosspayments.com/reference
"""
import hmac
import hashlib
import base64
import logging
import requests
from config import Config

logger = logging.getLogger(__name__)

TOSS_API_BASE = 'https://api.tosspayments.com/v1'


def _auth_header():
    """Basic Auth 헤더 (secret_key:)"""
    secret = Config.TOSS_SECRET_KEY
    if not secret:
        raise ValueError("TOSS_SECRET_KEY가 설정되지 않았습니다")
    encoded = base64.b64encode(f"{secret}:".encode()).decode()
    return {'Authorization': f'Basic {encoded}', 'Content-Type': 'application/json'}


# ============================================================
# 일반 결제 승인
# ============================================================

def confirm_payment(payment_key, order_id, amount):
    """
    결제 승인 확인 (Toss SDK 성공 후 서버에서 호출)
    https://docs.tosspayments.com/reference#결제-승인
    """
    url = f'{TOSS_API_BASE}/payments/confirm'
    payload = {
        'paymentKey': payment_key,
        'orderId': order_id,
        'amount': amount,
    }
    resp = requests.post(url, json=payload, headers=_auth_header(), timeout=30)
    data = resp.json()

    if resp.status_code == 200:
        logger.info(f"[Toss] 결제 승인 성공: order={order_id}, amount={amount}")
        return {'success': True, 'data': data}
    else:
        logger.error(f"[Toss] 결제 승인 실패: {data}")
        return {'success': False, 'error': data.get('message', '결제 승인 실패'), 'data': data}


# ============================================================
# 빌링키 발급 (구독용)
# ============================================================

def issue_billing_key(auth_key, customer_key):
    """
    빌링키 발급 (카드 등록 성공 후)
    https://docs.tosspayments.com/reference#빌링키-발급
    """
    url = f'{TOSS_API_BASE}/billing/authorizations/issue'
    payload = {
        'authKey': auth_key,
        'customerKey': customer_key,
    }
    resp = requests.post(url, json=payload, headers=_auth_header(), timeout=30)
    data = resp.json()

    if resp.status_code == 200:
        logger.info(f"[Toss] 빌링키 발급 성공: customer={customer_key}")
        return {
            'success': True,
            'billing_key': data.get('billingKey'),
            'card_company': data.get('card', {}).get('issuerCode'),
            'card_number': data.get('card', {}).get('number'),
            'data': data,
        }
    else:
        logger.error(f"[Toss] 빌링키 발급 실패: {data}")
        return {'success': False, 'error': data.get('message', '빌링키 발급 실패'), 'data': data}


# ============================================================
# 빌링키로 자동 결제 (구독 갱신)
# ============================================================

def charge_billing_key(billing_key, customer_key, order_id, amount, order_name):
    """
    빌링키로 자동 결제
    https://docs.tosspayments.com/reference#빌링키로-결제-승인
    """
    url = f'{TOSS_API_BASE}/billing/{billing_key}'
    payload = {
        'customerKey': customer_key,
        'orderId': order_id,
        'amount': amount,
        'orderName': order_name,
    }
    resp = requests.post(url, json=payload, headers=_auth_header(), timeout=30)
    data = resp.json()

    if resp.status_code == 200:
        logger.info(f"[Toss] 자동결제 성공: order={order_id}, amount={amount}")
        return {'success': True, 'data': data}
    else:
        logger.error(f"[Toss] 자동결제 실패: {data}")
        return {'success': False, 'error': data.get('message', '자동결제 실패'), 'data': data}


# ============================================================
# 결제 취소 (환불)
# ============================================================

def cancel_payment(payment_key, reason, cancel_amount=None):
    """
    결제 취소/환불
    cancel_amount: None이면 전액, 금액 지정 시 부분취소
    https://docs.tosspayments.com/reference#결제-취소
    """
    url = f'{TOSS_API_BASE}/payments/{payment_key}/cancel'
    payload = {'cancelReason': reason}
    if cancel_amount is not None:
        payload['cancelAmount'] = cancel_amount

    resp = requests.post(url, json=payload, headers=_auth_header(), timeout=30)
    data = resp.json()

    if resp.status_code == 200:
        logger.info(f"[Toss] 결제 취소 성공: paymentKey={payment_key}")
        return {'success': True, 'data': data}
    else:
        logger.error(f"[Toss] 결제 취소 실패: {data}")
        return {'success': False, 'error': data.get('message', '결제 취소 실패'), 'data': data}


# ============================================================
# 웹훅 시그니처 검증
# ============================================================

def verify_webhook_signature(body_bytes, signature):
    """
    Toss 웹훅 HMAC-SHA256 시그니처 검증
    """
    secret = Config.TOSS_WEBHOOK_SECRET
    if not secret:
        logger.warning("[Toss] TOSS_WEBHOOK_SECRET이 설정되지 않았습니다")
        return False

    expected = hmac.new(
        secret.encode('utf-8'),
        body_bytes,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
