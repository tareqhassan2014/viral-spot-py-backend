import {
  IsArray,
  IsBoolean,
  IsDateString,
  IsNumber,
  IsObject,
  IsOptional,
  IsString,
} from 'class-validator';

export class AnalysisMetadataDto {
  @IsString()
  id: string;

  @IsNumber()
  analysis_run: number;

  @IsString()
  analysis_type: string;

  @IsString()
  status: string;

  @IsNumber()
  total_reels_analyzed: number;

  @IsNumber()
  primary_reels_count: number;

  @IsNumber()
  competitor_reels_count: number;

  @IsNumber()
  transcripts_fetched: number;

  @IsOptional()
  @IsString()
  workflow_version?: string;

  @IsDateString()
  started_at: string;

  @IsOptional()
  @IsDateString()
  analysis_completed_at?: string;
}

export class PrimaryProfileDto {
  @IsString()
  id: string;

  @IsString()
  username: string;

  @IsOptional()
  @IsString()
  profile_name?: string;

  @IsOptional()
  @IsString()
  bio?: string;

  @IsOptional()
  @IsNumber()
  followers?: number;

  @IsOptional()
  @IsString()
  profile_image_url?: string;

  @IsOptional()
  @IsString()
  profile_image_path?: string;

  @IsOptional()
  @IsBoolean()
  is_verified?: boolean;

  @IsOptional()
  @IsString()
  account_type?: string;
}

export class CompetitorProfileDto {
  @IsString()
  id: string;

  @IsString()
  username: string;

  @IsOptional()
  @IsString()
  profile_name?: string;

  @IsOptional()
  @IsString()
  bio?: string;

  @IsOptional()
  @IsNumber()
  followers?: number;

  @IsOptional()
  @IsString()
  profile_image_url?: string;

  @IsOptional()
  @IsBoolean()
  is_verified?: boolean;

  @IsOptional()
  @IsString()
  account_type?: string;
}

export class AnalyzedReelDto {
  @IsString()
  content_id: string;

  @IsString()
  reel_type: string;

  @IsString()
  username: string;

  @IsNumber()
  rank_in_selection: number;

  @IsOptional()
  @IsNumber()
  view_count_at_analysis?: number;

  @IsOptional()
  @IsNumber()
  like_count_at_analysis?: number;

  @IsOptional()
  @IsNumber()
  comment_count_at_analysis?: number;

  @IsOptional()
  @IsBoolean()
  transcript_completed?: boolean;

  @IsOptional()
  @IsString()
  hook_text?: string;

  @IsOptional()
  @IsArray()
  power_words?: string[];

  @IsOptional()
  @IsObject()
  analysis_metadata?: any;
}

export class ContentReelDto {
  @IsString()
  id: string;

  @IsString()
  username: string;

  @IsOptional()
  @IsString()
  caption?: string;

  @IsOptional()
  @IsString()
  transcript?: string;

  @IsOptional()
  @IsNumber()
  view_count?: number;

  @IsOptional()
  @IsNumber()
  like_count?: number;

  @IsOptional()
  @IsNumber()
  comment_count?: number;

  @IsOptional()
  @IsDateString()
  posted_at?: string;

  @IsOptional()
  @IsString()
  content_type?: string;

  @IsOptional()
  @IsString()
  primary_category?: string;

  @IsOptional()
  @IsString()
  secondary_category?: string;

  @IsOptional()
  @IsString()
  content_style?: string;
}

export class ViralScriptDto {
  @IsString()
  id: string;

  @IsString()
  queue_id: string;

  @IsOptional()
  @IsString()
  script_title?: string;

  @IsOptional()
  @IsString()
  script_content?: string;

  @IsOptional()
  @IsString()
  script_summary?: string;

  @IsOptional()
  @IsString()
  script_type?: string;

  @IsOptional()
  @IsString()
  target_audience?: string;

  @IsOptional()
  @IsString()
  content_style?: string;

  @IsOptional()
  @IsString()
  hook_strategy?: string;

  @IsOptional()
  @IsString()
  engagement_tactics?: string;

  @IsDateString()
  created_at: string;
}

export class ViralAnalysisResultsDataDto {
  analysis_metadata: AnalysisMetadataDto;
  primary_profile: PrimaryProfileDto;
  competitor_profiles: CompetitorProfileDto[];
  analyzed_reels: AnalyzedReelDto[];
  primary_reels: ContentReelDto[];
  competitor_reels: ContentReelDto[];
  viral_scripts: ViralScriptDto[];

  @IsObject()
  analysis_data: any; // JSONB field with flexible AI analysis data

  @IsOptional()
  @IsArray()
  viral_ideas?: any[]; // Legacy compatibility array
}

export class ViralAnalysisResultsResponseDto {
  @IsBoolean()
  success: boolean;

  data: ViralAnalysisResultsDataDto;

  @IsOptional()
  @IsString()
  message?: string;
}
