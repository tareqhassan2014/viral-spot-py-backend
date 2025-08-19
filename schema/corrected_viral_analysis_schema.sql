-- ==============================================
-- CORRECTED VIRAL IDEAS ANALYSIS SCHEMA
-- ==============================================

-- 1. ADD TRANSCRIPT COLUMNS TO EXISTING CONTENT TABLE (same as before)
ALTER TABLE public.content 
ADD COLUMN transcript JSONB DEFAULT NULL,
ADD COLUMN transcript_language VARCHAR(10) DEFAULT NULL,
ADD COLUMN transcript_fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN transcript_available BOOLEAN DEFAULT FALSE;

-- 2. ADD QUOTA TRACKING TO VIRAL_IDEAS_QUEUE (simplified)
ALTER TABLE public.viral_ideas_queue
ADD COLUMN last_reel_fetch_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN last_discovery_fetch_at TIMESTAMP WITH TIME ZONE DEFAULT NULL; -- When we last used discover API

-- 3. CREATE ANALYSIS RESULTS TABLE
CREATE TABLE public.viral_analysis_results (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    queue_id UUID NOT NULL,
    analysis_run INTEGER DEFAULT 1, -- 1=initial, 2=first update, 3=second update...
    analysis_type VARCHAR(50) DEFAULT 'initial', -- 'initial' or 'recurring'
    
    -- Analysis metadata
    total_reels_analyzed INTEGER DEFAULT 0,
    primary_reels_count INTEGER DEFAULT 0,
    competitor_reels_count INTEGER DEFAULT 0,
    transcripts_fetched INTEGER DEFAULT 0,
    
    -- AI analysis results (structured for N8N workflow compatibility)
    viral_ideas JSONB DEFAULT NULL, -- Data-driven hook ideas from AI agent
    trending_patterns JSONB DEFAULT NULL, -- Winning patterns analysis
    hook_analysis JSONB DEFAULT NULL, -- Top competitor reels analysis
    raw_ai_output TEXT DEFAULT NULL, -- Full formatted output from N8N workflow
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'transcribing', 'analyzing', 'completed', 'failed'
    error_message TEXT DEFAULT NULL,
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    transcripts_completed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    analysis_completed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT viral_analysis_results_pkey PRIMARY KEY (id),
    CONSTRAINT viral_analysis_results_queue_id_fkey FOREIGN KEY (queue_id) REFERENCES public.viral_ideas_queue(id) ON DELETE CASCADE,
    CONSTRAINT viral_analysis_results_unique_run UNIQUE(queue_id, analysis_run)
);

-- 4. CREATE TABLE TO TRACK WHICH REELS WERE USED IN EACH ANALYSIS
CREATE TABLE public.viral_analysis_reels (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL,
    content_id VARCHAR(255) NOT NULL, -- Links to content.content_id
    reel_type VARCHAR(20) NOT NULL, -- 'primary' or 'competitor'
    username VARCHAR(255) NOT NULL,
    selection_reason VARCHAR(100) DEFAULT NULL, -- 'top_performer_last_month', 'newly_trending', etc.
    rank_in_selection INTEGER DEFAULT 0, -- 1-5 for competitors, 1-3 for primary
    
    -- Reel performance at time of analysis
    view_count_at_analysis BIGINT DEFAULT 0,
    like_count_at_analysis BIGINT DEFAULT 0,
    comment_count_at_analysis BIGINT DEFAULT 0,
    outlier_score_at_analysis NUMERIC DEFAULT 0,
    
    -- Transcript status
    transcript_requested BOOLEAN DEFAULT FALSE,
    transcript_completed BOOLEAN DEFAULT FALSE,
    transcript_error TEXT DEFAULT NULL,
    
    -- Per-reel hook analysis (from N8N Hook Analyzer)
    hook_text TEXT DEFAULT NULL, -- The actual hook (first sentence)
    power_words JSONB DEFAULT NULL, -- Array of power words identified
    
    -- Timestamps
    selected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    transcript_fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    CONSTRAINT viral_analysis_reels_pkey PRIMARY KEY (id),
    CONSTRAINT viral_analysis_reels_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.viral_analysis_results(id) ON DELETE CASCADE,
    CONSTRAINT viral_analysis_reels_unique_per_analysis UNIQUE(analysis_id, content_id)
);

-- 5. CREATE TABLE FOR INDIVIDUAL VIRAL IDEAS WITH SOURCE TRACKING
CREATE TABLE public.viral_ideas (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL,
    idea_text TEXT NOT NULL, -- The actual viral idea/hook
    idea_rank INTEGER DEFAULT 0, -- 1-10 ranking from AI analysis
    explanation TEXT DEFAULT NULL, -- Why this idea works
    category VARCHAR(100) DEFAULT NULL, -- 'hook', 'topic', 'format', etc.
    
    -- AI metadata
    confidence_score NUMERIC DEFAULT 0, -- AI confidence in this idea
    power_words JSONB DEFAULT NULL, -- Power words used in this idea
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT viral_ideas_pkey PRIMARY KEY (id),
    CONSTRAINT viral_ideas_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.viral_analysis_results(id) ON DELETE CASCADE
);

-- 6. CREATE JUNCTION TABLE TO TRACK WHICH REELS INSPIRED EACH IDEA
CREATE TABLE public.viral_idea_source_reels (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    idea_id UUID NOT NULL,
    content_id VARCHAR(255) NOT NULL, -- Links to content.content_id
    influence_type VARCHAR(50) DEFAULT 'primary', -- 'primary', 'supporting', 'inspiration'
    influence_weight NUMERIC DEFAULT 1.0, -- How much this reel influenced the idea (0-1)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT viral_idea_source_reels_pkey PRIMARY KEY (id),
    CONSTRAINT viral_idea_source_reels_idea_id_fkey FOREIGN KEY (idea_id) REFERENCES public.viral_ideas(id) ON DELETE CASCADE,
    CONSTRAINT viral_idea_source_reels_unique UNIQUE(idea_id, content_id)
);

-- 7. CREATE TABLE FOR FULL SCRIPT GENERATION
CREATE TABLE public.viral_scripts (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL,
    script_title VARCHAR(255) NOT NULL,
    script_content TEXT NOT NULL, -- Full script based on user's reel transcripts
    script_type VARCHAR(50) DEFAULT 'reel', -- 'reel', 'story', 'post', etc.
    
    -- Script metadata
    estimated_duration INTEGER DEFAULT NULL, -- Estimated seconds
    target_audience VARCHAR(255) DEFAULT NULL, -- Target demographic
    primary_hook TEXT DEFAULT NULL, -- Main hook for the script
    call_to_action TEXT DEFAULT NULL, -- CTA for the script
    
    -- Source tracking
    source_reels JSONB DEFAULT NULL, -- Array of content_ids used as inspiration
    script_structure JSONB DEFAULT NULL, -- Breakdown of script sections
    
    -- AI generation details
    generation_prompt TEXT DEFAULT NULL, -- Prompt used to generate script
    ai_model VARCHAR(100) DEFAULT NULL, -- AI model used
    generation_temperature NUMERIC DEFAULT NULL, -- Creativity setting
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'reviewed', 'approved', 'published'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT viral_scripts_pkey PRIMARY KEY (id),
    CONSTRAINT viral_scripts_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.viral_analysis_results(id) ON DELETE CASCADE
);

-- 8. CREATE INDEXES FOR PERFORMANCE
CREATE INDEX idx_viral_analysis_results_queue ON public.viral_analysis_results(queue_id, analysis_run DESC);
CREATE INDEX idx_viral_analysis_results_status ON public.viral_analysis_results(status, started_at DESC);
CREATE INDEX idx_viral_analysis_reels_analysis ON public.viral_analysis_reels(analysis_id, reel_type, rank_in_selection);
CREATE INDEX idx_viral_analysis_reels_transcript ON public.viral_analysis_reels(transcript_completed, transcript_fetched_at DESC) WHERE transcript_completed = TRUE;

-- New table indexes
CREATE INDEX idx_viral_ideas_analysis ON public.viral_ideas(analysis_id, idea_rank);
CREATE INDEX idx_viral_idea_source_reels_idea ON public.viral_idea_source_reels(idea_id);
CREATE INDEX idx_viral_idea_source_reels_content ON public.viral_idea_source_reels(content_id);
CREATE INDEX idx_viral_scripts_analysis ON public.viral_scripts(analysis_id, status);
CREATE INDEX idx_viral_scripts_type ON public.viral_scripts(script_type, created_at DESC);

-- 9. CREATE VIEW FOR LATEST ANALYSIS WITH REEL DETAILS
CREATE VIEW public.viral_analysis_latest AS
SELECT 
    var.id as analysis_id,
    var.queue_id,
    var.analysis_run,
    var.analysis_type,
    var.status as analysis_status,
    var.total_reels_analyzed,
    var.transcripts_fetched,
    var.viral_ideas,
    var.trending_patterns,
    var.hook_analysis,
    var.raw_ai_output,
    var.started_at,
    var.analysis_completed_at,
    
    -- Reel details
    varl.content_id,
    varl.reel_type,
    varl.username,
    varl.rank_in_selection,
    varl.view_count_at_analysis,
    varl.transcript_completed,
    varl.hook_text,
    varl.power_words,
    
    -- Content details
    c.url,
    c.description,
    c.shortcode,
    c.date_posted,
    c.view_count as current_view_count,
    c.like_count as current_like_count,
    c.transcript,
    c.transcript_language
    
FROM public.viral_analysis_results var
LEFT JOIN public.viral_analysis_reels varl ON var.id = varl.analysis_id
LEFT JOIN public.content c ON varl.content_id = c.content_id
ORDER BY var.queue_id, var.analysis_run DESC, varl.reel_type, varl.rank_in_selection;

-- 10. CREATE VIEW FOR QUICK ANALYSIS SUMMARY
CREATE VIEW public.viral_analysis_summary AS
SELECT 
    var.queue_id,
    var.analysis_run,
    var.analysis_type,
    var.status,
    var.total_reels_analyzed,
    var.transcripts_fetched,
    var.started_at,
    var.analysis_completed_at,
    
    -- Count breakdown
    COUNT(varl.id) FILTER (WHERE varl.reel_type = 'primary') as primary_reels_selected,
    COUNT(varl.id) FILTER (WHERE varl.reel_type = 'competitor') as competitor_reels_selected,
    COUNT(varl.id) FILTER (WHERE varl.transcript_completed = TRUE) as transcripts_completed,
    
    -- Latest viral ideas (for quick preview)
    var.viral_ideas->>0 as latest_viral_idea_preview
    
FROM public.viral_analysis_results var
LEFT JOIN public.viral_analysis_reels varl ON var.id = varl.analysis_id
GROUP BY var.id, var.queue_id, var.analysis_run, var.analysis_type, var.status, 
         var.total_reels_analyzed, var.transcripts_fetched, var.started_at, 
         var.analysis_completed_at, var.viral_ideas
ORDER BY var.queue_id, var.analysis_run DESC;

-- 11. CREATE VIEW FOR IDEAS WITH SOURCE REEL TRACEABILITY
CREATE VIEW public.viral_ideas_with_sources AS
SELECT 
    vi.id as idea_id,
    vi.analysis_id,
    vi.idea_text,
    vi.idea_rank,
    vi.explanation,
    vi.category,
    vi.confidence_score,
    vi.power_words,
    vi.created_at as idea_created_at,
    
    -- Source reel details
    visr.content_id as source_content_id,
    visr.influence_type,
    visr.influence_weight,
    
    -- Content details from source reel
    c.url as source_url,
    c.description as source_description,
    c.username as source_username,
    c.view_count as source_view_count,
    c.transcript as source_transcript,
    
    -- Analysis context
    var.queue_id,
    var.analysis_run,
    var.analysis_type
    
FROM public.viral_ideas vi
JOIN public.viral_idea_source_reels visr ON vi.id = visr.idea_id
JOIN public.content c ON visr.content_id = c.content_id
JOIN public.viral_analysis_results var ON vi.analysis_id = var.id
ORDER BY vi.analysis_id, vi.idea_rank, visr.influence_weight DESC;

-- 12. CREATE VIEW FOR SCRIPTS WITH SOURCE TRACKING
CREATE VIEW public.viral_scripts_with_sources AS
SELECT 
    vs.id as script_id,
    vs.analysis_id,
    vs.script_title,
    vs.script_content,
    vs.script_type,
    vs.estimated_duration,
    vs.target_audience,
    vs.primary_hook,
    vs.call_to_action,
    vs.source_reels,
    vs.script_structure,
    vs.status,
    vs.created_at as script_created_at,
    
    -- Analysis context
    var.queue_id,
    var.analysis_run,
    var.analysis_type,
    
    -- Source reel count
    jsonb_array_length(vs.source_reels) as source_reel_count
    
FROM public.viral_scripts vs
JOIN public.viral_analysis_results var ON vs.analysis_id = var.id
ORDER BY vs.analysis_id, vs.created_at DESC;

-- 13. CREATE COMPREHENSIVE VIEW FOR FULL TRACEABILITY
CREATE VIEW public.viral_analysis_complete AS
SELECT 
    var.queue_id,
    var.analysis_run,
    var.analysis_type,
    var.status as analysis_status,
    var.total_reels_analyzed,
    var.transcripts_fetched,
    
    -- Ideas summary
    COUNT(vi.id) as total_ideas_generated,
    COUNT(vs.id) as total_scripts_generated,
    
    -- Latest analysis timestamps
    var.started_at,
    var.analysis_completed_at,
    
    -- Sample data for preview
    (SELECT vi2.idea_text FROM viral_ideas vi2 WHERE vi2.analysis_id = var.id ORDER BY vi2.idea_rank LIMIT 1) as top_idea_preview,
    (SELECT vs2.script_title FROM viral_scripts vs2 WHERE vs2.analysis_id = var.id ORDER BY vs2.created_at DESC LIMIT 1) as latest_script_title
    
FROM public.viral_analysis_results var
LEFT JOIN public.viral_ideas vi ON var.id = vi.analysis_id
LEFT JOIN public.viral_scripts vs ON var.id = vs.analysis_id
GROUP BY var.id, var.queue_id, var.analysis_run, var.analysis_type, var.status,
         var.total_reels_analyzed, var.transcripts_fetched, var.started_at, var.analysis_completed_at
ORDER BY var.queue_id, var.analysis_run DESC;

-- 14. ADD COMMENTS FOR DOCUMENTATION
COMMENT ON TABLE public.viral_analysis_results IS 'Stores results of each viral ideas analysis run';
COMMENT ON COLUMN public.viral_analysis_results.analysis_run IS 'Sequential run number: 1=initial, 2=first update, etc.';
COMMENT ON COLUMN public.viral_analysis_results.viral_ideas IS 'AI-generated viral content ideas (JSON array)';
COMMENT ON COLUMN public.viral_analysis_results.trending_patterns IS 'Identified trending patterns from analysis';

COMMENT ON TABLE public.viral_analysis_reels IS 'Tracks which specific reels were used in each analysis';
COMMENT ON COLUMN public.viral_analysis_reels.reel_type IS 'Whether reel is from primary user or competitor';
COMMENT ON COLUMN public.viral_analysis_reels.selection_reason IS 'Why this reel was selected for analysis';
COMMENT ON COLUMN public.viral_analysis_reels.rank_in_selection IS 'Ranking within its category (1-3 for primary, 1-5 for competitors)';

COMMENT ON TABLE public.viral_ideas IS 'Individual viral ideas generated from AI analysis with rankings';
COMMENT ON COLUMN public.viral_ideas.idea_text IS 'The actual viral idea or hook text';
COMMENT ON COLUMN public.viral_ideas.idea_rank IS 'Ranking from 1-10 based on AI analysis';
COMMENT ON COLUMN public.viral_ideas.confidence_score IS 'AI confidence score for this idea (0-1)';

COMMENT ON TABLE public.viral_idea_source_reels IS 'Junction table linking ideas to their source reels';
COMMENT ON COLUMN public.viral_idea_source_reels.influence_type IS 'How the reel influenced the idea: primary, supporting, inspiration';
COMMENT ON COLUMN public.viral_idea_source_reels.influence_weight IS 'Strength of influence from this reel (0-1)';

COMMENT ON TABLE public.viral_scripts IS 'Full scripts generated from user reel transcripts';
COMMENT ON COLUMN public.viral_scripts.source_reels IS 'JSON array of content_ids used as script inspiration';
COMMENT ON COLUMN public.viral_scripts.script_structure IS 'JSON breakdown of script sections (intro, hook, body, cta)';
COMMENT ON COLUMN public.viral_scripts.generation_prompt IS 'AI prompt used to generate this script';