export class CompetitorProfileDto {
  username: string;
  name: string;
  profile_image_url: string | null;
  rank: number;
  image_available: boolean;
  image_downloaded: boolean;
  batch_id: string;
  created_at: string;
}

export class CompetitorProcessingDto {
  primary_username: string;
  target_username: string;
  cached: boolean;
  processing_time: number;
  image_available: boolean;
  rank: number;
  batch_id: string;
  created_at: string;
}

export class CompetitorSystemOptimizationDto {
  duplicate_prevention: boolean;
  resource_conservation: string;
  processing_saved: string;
  performance_benefit: string;
}

export class CompetitorErrorInformationDto {
  error_message?: string;
  has_errors: boolean;
  error_code?: string;
  troubleshooting?: string;
}

export class CompetitorAdditionResponseDto {
  success: boolean;
  data: {
    competitor_profile: CompetitorProfileDto;
    processing_information: CompetitorProcessingDto;
    system_optimization: CompetitorSystemOptimizationDto;
    error_information?: CompetitorErrorInformationDto;
    timestamp: string;
  };
  message: string;
}
