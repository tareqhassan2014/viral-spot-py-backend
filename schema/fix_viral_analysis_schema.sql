-- Fix missing updated_at column in viral_analysis_results table
-- This column is referenced in the code but doesn't exist in the current schema

ALTER TABLE public.viral_analysis_results 
ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_viral_analysis_results_updated_at ON public.viral_analysis_results(updated_at);

-- Update existing records to have the current timestamp
UPDATE public.viral_analysis_results 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- Make the column NOT NULL after updating existing records
ALTER TABLE public.viral_analysis_results 
ALTER COLUMN updated_at SET NOT NULL;