-- =========================================================================
-- PropMap AI 크레딧 과금 시스템 - DB 마이그레이션 v1
-- 작성일: 2026-04-21
-- 대상 DB: goldenrabbit_db
-- 목적: AI 매물 추천 크레딧 지갑/원장/팩상품/주문 테이블 생성
-- 의존: propnet_users(id) 테이블 존재 필수
-- 롤백: 파일 하단 ROLLBACK 블록 참조
-- =========================================================================

BEGIN;

-- -------------------------------------------------------------------------
-- 1) ai_credit_wallet : 크레딧 지갑 (propnet_uid 1:1)
-- -------------------------------------------------------------------------
-- 차감 우선순위: free → bundle → pack
-- balance_free   : 가입 보너스 (평생 1회, 재가입 시 추가 지급 없음)
-- balance_bundle : 월 번들 (매월 1일 리필, 구독 해지 시 즉시 소멸, 이월 없음)
-- balance_pack   : 유료 크레딧 팩 (영구 이월)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_credit_wallet (
    propnet_uid         INTEGER PRIMARY KEY REFERENCES propnet_users(id),
    balance_free        INTEGER NOT NULL DEFAULT 0,
    balance_bundle      INTEGER NOT NULL DEFAULT 0,
    balance_pack        INTEGER NOT NULL DEFAULT 0,
    signup_bonus_given  BOOLEAN NOT NULL DEFAULT FALSE,
    bundle_reset_at     DATE,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  ai_credit_wallet IS 'AI 매물 추천 크레딧 지갑. propnet_uid당 1행.';
COMMENT ON COLUMN ai_credit_wallet.balance_free IS '가입 보너스 잔여 (평생 1회 지급)';
COMMENT ON COLUMN ai_credit_wallet.balance_bundle IS '월 번들 잔여 (매월 리필, 이월 없음)';
COMMENT ON COLUMN ai_credit_wallet.balance_pack IS '유료 팩 잔여 (영구 이월)';
COMMENT ON COLUMN ai_credit_wallet.bundle_reset_at IS '마지막 번들 리필 월 (YYYY-MM-DD)';

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION ai_credit_wallet_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_acw_touch ON ai_credit_wallet;
CREATE TRIGGER trg_acw_touch
BEFORE UPDATE ON ai_credit_wallet
FOR EACH ROW EXECUTE FUNCTION ai_credit_wallet_touch_updated_at();


-- -------------------------------------------------------------------------
-- 2) ai_credit_ledger : 크레딧 이동 로그 (모든 +/- 기록)
-- -------------------------------------------------------------------------
-- source_type: 'signup' | 'bundle' | 'pack' | 'search_use' | 'admin' | 'refund' | 'cancel_bundle'
-- delta: +는 충전/지급, -는 차감
-- balance_snapshot: 차감/지급 후 {free, bundle, pack} 스냅샷
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_credit_ledger (
    id               BIGSERIAL PRIMARY KEY,
    propnet_uid      INTEGER NOT NULL,
    delta            INTEGER NOT NULL,
    source_type      VARCHAR(24) NOT NULL,
    source_ref       VARCHAR(128),
    balance_snapshot JSONB,
    note             TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  ai_credit_ledger IS 'AI 크레딧 이동 원장. 모든 충전/차감을 불변 기록.';
COMMENT ON COLUMN ai_credit_ledger.source_type IS 'signup|bundle|pack|search_use|admin|refund|cancel_bundle';
COMMENT ON COLUMN ai_credit_ledger.source_ref IS '세션ID / 주문ID / 플랜코드 / 관리자이메일 등';

CREATE INDEX IF NOT EXISTS idx_aicl_uid_time
    ON ai_credit_ledger (propnet_uid, created_at DESC);

-- 세션당 중복 차감 방지 (search_use에 대해서만 source_ref UNIQUE)
CREATE UNIQUE INDEX IF NOT EXISTS idx_aicl_search_once
    ON ai_credit_ledger (source_ref)
    WHERE source_type = 'search_use';


-- -------------------------------------------------------------------------
-- 3) ai_credit_packs : 크레딧 팩 상품 마스터
-- -------------------------------------------------------------------------
-- 현재(2026-04-21) 오너 확정: 별도 팩 판매 없음. 기존 Proptalk 요금제에 번들만.
-- 향후 AI 전용 소액 팩 도입 시 활성화. 스키마만 준비.
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_credit_packs (
    code         VARCHAR(32) PRIMARY KEY,
    name         VARCHAR(64) NOT NULL,
    credits      INTEGER NOT NULL,
    price_krw    INTEGER NOT NULL,
    is_active    BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order   INTEGER DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE ai_credit_packs IS 'AI 크레딧 팩 상품 마스터. 향후 단독 팩 판매 시 사용.';

-- 시드 데이터 (비활성 상태로 준비)
INSERT INTO ai_credit_packs (code, name, credits, price_krw, is_active, sort_order)
VALUES
    ('ai_pack_5',   'AI 추천 5회',   5,   3000,  FALSE, 1),
    ('ai_pack_20',  'AI 추천 20회',  20,  9900,  FALSE, 2),
    ('ai_pack_50',  'AI 추천 50회',  50,  19900, FALSE, 3)
ON CONFLICT (code) DO NOTHING;


-- -------------------------------------------------------------------------
-- 4) ai_credit_orders : 팩 주문/결제 (Toss 연동)
-- -------------------------------------------------------------------------
-- 현재는 번들 전용이므로 사용하지 않으나, 향후 팩 판매 시 Toss 결제 연동용.
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_credit_orders (
    order_id      VARCHAR(64) PRIMARY KEY,
    propnet_uid   INTEGER NOT NULL,
    pack_code     VARCHAR(32) NOT NULL,
    credits       INTEGER NOT NULL,
    amount_krw    INTEGER NOT NULL,
    payment_key   VARCHAR(128),
    status        VARCHAR(16) NOT NULL DEFAULT 'pending',
    approved_at   TIMESTAMPTZ,
    raw_response  JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  ai_credit_orders IS 'AI 크레딧 팩 주문. Toss 결제 연동.';
COMMENT ON COLUMN ai_credit_orders.status IS 'pending|paid|failed|refunded';

CREATE INDEX IF NOT EXISTS idx_aico_uid_time
    ON ai_credit_orders (propnet_uid, created_at DESC);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION ai_credit_orders_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_aico_touch ON ai_credit_orders;
CREATE TRIGGER trg_aico_touch
BEFORE UPDATE ON ai_credit_orders
FOR EACH ROW EXECUTE FUNCTION ai_credit_orders_touch_updated_at();


COMMIT;

-- =========================================================================
-- ROLLBACK (필요 시 수동 실행)
-- =========================================================================
-- BEGIN;
-- DROP TRIGGER  IF EXISTS trg_aico_touch ON ai_credit_orders;
-- DROP FUNCTION IF EXISTS ai_credit_orders_touch_updated_at();
-- DROP TRIGGER  IF EXISTS trg_acw_touch ON ai_credit_wallet;
-- DROP FUNCTION IF EXISTS ai_credit_wallet_touch_updated_at();
-- DROP TABLE IF EXISTS ai_credit_orders;
-- DROP TABLE IF EXISTS ai_credit_packs;
-- DROP TABLE IF EXISTS ai_credit_ledger;
-- DROP TABLE IF EXISTS ai_credit_wallet;
-- COMMIT;
