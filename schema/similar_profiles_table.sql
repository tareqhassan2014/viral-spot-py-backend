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
CREATE INDEX idx_similar_profiles_created_at ON similar_profiles(created_at);

-- Trigger for updated_at
CREATE TRIGGER update_similar_profiles_updated_at BEFORE UPDATE ON similar_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS Policy
ALTER TABLE similar_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow authenticated read access" ON similar_profiles
    FOR SELECT USING (auth.role() = 'authenticated');