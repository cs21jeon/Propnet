-- =========================================================================
-- billing_plans AI 크레딧 번들 컬럼 추가
-- 작성일: 2026-04-21
-- 대상 DB: voiceroom (Proptalk 전용)
-- 참고: billing_plans 소유자가 postgres이므로 sudo -u postgres psql로 실행
-- =========================================================================

ALTER TABLE billing_plans ADD COLUMN IF NOT EXISTS ai_credits_bundle INTEGER NOT NULL DEFAULT 0;
COMMENT ON COLUMN billing_plans.ai_credits_bundle IS '월 AI 추천 크레딧 번들 (구독 플랜용)';

-- 플랜별 AI 크레딧 번들 횟수 (오너 확정 2026-04-21)
UPDATE billing_plans SET ai_credits_bundle = 0   WHERE code = 'free';
UPDATE billing_plans SET ai_credits_bundle = 3   WHERE code = 'pack_1h';
UPDATE billing_plans SET ai_credits_bundle = 10  WHERE code = 'pack_10h';
UPDATE billing_plans SET ai_credits_bundle = 30  WHERE code = 'basic_30h';
UPDATE billing_plans SET ai_credits_bundle = 100 WHERE code = 'pro_90h';
UPDATE billing_plans SET ai_credits_bundle = 3   WHERE code = 'agent_regular';
UPDATE billing_plans SET ai_credits_bundle = 30  WHERE code = 'agent_basic';
UPDATE billing_plans SET ai_credits_bundle = 100 WHERE code = 'agent_pro';
