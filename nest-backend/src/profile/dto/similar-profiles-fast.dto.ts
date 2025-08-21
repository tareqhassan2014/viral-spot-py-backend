import { Transform, Type } from 'class-transformer';
import { IsBoolean, IsInt, IsOptional, Max, Min } from 'class-validator';

export class GetSimilarProfilesFastQueryDto {
  @IsOptional()
  @Type(() => Number)
  @IsInt({ message: 'limit must be an integer' })
  @Min(1, { message: 'limit must be at least 1' })
  @Max(80, { message: 'limit must not exceed 80' })
  @Transform(({ value }) => (value ? parseInt(value as string, 10) : 20))
  limit: number = 20;

  @IsOptional()
  @Type(() => Boolean)
  @IsBoolean({ message: 'force_refresh must be a boolean' })
  @Transform(({ value }) => {
    if (typeof value === 'string') {
      return value.toLowerCase() === 'true';
    }
    return Boolean(value);
  })
  force_refresh: boolean = false;
}

export class SimilarProfileFastDto {
  username: string;
  name: string;
  profile_image_url: string | null;
  rank: number;
}

export class SimilarProfilesFastDataDto {
  data: SimilarProfileFastDto[];
  cached: boolean;
}

export class GetSimilarProfilesFastResponseDto {
  success: boolean;
  data: SimilarProfileFastDto[];
  message: string;
}
