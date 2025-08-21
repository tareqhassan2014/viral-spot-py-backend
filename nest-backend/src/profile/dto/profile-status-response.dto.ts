export class CompletedProfileDataDto {
  created_at: string;
  last_scraped_at: string;
  followers_count: number;
  posts_count: number;
  profile_age_hours: number;
  data_freshness: 'fresh' | 'standard';
  status: 'exists';
  availability: 'ready';
  next_action: 'view_profile';
  profile_url: string;
  content_url: string;
}

export class QueueProcessingDataDto {
  attempts: number;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  request_id: string;
  timestamp: string;
  last_attempt?: string;
  error_message?: string;
}

export class ProgressTrackingDto {
  processing_duration_seconds?: number;
  processing_stage: string;
  queue_position?: number;
  estimated_time_remaining: string;
}

export class RetryRecoveryDto {
  is_retry_eligible: boolean;
  next_retry_time?: string;
}

export class UserExperienceDto {
  recommended_polling_interval: string;
  can_be_cancelled: boolean;
  next_action: string;
}

export class ErrorHandlingDto {
  error_type?: string;
  retry_recommended?: boolean;
  recommendation?: string;
  suggested_endpoint?: string;
}

export class StatusConsistencyDto {
  consistent: boolean;
  issues: string[];
  recommended_action: string;
}

export class ProfileStatusResponseDto {
  success: boolean;
  data: {
    // Core status fields
    completed: boolean;
    status: string;
    message: string;

    // Completed profile data (when completed = true)
    completed_profile_data?: CompletedProfileDataDto;

    // Queue processing data (when in queue)
    queue_processing_data?: QueueProcessingDataDto;

    // Progress tracking (when in queue)
    progress_tracking?: ProgressTrackingDto;

    // Retry and recovery (when failed)
    retry_recovery?: RetryRecoveryDto;

    // User experience
    user_experience?: UserExperienceDto;

    // Error handling
    error_handling?: ErrorHandlingDto;

    // Status consistency verification
    status_consistency?: StatusConsistencyDto;

    // Timestamp
    timestamp: string;
  };
  message?: string;
}
