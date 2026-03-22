-- ============================================================
-- Proptalk 결제/과금 테이블
-- 실행: psql -U goldenrabbit -d voiceroom -f init_billing.sql
-- ============================================================

-- 상품(플랜) 정의
CREATE TABLE IF NOT EXISTS billing_plans (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,       -- 'free', 'pack_1h', 'pack_10h', 'basic_30h', 'pro_90h'
    name VARCHAR(100) NOT NULL,             -- '무료 체험', '1시간 팩', ...
    plan_type VARCHAR(20) NOT NULL,         -- 'free', 'time_pack', 'subscription'
    minutes_included INTEGER NOT NULL,      -- 10, 60, 600, 1800, 5400
    price INTEGER NOT NULL DEFAULT 0,       -- 원 단위 (VAT 포함)
    overage_rate INTEGER DEFAULT 0,         -- 초과 시 분당 요금 (원)
    billing_cycle VARCHAR(20),              -- NULL (일회성), 'monthly'
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 사용자 잔여 시간/구독 상태
CREATE TABLE IF NOT EXISTS user_billing (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    current_plan_id INTEGER REFERENCES billing_plans(id),
    remaining_seconds FLOAT DEFAULT 600,    -- 10분 = 600초 (무료 제공)
    subscription_status VARCHAR(20) DEFAULT 'free',
        -- free, active, cancelled, expired, past_due
    subscription_started_at TIMESTAMP,
    subscription_expires_at TIMESTAMP,
    billing_key_encrypted TEXT,             -- AES-256 암호화된 Toss billingKey
    billing_key_iv TEXT,                    -- AES IV (base64)
    customer_key VARCHAR(100),              -- Toss customerKey (user_{id})
    auto_renew BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 결제 트랜잭션 (5년 보관 - 전자상거래법)
CREATE TABLE IF NOT EXISTS payment_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    plan_id INTEGER REFERENCES billing_plans(id),

    -- 주문 정보
    order_id VARCHAR(100) UNIQUE NOT NULL,  -- 우리 측 주문번호 (UUID)
    payment_key VARCHAR(200),               -- Toss paymentKey

    -- 금액
    amount INTEGER NOT NULL,                -- 결제 금액 (원)
    currency VARCHAR(10) DEFAULT 'KRW',

    -- 상태: pending, approved, failed, cancelled, refunded, partial_refund
    status VARCHAR(30) NOT NULL DEFAULT 'pending',

    -- 결제 방법
    method VARCHAR(30),                     -- card, bank_transfer, virtual_account
    card_company VARCHAR(50),
    card_number_masked VARCHAR(30),
    receipt_url TEXT,

    -- 환불
    refund_amount INTEGER DEFAULT 0,
    refund_reason TEXT,
    refunded_at TIMESTAMP,

    -- 메타
    minutes_granted INTEGER,                -- 이 결제로 부여된 분
    is_auto_billing BOOLEAN DEFAULT false,  -- 자동결제 여부
    billing_type VARCHAR(20),               -- 'one_time' or 'subscription'
    error_message TEXT,
    raw_response JSONB,                     -- Toss API 원본 응답 (감사용)

    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 사용량 차감 기록
CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    audio_file_id INTEGER REFERENCES audio_files(id),
    seconds_used FLOAT NOT NULL,            -- 이 건에서 차감된 초
    seconds_before FLOAT,                   -- 차감 전 잔여
    seconds_after FLOAT,                    -- 차감 후 잔여
    plan_code VARCHAR(50),                  -- 사용 시점 플랜
    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_user_billing_user ON user_billing(user_id);
CREATE INDEX IF NOT EXISTS idx_user_billing_status ON user_billing(subscription_status);
CREATE INDEX IF NOT EXISTS idx_user_billing_expires ON user_billing(subscription_expires_at);
CREATE INDEX IF NOT EXISTS idx_payment_tx_user ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_tx_order ON payment_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_tx_status ON payment_transactions(status);
CREATE INDEX IF NOT EXISTS idx_payment_tx_created ON payment_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created ON usage_logs(created_at);

-- 기본 플랜 데이터
INSERT INTO billing_plans (code, name, plan_type, minutes_included, price, overage_rate, billing_cycle, sort_order)
VALUES
    ('free',       '무료 체험',      'free',         10,    0,     0,  NULL,      0),
    ('pack_1h',    '1시간 팩',       'time_pack',    60,    4900,  0,  NULL,      1),
    ('pack_10h',   '10시간 팩',      'time_pack',    600,   19900, 0,  NULL,      2),
    ('basic_30h',  'Basic 30시간',   'subscription', 1800,  29900, 12, 'monthly', 3),
    ('pro_90h',    'Pro 90시간',     'subscription', 5400,  79900, 12, 'monthly', 4)
ON CONFLICT (code) DO NOTHING;
