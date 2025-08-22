import { Transform } from 'class-transformer';
import {
  IsBoolean,
  IsIn,
  IsInt,
  IsNumber,
  IsOptional,
  IsString,
  Max,
  Min,
} from 'class-validator';

export class GetReelsQueryDto {
  // General parameters
  @IsOptional()
  @IsString()
  search?: string;

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

  // Filtering parameters
  @IsOptional()
  @IsString()
  primary_categories?: string;

  @IsOptional()
  @IsString()
  secondary_categories?: string;

  @IsOptional()
  @IsString()
  tertiary_categories?: string;

  @IsOptional()
  @IsString()
  keywords?: string;

  @IsOptional()
  @Transform(({ value }) => parseFloat(value as string))
  @IsNumber()
  @Min(0)
  min_outlier_score?: number;

  @IsOptional()
  @Transform(({ value }) => parseFloat(value as string))
  @IsNumber()
  @Min(0)
  max_outlier_score?: number;

  @IsOptional()
  @Transform(({ value }) => parseInt(value as string))
  @IsInt()
  @Min(0)
  min_views?: number;

  @IsOptional()
  @Transform(({ value }) => parseInt(value as string))
  @IsInt()
  @Min(0)
  max_views?: number;

  @IsOptional()
  @Transform(({ value }) => parseInt(value as string))
  @IsInt()
  @Min(0)
  min_likes?: number;

  @IsOptional()
  @Transform(({ value }) => parseInt(value as string))
  @IsInt()
  @Min(0)
  max_likes?: number;

  @IsOptional()
  @Transform(({ value }) => parseInt(value as string))
  @IsInt()
  @Min(0)
  min_comments?: number;

  @IsOptional()
  @Transform(({ value }) => parseInt(value as string))
  @IsInt()
  @Min(0)
  max_comments?: number;

  @IsOptional()
  @Transform(({ value }) => parseInt(value as string))
  @IsInt()
  @Min(0)
  min_followers?: number;

  @IsOptional()
  @Transform(({ value }) => parseInt(value as string))
  @IsInt()
  @Min(0)
  max_followers?: number;

  @IsOptional()
  @IsString()
  date_range?: string;

  @IsOptional()
  @Transform(({ value }) => {
    if (typeof value === 'string') {
      return value.toLowerCase() === 'true';
    }
    return Boolean(value);
  })
  @IsBoolean()
  is_verified?: boolean;

  @IsOptional()
  @IsString()
  account_types?: string;

  @IsOptional()
  @IsString()
  content_types?: string;

  @IsOptional()
  @IsString()
  languages?: string;

  @IsOptional()
  @IsString()
  content_styles?: string;

  @IsOptional()
  @Transform(({ value }) => parseFloat(value as string))
  @IsNumber()
  @Min(0)
  @Max(100)
  min_account_engagement_rate?: number;

  @IsOptional()
  @Transform(({ value }) => parseFloat(value as string))
  @IsNumber()
  @Min(0)
  @Max(100)
  max_account_engagement_rate?: number;

  @IsOptional()
  @IsString()
  excluded_usernames?: string;

  // Sorting & Ordering parameters
  @IsOptional()
  @IsIn([
    'popular',
    'views',
    'likes',
    'comments',
    'recent',
    'oldest',
    'followers',
    'account_engagement',
    'content_engagement',
  ])
  sort_by?: string;

  @IsOptional()
  @Transform(({ value }) => {
    if (typeof value === 'string') {
      return value.toLowerCase() === 'true';
    }
    return Boolean(value);
  })
  @IsBoolean()
  random_order?: boolean = false;

  @IsOptional()
  @IsString()
  session_id?: string;
}

export class ReelItemDto {
  id: string;
  content_id: string;
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
  followers: number;
  profile_followers: number;
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

export class GetReelsResponseDto {
  success: boolean;
  data: {
    reels: ReelItemDto[];
    isLastPage: boolean;
  };
  message?: string;
}
