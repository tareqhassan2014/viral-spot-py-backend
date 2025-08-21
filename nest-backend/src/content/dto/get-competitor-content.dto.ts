import { Transform } from 'class-transformer';
import { IsIn, IsInt, IsOptional, Max, Min } from 'class-validator';

export class GetCompetitorContentQueryDto {
  @IsOptional()
  @Transform(({ value }) => parseInt(value as string))
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 24;

  @IsOptional()
  @Transform(({ value }) => parseInt(value as string))
  @IsInt()
  @Min(0)
  offset?: number = 0;

  @IsOptional()
  @IsIn(['popular', 'recent', 'views', 'likes'], {
    message: 'sort_by must be one of: popular, recent, views, likes',
  })
  @Transform(({ value }) => (value as string)?.toLowerCase())
  sort_by?: string = 'popular';
}

export class CompetitorContentItemDto {
  id: string;
  reel_id: string;
  content_id: string;
  content_type: string;
  shortcode: string;
  url: string;
  description: string;
  title: string;
  thumbnail_url: string | null;
  thumbnail_local: string | null;
  thumbnail: string | null;
  view_count: number;
  like_count: number;
  comment_count: number;
  outlier_score: number;
  outlierScore: string;
  date_posted: Date;
  username: string;
  profile: string;
  profile_name: string;
  bio: string;
  profile_followers: number;
  followers: number;
  profile_image_url: string | null;
  profileImage: string | null;
  is_verified: boolean;
  account_type: string;
  primary_category: string | null;
  secondary_category: string | null;
  tertiary_category: string | null;
  keyword_1: string | null;
  keyword_2: string | null;
  keyword_3: string | null;
  keyword_4: string | null;
  categorization_confidence: number;
  content_style: string;
  language: string;
  views: string;
  likes: string;
  comments: string;
}

export class GetCompetitorContentResponseDto {
  success: boolean;
  data: {
    reels: CompetitorContentItemDto[];
    total_count: number;
    has_more: boolean;
    username: string;
    sort_by: string;
  };
  message?: string;
}
