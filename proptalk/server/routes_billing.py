"""
결제/과금 API 라우트
"""
import uuid
import logging
from flask import request, jsonify, g
from auth import login_required
from models_billing import BillingPlan, UserBilling, PaymentTransaction, UsageLog
from billing_service import (
    get_billing_status, ensure_user_billing, add_time,
    encrypt_billing_key, decrypt_billing_key,
)

logger = logging.getLogger(__name__)


def register_billing_routes(app):

    # ============================================================
    # 과금 상태 조회
    # ============================================================
    @app.route('/api/billing/status', methods=['GET'])
    @login_required
    def billing_status():
        """현재 사용자의 과금 상태"""
        status = get_billing_status(g.user_id)
        return jsonify(status)

    # ============================================================
    # 요금제 목록
    # ============================================================
    @app.route('/api/billing/plans', methods=['GET'])
    def billing_plans():
        """활성 요금제 목록 (공개)"""
        plans = BillingPlan.list_active()
        return jsonify({'plans': plans})

    # ============================================================
    # 주문 생성
    # ============================================================
    @app.route('/api/billing/order', methods=['POST'])
    @login_required
    def create_order():
        """
        결제 주문 생성 → order_id 반환
        Request: { "plan_code": "pack_1h" }
        """
        data = request.get_json()
        plan_code = data.get('plan_code')

        if not plan_code:
            return jsonify({'error': '요금제를 선택해주세요'}), 400

        plan = BillingPlan.find_by_code(plan_code)
        if not plan or not plan['is_active']:
            return jsonify({'error': '유효하지 않은 요금제입니다'}), 400

        if plan['plan_type'] == 'free':
            return jsonify({'error': '무료 플랜은 결제가 필요 없습니다'}), 400

        # billing 행 보장
        ensure_user_billing(g.user_id)

        order_id = f"proptalk_{g.user_id}_{uuid.uuid4().hex[:12]}"
        billing_type = 'subscription' if plan['plan_type'] == 'subscription' else 'one_time'

        tx = PaymentTransaction.create(
            user_id=g.user_id,
            plan_id=plan['id'],
            order_id=order_id,
            amount=plan['price'],
            billing_type=billing_type,
        )

        return jsonify({
            'order_id': order_id,
            'amount': plan['price'],
            'order_name': f"Proptalk {plan['name']}",
            'plan': plan,
            'billing_type': billing_type,
            'customer_key': f"user_{g.user_id}",
        })

    # ============================================================
    # 일반 결제 승인 확인 (시간팩)
    # ============================================================
    @app.route('/api/billing/confirm', methods=['POST'])
    @login_required
    def confirm_order():
        """
        Toss SDK 결제 성공 후 승인 확인
        Request: { "payment_key": "...", "order_id": "...", "amount": 9900 }
        """
        data = request.get_json()
        payment_key = data.get('payment_key')
        order_id = data.get('order_id')
        amount = data.get('amount')

        if not all([payment_key, order_id, amount]):
            return jsonify({'error': '필수 파라미터가 누락되었습니다'}), 400

        # 주문 조회
        tx = PaymentTransaction.find_by_order_id(order_id)
        if not tx:
            return jsonify({'error': '주문을 찾을 수 없습니다'}), 404
        if tx['user_id'] != g.user_id:
            return jsonify({'error': '권한이 없습니다'}), 403
        if tx['status'] != 'pending':
            return jsonify({'error': '이미 처리된 주문입니다'}), 400

        # 금액 변조 방지
        if int(amount) != tx['amount']:
            logger.warning(f"[Billing] 금액 불일치: order={order_id}, expected={tx['amount']}, got={amount}")
            return jsonify({'error': '결제 금액이 일치하지 않습니다'}), 400

        # Toss API 승인
        from toss_service import confirm_payment
        result = confirm_payment(payment_key, order_id, int(amount))

        if not result['success']:
            PaymentTransaction.fail(order_id, result.get('error'), result.get('data'))
            return jsonify({'error': result.get('error', '결제 승인 실패')}), 400

        toss_data = result['data']
        plan = BillingPlan.find_by_id(tx['plan_id'])

        # 결제 승인 기록
        PaymentTransaction.approve(
            order_id=order_id,
            payment_key=payment_key,
            method=toss_data.get('method'),
            card_company=toss_data.get('card', {}).get('issuerCode') if toss_data.get('card') else None,
            card_number_masked=toss_data.get('card', {}).get('number') if toss_data.get('card') else None,
            receipt_url=toss_data.get('receipt', {}).get('url') if toss_data.get('receipt') else None,
            minutes_granted=plan['minutes_included'] if plan else None,
            raw_response=toss_data,
        )

        # 시간 추가
        if plan:
            add_time(g.user_id, plan['id'])

        status = get_billing_status(g.user_id)

        logger.info(f"[Billing] 결제 완료: user={g.user_id}, plan={plan['code'] if plan else '?'}, amount={amount}")

        return jsonify({
            'success': True,
            'message': f"{plan['name']} 결제가 완료되었습니다." if plan else '결제가 완료되었습니다.',
            'billing_status': status,
            'receipt_url': toss_data.get('receipt', {}).get('url') if toss_data.get('receipt') else None,
        })

    # ============================================================
    # 구독 빌링키 등록 + 첫 결제
    # ============================================================
    @app.route('/api/billing/subscribe', methods=['POST'])
    @login_required
    def subscribe():
        """
        빌링키 발급 + 첫 결제
        Request: { "auth_key": "...", "order_id": "...", "plan_code": "basic_30h" }
        """
        data = request.get_json()
        auth_key = data.get('auth_key')
        order_id = data.get('order_id')
        plan_code = data.get('plan_code')

        if not all([auth_key, order_id, plan_code]):
            return jsonify({'error': '필수 파라미터가 누락되었습니다'}), 400

        plan = BillingPlan.find_by_code(plan_code)
        if not plan or plan['plan_type'] != 'subscription':
            return jsonify({'error': '유효하지 않은 구독 요금제입니다'}), 400

        customer_key = f"user_{g.user_id}"

        # 1) 빌링키 발급
        from toss_service import issue_billing_key, charge_billing_key
        billing_result = issue_billing_key(auth_key, customer_key)

        if not billing_result['success']:
            return jsonify({'error': billing_result.get('error', '카드 등록 실패')}), 400

        billing_key = billing_result['billing_key']

        # 2) 빌링키 암호화 저장
        try:
            encrypted, iv = encrypt_billing_key(billing_key)
        except Exception as e:
            logger.error(f"[Billing] 빌링키 암호화 실패: {e}")
            return jsonify({'error': '결제 정보 저장 실패'}), 500

        # 3) 첫 결제
        charge_result = charge_billing_key(
            billing_key=billing_key,
            customer_key=customer_key,
            order_id=order_id,
            amount=plan['price'],
            order_name=f"Proptalk {plan['name']}",
        )

        if not charge_result['success']:
            return jsonify({'error': charge_result.get('error', '첫 결제 실패')}), 400

        toss_data = charge_result['data']

        # 4) 결제 기록
        tx = PaymentTransaction.find_by_order_id(order_id)
        if tx:
            PaymentTransaction.approve(
                order_id=order_id,
                payment_key=toss_data.get('paymentKey'),
                method=toss_data.get('method'),
                card_company=billing_result.get('card_company'),
                card_number_masked=billing_result.get('card_number'),
                receipt_url=toss_data.get('receipt', {}).get('url') if toss_data.get('receipt') else None,
                minutes_granted=plan['minutes_included'],
                raw_response=toss_data,
            )

        # 5) 구독 활성화
        ensure_user_billing(g.user_id)
        UserBilling.activate_subscription(
            user_id=g.user_id,
            plan_id=plan['id'],
            customer_key=customer_key,
            billing_key_encrypted=encrypted,
            billing_key_iv=iv,
        )

        status = get_billing_status(g.user_id)
        logger.info(f"[Billing] 구독 활성화: user={g.user_id}, plan={plan['code']}")

        return jsonify({
            'success': True,
            'message': f"{plan['name']} 구독이 시작되었습니다.",
            'billing_status': status,
        })

    # ============================================================
    # 구독 해지
    # ============================================================
    @app.route('/api/billing/subscription/cancel', methods=['POST'])
    @login_required
    def cancel_subscription():
        """구독 해지 (auto_renew=false, 만료일까지 사용 가능)"""
        billing = UserBilling.find_by_user_id(g.user_id)
        if not billing or billing['subscription_status'] not in ('active', 'past_due'):
            return jsonify({'error': '활성 구독이 없습니다'}), 400

        UserBilling.cancel_subscription(g.user_id)
        status = get_billing_status(g.user_id)

        logger.info(f"[Billing] 구독 해지: user={g.user_id}")

        return jsonify({
            'success': True,
            'message': '구독이 해지되었습니다. 현재 기간 만료일까지 이용 가능합니다.',
            'billing_status': status,
        })

    # ============================================================
    # 환불 요청
    # ============================================================
    @app.route('/api/billing/refund', methods=['POST'])
    @login_required
    def request_refund():
        """
        환불 요청 (7일 이내, 미이용 시 전액)
        Request: { "order_id": "...", "reason": "..." }
        """
        data = request.get_json()
        order_id = data.get('order_id')
        reason = data.get('reason', '사용자 요청')

        if not order_id:
            return jsonify({'error': '주문번호가 필요합니다'}), 400

        tx = PaymentTransaction.find_by_order_id(order_id)
        if not tx or tx['user_id'] != g.user_id:
            return jsonify({'error': '주문을 찾을 수 없습니다'}), 404
        if tx['status'] != 'approved':
            return jsonify({'error': '환불 가능한 주문이 아닙니다'}), 400

        # 7일 이내 확인
        from datetime import datetime, timedelta
        if tx['completed_at'] and (datetime.now() - tx['completed_at']) > timedelta(days=7):
            return jsonify({'error': '결제 후 7일이 경과하여 환불이 불가합니다'}), 400

        # Toss 환불 API
        from toss_service import cancel_payment
        refund_result = cancel_payment(tx['payment_key'], reason)

        if not refund_result['success']:
            return jsonify({'error': refund_result.get('error', '환불 처리 실패')}), 400

        # 환불 기록
        PaymentTransaction.refund(order_id, tx['amount'], reason)

        # 시간 차감 (부여된 분만큼 회수)
        if tx.get('minutes_granted'):
            seconds_to_remove = tx['minutes_granted'] * 60
            billing = UserBilling.find_by_user_id(g.user_id)
            if billing:
                UserBilling.deduct_seconds(g.user_id, seconds_to_remove)

        logger.info(f"[Billing] 환불 완료: user={g.user_id}, order={order_id}, amount={tx['amount']}")

        return jsonify({
            'success': True,
            'message': f"{tx['amount']:,}원이 환불 처리되었습니다.",
            'billing_status': get_billing_status(g.user_id),
        })

    # ============================================================
    # 결제 이력
    # ============================================================
    @app.route('/api/billing/history', methods=['GET'])
    @login_required
    def billing_history():
        """결제 이력 조회"""
        transactions = PaymentTransaction.list_for_user(g.user_id)
        return jsonify({'transactions': transactions})

    # ============================================================
    # 사용량 이력
    # ============================================================
    @app.route('/api/billing/usage', methods=['GET'])
    @login_required
    def usage_history():
        """사용량 이력 조회"""
        logs = UsageLog.list_for_user(g.user_id)
        total = UsageLog.total_seconds_for_user(g.user_id)
        return jsonify({
            'usage_logs': logs,
            'total_seconds_used': total,
        })

    # ============================================================
    # 토스 웹훅
    # ============================================================
    @app.route('/api/billing/webhook', methods=['POST'])
    def toss_webhook():
        """
        토스페이먼츠 웹훅 수신
        결제 상태 변경 시 호출됨
        """
        from toss_service import verify_webhook_signature

        signature = request.headers.get('Toss-Signature', '')
        body = request.get_data()

        if not verify_webhook_signature(body, signature):
            logger.warning("[Billing] 웹훅 시그니처 검증 실패")
            return jsonify({'error': 'Invalid signature'}), 403

        data = request.get_json()
        event_type = data.get('eventType')

        logger.info(f"[Billing] 웹훅 수신: type={event_type}")

        if event_type == 'PAYMENT_STATUS_CHANGED':
            payload = data.get('data', {})
            order_id = payload.get('orderId')
            status = payload.get('status')

            if order_id and status:
                tx = PaymentTransaction.find_by_order_id(order_id)
                if tx:
                    if status == 'CANCELED':
                        PaymentTransaction.refund(
                            order_id,
                            payload.get('cancels', [{}])[0].get('cancelAmount', tx['amount']),
                            '토스 웹훅 취소'
                        )
                    logger.info(f"[Billing] 웹훅 처리: order={order_id}, status={status}")

        # 감사 로그
        from models import execute as db_execute
        import json
        db_execute(
            """INSERT INTO access_logs (action, resource_type, details, ip_address)
               VALUES ('webhook_toss', 'payment', %s, %s)""",
            (json.dumps(data), request.remote_addr)
        )

        return jsonify({'success': True}), 200
