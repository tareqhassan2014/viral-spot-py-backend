import { IsIn, IsOptional } from 'class-validator';

export class ProfileRequestQueryDto {
  @IsOptional()
  @IsIn(['frontend', 'api', 'admin', 'crawler', 'bulk'])
  source?: string = 'frontend';
}

export class ProfileRequestResponseDto {
  queued: boolean;
  message: string;
  estimated_time: string;
  profile_type: string;
  status: string;
  priority?: string;
  request_id?: string;
  queue_position?: number;
  next_check_recommended?: string;
  created_at?: string;
  skip_reason?: string;
  verification_status?: string;
  error_recovery?: boolean;
  fallback_mode?: boolean;
  error_details?: string;
}

export class RequestProfileProcessingResponseDto {
  success: boolean;
  data: ProfileRequestResponseDto;
}
