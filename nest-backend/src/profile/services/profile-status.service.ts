import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { ProfileStatusResponseDto } from '../dto/profile-status-response.dto';
import {
  PrimaryProfile,
  PrimaryProfileDocument,
} from '../schemas/primary-profile.schema';
import { Queue, QueueDocument } from '../schemas/queue.schema';

@Injectable()
export class ProfileStatusService {
  private readonly logger = new Logger(ProfileStatusService.name);

  constructor(
    @InjectModel(PrimaryProfile.name)
    private primaryProfileModel: Model<PrimaryProfileDocument>,
    @InjectModel(Queue.name)
    private queueModel: Model<QueueDocument>,
  ) {}

  /**
   * Check comprehensive profile processing status with advanced state tracking
   *
   * Features:
   * - Primary profile completion detection with metadata
   * - Real-time queue status monitoring with progress tracking
   * - Processing duration calculations and stage identification
   * - Intelligent polling recommendations and error handling
   * - Enhanced user experience with actionable next steps
   */
  async checkProfileStatus(
    username: string,
  ): Promise<ProfileStatusResponseDto> {
    try {
      this.logger.log(`🔍 Checking profile status: ${username}`);

      // Step 1: Check if profile exists in primary_profiles (processing complete)
      const primaryProfile = await this.primaryProfileModel
        .findOne({
          username,
        })
        .exec();

      if (primaryProfile) {
        return this.buildCompletedProfileResponse(primaryProfile, username);
      }

      // Step 2: Check queue status for comprehensive tracking
      const queueItem = await this.queueModel
        .findOne({ username })
        .sort({ timestamp: -1 }) // Get most recent entry
        .exec();

      if (queueItem) {
        return await this.buildQueueStatusResponse(queueItem, username);
      }

      // Step 3: Profile not found in either system
      return this.buildNotFoundResponse(username);
    } catch (error) {
      return this.buildErrorResponse(error, username);
    }
  }

  private buildCompletedProfileResponse(
    primaryProfile: PrimaryProfileDocument,
    username: string,
  ): ProfileStatusResponseDto {
    this.logger.log(
      `✅ Profile ${username} found in primary_profiles - processing complete`,
    );

    // Calculate profile age and data freshness
    const now = new Date();
    const profileAgeHours =
      (now.getTime() - primaryProfile.createdAt.getTime()) / (1000 * 60 * 60);
    const dataFreshness = profileAgeHours < 24 ? 'fresh' : 'standard';

    return {
      success: true,
      data: {
        completed: true,
        status: 'exists',
        message: 'Profile processing completed',
        completed_profile_data: {
          created_at: primaryProfile.createdAt.toISOString(),
          last_scraped_at: primaryProfile.updatedAt.toISOString(),
          followers_count: primaryProfile.followers || 0,
          posts_count: primaryProfile.posts_count || 0,
          profile_age_hours: Math.round(profileAgeHours * 100) / 100,
          data_freshness: dataFreshness,
          status: 'exists',
          availability: 'ready',
          next_action: 'view_profile',
          profile_url: `/api/profile/${username}`,
          content_url: `/api/profile/${username}/posts`,
        },
        user_experience: {
          recommended_polling_interval: 'stop',
          can_be_cancelled: false,
          next_action: 'view_profile',
        },
        timestamp: new Date().toISOString(),
      },
    };
  }

  private async buildQueueStatusResponse(
    queueItem: QueueDocument,
    username: string,
  ): Promise<ProfileStatusResponseDto> {
    this.logger.log(
      `📊 Queue status for ${username}: ${queueItem.status} (priority: ${queueItem.priority}, attempts: ${queueItem.attempts})`,
    );

    // Calculate enhanced status metrics
    const processingDuration = this.calculateProcessingDuration(
      queueItem.status,
      queueItem.last_attempt,
    );
    const queuePosition = await this.estimateQueuePosition(
      queueItem.priority,
      queueItem.timestamp,
    );
    const estimatedTimeRemaining = this.calculateEstimatedTime(
      queueItem.status,
      queuePosition,
      processingDuration,
    );
    const processingStage = this.determineProcessingStage(
      queueItem.status,
      processingDuration,
    );
    const isRetryEligible =
      queueItem.status === 'FAILED' && queueItem.attempts < 3;
    const nextRetryTime = isRetryEligible
      ? this.calculateNextRetryTime(queueItem.attempts, queueItem.last_attempt)
      : null;

    return {
      success: true,
      data: {
        completed: false,
        status: queueItem.status,
        message: `Profile is ${queueItem.status.toLowerCase()}`,
        queue_processing_data: {
          attempts: queueItem.attempts,
          priority: queueItem.priority as 'HIGH' | 'MEDIUM' | 'LOW',
          request_id: queueItem.request_id,
          timestamp: queueItem.timestamp.toISOString(),
          last_attempt: queueItem.last_attempt?.toISOString(),
          error_message: queueItem.error_message,
        },
        progress_tracking: {
          processing_duration_seconds: processingDuration
            ? Math.round(processingDuration * 100) / 100
            : undefined,
          processing_stage: processingStage,
          queue_position: queuePosition,
          estimated_time_remaining: estimatedTimeRemaining,
        },
        retry_recovery: {
          is_retry_eligible: isRetryEligible,
          next_retry_time: nextRetryTime?.toISOString(),
        },
        user_experience: {
          recommended_polling_interval: this.getRecommendedPollingInterval(
            queueItem.status,
            processingDuration,
          ),
          can_be_cancelled: ['PENDING', 'PROCESSING'].includes(
            queueItem.status,
          ),
          next_action: this.determineNextAction(
            queueItem.status,
            isRetryEligible,
          ),
        },
        timestamp: new Date().toISOString(),
      },
    };
  }

  private buildNotFoundResponse(username: string): ProfileStatusResponseDto {
    this.logger.log(
      `❓ Profile ${username} not found in queue or primary profiles`,
    );

    return {
      success: true,
      data: {
        completed: false,
        status: 'NOT_FOUND',
        message: 'Profile not found in queue or database',
        error_handling: {
          recommendation: 'Submit processing request first',
          suggested_endpoint: `/api/profile/${username}/request`,
        },
        user_experience: {
          recommended_polling_interval: 'stop',
          can_be_cancelled: false,
          next_action: 'request_processing',
        },
        timestamp: new Date().toISOString(),
      },
    };
  }

  private buildErrorResponse(
    error: unknown,
    username: string,
  ): ProfileStatusResponseDto {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error';

    this.logger.error(
      `❌ Error checking profile status for ${username}: ${errorMessage}`,
    );

    return {
      success: true,
      data: {
        completed: false,
        status: 'ERROR',
        message: `Error checking status: ${errorMessage}`,
        error_handling: {
          error_type: 'system_error',
          retry_recommended: true,
        },
        user_experience: {
          recommended_polling_interval: '60 seconds',
          can_be_cancelled: false,
          next_action: 'retry_status_check',
        },
        timestamp: new Date().toISOString(),
      },
    };
  }

  /**
   * Calculate current processing duration in seconds
   */
  private calculateProcessingDuration(
    status: string,
    lastAttempt: Date | null,
  ): number | null {
    if (status !== 'PROCESSING' || !lastAttempt) {
      return null;
    }

    const now = new Date();
    return (now.getTime() - lastAttempt.getTime()) / 1000;
  }

  /**
   * Estimate current queue position based on priority and submission time
   */
  async estimateQueuePosition(
    priority: string,
    timestamp: Date,
  ): Promise<number> {
    try {
      if (priority === 'HIGH') {
        const position = await this.queueModel
          .countDocuments({
            priority: 'HIGH',
            timestamp: { $lt: timestamp },
            status: { $in: ['PENDING', 'PROCESSING'] },
          })
          .exec();
        return Math.max(1, position + 1);
      } else if (priority === 'MEDIUM') {
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
              timestamp: { $lt: timestamp },
              status: { $in: ['PENDING', 'PROCESSING'] },
            })
            .exec(),
        ]);
        return Math.max(1, highCount + mediumCount + 1);
      } else {
        // LOW priority
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
              timestamp: { $lt: timestamp },
              status: { $in: ['PENDING', 'PROCESSING'] },
            })
            .exec(),
        ]);
        return Math.max(1, higherPriorityCount + lowCount + 1);
      }
    } catch (error) {
      this.logger.error(`Error estimating queue position: ${error}`);
      return 1;
    }
  }

  /**
   * Calculate estimated time remaining based on status and queue metrics
   */
  private calculateEstimatedTime(
    status: string,
    queuePosition: number | null,
    processingDuration: number | null,
  ): string {
    if (status === 'COMPLETED') {
      return 'complete';
    } else if (status === 'FAILED') {
      return 'failed - requires retry';
    } else if (status === 'PROCESSING') {
      if (processingDuration) {
        const averageTotalTime = 4 * 60; // 4 minutes average
        const remaining = Math.max(0, averageTotalTime - processingDuration);
        return remaining < 60
          ? `${Math.round(remaining)} seconds`
          : `${Math.round(remaining / 60)} minutes`;
      }
      return '2-4 minutes';
    } else if (status === 'PENDING') {
      if (queuePosition) {
        if (queuePosition === 1) return '1-2 minutes';
        if (queuePosition <= 3) return '3-8 minutes';
        if (queuePosition <= 10) return '10-25 minutes';
        return '25+ minutes';
      }
      return '5-15 minutes';
    }
    return 'unknown';
  }

  /**
   * Determine user-friendly processing stage description
   */
  private determineProcessingStage(
    status: string,
    processingDuration: number | null,
  ): string {
    if (status === 'PENDING') return 'queued';
    if (status === 'COMPLETED') return 'completed';
    if (status === 'FAILED') return 'failed';

    if (status === 'PROCESSING') {
      if (!processingDuration) return 'starting';
      if (processingDuration < 60) return 'initializing';
      if (processingDuration < 120) return 'fetching_profile_data';
      if (processingDuration < 180) return 'analyzing_content';
      if (processingDuration < 240) return 'processing_insights';
      return 'finalizing';
    }

    return 'unknown';
  }

  /**
   * Calculate next retry time using exponential backoff
   */
  private calculateNextRetryTime(
    attempts: number,
    lastAttempt: Date | null,
  ): Date | null {
    if (!lastAttempt || attempts >= 3) return null;

    // Exponential backoff: 2^attempts minutes (max 30 minutes)
    const backoffMinutes = Math.min(Math.pow(2, attempts), 30);
    const nextRetry = new Date(
      lastAttempt.getTime() + backoffMinutes * 60 * 1000,
    );

    return nextRetry;
  }

  /**
   * Get intelligent polling interval recommendations
   */
  private getRecommendedPollingInterval(
    status: string,
    processingDuration: number | null,
  ): string {
    if (status === 'PENDING') return '30 seconds';
    if (status === 'PROCESSING') {
      return processingDuration && processingDuration < 60
        ? '15 seconds'
        : '30 seconds';
    }
    if (['COMPLETED', 'FAILED'].includes(status)) return 'stop';
    return '60 seconds';
  }

  /**
   * Determine recommended next action for user
   */
  private determineNextAction(
    status: string,
    isRetryEligible: boolean,
  ): string {
    switch (status) {
      case 'COMPLETED':
        return 'view_profile';
      case 'PENDING':
        return 'wait_for_processing';
      case 'PROCESSING':
        return 'monitor_progress';
      case 'FAILED':
        return isRetryEligible ? 'retry_processing' : 'contact_support';
      default:
        return 'check_system_status';
    }
  }

  /**
   * Verify status consistency between primary profiles and queue
   */
  async verifyStatusConsistency(username: string): Promise<{
    consistent: boolean;
    issues: string[];
    recommended_action: string;
  }> {
    try {
      const issues: string[] = [];

      const [primaryProfile, queueItem] = await Promise.all([
        this.primaryProfileModel.findOne({ username }).exec(),
        this.queueModel.findOne({ username }).sort({ timestamp: -1 }).exec(),
      ]);

      // Check for inconsistencies
      if (primaryProfile && queueItem) {
        if (
          queueItem.status === 'PENDING' ||
          queueItem.status === 'PROCESSING'
        ) {
          issues.push('Profile exists but queue shows active processing');
        }

        if (queueItem.status === 'COMPLETED' && !primaryProfile) {
          issues.push('Queue shows completed but no primary profile exists');
        }
      }

      if (queueItem && queueItem.status === 'PROCESSING') {
        const processingDuration =
          (new Date().getTime() - (queueItem.last_attempt?.getTime() || 0)) /
          1000;
        if (processingDuration > 600) {
          // 10 minutes
          issues.push('Processing job appears stuck (over 10 minutes)');
        }
      }

      return {
        consistent: issues.length === 0,
        issues,
        recommended_action:
          issues.length > 0 ? 'contact_support' : 'continue_monitoring',
      };
    } catch (error) {
      return {
        consistent: false,
        issues: [`Consistency check failed: ${error}`],
        recommended_action: 'retry_status_check',
      };
    }
  }
}
