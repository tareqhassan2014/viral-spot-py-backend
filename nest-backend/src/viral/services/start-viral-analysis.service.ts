import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  AlreadyProcessingResponseDto,
  StartViralAnalysisResponseDto,
} from '../dto/start-viral-analysis.dto';
import {
  ViralIdeasQueue,
  ViralIdeasQueueDocument,
} from '../entities/viral-ideas-queue.schema';

@Injectable()
export class StartViralAnalysisService {
  private readonly logger = new Logger(StartViralAnalysisService.name);

  constructor(
    @InjectModel(ViralIdeasQueue.name)
    private viralQueueModel: Model<ViralIdeasQueueDocument>,
  ) {}

  /**
   * POST /api/viral-ideas/queue/{queue_id}/start ⚡
   * Viral Analysis Queue Signal with Intelligent Worker Process Coordination
   *
   * Description: The Start Viral Analysis endpoint provides comprehensive queue signaling and worker coordination
   * for viral content analysis workflows. This endpoint serves as a critical trigger mechanism that signals the
   * background processing system that a specific viral ideas analysis job is ready for processing.
   * Usage: Manual analysis triggers, priority processing, queue management, development testing.
   */
  async startViralAnalysisProcessing(
    queueId: string,
  ): Promise<StartViralAnalysisResponseDto | AlreadyProcessingResponseDto> {
    this.logger.log(`🎯 Starting viral analysis signal for queue: ${queueId}`);

    const startTime = Date.now();

    try {
      // Step 1: Input validation
      if (!queueId) {
        throw new Error('queue_id parameter is required');
      }

      // Step 2: Validate UUID format
      const uuidRegex =
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      if (!uuidRegex.test(queueId)) {
        throw new Error('queue_id must be a valid UUID');
      }

      // Step 3: Verify the queue entry exists and get current status
      const queueEntry = await this.viralQueueModel.findById(queueId).exec();

      if (!queueEntry) {
        this.logger.warn(`❌ Queue entry not found: ${queueId}`);
        throw new Error('Queue entry not found');
      }

      const currentStatus = queueEntry.status;
      this.logger.log(
        `📊 Queue entry found - Status: ${currentStatus}, User: @${queueEntry.primary_username}`,
      );

      // Step 4: Validate queue state for processing
      const validStates = ['pending', 'failed', 'paused'];
      if (!validStates.includes(currentStatus)) {
        this.logger.warn(
          `⚠️ Invalid queue state for processing: ${currentStatus}`,
        );
        throw new Error(
          `Queue entry is in '${currentStatus}' state and cannot be started. Valid states: ${validStates.join(', ')}`,
        );
      }

      // Step 5: Check if processing is already in progress
      if (currentStatus === 'processing') {
        this.logger.log(
          `ℹ️ Queue entry already in processing state: ${queueId}`,
        );
        return {
          success: true,
          data: {
            queue_id: queueId,
            status: currentStatus,
            current_step: queueEntry.current_step || 'Processing...',
            progress_percentage: queueEntry.progress_percentage || 0,
            session_id: queueEntry.session_id,
            primary_username: queueEntry.primary_username,
            processing_state: 'already_started',
          },
          message: 'Analysis is already in progress',
        };
      }

      // Step 6: Update queue entry to signal it's ready for processing
      await this.viralQueueModel
        .findByIdAndUpdate(queueId, {
          updated_at: new Date(),
          current_step: 'Signaled for processing - awaiting worker pickup',
        })
        .exec();

      this.logger.log(`✅ Queue entry signaled for processing: ${queueId}`);

      const processingTime = Date.now() - startTime;

      // Step 7: Generate processing signal response
      this.logger.log(
        `🚀 Viral analysis queued successfully: ${queueId} (${processingTime}ms)`,
      );

      return {
        success: true,
        data: {
          queue_processing: {
            queue_id: queueId,
            status: currentStatus,
            signal_sent: true,
            processing_state: 'ready_for_pickup',
            worker_coordination: 'background_processor_notified',
          },
          queue_details: {
            session_id: queueEntry.session_id,
            primary_username: queueEntry.primary_username,
            priority: queueEntry.priority || 5,
            submitted_at: queueEntry.submitted_at,
            current_step: 'Awaiting processing',
            progress_percentage: 0,
          },
          next_steps: {
            worker_processing:
              'Background ViralIdeasProcessor will pick up this job',
            status_updates:
              'Status will change to "processing" when worker begins',
            monitoring: `Use /api/viral-ideas/queue/${queueEntry.session_id} to monitor progress`,
            expected_duration:
              '5-15 minutes depending on competitors and content volume',
          },
          timestamp: new Date().toISOString(),
        },
        message: 'Analysis queued successfully - processor will start shortly',
      };
    } catch (error) {
      const processingTime = Date.now() - startTime;
      this.logger.error(
        `❌ Error starting viral analysis for queue ${queueId}: ${error instanceof Error ? error.message : 'Unknown error'} (${processingTime}ms)`,
      );
      throw error;
    }
  }
}
