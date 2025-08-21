import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  GetViralIdeasQueueStatusResponseDto,
  ViralIdeasQueueStatusDto,
} from '../dto/viral-ideas-queue-status.dto';
import {
  ViralIdeasCompetitor,
  ViralIdeasCompetitorDocument,
} from '../entities/viral-ideas-competitor.schema';
import {
  ViralIdeasQueue,
  ViralIdeasQueueDocument,
} from '../entities/viral-ideas-queue.schema';

@Injectable()
export class ViralIdeasQueueStatusService {
  private readonly logger = new Logger(ViralIdeasQueueStatusService.name);

  constructor(
    @InjectModel(ViralIdeasQueue.name)
    private viralQueueModel: Model<ViralIdeasQueueDocument>,
    @InjectModel(ViralIdeasCompetitor.name)
    private viralCompetitorModel: Model<ViralIdeasCompetitorDocument>,
  ) {}

  /**
   * Retrieves the status of a specific viral ideas analysis job from the queue
   */
  async getViralIdeasQueueStatus(
    sessionId: string,
  ): Promise<GetViralIdeasQueueStatusResponseDto> {
    this.logger.log(
      `🔍 Getting viral ideas queue status for session: ${sessionId}`,
    );

    const startTime = Date.now();

    // Get queue record by session_id
    const queueRecord = await this.viralQueueModel
      .findOne({ session_id: sessionId })
      .exec();

    if (!queueRecord) {
      this.logger.warn(`❌ Queue entry not found for session: ${sessionId}`);
      throw new NotFoundException('Queue entry not found');
    }

    // Get competitors for this queue
    const competitors = await this.viralCompetitorModel
      .find({
        queue_id: queueRecord._id,
        is_active: true,
      })
      .select('competitor_username processing_status')
      .lean()
      .exec();

    const competitorUsernames = competitors.map(
      (comp) => comp.competitor_username,
    );

    // Transform the data to match the Python API response format
    const queueStatusData: ViralIdeasQueueStatusDto = {
      id: queueRecord._id.toString(),
      session_id: queueRecord.session_id,
      primary_username: queueRecord.primary_username,
      status: queueRecord.status,
      progress_percentage: queueRecord.progress_percentage || 0,
      content_type: queueRecord.content_strategy?.contentType || '',
      target_audience: queueRecord.content_strategy?.targetAudience || '',
      main_goals: queueRecord.content_strategy?.goals || '',
      competitors: competitorUsernames,
      submitted_at: queueRecord.submitted_at?.toISOString() || '',
      started_processing_at:
        queueRecord.started_processing_at?.toISOString() || null,
      completed_at: queueRecord.completed_at?.toISOString() || null,
    };

    const processingTime = Date.now() - startTime;

    this.logger.log(
      `✅ Successfully retrieved queue status for session: ${sessionId} (${processingTime}ms)`,
    );

    return {
      success: true,
      data: queueStatusData,
    };
  }
}
