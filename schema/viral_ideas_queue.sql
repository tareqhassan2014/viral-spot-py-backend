-- ==============================================
-- VIRAL IDEAS QUEUE SYSTEM
-- ==============================================
-- Tracks form submissions and competitor selections for viral ideas analysis

-- Main analysis queue - tracks each viral ideas request
CREATE TABLE viral_ideas_queue (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Primary profile being analyzed
    primary_username VARCHAR(255) NOT NULL,
    
    -- Form data from the viral ideas flow
    content_strategy JSONB DEFAULT '{}', -- ContentStrategyData from form step 3
    -- Expected structure for content_strategy:
    -- {
    --   "contentType": "Business Tips, Tech Reviews",     -- "What type of content do you create?"
    --   "targetAudience": "Entrepreneurs, Young Professionals", -- "Who is your target audience?"
    --   "goals": "Increase followers, Build brand awareness"     -- "What are your main goals?"
    -- }
    analysis_settings JSONB DEFAULT '{}', -- Any additional settings/preferences
    
    -- Queue status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'paused'
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
    
    -- Analysis progress
    current_step VARCHAR(100), -- Current processing step
    progress_percentage INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Scheduling for automatic re-runs
    auto_rerun_enabled BOOLEAN DEFAULT TRUE, -- Whether to automatically re-run analysis
    rerun_frequency_hours INTEGER DEFAULT 24, -- How often to re-run (24 hours default)
    last_analysis_at TIMESTAMP WITH TIME ZONE, -- When analysis was last completed
    next_scheduled_run TIMESTAMP WITH TIME ZONE, -- When next analysis should run
    total_runs INTEGER DEFAULT 0, -- Track how many times this has been analyzed
    
    -- Timestamps
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_processing_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Competitor selections for each analysis
CREATE TABLE viral_ideas_competitors (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    queue_id UUID REFERENCES viral_ideas_queue(id) ON DELETE CASCADE,
    
    -- Competitor details
    competitor_username VARCHAR(255) NOT NULL,
    selection_method VARCHAR(50) DEFAULT 'suggested', -- 'suggested', 'manual', 'api'
    
    -- Status tracking
    is_active BOOLEAN DEFAULT TRUE, -- Can be set to false if removed later
    processing_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    
    -- Metadata
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    removed_at TIMESTAMP WITH TIME ZONE,
    
    -- Unique constraint to prevent duplicate competitors per analysis
    UNIQUE(queue_id, competitor_username)
);

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================

-- Queue indexes
CREATE INDEX idx_viral_queue_session_id ON viral_ideas_queue(session_id);
CREATE INDEX idx_viral_queue_primary_username ON viral_ideas_queue(primary_username);
CREATE INDEX idx_viral_queue_status ON viral_ideas_queue(status);
CREATE INDEX idx_viral_queue_priority ON viral_ideas_queue(priority);
CREATE INDEX idx_viral_queue_submitted_at ON viral_ideas_queue(submitted_at DESC);
CREATE INDEX idx_viral_queue_next_run ON viral_ideas_queue(next_scheduled_run) WHERE auto_rerun_enabled = TRUE;
CREATE INDEX idx_viral_queue_auto_rerun ON viral_ideas_queue(auto_rerun_enabled, next_scheduled_run);

-- Competitors indexes
CREATE INDEX idx_viral_competitors_queue_id ON viral_ideas_competitors(queue_id);
CREATE INDEX idx_viral_competitors_username ON viral_ideas_competitors(competitor_username);
CREATE INDEX idx_viral_competitors_active ON viral_ideas_competitors(is_active) WHERE is_active = TRUE;

-- ==============================================
-- AUTO-UPDATE TRIGGERS
-- ==============================================
CREATE OR REPLACE FUNCTION update_viral_queue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER viral_ideas_queue_updated_at BEFORE UPDATE ON viral_ideas_queue
    FOR EACH ROW EXECUTE FUNCTION update_viral_queue_updated_at();

-- ==============================================
-- VALIDATION FUNCTIONS
-- ==============================================

-- Function to validate content_strategy JSONB structure
CREATE OR REPLACE FUNCTION validate_content_strategy(strategy_data JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if required fields exist and are strings
    RETURN (
        strategy_data ? 'contentType' AND 
        strategy_data ? 'targetAudience' AND 
        strategy_data ? 'goals' AND
        jsonb_typeof(strategy_data->'contentType') = 'string' AND
        jsonb_typeof(strategy_data->'targetAudience') = 'string' AND
        jsonb_typeof(strategy_data->'goals') = 'string'
    );
END;
$$ LANGUAGE plpgsql;

-- Function to extract content strategy fields as text
CREATE OR REPLACE FUNCTION extract_content_strategy_field(strategy_data JSONB, field_name TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN strategy_data->>field_name;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- CHECK CONSTRAINTS
-- ==============================================

-- Ensure content_strategy has valid structure when not empty
ALTER TABLE viral_ideas_queue 
ADD CONSTRAINT check_valid_content_strategy 
CHECK (
    content_strategy = '{}'::jsonb OR 
    validate_content_strategy(content_strategy)
);

-- ==============================================
-- USEFUL VIEWS
-- ==============================================

-- View to get queue items with competitor count and form data
CREATE VIEW viral_queue_summary AS
SELECT 
    q.id,
    q.session_id,
    q.primary_username,
    q.status,
    q.priority,
    q.progress_percentage,
    q.auto_rerun_enabled,
    q.rerun_frequency_hours,
    q.last_analysis_at,
    q.next_scheduled_run,
    q.total_runs,
    q.submitted_at,
    q.started_processing_at,
    q.completed_at,
    -- Form responses (easily accessible)
    extract_content_strategy_field(q.content_strategy, 'contentType') as content_type,
    extract_content_strategy_field(q.content_strategy, 'targetAudience') as target_audience,
    extract_content_strategy_field(q.content_strategy, 'goals') as main_goals,
    q.content_strategy as full_content_strategy,
    COUNT(c.id) FILTER (WHERE c.is_active = TRUE) as active_competitors_count,
    COUNT(c.id) as total_competitors_count
FROM viral_ideas_queue q
LEFT JOIN viral_ideas_competitors c ON q.id = c.queue_id
GROUP BY q.id, q.session_id, q.primary_username, q.status, q.priority, q.progress_percentage, 
         q.auto_rerun_enabled, q.rerun_frequency_hours, q.last_analysis_at, q.next_scheduled_run, 
         q.total_runs, q.submitted_at, q.started_processing_at, q.completed_at, q.content_strategy;

-- View to get competitor details for each analysis
CREATE VIEW viral_queue_competitors AS
SELECT 
    q.session_id,
    q.primary_username,
    q.status as analysis_status,
    c.competitor_username,
    c.selection_method,
    c.is_active,
    c.processing_status,
    c.added_at,
    c.removed_at
FROM viral_ideas_queue q
JOIN viral_ideas_competitors c ON q.id = c.queue_id
ORDER BY q.submitted_at DESC, c.added_at ASC;

-- ==============================================
-- CRON JOB HELPER QUERIES
-- ==============================================

-- Query to find analyses that need to be re-run (for cron jobs)
-- Example usage:
-- SELECT * FROM viral_ideas_queue 
-- WHERE auto_rerun_enabled = TRUE 
-- AND next_scheduled_run <= NOW() 
-- AND status IN ('completed', 'failed')
-- ORDER BY priority ASC, next_scheduled_run ASC;

-- ==============================================
-- EXAMPLE QUERIES FOR FORM DATA
-- ==============================================

-- Insert a new viral ideas analysis with form data
-- INSERT INTO viral_ideas_queue (session_id, primary_username, content_strategy) 
-- VALUES (
--     'session_12345', 
--     'example_user',
--     '{
--         "contentType": "Business Tips, Tech Reviews",
--         "targetAudience": "Entrepreneurs, Young Professionals", 
--         "goals": "Increase followers, Build brand awareness"
--     }'::jsonb
-- );

-- Query form responses for analytics
-- SELECT 
--     primary_username,
--     content_type,
--     target_audience, 
--     main_goals,
--     submitted_at
-- FROM viral_queue_summary 
-- WHERE status = 'completed'
-- ORDER BY submitted_at DESC;

-- Find users with similar content types
-- SELECT primary_username, content_type
-- FROM viral_queue_summary 
-- WHERE content_type ILIKE '%Business Tips%'
--   AND status = 'completed';

-- Search by specific form fields using JSONB operators
-- SELECT primary_username, content_strategy
-- FROM viral_ideas_queue 
-- WHERE content_strategy->>'goals' ILIKE '%increase followers%';

-- Get aggregated insights from form data
-- SELECT 
--     TRIM(unnest(string_to_array(content_type, ','))) as content_category,
--     COUNT(*) as frequency
-- FROM viral_queue_summary 
-- WHERE content_type IS NOT NULL
-- GROUP BY content_category
-- ORDER BY frequency DESC;