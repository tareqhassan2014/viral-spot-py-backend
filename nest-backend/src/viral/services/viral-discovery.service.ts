import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { ViralDiscoveryResponseDto } from '../dto/viral-discovery-response.dto';
import {
  ViralIdeasQueue,
  ViralIdeasQueueDocument,
} from '../entities/viral-ideas-queue.schema';

@Injectable()
export class ViralDiscoveryService {
  private readonly logger = new Logger(ViralDiscoveryService.name);

  constructor(
    @InjectModel(ViralIdeasQueue.name)
    private viralQueueModel: Model<ViralIdeasQueueDocument>,
  ) {}

  /**
   * Checks if there's already an existing analysis for a profile
   * Implements intelligent duplicate prevention with multi-tier search strategy
   */
  async checkExistingViralAnalysis(
    username: string,
  ): Promise<ViralDiscoveryResponseDto> {
    this.logger.log(
      `🔍 Checking for existing viral analysis for: @${username}`,
    );

    // Phase 1: Search for completed analyses (priority)
    this.logger.log(
      `📋 Phase 1: Searching for completed analysis for @${username}`,
    );

    const completedAnalysis = await this.viralQueueModel
      .findOne({
        primary_username: username,
        status: 'completed',
      })
      .sort({ completed_at: -1 })
      .exec();

    if (completedAnalysis) {
      return this.buildCompletedAnalysisResponse(completedAnalysis, username);
    }

    // Phase 2: Search for active analyses
    this.logger.log(
      `📊 Phase 2: Searching for active analysis for @${username}`,
    );

    const activeAnalysis = await this.viralQueueModel
      .findOne({
        primary_username: username,
        status: { $in: ['pending', 'processing'] },
      })
      .sort({ submitted_at: -1 })
      .exec();

    if (activeAnalysis) {
      return this.buildActiveAnalysisResponse(activeAnalysis, username);
    }

    // Phase 3: No analysis found
    this.logger.log(`🔍 No existing analysis found for @${username}`);
    throw new NotFoundException(
      `No existing analysis found for username: ${username}`,
    );
  }

  private buildCompletedAnalysisResponse(
    completedAnalysis: ViralIdeasQueueDocument,
    username: string,
  ): ViralDiscoveryResponseDto {
    this.logger.log(
      `✅ Found existing COMPLETED analysis for @${username}: queue_id=${String(completedAnalysis._id)}`,
    );

    // Calculate analysis age
    const completedAt = completedAnalysis.completed_at;
    let analysisAgeHours: number | null = null;
    if (completedAt) {
      const completedTime = new Date(completedAt);
      analysisAgeHours =
        (Date.now() - completedTime.getTime()) / (1000 * 60 * 60);
    }

    return {
      success: true,
      data: {
        analysis_discovery: {
          discovery_type: 'completed',
          analysis_found: true,
          immediate_access: true,
          queue_id: String(completedAnalysis._id),
          session_id: completedAnalysis.session_id,
        },
        analysis_details: {
          id: String(completedAnalysis._id),
          session_id: completedAnalysis.session_id,
          primary_username: completedAnalysis.primary_username,
          status: completedAnalysis.status,
          progress_percentage: completedAnalysis.progress_percentage || 100,
          current_step: completedAnalysis.current_step || 'Analysis completed',
          priority: completedAnalysis.priority || 5,
          total_runs: completedAnalysis.total_runs || 1,
        },
        timeline_information: {
          submitted_at: String(completedAnalysis.submitted_at),
          started_at: completedAnalysis.started_processing_at
            ? String(completedAnalysis.started_processing_at)
            : undefined,
          completed_at: completedAnalysis.completed_at
            ? String(completedAnalysis.completed_at)
            : undefined,
          analysis_age_hours: analysisAgeHours
            ? Math.round(analysisAgeHours * 100) / 100
            : null,
          freshness_status:
            analysisAgeHours && analysisAgeHours < 24 ? 'recent' : 'available',
        },
        access_information: {
          results_endpoint: `/api/viral-analysis/${String(completedAnalysis._id)}/results`,
          content_endpoint: `/api/viral-analysis/${String(completedAnalysis._id)}/content`,
          status_endpoint: `/api/viral-ideas/queue/${completedAnalysis.session_id}`,
          immediate_load: true,
        },
        system_optimization: {
          duplicate_prevention: true,
          resource_conservation: 'existing_analysis_reused',
          processing_saved: 'no_new_analysis_needed',
          performance_benefit: 'immediate_result_access',
        },
        error_information: {
          error_message: completedAnalysis.error_message,
          has_errors: Boolean(completedAnalysis.error_message),
        },
        rerun_information: {
          auto_rerun_enabled: completedAnalysis.auto_rerun_enabled || false,
          can_trigger_rerun: true,
          rerun_recommendation:
            'Analysis completed successfully - rerun if needed for fresh data',
        },
        analysis_type: 'completed',
        timestamp: new Date().toISOString(),
      },
      message: `Found existing completed analysis for @${username}`,
    };
  }

  private buildActiveAnalysisResponse(
    activeAnalysis: ViralIdeasQueueDocument,
    username: string,
  ): ViralDiscoveryResponseDto {
    this.logger.log(
      `✅ Found existing ACTIVE analysis for @${username}: queue_id=${String(activeAnalysis._id)}, status=${activeAnalysis.status}`,
    );

    // Calculate processing duration and estimate completion
    let processingDurationMinutes: number | null = null;
    let estimatedCompletion: string | null = null;

    if (activeAnalysis.submitted_at) {
      const submittedTime = new Date(activeAnalysis.submitted_at);
      processingDurationMinutes =
        (Date.now() - submittedTime.getTime()) / (1000 * 60);

      if (activeAnalysis.status === 'pending') {
        estimatedCompletion = '2-15 minutes (waiting to start)';
      } else if (activeAnalysis.status === 'processing') {
        const progress = activeAnalysis.progress_percentage || 0;
        if (progress > 0) {
          const estimatedRemaining = Math.max(
            1,
            Math.floor((100 - progress) * 0.1),
          );
          estimatedCompletion = `${estimatedRemaining}-${
            estimatedRemaining + 5
          } minutes remaining`;
        } else {
          estimatedCompletion = '5-10 minutes remaining';
        }
      }
    }

    return {
      success: true,
      data: {
        analysis_discovery: {
          discovery_type: 'active',
          analysis_found: true,
          immediate_access: false,
          queue_id: String(activeAnalysis._id),
          session_id: activeAnalysis.session_id,
        },
        analysis_details: {
          id: String(activeAnalysis._id),
          session_id: activeAnalysis.session_id,
          primary_username: activeAnalysis.primary_username,
          status: activeAnalysis.status,
          progress_percentage: activeAnalysis.progress_percentage || 0,
          current_step: activeAnalysis.current_step || 'Processing...',
          priority: activeAnalysis.priority || 5,
          total_runs: activeAnalysis.total_runs || 0,
        },
        timeline_information: {
          submitted_at: String(activeAnalysis.submitted_at),
          started_at: activeAnalysis.started_processing_at
            ? String(activeAnalysis.started_processing_at)
            : undefined,
          completed_at: activeAnalysis.completed_at
            ? String(activeAnalysis.completed_at)
            : undefined,
          processing_duration_minutes: processingDurationMinutes
            ? Math.round(processingDurationMinutes * 100) / 100
            : null,
          estimated_completion: estimatedCompletion,
        },
        monitoring_information: {
          status_endpoint: `/api/viral-ideas/queue/${activeAnalysis.session_id}`,
          polling_recommended: true,
          polling_interval_seconds: 10,
          progress_available: (activeAnalysis.progress_percentage || 0) > 0,
        },
        system_optimization: {
          duplicate_prevention: true,
          resource_conservation: 'existing_analysis_in_progress',
          processing_saved: 'analysis_already_queued',
          performance_benefit: 'avoid_duplicate_processing',
        },
        error_information: {
          error_message: activeAnalysis.error_message,
          has_errors: Boolean(activeAnalysis.error_message),
        },
        next_steps: {
          wait_for_completion: true,
          monitor_progress: `/api/viral-ideas/queue/${activeAnalysis.session_id}`,
          expected_result_access: 'Results will be available upon completion',
          alternative_action:
            'Monitor progress or wait for completion notification',
        },
        analysis_type: 'active',
        timestamp: new Date().toISOString(),
      },
      message: `Found existing active analysis for @${username}`,
    };
  }
}
