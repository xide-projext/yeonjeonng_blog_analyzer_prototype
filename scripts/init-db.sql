-- Blog SEO Analyzer Database Initialization Script

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS analysis;
CREATE SCHEMA IF NOT EXISTS crawling;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Set search path
SET search_path TO public, analysis, crawling, monitoring;

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Blog posts table
CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content TEXT,
    meta_description TEXT,
    meta_keywords TEXT,
    author VARCHAR(255),
    published_date TIMESTAMP WITH TIME ZONE,
    platform VARCHAR(100),
    language VARCHAR(10) DEFAULT 'ko',
    crawled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    user_id UUID REFERENCES users(id) ON DELETE CASCADE
);

-- SEO analysis results
CREATE TABLE IF NOT EXISTS seo_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blog_post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE,
    overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    keyword_density JSONB,
    meta_score INTEGER,
    heading_structure JSONB,
    link_analysis JSONB,
    image_optimization JSONB,
    readability_score FLOAT,
    technical_seo JSONB,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- NLP analysis results
CREATE TABLE IF NOT EXISTS nlp_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blog_post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE,
    keywords JSONB,
    topics JSONB,
    sentiment_score FLOAT,
    tone_analysis JSONB,
    entity_extraction JSONB,
    language_quality JSONB,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Competition analysis
CREATE TABLE IF NOT EXISTS competition_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blog_post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE,
    competitor_urls TEXT[],
    keyword_overlap JSONB,
    content_gaps JSONB,
    ranking_potential JSONB,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Analysis jobs for async processing
CREATE TABLE IF NOT EXISTS analysis_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blog_post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    result JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crawling logs
CREATE TABLE crawling.crawl_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    status_code INTEGER,
    response_time FLOAT,
    error_message TEXT,
    user_agent TEXT,
    crawled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance monitoring
CREATE TABLE monitoring.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_blog_posts_url ON blog_posts(url);
CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status);
CREATE INDEX IF NOT EXISTS idx_blog_posts_user_id ON blog_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_platform ON blog_posts(platform);
CREATE INDEX IF NOT EXISTS idx_blog_posts_created_at ON blog_posts(crawled_at);

CREATE INDEX IF NOT EXISTS idx_seo_analysis_blog_post_id ON seo_analysis(blog_post_id);
CREATE INDEX IF NOT EXISTS idx_nlp_analysis_blog_post_id ON nlp_analysis(blog_post_id);
CREATE INDEX IF NOT EXISTS idx_competition_analysis_blog_post_id ON competition_analysis(blog_post_id);

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_job_type ON analysis_jobs(job_type);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_blog_posts_content_gin ON blog_posts USING gin(to_tsvector('korean', content));
CREATE INDEX IF NOT EXISTS idx_blog_posts_title_gin ON blog_posts USING gin(to_tsvector('korean', title));

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: admin123)
INSERT INTO users (email, username, hashed_password, is_active, is_verified)
VALUES (
    'admin@blog-seo-analyzer.com',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsf5oQ7l2',
    true,
    true
) ON CONFLICT (email) DO NOTHING; 