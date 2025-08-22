export class QueueProcessingDto {
  queue_id: string;
  status: string;
  signal_sent: boolean;
  processing_state: string;
  worker_coordination: string;
}

export class QueueDetailsDto {
  session_id: string;
  primary_username: string;
  priority: number;
  submitted_at: Date;
  current_step: string;
  progress_percentage: number;
}

export class NextStepsDto {
  worker_processing: string;
  status_updates: string;
  monitoring: string;
  expected_duration: string;
}

export class StartViralAnalysisDataDto {
  queue_processing: QueueProcessingDto;
  queue_details: QueueDetailsDto;
  next_steps: NextStepsDto;
  timestamp: string;
}

export class StartViralAnalysisResponseDto {
  success: boolean;
  data: StartViralAnalysisDataDto;
  message: string;
}

export class AlreadyProcessingDataDto {
  queue_id: string;
  status: string;
  current_step: string;
  progress_percentage: number;
  session_id: string;
  primary_username: string;
  processing_state: string;
}

export class AlreadyProcessingResponseDto {
  success: boolean;
  data: AlreadyProcessingDataDto;
  message: string;
}
