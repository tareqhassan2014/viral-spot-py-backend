import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  CreateViralIdeasQueueDto,
  CreateViralIdeasQueueResponseDto,
} from '../dto/viral-ideas-queue.dto';
import {
  ViralIdeasCompetitor,
  ViralIdeasCompetitorDocument,
} from '../entities/viral-ideas-competitor.schema';
import {
  ViralIdeasQueue,
  ViralIdeasQueueDocument,
} from '../entities/viral-ideas-queue.schema';

@Injectable()
export class ViralIdeasQueueCreationService {
  private readonly logger = new Logger(ViralIdeasQueueCreationService.name);

  constructor(
    @InjectModel(ViralIdeasQueue.name)
    private viralQueueModel: Model<ViralIdeasQueueDocument>,
    @InjectModel(ViralIdeasCompetitor.name)
    private viralCompetitorModel: Model<ViralIdeasCompetitorDocument>,
  ) {}

  /**
   * Creates a new viral ideas analysis job and adds it to the queue
   */
  async createViralIdeasQueue(
    queueData: CreateViralIdeasQueueDto,
  ): Promise<CreateViralIdeasQueueResponseDto> {
    this.logger.log(
      `🚀 Creating viral ideas queue for @${queueData.primary_username}`,
    );

    const startTime = Date.now();

    // Create the main queue entry
    const newQueueEntry = new this.viralQueueModel({
      session_id: queueData.session_id,
      primary_username: queueData.primary_username,
      content_strategy: {
        contentType: queueData.content_strategy.contentType,
        targetAudience: queueData.content_strategy.targetAudience,
        goals: queueData.content_strategy.goals,
      },
      status: 'pending',
      priority: 5, // Default priority
      progress_percentage: 0,
      submitted_at: new Date(),
    });

    const savedQueue = await newQueueEntry.save();

    // Insert competitors if provided
    if (
      queueData.selected_competitors &&
      queueData.selected_competitors.length > 0
    ) {
      const competitorRecords = queueData.selected_competitors.map(
        (competitorUsername) => ({
          queue_id: savedQueue._id,
          competitor_username: competitorUsername,
          selection_method: 'manual',
          is_active: true,
          processing_status: 'pending',
          added_at: new Date(),
        }),
      );

      try {
        await this.viralCompetitorModel.insertMany(competitorRecords);
        this.logger.log(
          `✅ Added ${competitorRecords.length} competitors to queue ${String(savedQueue._id)}`,
        );
      } catch (error) {
        this.logger.warn(
          `⚠️ Failed to insert some competitors for queue ${String(savedQueue._id)}: ${String(error)}`,
        );
      }
    }

    const processingTime = Date.now() - startTime;

    this.logger.log(
      `✅ Successfully created viral ideas queue for @${queueData.primary_username} (${processingTime}ms)`,
    );

    return {
      success: true,
      data: {
        id: String(savedQueue._id),
        session_id: savedQueue.session_id,
        primary_username: savedQueue.primary_username,
        status: savedQueue.status,
        submitted_at: savedQueue.submitted_at.toISOString(),
      },
      message: `Viral ideas analysis queued for @${queueData.primary_username}`,
    };
  }
}
