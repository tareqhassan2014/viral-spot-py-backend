import { Transform } from 'class-transformer';
import { IsInt, IsOptional, IsString, Max, Min } from 'class-validator';

export class GetViralAnalysisContentQueryDto {
  @IsOptional()
  @IsString()
  @Transform(({ value }) => value?.toLowerCase())
  content_type?: string = 'all';

  @IsOptional()
  @Transform(({ value }) => parseInt(value))
  @IsInt()
  @Min(1)
  @Max(200)
  limit?: number = 100;

  @IsOptional()
  @Transform(({ value }) => parseInt(value))
  @IsInt()
  @Min(0)
  offset?: number = 0;
}

export class AnalysisContentItemDto {
  @IsString()
  id: string;

  @IsString()
  content_id: string;

  @IsString()
  username: string;

  @IsOptional()
  @IsString()
  description?: string;

  @IsOptional()
  @IsString()
  transcript?: string;

  @IsOptional()
  @IsInt()
  view_count?: number;

  @IsOptional()
  @IsInt()
  like_count?: number;

  @IsOptional()
  @IsInt()
  comment_count?: number;

  @IsOptional()
  @IsString()
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

  @IsOptional()
  @IsInt()
  outlier_score?: number;

  @IsOptional()
  @IsString()
  reel_type?: string; // 'primary' or 'competitor'

  // Profile information
  @IsOptional()
  @IsString()
  profile_name?: string;

  @IsOptional()
  @IsString()
  profile_image_url?: string;

  @IsOptional()
  @IsInt()
  followers?: number;

  @IsOptional()
  @IsString()
  account_type?: string;
}

export class ViralAnalysisContentDataDto {
  content: AnalysisContentItemDto[];
  isLastPage: boolean;
  totalCount: number;
  currentPage: number;
  pageSize: number;
}

export class ViralAnalysisContentResponseDto {
  success: boolean;
  data: ViralAnalysisContentDataDto;
  message?: string;
}
