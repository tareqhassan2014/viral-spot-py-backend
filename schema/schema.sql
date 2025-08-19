-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE account_type AS ENUM ('Influencer', 'Theme Page', 'Business Page', 'Personal');
CREATE TYPE queue_priority AS ENUM ('HIGH', 'LOW');
CREATE TYPE queue_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'PAUSED');
CREATE TYPE content_type AS ENUM ('reel', 'post', 'story');

-- Primary Profiles Table (main profiles we've fetched content for)
CREATE TABLE primary_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    profile_name VARCHAR(255),
    bio TEXT,
    followers INTEGER DEFAULT 0,
    posts_count INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    is_business_account BOOLEAN DEFAULT FALSE,
    profile_url VARCHAR(500),
    profile_image_url TEXT,
    profile_image_path TEXT, -- Path in Supabase bucket
    hd_profile_image_path TEXT, -- HD image path in bucket
    account_type account_type DEFAULT 'Personal',
    language VARCHAR(10) DEFAULT 'en',
    content_type VARCHAR(50) DEFAULT 'entertainment',
    
    -- Metrics
    total_reels INTEGER DEFAULT 0,
    median_views BIGINT DEFAULT 0,
    mean_views DECIMAL(12,2) DEFAULT 0,
    std_views DECIMAL(12,2) DEFAULT 0,
    total_views BIGINT DEFAULT 0,
    total_likes BIGINT DEFAULT 0,
    total_comments BIGINT DEFAULT 0,
    
    -- Categorization
    profile_primary_category VARCHAR(100),
    profile_secondary_category VARCHAR(100),
    profile_tertiary_category VARCHAR(100),
    profile_categorization_confidence DECIMAL(3,2) DEFAULT 0.5,
    account_type_confidence DECIMAL(3,2) DEFAULT 0.5,
    
    -- Similar accounts (denormalized for performance)
    similar_account1 VARCHAR(255),
    similar_account2 VARCHAR(255),
    similar_account3 VARCHAR(255),
    similar_account4 VARCHAR(255),
    similar_account5 VARCHAR(255),
    similar_account6 VARCHAR(255),
    similar_account7 VARCHAR(255),
    similar_account8 VARCHAR(255),
    similar_account9 VARCHAR(255),
    similar_account10 VARCHAR(255),
    similar_account11 VARCHAR(255),
    similar_account12 VARCHAR(255),
    similar_account13 VARCHAR(255),
    similar_account14 VARCHAR(255),
    similar_account15 VARCHAR(255),
    similar_account16 VARCHAR(255),
    similar_account17 VARCHAR(255),
    similar_account18 VARCHAR(255),
    similar_account19 VARCHAR(255),
    similar_account20 VARCHAR(255),
    
    -- Timestamps
    last_full_scrape TIMESTAMP WITH TIME ZONE,
    analysis_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Secondary Profiles Table (similar profiles with basic info)
CREATE TABLE secondary_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    biography TEXT,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    media_count INTEGER DEFAULT 0,
    profile_pic_url TEXT,
    profile_pic_path TEXT, -- Path in Supabase bucket
    is_verified BOOLEAN DEFAULT FALSE,
    is_private BOOLEAN DEFAULT FALSE,
    business_email VARCHAR(255),
    external_url TEXT,
    category VARCHAR(100),
    pk VARCHAR(255),
    social_context TEXT,
    estimated_account_type account_type DEFAULT 'Personal',
    
    -- Categorization
    primary_category VARCHAR(100),
    secondary_category VARCHAR(100),
    tertiary_category VARCHAR(100),
    categorization_confidence DECIMAL(3,2) DEFAULT 0.5,
    account_type_confidence DECIMAL(3,2) DEFAULT 0.5,
    
    -- Metadata
    estimated_language VARCHAR(10) DEFAULT 'en',
    click_count INTEGER DEFAULT 0,
    search_count INTEGER DEFAULT 0,
    promotion_eligible BOOLEAN DEFAULT FALSE,
    discovered_by VARCHAR(255), -- Username of primary profile that discovered this
    discovery_reason VARCHAR(100),
    api_source VARCHAR(100),
    similarity_rank INTEGER,
    
    -- Timestamps
    last_basic_scrape TIMESTAMP WITH TIME ZONE,
    last_full_scrape TIMESTAMP WITH TIME ZONE,
    analysis_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key to primary profile that discovered this
    discovered_by_id UUID REFERENCES primary_profiles(id) ON DELETE SET NULL
);

-- Content Table (reels, posts, etc.)
CREATE TABLE content (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    content_id VARCHAR(255) UNIQUE NOT NULL, -- Instagram's ID
    shortcode VARCHAR(255) UNIQUE NOT NULL,
    content_type content_type DEFAULT 'reel',
    url TEXT,
    description TEXT,
    thumbnail_url TEXT,
    thumbnail_path TEXT, -- Path in Supabase bucket
    display_url_path TEXT, -- Display image path in bucket
    video_thumbnail_path TEXT, -- Video thumbnail path in bucket
    
    -- Metrics
    view_count BIGINT DEFAULT 0,
    like_count BIGINT DEFAULT 0,
    comment_count BIGINT DEFAULT 0,
    outlier_score DECIMAL(10,4) DEFAULT 0,
    
    -- Metadata
    date_posted TIMESTAMP WITH TIME ZONE,
    username VARCHAR(255) NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    content_style VARCHAR(50) DEFAULT 'video',
    
    -- Categorization
    primary_category VARCHAR(100),
    secondary_category VARCHAR(100),
    tertiary_category VARCHAR(100),
    categorization_confidence DECIMAL(3,2) DEFAULT 0.5,
    
    -- Keywords
    keyword_1 VARCHAR(100),
    keyword_2 VARCHAR(100),
    keyword_3 VARCHAR(100),
    keyword_4 VARCHAR(100),
    
    -- All image URLs (JSONB for flexibility)
    all_image_urls JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key to primary profile
    profile_id UUID REFERENCES primary_profiles(id) ON DELETE CASCADE
);

-- Queue Table (for processing pipeline)
CREATE TABLE queue (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    source VARCHAR(100) DEFAULT 'manual',
    priority queue_priority DEFAULT 'LOW',
    status queue_status DEFAULT 'PENDING',
    attempts INTEGER DEFAULT 0,
    last_attempt TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    request_id VARCHAR(50) UNIQUE,
    
    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_primary_profiles_username ON primary_profiles(username);
CREATE INDEX idx_primary_profiles_account_type ON primary_profiles(account_type);
CREATE INDEX idx_primary_profiles_followers ON primary_profiles(followers);
CREATE INDEX idx_primary_profiles_median_views ON primary_profiles(median_views);
CREATE INDEX idx_primary_profiles_created_at ON primary_profiles(created_at);

CREATE INDEX idx_secondary_profiles_username ON secondary_profiles(username);
CREATE INDEX idx_secondary_profiles_discovered_by ON secondary_profiles(discovered_by);
CREATE INDEX idx_secondary_profiles_followers ON secondary_profiles(followers_count);
CREATE INDEX idx_secondary_profiles_created_at ON secondary_profiles(created_at);

CREATE INDEX idx_content_username ON content(username);
CREATE INDEX idx_content_profile_id ON content(profile_id);
CREATE INDEX idx_content_shortcode ON content(shortcode);
CREATE INDEX idx_content_view_count ON content(view_count);
CREATE INDEX idx_content_primary_category ON content(primary_category);
CREATE INDEX idx_content_date_posted ON content(date_posted);
CREATE INDEX idx_content_created_at ON content(created_at);

CREATE INDEX idx_queue_username ON queue(username);
CREATE INDEX idx_queue_status ON queue(status);
CREATE INDEX idx_queue_priority ON queue(priority);
CREATE INDEX idx_queue_request_id ON queue(request_id);
CREATE INDEX idx_queue_created_at ON queue(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_primary_profiles_updated_at BEFORE UPDATE ON primary_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_secondary_profiles_updated_at BEFORE UPDATE ON secondary_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_updated_at BEFORE UPDATE ON content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_queue_updated_at BEFORE UPDATE ON queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE primary_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE secondary_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE content ENABLE ROW LEVEL SECURITY;
ALTER TABLE queue ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your auth setup)
-- Example: Allow authenticated users to read all data
CREATE POLICY "Allow authenticated read access" ON primary_profiles
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" ON secondary_profiles
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" ON content
    FOR SELECT USING (auth.role() = 'authenticated');

-- Queue policies - more restrictive
CREATE POLICY "Allow authenticated read own queue items" ON queue
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated insert queue items" ON queue
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated update own queue items" ON queue
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Storage buckets setup (run in Supabase Dashboard)
-- CREATE BUCKET 'profile-images' WITH PUBLIC ACCESS;
-- CREATE BUCKET 'content-thumbnails' WITH PUBLIC ACCESS;

-- View for queue statistics
CREATE VIEW queue_stats AS
SELECT 
    COUNT(*) FILTER (WHERE status = 'PENDING') as pending_count,
    COUNT(*) FILTER (WHERE status = 'PROCESSING') as processing_count,
    COUNT(*) FILTER (WHERE status = 'COMPLETED') as completed_count,
    COUNT(*) FILTER (WHERE status = 'FAILED') as failed_count,
    COUNT(*) FILTER (WHERE status = 'PAUSED') as paused_count,
    COUNT(*) FILTER (WHERE priority = 'HIGH') as high_priority_count,
    COUNT(*) FILTER (WHERE priority = 'LOW') as low_priority_count,
    COUNT(*) as total_count
FROM queue;

-- Similar Profiles Table (lightweight for fast loading)
-- Optimized for 20-80 similar profiles per batch call
CREATE TABLE similar_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    primary_username VARCHAR(255) NOT NULL, -- The main profile these are similar to
    similar_username VARCHAR(255) NOT NULL, -- The similar profile's username
    similar_name VARCHAR(255), -- Display name of the similar profile
    profile_image_path TEXT, -- Path in Supabase 'profile-images' bucket
    profile_image_url TEXT, -- CDN URL for the stored image (cached for performance)
    similarity_rank INTEGER DEFAULT 0, -- Order of similarity (1 = most similar, up to 80)
    batch_id UUID, -- Groups profiles fetched together for cache invalidation
    
    -- Performance flags
    image_downloaded BOOLEAN DEFAULT FALSE, -- Track if image is successfully stored locally
    fetch_failed BOOLEAN DEFAULT FALSE, -- Mark profiles that failed to process
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure we don't have duplicates
    UNIQUE(primary_username, similar_username)
);

-- Indexes optimized for batch operations (20-80 profiles per call)
CREATE INDEX idx_similar_profiles_primary_username ON similar_profiles(primary_username);
CREATE INDEX idx_similar_profiles_batch_lookup ON similar_profiles(primary_username, similarity_rank, image_downloaded);
CREATE INDEX idx_similar_profiles_batch_id ON similar_profiles(batch_id);
CREATE INDEX idx_similar_profiles_ready_display ON similar_profiles(primary_username, image_downloaded, similarity_rank) WHERE image_downloaded = TRUE;
CREATE INDEX idx_similar_profiles_similar_profiles_created_at ON similar_profiles(created_at);

-- Trigger for updated_at
CREATE TRIGGER update_similar_profiles_updated_at BEFORE UPDATE ON similar_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS Policy
ALTER TABLE similar_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow authenticated read access similar_profiles" ON similar_profiles
    FOR SELECT USING (auth.role() = 'authenticated');

-- View for primary profile stats
CREATE VIEW primary_profile_stats AS
SELECT 
    COUNT(*) as total_profiles,
    AVG(followers) as avg_followers,
    AVG(median_views) as avg_median_views,
    SUM(total_views) as total_views_all,
    COUNT(DISTINCT account_type) as account_types_count
FROM primary_profiles;