-- AI Financial Statement Generation System Database Schema
-- Supabase PostgreSQL Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Reports table: Store processed data, edits, and metadata
CREATE TABLE reports (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  year INTEGER DEFAULT 2025,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'processing', 'ready', 'finalized', 'error')),
  raw_data JSONB,  -- Healed/mapped DataFrame as JSON
  edited_data JSONB,  -- Post-edit changes
  mapping JSONB,  -- Semantic mapping output
  qa_report JSONB,  -- Grok audit results
  file_path TEXT,  -- Original file path
  file_type TEXT,  -- 'pdf' or 'excel'
  processing_log JSONB,  -- Step-by-step processing log
  error_message TEXT,  -- Error details if status is 'error'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for reports table
CREATE INDEX idx_reports_user ON reports(user_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_year ON reports(year);
CREATE INDEX idx_reports_created_at ON reports(created_at);

-- Verification table: Steps + math proofs for audit trail
CREATE TABLE verifications (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
  steps JSONB,  -- Array: [{"step": 1, "model": "gemini-2.5-pro", "input_hash": "...", "output_summary": "...", "latency_seconds": 1.23}]
  math_proofs JSONB,  -- e.g., {"trial_balance": "∑Debits=12345.67 == ∑Credits=12345.67", "ratios": {"current": "Assets/Liabilities=2.1"}}
  cert_hash TEXT,  -- SHA256 of certificate PDF
  cert_file_path TEXT,  -- Path to generated certificate
  overall_score DECIMAL(5,2),  -- Overall confidence score
  compliance_status TEXT,  -- 'PASS', 'FAIL', 'REVIEW'
  signed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for verifications table
CREATE INDEX idx_verifications_report ON verifications(report_id);
CREATE INDEX idx_verifications_compliance ON verifications(compliance_status);

-- Cache table: For AI model response caching
CREATE TABLE ai_cache (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  input_hash TEXT UNIQUE NOT NULL,  -- SHA256 hash of input
  model_name TEXT NOT NULL,  -- 'gemini-2.5-pro', 'gemini-2.5-flash', 'grok-4-fast'
  response JSONB NOT NULL,  -- Cached response
  token_count INTEGER,  -- Number of tokens used
  cost_usd DECIMAL(10,4),  -- Cost in USD
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()  -- TTL for cache entry
);

-- Create indexes for cache table
CREATE INDEX idx_ai_cache_hash ON ai_cache(input_hash);
CREATE INDEX idx_ai_cache_model ON ai_cache(model_name);
CREATE INDEX idx_ai_cache_expires ON ai_cache(expires_at);

-- Metrics table: For monitoring and analytics
CREATE TABLE metrics (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
  model_name TEXT NOT NULL,
  operation_type TEXT NOT NULL,  -- 'extraction', 'mapping', 'generation', 'audit'
  latency_seconds DECIMAL(8,3),
  token_count INTEGER,
  cost_usd DECIMAL(10,4),
  success BOOLEAN DEFAULT true,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for metrics table
CREATE INDEX idx_metrics_report ON metrics(report_id);
CREATE INDEX idx_metrics_model ON metrics(model_name);
CREATE INDEX idx_metrics_operation ON metrics(operation_type);
CREATE INDEX idx_metrics_created_at ON metrics(created_at);

-- User preferences table
CREATE TABLE user_preferences (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  default_format JSONB,  -- Default formatting preferences
  notification_settings JSONB,  -- Email/push notification preferences
  auto_save BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create unique index for user preferences
CREATE UNIQUE INDEX idx_user_preferences_user ON user_preferences(user_id);

-- Enable Row Level Security
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- RLS Policies for reports table
CREATE POLICY "Users can view own reports" ON reports FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own reports" ON reports FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own reports" ON reports FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own reports" ON reports FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for verifications table
CREATE POLICY "Users can view own verifications" ON verifications FOR SELECT USING (
  auth.uid() = (SELECT user_id FROM reports WHERE id = report_id)
);
CREATE POLICY "Users can insert own verifications" ON verifications FOR INSERT WITH CHECK (
  auth.uid() = (SELECT user_id FROM reports WHERE id = report_id)
);

-- RLS Policies for user_preferences table
CREATE POLICY "Users can manage own preferences" ON user_preferences FOR ALL USING (auth.uid() = user_id);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM ai_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Views for common queries
CREATE VIEW user_reports_summary AS
SELECT 
    r.id,
    r.user_id,
    r.year,
    r.status,
    r.file_type,
    r.created_at,
    r.updated_at,
    v.compliance_status,
    v.overall_score
FROM reports r
LEFT JOIN verifications v ON r.id = v.report_id;

CREATE VIEW system_metrics AS
SELECT 
    model_name,
    operation_type,
    COUNT(*) as total_requests,
    AVG(latency_seconds) as avg_latency,
    SUM(token_count) as total_tokens,
    SUM(cost_usd) as total_cost,
    COUNT(*) FILTER (WHERE success = true) as success_count,
    COUNT(*) FILTER (WHERE success = false) as error_count
FROM metrics
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY model_name, operation_type;

-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON reports TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON verifications TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_preferences TO authenticated;
GRANT SELECT ON user_reports_summary TO authenticated;
GRANT SELECT ON system_metrics TO authenticated;

-- Grant permissions to service role for backend operations
GRANT ALL ON reports TO service_role;
GRANT ALL ON verifications TO service_role;
GRANT ALL ON ai_cache TO service_role;
GRANT ALL ON metrics TO service_role;
GRANT ALL ON user_preferences TO service_role;
GRANT ALL ON user_reports_summary TO service_role;
GRANT ALL ON system_metrics TO service_role;
