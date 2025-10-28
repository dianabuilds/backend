-- Ensure subscription_plans has billing_interval with sane defaults
ALTER TABLE subscription_plans
    ADD COLUMN IF NOT EXISTS billing_interval text;

UPDATE subscription_plans
SET billing_interval = 'month'
WHERE billing_interval IS NULL;

ALTER TABLE subscription_plans
    ALTER COLUMN billing_interval SET DEFAULT 'month';

ALTER TABLE subscription_plans
    ALTER COLUMN billing_interval SET NOT NULL;

-- Ensure payment_transactions has gross_cents populated
ALTER TABLE payment_transactions
    ADD COLUMN IF NOT EXISTS gross_cents integer;

UPDATE payment_transactions
SET gross_cents = COALESCE(gross_cents, net_cents, 0);

ALTER TABLE payment_transactions
    ALTER COLUMN gross_cents SET DEFAULT 0;

ALTER TABLE payment_transactions
    ALTER COLUMN gross_cents SET NOT NULL;
