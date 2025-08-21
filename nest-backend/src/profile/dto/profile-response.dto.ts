export class ProfileResponseDto {
  username: string;
  profile_name: string;
  bio: string;
  followers: number;
  profile_image_url: string | null;
  profile_image_local: string | null;
  is_verified: boolean;
  is_business_account: boolean;
  reels_count: number;
  average_views: number;
  primary_category: string | null;
  profile_type: string;
  url: string;
  posts_count: number;
  account_type: string;
  language: string;
  content_type: string;
  median_views: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  secondary_category: string | null;
  tertiary_category: string | null;
  categorization_confidence: number;
  similar_accounts: string[];
  last_full_scrape: Date | null;
  analysis_timestamp: Date | null;
  created_at: Date | null;
  updated_at: Date | null;
}

export class GetProfileResponseDto {
  success: boolean;
  data: ProfileResponseDto;
  message: string;
}
