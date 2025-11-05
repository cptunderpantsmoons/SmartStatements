-- AI Financial Statement Generation System - Database Schema
-- Execute this in Supabase SQL Editor to set up the database

-- ============================================
-- Enable Extensions
-- ============================================
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ============================================
-- Reports Table
-- ============================================
create table if not exists reports (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null,
  year integer not null check (year >= 2000 and year <= 2100),
  status text not null check (status in ('processing', 'completed', 'failed', 'review')),
  file_path text not null,
  file_type text not null,
  overall_score numeric(5, 2),
  
  -- Processing details
  raw_data jsonb,
  healing_result jsonb,
  mapping_result jsonb,
  qa_report jsonb,
  certificate_data jsonb,
  
  -- Tracking
  processing_log text[],
  error_message text,
  
  -- Timestamps
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  completed_at timestamp with time zone,
  
  -- Relationships
  constraint fk_reports_user foreign key (user_id) references auth.users(id) on delete cascade
);

-- Create indexes for common queries
create index idx_reports_user_id on reports(user_id);
create index idx_reports_status on reports(status);
create index idx_reports_year on reports(year);
create index idx_reports_created_at on reports(created_at);
create index idx_reports_user_status on reports(user_id, status);

-- Enable RLS (Row Level Security)
alter table reports enable row level security;

-- RLS Policy: Users can only see their own reports
create policy "Users can view their own reports" on reports
  for select using (auth.uid() = user_id);

create policy "Users can insert their own reports" on reports
  for insert with check (auth.uid() = user_id);

create policy "Users can update their own reports" on reports
  for update using (auth.uid() = user_id);

create policy "Users can delete their own reports" on reports
  for delete using (auth.uid() = user_id);

-- ============================================
-- AI Requests Cache Table (for logging)
-- ============================================
create table if not exists ai_requests (
  id uuid primary key default uuid_generate_v4(),
  report_id uuid,
  user_id uuid not null,
  
  -- Request details
  model_name text not null,
  operation_type text not null,
  input_hash text,
  
  -- Response details
  token_count integer,
  cost_usd numeric(10, 4),
  latency_seconds numeric(8, 3),
  
  -- Status
  status text not null check (status in ('success', 'error')),
  error_message text,
  
  -- Timestamps
  created_at timestamp with time zone default now(),
  expires_at timestamp with time zone,
  
  constraint fk_ai_requests_report foreign key (report_id) references reports(id) on delete set null,
  constraint fk_ai_requests_user foreign key (user_id) references auth.users(id) on delete cascade
);

create index idx_ai_requests_user_id on ai_requests(user_id);
create index idx_ai_requests_report_id on ai_requests(report_id);
create index idx_ai_requests_created_at on ai_requests(created_at);
create index idx_ai_requests_model on ai_requests(model_name);

alter table ai_requests enable row level security;

create policy "Users can view their own AI requests" on ai_requests
  for select using (auth.uid() = user_id);

-- ============================================
-- Processing Steps Table (audit trail)
-- ============================================
create table if not exists processing_steps (
  id uuid primary key default uuid_generate_v4(),
  report_id uuid not null,
  
  -- Step details
  step_number integer not null,
  step_name text not null,
  model_used text,
  
  -- I/O hashing
  input_hash text,
  output_hash text,
  
  -- Performance
  latency_seconds numeric(8, 3),
  
  -- Timestamps
  created_at timestamp with time zone default now(),
  
  constraint fk_processing_steps_report foreign key (report_id) references reports(id) on delete cascade
);

create index idx_processing_steps_report_id on processing_steps(report_id);
create index idx_processing_steps_step_number on processing_steps(report_id, step_number);

-- ============================================
-- Account Mappings Table
-- ============================================
create table if not exists account_mappings (
  id uuid primary key default uuid_generate_v4(),
  report_id uuid not null,
  
  -- Mapping details
  account_2025 text not null,
  account_2024_match text not null,
  similarity_score numeric(3, 2),
  action text not null check (action in ('AUTO_MAP', 'REVIEW_NEEDED', 'NEW_ACCOUNT')),
  confidence numeric(3, 2),
  
  -- Synonyms and reasoning
  synonyms_used text[],
  reasoning text,
  
  -- Audit
  created_at timestamp with time zone default now(),
  
  constraint fk_account_mappings_report foreign key (report_id) references reports(id) on delete cascade
);

create index idx_account_mappings_report_id on account_mappings(report_id);
create index idx_account_mappings_action on account_mappings(action);

-- ============================================
-- Files Table (for tracking uploaded files)
-- ============================================
create table if not exists files (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null,
  report_id uuid,
  
  -- File info
  file_name text not null,
  file_path text not null,
  file_type text not null,
  file_size_bytes integer,
  
  -- Tracking
  uploaded_at timestamp with time zone default now(),
  processed_at timestamp with time zone,
  
  constraint fk_files_user foreign key (user_id) references auth.users(id) on delete cascade,
  constraint fk_files_report foreign key (report_id) references reports(id) on delete set null
);

create index idx_files_user_id on files(user_id);
create index idx_files_report_id on files(report_id);
create index idx_files_uploaded_at on files(uploaded_at);

alter table files enable row level security;

create policy "Users can view their own files" on files
  for select using (auth.uid() = user_id);

-- ============================================
-- System Metrics Table
-- ============================================
create table if not exists system_metrics (
  id uuid primary key default uuid_generate_v4(),
  
  -- Metrics
  total_reports integer,
  total_cost_usd numeric(12, 2),
  total_tokens_used integer,
  
  -- Counts by status
  processing_count integer default 0,
  completed_count integer default 0,
  failed_count integer default 0,
  review_count integer default 0,
  
  -- Performance
  avg_processing_time_seconds numeric(8, 2),
  median_processing_time_seconds numeric(8, 2),
  
  -- Cache metrics
  cache_hits integer default 0,
  cache_misses integer default 0,
  
  -- Timestamps
  recorded_at timestamp with time zone default now()
);

create index idx_system_metrics_recorded_at on system_metrics(recorded_at);

-- ============================================
-- Audit Log Table (for compliance)
-- ============================================
create table if not exists audit_logs (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid,
  
  -- Action details
  action text not null,
  resource_type text,
  resource_id uuid,
  
  -- Changes
  changes jsonb,
  
  -- Timestamps
  created_at timestamp with time zone default now(),
  ip_address inet
);

create index idx_audit_logs_user_id on audit_logs(user_id);
create index idx_audit_logs_created_at on audit_logs(created_at);
create index idx_audit_logs_resource on audit_logs(resource_type, resource_id);

-- ============================================
-- Views for Common Queries
-- ============================================

-- View: User report summary
create or replace view report_summary as
select 
  r.user_id,
  r.year,
  count(*) as total_reports,
  count(case when r.status = 'completed' then 1 end) as completed_count,
  count(case when r.status = 'processing' then 1 end) as processing_count,
  count(case when r.status = 'failed' then 1 end) as failed_count,
  count(case when r.status = 'review' then 1 end) as review_count,
  avg(extract(epoch from (r.updated_at - r.created_at))) as avg_processing_seconds,
  avg(r.overall_score) as avg_score
from reports r
group by r.user_id, r.year;

-- View: AI usage summary
create or replace view ai_usage_summary as
select 
  model_name,
  operation_type,
  count(*) as request_count,
  sum(token_count) as total_tokens,
  sum(cost_usd) as total_cost,
  avg(latency_seconds) as avg_latency,
  count(case when status = 'error' then 1 end) as error_count,
  date(created_at) as date
from ai_requests
group by model_name, operation_type, date(created_at);

-- ============================================
-- Triggers for Audit Trail
-- ============================================

-- Trigger: Auto-update updated_at timestamp
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger update_reports_updated_at before update on reports
  for each row execute function update_updated_at_column();

-- ============================================
-- Supabase Storage Setup Instructions
-- ============================================
-- Run these commands in Supabase dashboard to create storage buckets:
-- 
-- 1. Create 'uploads' bucket (private):
--    - Go to Storage > New bucket
--    - Name: uploads
--    - Uncheck "Public bucket"
--    - Create bucket
--
-- 2. Create 'outputs' bucket (public):
--    - Go to Storage > New bucket
--    - Name: outputs
--    - Check "Public bucket"
--    - Create bucket
--
-- 3. Set RLS policies on buckets:
--    - For uploads: Allow authenticated users to upload/read their own files
--    - For outputs: Allow public read, authenticated write
