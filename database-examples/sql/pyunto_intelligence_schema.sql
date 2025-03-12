-- Database schema for storing and analyzing Pyunto Intelligence API usage
-- This example shows how to create tables for tracking API usage, results, and billing

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create a schema specifically for Pyunto Intelligence data
CREATE SCHEMA pyunto;

-- Assistants table - stores information about configured assistants
CREATE TABLE pyunto.assistants (
    assistant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    feature_type VARCHAR(50) NOT NULL CHECK (feature_type IN ('IMAGE', 'TEXT', 'AUDIO')),
    features_count INTEGER NOT NULL DEFAULT 1,
    configuration JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE pyunto.assistants IS 'Stores smart assistant configurations from Pyunto Intelligence';

-- API Keys table - stores API keys for authentication
CREATE TABLE pyunto.api_keys (
    key_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(255) NOT NULL,  -- Store hashed API key for security
    key_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE pyunto.api_keys IS 'Stores hashed API keys for Pyunto Intelligence';
COMMENT ON COLUMN pyunto.api_keys.key_hash IS 'Securely hashed API key - never store raw API keys';

-- API Usage table - tracks all API calls
CREATE TABLE pyunto.api_usage (
    usage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID REFERENCES pyunto.api_keys(key_id),
    assistant_id UUID REFERENCES pyunto.assistants(assistant_id),
    request_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    response_timestamp TIMESTAMP WITH TIME ZONE,
    latency_ms INTEGER,
    status_code INTEGER,
    input_type VARCHAR(50) NOT NULL,
    input_size_bytes INTEGER,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    error_message TEXT,
    is_billable BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_api_usage_timestamps ON pyunto.api_usage(request_timestamp);
CREATE INDEX idx_api_usage_assistant ON pyunto.api_usage(assistant_id);
CREATE INDEX idx_api_usage_api_key ON pyunto.api_usage(api_key_id);

-- API Results table - stores the results from API calls
CREATE TABLE pyunto.api_results (
    result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usage_id UUID NOT NULL REFERENCES pyunto.api_usage(usage_id),
    result_data JSONB NOT NULL,
    confidence_score DECIMAL(5,4),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_results_usage ON pyunto.api_results(usage_id);

-- Billing table - for tracking billing and subscription information
CREATE TABLE pyunto.billing (
    billing_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    month_year VARCHAR(7) NOT NULL, -- Format: YYYY-MM
    api_calls_count INTEGER DEFAULT 0,
    total_amount DECIMAL(10,2) DEFAULT 0,
    subscription_plan VARCHAR(50),
    subscription_id VARCHAR(100),
    is_paid BOOLEAN DEFAULT FALSE,
    invoice_number VARCHAR(100),
    invoice_date TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_billing_month_year ON pyunto.billing(month_year);

-- Subscription Limits table - for tracking subscription limits and usage
CREATE TABLE pyunto.subscription_limits (
    limit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_plan VARCHAR(50) NOT NULL,
    monthly_api_limit INTEGER NOT NULL,
    concurrent_api_limit INTEGER NOT NULL,
    max_input_size_bytes INTEGER,
    is_custom_export_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert some default subscription limits
INSERT INTO pyunto.subscription_limits 
    (subscription_plan, monthly_api_limit, concurrent_api_limit, max_input_size_bytes, is_custom_export_enabled)
VALUES
    ('STANDARD', 3000, 1, 5242880, FALSE),   -- 5MB
    ('PRO', 40000, 5, 10485760, FALSE),      -- 10MB
    ('ENTERPRISE', 300000, 20, 52428800, TRUE); -- 50MB

-- Errors log table - detailed tracking of API errors
CREATE TABLE pyunto.error_logs (
    error_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usage_id UUID REFERENCES pyunto.api_usage(usage_id),
    error_code VARCHAR(100),
    error_message TEXT,
    error_details JSONB,
    stack_trace TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_error_logs_usage ON pyunto.error_logs(usage_id);
CREATE INDEX idx_error_logs_error_code ON pyunto.error_logs(error_code);

-- Usage statistics view - for easier reporting
CREATE OR REPLACE VIEW pyunto.usage_statistics AS
SELECT
    DATE_TRUNC('day', u.request_timestamp) AS usage_date,
    a.name AS assistant_name,
    a.feature_type,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN u.status_code >= 200 AND u.status_code < 300 THEN 1 ELSE 0 END) AS successful_requests,
    SUM(CASE WHEN u.status_code >= 400 THEN 1 ELSE 0 END) AS error_requests,
    ROUND(AVG(u.latency_ms)) AS avg_latency_ms,
    MAX(u.latency_ms) AS max_latency_ms,
    SUM(u.input_size_bytes) AS total_bytes_processed
FROM
    pyunto.api_usage u
JOIN
    pyunto.assistants a ON u.assistant_id = a.assistant_id
GROUP BY
    usage_date, a.name, a.feature_type
ORDER BY
    usage_date DESC, a.name;

-- Monthly billing view - for financial reporting
CREATE OR REPLACE VIEW pyunto.monthly_billing_summary AS
SELECT
    TO_CHAR(u.request_timestamp, 'YYYY-MM') AS month_year,
    COUNT(*) AS total_api_calls,
    COUNT(DISTINCT u.assistant_id) AS unique_assistants_used,
    COUNT(DISTINCT DATE_TRUNC('day', u.request_timestamp)) AS active_days,
    SUM(CASE WHEN u.status_code >= 200 AND u.status_code < 300 THEN 1 ELSE 0 END) AS successful_calls,
    SUM(CASE WHEN u.status_code >= 400 THEN 1 ELSE 0 END) AS error_calls,
    ROUND(COUNT(*) * 0.01, 2) AS estimated_cost -- Example: $0.01 per API call
FROM
    pyunto.api_usage u
WHERE
    u.is_billable = TRUE
GROUP BY
    month_year
ORDER BY
    month_year DESC;

-- Function to update API key last used timestamp
CREATE OR REPLACE FUNCTION pyunto.update_api_key_last_used()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE pyunto.api_keys
    SET last_used_at = NEW.request_timestamp
    WHERE key_id = NEW.api_key_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updating API key last used timestamp
CREATE TRIGGER update_api_key_usage_time
AFTER INSERT ON pyunto.api_usage
FOR EACH ROW
EXECUTE FUNCTION pyunto.update_api_key_last_used();

-- Function to calculate and update monthly billing
CREATE OR REPLACE FUNCTION pyunto.update_monthly_billing()
RETURNS TRIGGER AS $$
DECLARE
    month_year VARCHAR(7);
    call_count INTEGER;
    amount DECIMAL(10,2);
BEGIN
    -- Get month and year
    month_year := TO_CHAR(NEW.request_timestamp, 'YYYY-MM');
    
    -- Count total billable API calls for this month
    SELECT COUNT(*) INTO call_count
    FROM pyunto.api_usage
    WHERE TO_CHAR(request_timestamp, 'YYYY-MM') = month_year
    AND is_billable = TRUE;
    
    -- Calculate amount (example: $0.01 per API call)
    amount := call_count * 0.01;
    
    -- Update or insert billing record
    INSERT INTO pyunto.billing (month_year, api_calls_count, total_amount)
    VALUES (month_year, call_count, amount)
    ON CONFLICT (month_year) 
    DO UPDATE SET
        api_calls_count = EXCLUDED.api_calls_count,
        total_amount = EXCLUDED.total_amount,
        updated_at = CURRENT_TIMESTAMP;
        
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updating monthly billing
CREATE TRIGGER update_billing_on_api_usage
AFTER INSERT ON pyunto.api_usage
FOR EACH ROW
WHEN (NEW.is_billable = TRUE)
EXECUTE FUNCTION pyunto.update_monthly_billing();

-- Sample queries for common use cases

-- 1. Get usage statistics for the last 30 days
SELECT * FROM pyunto.usage_statistics
WHERE usage_date >= CURRENT_DATE - INTERVAL '30 days';

-- 2. Get error rate by assistant
SELECT
    a.name AS assistant_name,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN u.status_code >= 400 THEN 1 ELSE 0 END) AS error_requests,
    ROUND((SUM(CASE WHEN u.status_code >= 400 THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100, 2) AS error_rate_percent
FROM
    pyunto.api_usage u
JOIN
    pyunto.assistants a ON u.assistant_id = a.assistant_id
WHERE
    u.request_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY
    a.name
ORDER BY
    error_rate_percent DESC;

-- 3. Get daily usage trend
SELECT
    DATE_TRUNC('day', request_timestamp) AS usage_date,
    COUNT(*) AS api_calls
FROM
    pyunto.api_usage
WHERE
    request_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY
    usage_date
ORDER BY
    usage_date;

-- 4. Get API key usage statistics
SELECT
    k.key_name,
    COUNT(*) AS total_calls,
    MIN(u.request_timestamp) AS first_used,
    MAX(u.request_timestamp) AS last_used,
    COUNT(DISTINCT DATE_TRUNC('day', u.request_timestamp)) AS active_days
FROM
    pyunto.api_keys k
JOIN
    pyunto.api_usage u ON k.key_id = u.api_key_id
GROUP BY
    k.key_id, k.key_name
ORDER BY
    total_calls DESC;

-- 5. Get detailed error logs with their API usage context
SELECT
    e.error_id,
    e.error_code,
    e.error_message,
    u.request_timestamp,
    a.name AS assistant_name,
    a.feature_type,
    u.input_type,
    u.input_size_bytes
FROM
    pyunto.error_logs e
JOIN
    pyunto.api_usage u ON e.usage_id = u.usage_id
JOIN
    pyunto.assistants a ON u.assistant_id = a.assistant_id
WHERE
    u.request_timestamp >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY
    u.request_timestamp DESC;
