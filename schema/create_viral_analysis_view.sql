-- Create the missing viral_analysis_latest view for AI processing
-- This view joins viral analysis results with reel details for AI pipeline

CREATE OR REPLACE VIEW public.viral_analysis_latest AS
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
    c.comment_count as current_comment_count,
    c.transcript,
    c.transcript_language,
    c.transcript_available
    
FROM viral_analysis_results var
JOIN viral_analysis_reels varl ON var.id = varl.analysis_id
JOIN content c ON varl.content_id = c.content_id
WHERE var.status IN ('transcripts_completed', 'completed')
ORDER BY var.started_at DESC, varl.rank_in_selection ASC;

-- Add helpful comment
COMMENT ON VIEW viral_analysis_latest IS 'Pre-joined view of viral analysis results with reel details for AI processing pipeline';