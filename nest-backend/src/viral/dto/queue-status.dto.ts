import { IsDateString, IsNumber, IsOptional, IsString } from 'class-validator';

export class QueueStatisticsDto {
  @IsNumber()
  pending: number;

  @IsNumber()
  processing: number;

  @IsNumber()
  completed: number;

  @IsNumber()
  failed: number;

  @IsNumber()
  total: number;
}

export class RecentQueueItemDto {
  @IsString()
  id: string;

  @IsString()
  primary_username: string;

  @IsString()
  status: string;

  @IsNumber()
  progress_percentage: number;

  @IsOptional()
  @IsString()
  current_step?: string;

  @IsDateString()
  submitted_at: string;

  @IsOptional()
  @IsString()
  content_type?: string;

  @IsOptional()
  @IsString()
  target_audience?: string;

  @IsOptional()
  @IsNumber()
  active_competitors_count?: number;
}

export class QueueStatusDataDto {
  statistics: QueueStatisticsDto;
  recent_items: RecentQueueItemDto[];
}

export class QueueStatusResponseDto {
  success: boolean;
  data: QueueStatusDataDto;
  message?: string;
}
