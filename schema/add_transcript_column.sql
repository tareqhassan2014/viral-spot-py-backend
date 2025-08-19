-- Add transcript column to content table for storing Instagram reel transcripts
-- This will store the transcript data from the Instagram Transcripts API

ALTER TABLE content 
ADD COLUMN transcript JSONB DEFAULT NULL,
ADD COLUMN transcript_language VARCHAR(10) DEFAULT NULL,
ADD COLUMN transcript_fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN transcript_available BOOLEAN DEFAULT FALSE;

-- Add index for transcript searches
CREATE INDEX idx_content_transcript_available ON content(transcript_available) WHERE transcript_available = TRUE;
CREATE INDEX idx_content_transcript_fetched ON content(transcript_fetched_at DESC) WHERE transcript_fetched_at IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN content.transcript IS 'JSONB array of transcript segments with text, offset, and duration from Instagram Transcripts API';
COMMENT ON COLUMN content.transcript_language IS 'Language code of the transcript (e.g., en, es, fr)';
COMMENT ON COLUMN content.transcript_fetched_at IS 'Timestamp when transcript was last fetched';
COMMENT ON COLUMN content.transcript_available IS 'Boolean flag indicating if transcript is available for this content';