export class UsernameOptionDto {
  username: string;
  profile_name: string;
}

export class FilterOptionsDataDto {
  primary_categories: string[];
  secondary_categories: string[];
  tertiary_categories: string[];
  keywords: string[];
  usernames: UsernameOptionDto[];
  account_types: string[];
  content_types: string[];
  languages: string[];
  content_styles: string[];
}

export class GetFilterOptionsResponseDto {
  success: boolean;
  data: FilterOptionsDataDto;
  message?: string;
}
