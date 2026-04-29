"""
AI 크레딧 과금 API Blueprint.

경로 (app.py에서 url_prefix='/api'로 등록)
  GET  /api/ai/billing/status  : 잔여 크레딧 조회

인증: propnet_token 쿠키 (propnet.kr SSO)
"""

from __future__ import annotations

import logging
import sys
from functools import wraps

from flask import Blueprint, g, jsonify, request

sys.path.insert(0, '/home/webapp/goldenrabbit/backend/shared')
from propnet_auth.jwt_utils import verify_token  # noqa: E402

from psycopg2.extras import RealDictCursor  # noqa: E402
from services.database_service import get_db_connection  # noqa: E402
from services import ai_billing_service as billing  # noqa: E402

logger = logging.getLogger(__name__)

bp = Blueprint("ai_billing", __name__)


# -----------------------------------------------------------------------------
# 인증 데코레이터 — propnet 로그인 필수
# -----------------------------------------------------------------------------

def propnet_login_required(fn):
    """propnet_token 쿠키로 인증. g.propnet_user_id, g.propnet_role 설정."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.cookies.get('propnet_token')
        if not token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
        if not token:
            return jsonify({'error': 'unauthorized', 'detail': 'login required'}), 401

        try:
            payload = verify_token(token, expected_type='access')
        except Exception:
            return jsonify({'error': 'unauthorized', 'detail': 'invalid token'}), 401

        if not payload:
            return jsonify({'error': 'unauthorized', 'detail': 'invalid token'}), 401

        g.propnet_user_id = payload.get('sub')
        g.propnet_role = payload.get('role', 'user')
        return fn(*args, **kwargs)
    return wrapper


# -----------------------------------------------------------------------------
# GET /api/ai/billing/status — 잔여 크레딧 조회
# -----------------------------------------------------------------------------

@bp.route("/ai/billing/status", methods=["GET"])
@propnet_login_required
def credit_status():
    uid = g.propnet_user_id
    role = g.propnet_role

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            status = billing.get_credit_status(cur, uid, role=role)
    return jsonify(status)
