import { Type } from 'class-transformer';
import {
  IsArray,
  IsNotEmpty,
  IsOptional,
  IsString,
  ValidateNested,
} from 'class-validator';

export class ContentStrategyDto {
  @IsString()
  @IsNotEmpty()
  contentType: string;

  @IsString()
  @IsNotEmpty()
  targetAudience: string;

  @IsString()
  @IsNotEmpty()
  goals: string;
}

export class CreateViralIdeasQueueDto {
  @IsString()
  @IsNotEmpty()
  session_id: string;

  @IsString()
  @IsNotEmpty()
  primary_username: string;

  @IsArray()
  @IsString({ each: true })
  @IsOptional()
  selected_competitors: string[] = [];

  @ValidateNested()
  @Type(() => ContentStrategyDto)
  content_strategy: ContentStrategyDto;
}

export class ViralIdeasQueueResponseDto {
  id: string;
  session_id: string;
  primary_username: string;
  status: string;
  submitted_at: string;
}

export class CreateViralIdeasQueueResponseDto {
  success: boolean;
  data: ViralIdeasQueueResponseDto;
  message: string;
}
