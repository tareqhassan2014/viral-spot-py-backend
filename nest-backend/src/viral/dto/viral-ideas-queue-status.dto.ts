export class ViralIdeasQueueStatusDto {
  id: string;
  session_id: string;
  primary_username: string;
  status: string;
  progress_percentage: number;
  content_type: string;
  target_audience: string;
  main_goals: string;
  competitors: string[];
  submitted_at: string;
  started_processing_at: string | null;
  completed_at: string | null;
}

export class GetViralIdeasQueueStatusResponseDto {
  success: boolean;
  data: ViralIdeasQueueStatusDto;
}
