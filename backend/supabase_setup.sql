-- Run in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS policies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_number TEXT UNIQUE NOT NULL,
  holder_name TEXT NOT NULL,
  coverage_type TEXT NOT NULL,
  coverage_limit DECIMAL NOT NULL,
  deductible DECIMAL NOT NULL,
  is_active BOOLEAN DEFAULT true,
  expiry_date DATE NOT NULL
);

INSERT INTO policies (policy_number, holder_name, coverage_type, coverage_limit, deductible, is_active, expiry_date)
VALUES
  ('POL-001', 'Alice Johnson', 'comprehensive', 50000.00, 500.00, true, '2026-12-31'),
  ('POL-002', 'Bob Martinez', 'collision', 30000.00, 1000.00, true, '2026-06-30'),
  ('POL-003', 'Carol Williams', 'third-party', 15000.00, 250.00, true, '2026-09-30'),
  ('POL-004', 'David Lee', 'comprehensive', 75000.00, 750.00, false, '2024-12-31'),
  ('POL-005', 'Emily Chen', 'fire', 40000.00, 500.00, true, '2026-12-31')
ON CONFLICT (policy_number) DO NOTHING;

CREATE TABLE IF NOT EXISTS claims (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_number TEXT NOT NULL,
  claimant_name TEXT NOT NULL,
  incident_type TEXT NOT NULL,
  incident_description TEXT NOT NULL,
  photo_urls JSONB DEFAULT '[]',
  policy_valid BOOLEAN,
  policy_holder_name TEXT,
  coverage_type TEXT,
  coverage_limit DECIMAL,
  deductible DECIMAL,
  damage_description TEXT,
  estimated_repair_cost DECIMAL,
  damage_severity TEXT,
  fraud_risk TEXT,
  fraud_flags JSONB DEFAULT '[]',
  decision TEXT CHECK (decision IN ('approved', 'denied', 'escalated')),
  decision_reason TEXT,
  payout_amount DECIMAL,
  email_draft TEXT,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Storage bucket instructions (Dashboard > Storage):
-- 1) Create bucket: claim-photos
-- 2) Public bucket: enabled
-- 3) Allowed MIME types: image/jpeg, image/png, image/webp
