import { Transform } from 'class-transformer';
import { IsInt, IsOptional, IsString, Max, Min } from 'class-validator';

export class GetUserContentQueryDto {
  @IsOptional()
  @Transform(({ value }) => parseInt(value))
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 24;

  @IsOptional()
  @Transform(({ value }) => parseInt(value))
  @IsInt()
  @Min(0)
  offset?: number = 0;

  @IsOptional()
  @IsString()
  @Transform(({ value }) => value?.toLowerCase())
  sort_by?: string = 'recent';
}

export class UserContentItemDto {
  id: string;
  username: string;
  caption: string;
  view_count: string;
  like_count: string;
  comment_count: string;
  share_count: string;
  date_posted: Date;
  content_type: string;
  thumbnail_url: string | null;
  video_url: string | null;
  outlier_score: number;
  profile: {
    username: string;
    profile_name: string;
    bio: string;
    followers: string;
    profile_image_url: string | null;
    is_verified: boolean;
    account_type: string;
  };
  engagement_rate: number;
  performance_score: number;
  content_url: string;
}

export class GetUserContentResponseDto {
  success: boolean;
  data: {
    reels: UserContentItemDto[];
    total_count: number;
    has_more: boolean;
    username: string;
    sort_by: string;
  };
  message?: string;
}
