-- ==============================================
-- FORCE DELETE VIRAL IDEAS SCHEMA
-- ==============================================
-- This script forcefully removes all viral ideas related database objects

-- Drop everything with CASCADE to force removal
DROP TABLE IF EXISTS viral_ideas_queue CASCADE;
DROP TABLE IF EXISTS viral_ideas_competitors CASCADE;

-- Drop views explicitly
DROP VIEW IF EXISTS viral_queue_summary CASCADE;
DROP VIEW IF EXISTS viral_queue_competitors CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_viral_queue_updated_at() CASCADE;
DROP FUNCTION IF EXISTS validate_content_strategy(JSONB) CASCADE;
DROP FUNCTION IF EXISTS extract_content_strategy_field(JSONB, TEXT) CASCADE;

-- Check if tables still exist and show confirmation
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'viral_ideas_queue') THEN
        RAISE NOTICE 'SUCCESS: viral_ideas_queue table has been deleted';
    ELSE
        RAISE NOTICE 'WARNING: viral_ideas_queue table still exists';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'viral_ideas_competitors') THEN
        RAISE NOTICE 'SUCCESS: viral_ideas_competitors table has been deleted';
    ELSE
        RAISE NOTICE 'WARNING: viral_ideas_competitors table still exists';
    END IF;
END $$;

-- Show remaining viral-related objects (should be empty)
SELECT 'TABLES' as object_type, tablename as name FROM pg_tables WHERE tablename LIKE '%viral%'
UNION ALL
SELECT 'VIEWS' as object_type, viewname as name FROM pg_views WHERE viewname LIKE '%viral%'
UNION ALL
SELECT 'FUNCTIONS' as object_type, proname as name FROM pg_proc WHERE proname LIKE '%viral%'
ORDER BY object_type, name;