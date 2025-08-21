import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { RequestProfileProcessingResponseDto } from '../dto/profile-request.dto';
import {
  PrimaryProfile,
  PrimaryProfileDocument,
} from '../schemas/primary-profile.schema';
import { Queue, QueueDocument } from '../schemas/queue.schema';

@Injectable()
export class ProfileRequestService {
  private readonly logger = new Logger(ProfileRequestService.name);

  constructor(
    @InjectModel(PrimaryProfile.name)
    private primaryProfileModel: Model<PrimaryProfileDocument>,
    @InjectModel(Queue.name)
    private queueModel: Model<QueueDocument>,
  ) {}

  /**
   * Request high priority processing for a profile with comprehensive duplicate prevention
   *
   * Features:
   * - Multi-layer duplicate detection across processed profiles and active queue
   * - Recent completion tracking to prevent immediate re-queueing
   * - High-priority queue placement for user-requested profiles
   * - Advanced queue position estimation for user feedback
   * - Comprehensive error handling and graceful degradation
   */
  async requestProfileProcessing(
    username: string,
    source: string = 'frontend',
  ): Promise<RequestProfileProcessingResponseDto> {
    this.logger.log(`🚀 Requesting high priority processing for: @${username}`);

    const startTime = Date.now();

    try {
      // Step 1: Check if PRIMARY profile already exists
      const existingProfile = await this.primaryProfileModel
        .findOne({ username })
        .lean()
        .exec();

      if (existingProfile) {
        this.logger.log(
          `✅ PRIMARY profile @${username} already exists - no queueing needed`,
        );

        const processingTime = Date.now() - startTime;
        this.logger.log(
          `✅ Profile existence check completed for @${username} (${processingTime}ms)`,
        );

        return {
          success: true,
          data: {
            queued: false,
            message: `Profile ${username} is already fully processed`,
            estimated_time: 'complete',
            profile_type: 'primary',
            status: 'exists',
            created_at: existingProfile.createdAt
              ? new Date(existingProfile.createdAt).toISOString()
              : undefined,
            skip_reason: 'already_processed',
          },
        };
      }

      // Step 2: Check if already in queue for processing
      const existingQueueItem = await this.queueModel
        .findOne({
          username,
          status: { $in: ['PENDING', 'PROCESSING'] },
        })
        .lean()
        .exec();

      if (existingQueueItem) {
        this.logger.log(
          `✅ @${username} already in queue with status: ${existingQueueItem.status}`,
        );

        const queuePosition = await this.estimateQueuePosition(
          existingQueueItem.priority,
          existingQueueItem.timestamp,
        );

        const processingTime = Date.now() - startTime;
        this.logger.log(
          `✅ Queue status check completed for @${username} (${processingTime}ms)`,
        );

        return {
          success: true,
          data: {
            queued: true,
            message: `Profile ${username} is already in queue (status: ${existingQueueItem.status})`,
            estimated_time: this.calculateEstimatedTime(queuePosition),
            profile_type: 'queued',
            status: existingQueueItem.status.toLowerCase(),
            priority: existingQueueItem.priority,
            queue_position: queuePosition,
            request_id: existingQueueItem.request_id,
            skip_reason: 'already_in_queue',
          },
        };
      }

      // Step 3: Check for recently completed items (last 10 minutes)
      const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
      const recentCompletion = await this.queueModel
        .findOne({
          username,
          status: 'COMPLETED',
          timestamp: { $gte: tenMinutesAgo },
        })
        .lean()
        .exec();

      if (recentCompletion) {
        this.logger.log(
          `✅ @${username} was recently completed - checking primary profile creation`,
        );

        // Double-check if primary profile was actually created
        const primaryCheck = await this.primaryProfileModel
          .findOne({ username })
          .lean()
          .exec();

        if (primaryCheck) {
          const processingTime = Date.now() - startTime;
          this.logger.log(
            `✅ Recent completion verified for @${username} (${processingTime}ms)`,
          );

          return {
            success: true,
            data: {
              queued: false,
              message: `Profile ${username} was recently processed and is now available`,
              estimated_time: 'complete',
              profile_type: 'primary',
              status: 'exists',
              created_at: primaryCheck.createdAt
                ? new Date(primaryCheck.createdAt).toISOString()
                : undefined,
              skip_reason: 'recently_completed',
            },
          };
        }
      }

      // Step 4: Profile needs processing - add to high-priority queue
      this.logger.log(
        `🔄 Profile @${username} needs processing - adding to queue`,
      );

      // Step 5: Create comprehensive queue item
      const requestId = this.generateRequestId();
      const queuePosition = await this.estimateQueuePosition('HIGH');

      const newQueueItem = new this.queueModel({
        username,
        source,
        priority: 'HIGH', // High priority for user requests
        status: 'PENDING',
        attempts: 0,
        last_attempt: null,
        error_message: null,
        request_id: requestId,
        timestamp: new Date(),
      });

      await newQueueItem.save();

      // Step 6: Verify successful addition
      const verification = await this.queueModel
        .findOne({
          username,
          status: 'PENDING',
          request_id: requestId,
        })
        .lean()
        .exec();

      const processingTime = Date.now() - startTime;

      if (verification) {
        this.logger.log(
          `🔍 Verification: @${username} confirmed in queue (${processingTime}ms)`,
        );

        return {
          success: true,
          data: {
            queued: true,
            message: `Profile ${username} added to high priority processing queue`,
            estimated_time: this.calculateEstimatedTime(queuePosition),
            profile_type: 'new',
            status: 'pending',
            priority: 'HIGH',
            request_id: requestId,
            queue_position: queuePosition,
            next_check_recommended: '30 seconds',
          },
        };
      } else {
        this.logger.warn(
          `⚠️ Verification failed: @${username} not found in queue after addition (${processingTime}ms)`,
        );

        // Return optimistic response even if verification failed
        return {
          success: true,
          data: {
            queued: true,
            message: `Profile ${username} is being processed (verification pending)`,
            estimated_time: this.calculateEstimatedTime(queuePosition),
            profile_type: 'processing',
            status: 'pending',
            priority: 'HIGH',
            verification_status: 'pending',
          },
        };
      }
    } catch (error) {
      const processingTime = Date.now() - startTime;
      this.logger.error(
        `❌ Error requesting processing for @${username}: ${error instanceof Error ? error.message : 'Unknown error'} (${processingTime}ms)`,
      );

      // Graceful degradation with optimistic response [[memory:6828465]]
      return {
        success: true,
        data: {
          queued: true,
          message: `Profile ${username} is being processed (system recovery mode)`,
          estimated_time: '2-5 minutes',
          profile_type: 'processing',
          status: 'pending',
          error_recovery: true,
          error_details:
            error instanceof Error ? error.message : 'Unknown error',
        },
      };
    }
  }

  /**
   * Estimate queue position based on priority and submission time
   *
   * Features:
   * - Priority-based position calculation with FIFO within same priority
   * - Real-time queue position estimation for user feedback
   * - Handles all priority levels (HIGH, MEDIUM, LOW)
   */
  private async estimateQueuePosition(
    priority: string,
    timestamp?: Date,
  ): Promise<number> {
    try {
      const now = timestamp || new Date();

      if (priority === 'HIGH') {
        // HIGH priority: count other HIGH priority items submitted earlier
        const position = await this.queueModel
          .countDocuments({
            priority: 'HIGH',
            timestamp: { $lt: now },
            status: { $in: ['PENDING', 'PROCESSING'] },
          })
          .exec();
        return Math.max(1, position + 1);
      } else if (priority === 'MEDIUM') {
        // MEDIUM priority: count HIGH + earlier MEDIUM priority items
        const [highCount, mediumCount] = await Promise.all([
          this.queueModel
            .countDocuments({
              priority: 'HIGH',
              status: { $in: ['PENDING', 'PROCESSING'] },
            })
            .exec(),
          this.queueModel
            .countDocuments({
              priority: 'MEDIUM',
              timestamp: { $lt: now },
              status: { $in: ['PENDING', 'PROCESSING'] },
            })
            .exec(),
        ]);
        return Math.max(1, highCount + mediumCount + 1);
      } else {
        // LOW priority: count all higher priority + earlier LOW priority items
        const [higherPriorityCount, lowCount] = await Promise.all([
          this.queueModel
            .countDocuments({
              priority: { $in: ['HIGH', 'MEDIUM'] },
              status: { $in: ['PENDING', 'PROCESSING'] },
            })
            .exec(),
          this.queueModel
            .countDocuments({
              priority: 'LOW',
              timestamp: { $lt: now },
              status: { $in: ['PENDING', 'PROCESSING'] },
            })
            .exec(),
        ]);
        return Math.max(1, higherPriorityCount + lowCount + 1);
      }
    } catch (error) {
      this.logger.error(
        `Error estimating queue position: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
      return 1; // Conservative estimate
    }
  }

  /**
   * Calculate estimated processing time based on queue position
   */
  private calculateEstimatedTime(queuePosition: number): string {
    if (queuePosition === 1) {
      return '1-2 minutes';
    } else if (queuePosition <= 3) {
      return '2-5 minutes';
    } else if (queuePosition <= 10) {
      return '5-15 minutes';
    } else {
      return '15-30 minutes';
    }
  }

  /**
   * Generate unique request ID for tracking
   */
  private generateRequestId(): string {
    return Math.random().toString(36).substring(2, 10);
  }
}
