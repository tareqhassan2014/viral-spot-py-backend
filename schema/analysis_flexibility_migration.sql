-- ============================================================================
-- ANALYSIS FLEXIBILITY MIGRATION
-- Only touches analysis-related fields to add flexibility
-- ============================================================================

BEGIN;

-- Step 1: Add new flexible fields to viral_analysis_results
ALTER TABLE public.viral_analysis_results 
ADD COLUMN IF NOT EXISTS analysis_data JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS workflow_version VARCHAR(50) DEFAULT 'legacy';

-- Step 2: Add flexible fields to viral_scripts for enhanced traceability
ALTER TABLE public.viral_scripts
ADD COLUMN IF NOT EXISTS hook_metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS voice_analysis JSONB DEFAULT '{}'::jsonb;

-- Step 3: Migrate existing data to new format
UPDATE public.viral_analysis_results 
SET analysis_data = jsonb_build_object(
    'workflow_version', COALESCE(workflow_version, 'legacy'),
    'migration_timestamp', NOW()::text,
    'legacy_data', jsonb_build_object(
        'viral_ideas', COALESCE(viral_ideas, '[]'::jsonb),
        'trending_patterns', COALESCE(trending_patterns, '{}'::jsonb),
        'hook_analysis', COALESCE(hook_analysis, '[]'::jsonb),
        'raw_ai_output', COALESCE(raw_ai_output, '')
    )
),
workflow_version = 'legacy_migrated'
WHERE analysis_data = '{}'::jsonb;

-- Step 4: Update workflow_version for new format tracking
UPDATE public.viral_analysis_results 
SET workflow_version = 'hook_based_v2'
WHERE workflow_version = 'legacy_migrated' AND analysis_data ? 'legacy_data';

-- Step 5: Add indexes for performance on new JSONB fields
CREATE INDEX IF NOT EXISTS idx_viral_analysis_results_analysis_data_gin 
ON public.viral_analysis_results USING gin (analysis_data);

CREATE INDEX IF NOT EXISTS idx_viral_analysis_results_workflow_version 
ON public.viral_analysis_results (workflow_version);

CREATE INDEX IF NOT EXISTS idx_viral_scripts_hook_metadata_gin 
ON public.viral_scripts USING gin (hook_metadata);

-- Step 6: Remove old rigid columns ONLY after successful migration
-- (Commented out for safety - run manually after verification)
/*
ALTER TABLE public.viral_analysis_results 
DROP COLUMN IF EXISTS viral_ideas,
DROP COLUMN IF EXISTS trending_patterns, 
DROP COLUMN IF EXISTS hook_analysis,
DROP COLUMN IF EXISTS raw_ai_output;
*/

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check migration status
SELECT 
    workflow_version,
    COUNT(*) as count,
    COUNT(CASE WHEN analysis_data != '{}'::jsonb THEN 1 END) as with_analysis_data
FROM public.viral_analysis_results 
GROUP BY workflow_version;

-- Check sample migrated data
SELECT 
    id,
    workflow_version,
    jsonb_pretty(analysis_data) as analysis_data_sample
FROM public.viral_analysis_results 
WHERE analysis_data != '{}'::jsonb 
LIMIT 2;

-- ============================================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================================
/*
BEGIN;
-- Restore original columns if needed
UPDATE public.viral_analysis_results 
SET 
    viral_ideas = (analysis_data->'legacy_data'->>'viral_ideas')::jsonb,
    trending_patterns = (analysis_data->'legacy_data'->>'trending_patterns')::jsonb,
    hook_analysis = (analysis_data->'legacy_data'->>'hook_analysis')::jsonb,
    raw_ai_output = analysis_data->'legacy_data'->>'raw_ai_output'
WHERE analysis_data ? 'legacy_data';

-- Remove new columns
ALTER TABLE public.viral_analysis_results 
DROP COLUMN IF EXISTS analysis_data,
DROP COLUMN IF EXISTS workflow_version;

ALTER TABLE public.viral_scripts
DROP COLUMN IF EXISTS hook_metadata,
DROP COLUMN IF EXISTS voice_analysis;
COMMIT;
*/