-- ==============================================
-- VIRAL IDEAS PROCESSOR SCHEMA UPDATES
-- ==============================================
-- These are the exact changes needed to your existing schema

-- 1. ADD TRANSCRIPT COLUMNS TO EXISTING CONTENT TABLE
ALTER TABLE public.content 
ADD COLUMN transcript JSONB DEFAULT NULL,
ADD COLUMN transcript_language VARCHAR(10) DEFAULT NULL,
ADD COLUMN transcript_fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN transcript_available BOOLEAN DEFAULT FALSE,
ADD COLUMN last_viral_analysis_fetch TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN viral_analysis_priority INTEGER DEFAULT 0;

-- 2. ADD QUOTA TRACKING COLUMNS TO EXISTING VIRAL_IDEAS_QUEUE TABLE
ALTER TABLE public.viral_ideas_queue
ADD COLUMN last_reel_fetch_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN reels_fetched_this_cycle INTEGER DEFAULT 0,
ADD COLUMN cycle_quota_reset_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN max_reels_per_cycle INTEGER DEFAULT 12;

-- 3. CREATE NEW TRACKING TABLE FOR ANALYSIS RUNS
CREATE TABLE public.viral_ideas_reel_analysis (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    queue_id UUID NOT NULL,
    content_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    analysis_run INTEGER DEFAULT 1,
    reel_rank INTEGER DEFAULT 0,
    was_new_reel BOOLEAN DEFAULT FALSE,
    transcript_analyzed BOOLEAN DEFAULT FALSE,
    view_count_at_analysis BIGINT DEFAULT 0,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT viral_ideas_reel_analysis_pkey PRIMARY KEY (id),
    CONSTRAINT viral_ideas_reel_analysis_queue_id_fkey FOREIGN KEY (queue_id) REFERENCES public.viral_ideas_queue(id) ON DELETE CASCADE,
    CONSTRAINT viral_ideas_reel_analysis_unique_per_run UNIQUE(queue_id, content_id, analysis_run)
);

-- 4. CREATE INDEXES FOR PERFORMANCE
-- Content table indexes
CREATE INDEX idx_content_transcript_available ON public.content(transcript_available) WHERE transcript_available = TRUE;
CREATE INDEX idx_content_transcript_fetched ON public.content(transcript_fetched_at DESC) WHERE transcript_fetched_at IS NOT NULL;
CREATE INDEX idx_content_viral_analysis_fetch ON public.content(last_viral_analysis_fetch DESC) WHERE last_viral_analysis_fetch IS NOT NULL;
CREATE INDEX idx_content_viral_priority ON public.content(viral_analysis_priority) WHERE viral_analysis_priority > 0;

-- Viral analysis tracking indexes
CREATE INDEX idx_viral_reel_analysis_queue ON public.viral_ideas_reel_analysis(queue_id, analysis_run);
CREATE INDEX idx_viral_reel_analysis_latest ON public.viral_ideas_reel_analysis(queue_id, analysis_run DESC, was_new_reel) WHERE was_new_reel = TRUE;
CREATE INDEX idx_viral_reel_analysis_transcripts ON public.viral_ideas_reel_analysis(transcript_analyzed, analyzed_at DESC) WHERE transcript_analyzed = TRUE;

-- Queue cycle tracking indexes  
CREATE INDEX idx_viral_queue_cycle_reset ON public.viral_ideas_queue(cycle_quota_reset_at) WHERE cycle_quota_reset_at IS NOT NULL;
CREATE INDEX idx_viral_queue_reel_fetch ON public.viral_ideas_queue(last_reel_fetch_at DESC) WHERE last_reel_fetch_at IS NOT NULL;

-- 5. CREATE VIEW FOR EASY ACCESS TO LATEST ANALYSIS RESULTS
CREATE VIEW public.viral_ideas_latest_analysis AS
SELECT 
    vira.queue_id,
    vira.analysis_run,
    vira.username,
    vira.content_id,
    vira.reel_rank,
    vira.was_new_reel,
    vira.transcript_analyzed,
    vira.view_count_at_analysis,
    vira.analyzed_at,
    c.url,
    c.description,
    c.view_count as current_view_count,
    c.like_count,
    c.comment_count,
    c.transcript_available,
    c.transcript,
    c.transcript_language,
    c.date_posted,
    c.shortcode
FROM public.viral_ideas_reel_analysis vira
JOIN public.content c ON vira.content_id = c.content_id
ORDER BY vira.queue_id, vira.analysis_run DESC, vira.reel_rank ASC;

-- 6. ADD COMMENTS FOR DOCUMENTATION
COMMENT ON COLUMN public.content.transcript IS 'JSONB array of transcript segments with text, offset, and duration from Instagram Transcripts API';
COMMENT ON COLUMN public.content.transcript_language IS 'Language code of the transcript (e.g., en, es, fr)';
COMMENT ON COLUMN public.content.transcript_fetched_at IS 'Timestamp when transcript was last fetched';
COMMENT ON COLUMN public.content.transcript_available IS 'Boolean flag indicating if transcript is available for this content';
COMMENT ON COLUMN public.content.last_viral_analysis_fetch IS 'Timestamp when this reel was last fetched for viral ideas analysis';
COMMENT ON COLUMN public.content.viral_analysis_priority IS 'Priority level for viral analysis fetching (0=normal, 1=high priority)';

COMMENT ON COLUMN public.viral_ideas_queue.last_reel_fetch_at IS 'Timestamp of last reel fetch for this analysis';
COMMENT ON COLUMN public.viral_ideas_queue.reels_fetched_this_cycle IS 'Number of reels fetched in current 24-hour cycle';
COMMENT ON COLUMN public.viral_ideas_queue.cycle_quota_reset_at IS 'When the 24-hour quota cycle resets';
COMMENT ON COLUMN public.viral_ideas_queue.max_reels_per_cycle IS 'Maximum reels that can be fetched per 24-hour cycle';

COMMENT ON TABLE public.viral_ideas_reel_analysis IS 'Tracks which reels were analyzed in each viral ideas analysis run';
COMMENT ON COLUMN public.viral_ideas_reel_analysis.analysis_run IS 'Run number: 1=initial analysis, 2+=recurring updates';
COMMENT ON COLUMN public.viral_ideas_reel_analysis.was_new_reel IS 'True if this reel was newly discovered in this analysis cycle';
COMMENT ON COLUMN public.viral_ideas_reel_analysis.reel_rank IS 'Performance ranking (1=best, 2=second best, 3=third best)';

-- 7. UPDATE EXISTING CONSTRAINTS (if the validation function doesn't exist)
-- Note: Your schema already has the validation function, so this should work
-- If it doesn't exist, you'll need to create it first