import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { ProcessPendingViralIdeasResponseDto } from '../dto/process-pending-viral-ideas.dto';
import {
  ViralIdeasQueue,
  ViralIdeasQueueDocument,
} from '../entities/viral-ideas-queue.schema';

@Injectable()
export class ProcessPendingViralIdeasService {
  private readonly logger = new Logger(ProcessPendingViralIdeasService.name);

  constructor(
    @InjectModel(ViralIdeasQueue.name)
    private viralQueueModel: Model<ViralIdeasQueueDocument>,
  ) {}

  /**
   * POST /api/viral-ideas/process-pending ⚡
   * Batch Processing Engine for Pending Viral Ideas Queue Management
   *
   * Description: This endpoint provides comprehensive batch processing capabilities for pending viral ideas
   * analysis jobs in the queue. It identifies all pending queue entries, signals them for processing,
   * and coordinates with background workers to ensure efficient queue management and processing.
   * Usage: Administrative queue management, batch processing operations, queue health maintenance.
   */
  async processPendingViralIdeas(): Promise<ProcessPendingViralIdeasResponseDto> {
    this.logger.log('🔄 Starting batch processing of pending viral ideas');

    const startTime = Date.now();

    try {
      // Step 1: Find all pending queue entries
      const pendingEntries = await this.viralQueueModel
        .find({
          status: { $in: ['pending', 'failed', 'paused'] },
        })
        .sort({ submitted_at: 1 }) // Process oldest first
        .exec();

      this.logger.log(
        `📊 Found ${pendingEntries.length} pending queue entries to process`,
      );

      if (pendingEntries.length === 0) {
        const processingTime = Date.now() - startTime;
        this.logger.log(
          `✅ No pending entries found - queue is clean (${processingTime}ms)`,
        );

        return {
          success: true,
          data: {
            processing_stats: {
              total_pending: 0,
              successfully_processed: 0,
              failed_to_process: 0,
              skipped: 0,
            },
            processing_details: {
              started_at: new Date(startTime).toISOString(),
              completed_at: new Date().toISOString(),
              processing_duration_ms: processingTime,
              batch_size: 0,
            },
            processed_items: [],
            next_steps: {
              monitoring: 'No items to monitor - queue is empty',
              worker_status: 'Workers are idle - no pending jobs',
              queue_health: 'Queue is healthy and clean',
            },
          },
          message: 'No pending viral ideas found - queue is already clean',
        };
      }

      // Step 2: Process each pending entry
      const processedItems: Array<{
        queue_id: string;
        session_id: string;
        primary_username: string;
        status: string;
        processing_result: 'success' | 'failed' | 'skipped';
        error_message?: string;
      }> = [];
      let successCount = 0;
      let failedCount = 0;
      let skippedCount = 0;

      for (const entry of pendingEntries) {
        try {
          // Validate entry before processing
          if (!entry._id || !entry.session_id) {
            this.logger.warn(
              `⚠️ Skipping invalid entry: missing ID or session_id`,
            );
            skippedCount++;
            processedItems.push({
              queue_id: entry._id?.toString() || 'unknown',
              session_id: entry.session_id || 'unknown',
              primary_username: entry.primary_username || 'unknown',
              status: entry.status || 'unknown',
              processing_result: 'skipped' as const,
              error_message: 'Invalid entry - missing required fields',
            });
            continue;
          }

          // Signal entry for processing (similar to startViralAnalysisProcessing)
          await this.viralQueueModel
            .findByIdAndUpdate(entry._id, {
              updated_at: new Date(),
              current_step: 'Batch processed - signaled for worker pickup',
            })
            .exec();

          successCount++;
          processedItems.push({
            queue_id: entry._id.toString(),
            session_id: entry.session_id,
            primary_username: entry.primary_username || 'unknown',
            status: entry.status || 'pending',
            processing_result: 'success' as const,
          });

          this.logger.log(
            `✅ Signaled queue entry for processing: ${entry._id?.toString()} (@${entry.primary_username})`,
          );
        } catch (error) {
          failedCount++;
          const errorMessage =
            error instanceof Error ? error.message : 'Unknown error';

          this.logger.error(
            `❌ Failed to process queue entry ${entry._id?.toString()}: ${errorMessage}`,
          );

          processedItems.push({
            queue_id: entry._id?.toString() || 'unknown',
            session_id: entry.session_id || 'unknown',
            primary_username: entry.primary_username || 'unknown',
            status: entry.status || 'unknown',
            processing_result: 'failed' as const,
            error_message: errorMessage,
          });
        }
      }

      const completedAt = new Date();
      const processingTime = completedAt.getTime() - startTime;

      this.logger.log(
        `🚀 Batch processing completed: ${successCount} successful, ${failedCount} failed, ${skippedCount} skipped (${processingTime}ms)`,
      );

      return {
        success: true,
        data: {
          processing_stats: {
            total_pending: pendingEntries.length,
            successfully_processed: successCount,
            failed_to_process: failedCount,
            skipped: skippedCount,
          },
          processing_details: {
            started_at: new Date(startTime).toISOString(),
            completed_at: completedAt.toISOString(),
            processing_duration_ms: processingTime,
            batch_size: pendingEntries.length,
          },
          processed_items: processedItems,
          next_steps: {
            monitoring: `Monitor ${successCount} signaled jobs using individual queue status endpoints`,
            worker_status: `Background workers will pick up ${successCount} jobs for processing`,
            queue_health: `Queue processed: ${successCount}/${pendingEntries.length} entries signaled successfully`,
          },
        },
        message: `Batch processing completed: ${successCount} entries signaled for processing`,
      };
    } catch (error) {
      const processingTime = Date.now() - startTime;
      this.logger.error(
        `❌ Error in batch processing pending viral ideas: ${error instanceof Error ? error.message : 'Unknown error'} (${processingTime}ms)`,
      );
      throw error;
    }
  }
}
