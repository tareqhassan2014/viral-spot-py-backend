export class SecondaryProfileDto {
  username: string;
  profile_name: string;
  bio: string;
  followers: number;
  profile_image_url: string | null;
  profile_image_local: string | null;
  is_verified: boolean;
  primary_category?: string;
  secondary_category?: string;
  tertiary_category?: string;
  account_type: string;
  url: string;
  reels_count: number;
  average_views: number;
  is_secondary: boolean;
  created_at?: string;
  updated_at?: string;
}

export class GetSecondaryProfileResponseDto {
  success: boolean;
  data: SecondaryProfileDto;
}
