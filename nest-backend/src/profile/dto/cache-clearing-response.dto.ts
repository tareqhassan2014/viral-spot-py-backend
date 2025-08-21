export class CacheClearingDto {
  username: string;
  operation_status: 'completed' | 'failed';
  cache_cleared: boolean;
  operation_duration_seconds: number;
}

export class CacheDetailsDto {
  profiles_cleared: number;
  images_invalidated: number;
  cache_type: string;
  cdn_coordination: 'completed' | 'no_action_needed' | 'failed';
}

export class PerformanceImpactDto {
  system_impact: 'minimal' | 'none' | 'moderate';
  concurrent_operations: 'unaffected' | 'affected';
  cache_regeneration: 'on_next_request' | 'on_first_request';
}

export class NextStepsDto {
  cache_status: 'cleared' | 'no_cache_found' | 'partially_cleared';
  next_request_behavior: string;
  recommended_action: string;
}

export class CacheErrorDto {
  error: string;
  error_code: string;
  username?: string;
  operation_duration_seconds?: number;
  troubleshooting: string;
  timestamp: string;
}

export class CacheClearingResponseDto {
  success: boolean;
  data?: {
    cache_clearing: CacheClearingDto;
    cache_details: CacheDetailsDto;
    performance_impact: PerformanceImpactDto;
    next_steps: NextStepsDto;
    timestamp: string;
  };
  message?: string;
  error?: CacheErrorDto;
}
