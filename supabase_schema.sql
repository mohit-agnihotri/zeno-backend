-- Zeno Supabase Database Schema v2
-- Run this in Supabase SQL Editor

-- Drop existing tables to avoid type conflicts (like UUID vs TEXT for user id)
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS resumes;
DROP TABLE IF EXISTS users;

-- Enable pgvector extension for AI matchmaking
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Users Table (simplified — no auth.users FK for demo mode)
CREATE TABLE users (
    id TEXT PRIMARY KEY,  -- e.g. "user_demo_123"
    name TEXT DEFAULT 'User',
    email TEXT,
    city TEXT,
    college TEXT,
    graduation_year INTEGER,
    profile_type TEXT DEFAULT 'Fresher',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Resumes Table
CREATE TABLE resumes (
    user_id TEXT REFERENCES users(id) PRIMARY KEY,
    file_url TEXT,
    parsed_skills JSONB DEFAULT '[]',
    parsed_text TEXT,
    ats_score INTEGER DEFAULT 0,
    resume_vector vector(384),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Applications Table (Kanban Tracker)
-- Now stores all info inline — no foreign key to jobs table (since we use local jobs)
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    job_title TEXT NOT NULL,
    company TEXT NOT NULL,
    city TEXT DEFAULT 'Remote',
    job_type TEXT DEFAULT 'Full-time',
    apply_url TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    status TEXT DEFAULT 'applied',  -- applied, viewed, replied, offer, rejected
    applied_at TEXT DEFAULT to_char(now(), 'DD Mon'),
    seen_at TEXT,
    replied_at TEXT
);

-- Insert default demo user (so backend won't crash)
INSERT INTO users (id, name, email, city) 
VALUES ('user_demo_123', 'User', 'demo@zeno.app', 'India')
ON CONFLICT (id) DO NOTHING;

-- Disable RLS for demo mode (enable later with proper auth)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE resumes DISABLE ROW LEVEL SECURITY;
ALTER TABLE applications DISABLE ROW LEVEL SECURITY;
