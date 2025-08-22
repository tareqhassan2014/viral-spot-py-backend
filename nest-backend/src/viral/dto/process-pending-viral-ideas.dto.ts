export class ProcessingStatsDto {
  total_pending: number;
  successfully_processed: number;
  failed_to_process: number;
  skipped: number;
}

export class ProcessingDetailsDto {
  started_at: string;
  completed_at: string;
  processing_duration_ms: number;
  batch_size: number;
}

export class ProcessedQueueItemDto {
  queue_id: string;
  session_id: string;
  primary_username: string;
  status: string;
  processing_result: 'success' | 'failed' | 'skipped';
  error_message?: string;
}

export class ProcessPendingViralIdeasDataDto {
  processing_stats: ProcessingStatsDto;
  processing_details: ProcessingDetailsDto;
  processed_items: ProcessedQueueItemDto[];
  next_steps: {
    monitoring: string;
    worker_status: string;
    queue_health: string;
  };
}

export class ProcessPendingViralIdeasResponseDto {
  success: boolean;
  data: ProcessPendingViralIdeasDataDto;
  message: string;
}
