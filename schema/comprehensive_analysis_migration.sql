-- ============================================================================
-- COMPREHENSIVE ANALYSIS MIGRATION - Maximum Future Flexibility
-- Designed for early prod - prioritizes development ease over data preservation
-- ============================================================================

BEGIN;

-- Step 1: Add flexible analysis storage to viral_analysis_results
ALTER TABLE public.viral_analysis_results 
ADD COLUMN IF NOT EXISTS analysis_data JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS workflow_version VARCHAR(50) DEFAULT 'v2_json';

-- Step 2: Add flexible metadata to viral_analysis_reels
ALTER TABLE public.viral_analysis_reels
ADD COLUMN IF NOT EXISTS analysis_metadata JSONB DEFAULT '{}'::jsonb;

-- Step 3: Remove rigid columns from viral_analysis_results (future flexibility)
ALTER TABLE public.viral_analysis_results 
DROP COLUMN IF EXISTS viral_ideas,
DROP COLUMN IF EXISTS trending_patterns,
DROP COLUMN IF EXISTS hook_analysis,
DROP COLUMN IF EXISTS raw_ai_output;

-- Step 4: Add performance indexes for JSONB queries
CREATE INDEX IF NOT EXISTS idx_viral_analysis_results_analysis_data_gin 
ON public.viral_analysis_results USING gin (analysis_data);

CREATE INDEX IF NOT EXISTS idx_viral_analysis_results_workflow_version 
ON public.viral_analysis_results (workflow_version);

CREATE INDEX IF NOT EXISTS idx_viral_analysis_reels_analysis_metadata_gin 
ON public.viral_analysis_reels USING gin (analysis_metadata);

-- Step 5: Add indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_analysis_data_hooks 
ON public.viral_analysis_results USING gin ((analysis_data->'generated_hooks'));

CREATE INDEX IF NOT EXISTS idx_analysis_data_profile 
ON public.viral_analysis_results USING gin ((analysis_data->'profile_analysis'));

-- Step 6: Update viral_scripts to ensure it has all needed flexible fields
-- (viral_scripts already has source_reels jsonb and script_structure jsonb - perfect!)

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES (run these manually after migration)
-- ============================================================================

/*
-- Check new structure:
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'viral_analysis_results' 
ORDER BY ordinal_position;

-- Verify indexes:
SELECT schemaname, tablename, indexname 
FROM pg_indexes 
WHERE tablename IN ('viral_analysis_results', 'viral_analysis_reels', 'viral_scripts')
ORDER BY tablename, indexname;

-- Check sample data structure:
SELECT workflow_version, COUNT(*) 
FROM viral_analysis_results 
GROUP BY workflow_version;
*/

-- ============================================================================
-- NOTES FOR DEVELOPERS
-- ============================================================================

/*
NEW ANALYSIS_DATA STRUCTURE:
{
  "workflow_version": "hook_based_v2",
  "analysis_timestamp": "2024-01-15T10:30:00Z",
  "profile_analysis": {
    "core_identity": "...",
    "content_themes": [...],
    "audience_pain_points": [...],
    "signature_approaches": [...]
  },
  "individual_reel_analyses": [
    {
      "reel_id": "uuid",
      "reel_type": "primary|competitor",
      "username": "@user",
      "reel_metadata": {...},
      "hook_analysis": {
        "hook_text": "...",
        "effectiveness_score": 9.2,
        "psychological_triggers": [...],
        "power_words": [...],
        "why_it_works": "..."
      }
    }
  ],
  "generated_hooks": [
    {
      "hook_id": 1,
      "hook_text": "...",
      "source_reel_id": "uuid",
      "source_reel_metadata": {...},
      "adaptation_strategy": "...",
      "effectiveness_score": 9.3,
      "psychological_triggers": [...],
      "creator_voice_elements": [...]
    }
  ],
  "scripts_metadata": [...],
  // FUTURE: Add any new analysis types here without schema changes!
  "sentiment_analysis": {...},
  "performance_predictions": {...},
  "trend_analysis": {...}
}

VIRAL_SCRIPTS TABLE (already flexible):
- source_reels JSONB: Complete hook traceability
- script_structure JSONB: Voice analysis, timing, etc.

DEPRECATED TABLES (keep but don't use in new workflow):
- viral_ideas (use analysis_data.generated_hooks instead)
- viral_idea_source_reels (use embedded metadata instead)
*/