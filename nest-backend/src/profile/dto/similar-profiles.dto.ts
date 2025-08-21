import { Transform, Type } from 'class-transformer';
import { IsInt, IsOptional, Max, Min } from 'class-validator';

export class GetSimilarProfilesQueryDto {
  @IsOptional()
  @Type(() => Number)
  @IsInt({ message: 'limit must be an integer' })
  @Min(1, { message: 'limit must be at least 1' })
  @Max(100, { message: 'limit must not exceed 100' })
  @Transform(({ value }) => (value ? parseInt(value as string, 10) : 20))
  limit: number = 20;
}

export class SimilarProfileDto {
  username: string;
  profile_name: string;
  followers: number;
  average_views: number;
  primary_category: string | null;
  secondary_category: string | null;
  tertiary_category: string | null;
  profile_image_url: string | null;
  profile_image_local: string | null;
  profile_pic_url: string | null;
  profile_pic_local: string | null;
  bio: string;
  is_verified: boolean;
  total_reels: number;
  similarity_score: number;
  rank: number;
  url: string;
}

export class TargetProfileDto {
  username: string;
  profile_name: string;
  followers: number;
  average_views: number;
  primary_category: string | null;
  keywords_analyzed: number;
}

export class AnalysisSummaryDto {
  total_profiles_compared: number;
  profiles_with_similarity: number;
  target_keywords_count: number;
  top_score: number;
}

export class GetSimilarProfilesResponseDto {
  success: boolean;
  data: SimilarProfileDto[];
  count: number;
  target_username: string;
  target_profile: TargetProfileDto;
  analysis_summary: AnalysisSummaryDto;
  message: string;
}
