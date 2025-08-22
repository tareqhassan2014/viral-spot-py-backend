import { Body, Controller, Get, Logger, Param, Post } from '@nestjs/common';
import { ProcessPendingViralIdeasResponseDto } from './dto/process-pending-viral-ideas.dto';
import { QueueStatusResponseDto } from './dto/queue-status.dto';
import {
  AlreadyProcessingResponseDto,
  StartViralAnalysisResponseDto,
} from './dto/start-viral-analysis.dto';
import { ViralAnalysisResultsResponseDto } from './dto/viral-analysis-results.dto';
import { ViralDiscoveryResponseDto } from './dto/viral-discovery-response.dto';
import { GetViralIdeasQueueStatusResponseDto } from './dto/viral-ideas-queue-status.dto';
import {
  CreateViralIdeasQueueDto,
  CreateViralIdeasQueueResponseDto,
} from './dto/viral-ideas-queue.dto';
import { ProcessPendingViralIdeasService } from './services/process-pending-viral-ideas.service';
import { QueueStatusService } from './services/queue-status.service';
import { StartViralAnalysisService } from './services/start-viral-analysis.service';
import { ViralAnalysisResultsService } from './services/viral-analysis-results.service';
import { ViralAnalysisService } from './services/viral-analysis.service';
import { ViralDiscoveryService } from './services/viral-discovery.service';
import { ViralIdeasQueueCreationService } from './services/viral-ideas-queue-creation.service';
import { ViralIdeasQueueStatusService } from './services/viral-ideas-queue-status.service';
import { ViralQueueService } from './services/viral-queue.service';

@Controller('/viral')
export class ViralController {
  private readonly logger = new Logger(ViralController.name);

  constructor(
    private readonly discoveryService: ViralDiscoveryService,
    private readonly queueService: ViralQueueService,
    private readonly analysisService: ViralAnalysisService,
    private readonly queueCreationService: ViralIdeasQueueCreationService,
    private readonly queueStatusService: ViralIdeasQueueStatusService,
    private readonly processPendingViralIdeasService: ProcessPendingViralIdeasService,
    private readonly startViralAnalysisService: StartViralAnalysisService,
    private readonly overallQueueStatusService: QueueStatusService,
    private readonly viralAnalysisResultsService: ViralAnalysisResultsService,
  ) {}

  /**
   * POST /api/viral-ideas/queue ⚡ NEW
   * Creates a new viral ideas analysis job and adds it to the queue
   *
   * This endpoint validates the request body, creates a queue entry in the viral_ideas_queue
   * collection, and links any selected competitors to the queue entry. It follows the same
   * pattern as the Python FastAPI implementation.
   *
   * @param queueData - The viral ideas queue creation request data
   * @returns Promise<CreateViralIdeasQueueResponseDto> - Queue creation response with ID and status
   */
  @Post('/ideas/queue')
  async createViralIdeasQueue(
    @Body() queueData: CreateViralIdeasQueueDto,
  ): Promise<CreateViralIdeasQueueResponseDto> {
    return await this.queueCreationService.createViralIdeasQueue(queueData);
  }

  /**
   * GET /api/viral-ideas/queue/{session_id} ⚡ NEW
   * Retrieves the status of a specific viral ideas analysis job from the queue
   *
   * This endpoint fetches comprehensive queue status information including progress,
   * content strategy details, and associated competitors. It's designed for real-time
   * polling to track analysis progress and provide detailed status updates.
   *
   * @param sessionId - The unique session identifier for the queue entry
   * @returns Promise<GetViralIdeasQueueStatusResponseDto> - Complete queue status with competitors
   */
  @Get('/ideas/queue/:session_id')
  async getViralIdeasQueueStatus(
    @Param('session_id') sessionId: string,
  ): Promise<GetViralIdeasQueueStatusResponseDto> {
    return await this.queueStatusService.getViralIdeasQueueStatus(sessionId);
  }

  /**
   * GET /api/viral-ideas/check-existing/{username} ⚡ NEW
   * Description: Checks if there's already an existing analysis (completed or active) for a profile with intelligent duplicate prevention.
   * Usage: Prevents duplicate analysis creation, enables immediate access to existing results, and optimizes resource utilization.
   */
  @Get('/ideas/check-existing/:username')
  checkExistingViralAnalysis(
    @Param('username') username: string,
  ): Promise<ViralDiscoveryResponseDto> {
    return this.discoveryService.checkExistingViralAnalysis(username);
  }

  /**
   * POST /api/viral-ideas/queue/{queue_id}/start ⚡
   * Viral Analysis Queue Signal with Intelligent Worker Process Coordination
   *
   * Description: The Start Viral Analysis endpoint provides comprehensive queue signaling and worker coordination
   * for viral content analysis workflows. This endpoint serves as a critical trigger mechanism that signals the
   * background processing system that a specific viral ideas analysis job is ready for processing.
   *
   * Key Features:
   * - Queue Signal Management: Intelligent signaling system for background worker process coordination
   * - Job State Verification: Comprehensive queue entry validation and status verification before processing
   * - Worker Process Integration: Seamless coordination with background ViralIdeasProcessor workers
   * - Status Tracking: Real-time status monitoring and progress tracking throughout the analysis lifecycle
   *
   * Usage: Manual analysis triggers, priority processing, queue management, development testing, administrative control.
   */
  @Post('/ideas/queue/:queue_id/start')
  async startViralAnalysisProcessing(
    @Param('queue_id') queueId: string,
  ): Promise<StartViralAnalysisResponseDto | AlreadyProcessingResponseDto> {
    return await this.startViralAnalysisService.startViralAnalysisProcessing(
      queueId,
    );
  }

  /**
   * POST /api/viral-ideas/queue/{queue_id}/process ⚡ NEW
   * Description: Immediately triggers the processing of a specific item in the queue.
   * Usage: Administrative tool for immediate processing, debugging, and manual intervention.
   */
  @Post('/ideas/queue/:queue_id/process')
  processViralAnalysisQueue(@Param('queue_id') queueId: string) {
    return this.queueService.processViralAnalysisQueue(queueId);
  }

  /**
   * POST /api/viral-ideas/process-pending ⚡
   * Batch Processing Engine for Pending Viral Ideas Queue Management
   *
   * Description: This endpoint provides comprehensive batch processing capabilities for pending viral ideas
   * analysis jobs in the queue. It identifies all pending queue entries, signals them for processing,
   * and coordinates with background workers to ensure efficient queue management and processing.
   *
   * Key Features:
   * - Batch Queue Processing: Processes all pending, failed, and paused queue entries in a single operation
   * - Intelligent Entry Validation: Validates each queue entry before processing to ensure data integrity
   * - Worker Coordination: Signals background workers to pick up processed entries for analysis
   * - Comprehensive Statistics: Provides detailed processing statistics and results tracking
   *
   * Usage: Administrative queue management, batch processing operations, queue health maintenance, system cleanup.
   */
  @Post('/ideas/process-pending')
  async processPendingViralIdeas(): Promise<ProcessPendingViralIdeasResponseDto> {
    return await this.processPendingViralIdeasService.processPendingViralIdeas();
  }

  /**
   * GET /api/viral-ideas/queue-status ⚡ NEW
   * Description: Gets overall statistics for the viral ideas queue.
   * Usage: A dashboard-like feature to monitor the health of the processing queue.
   */
  @Get('/ideas/queue-status')
  getViralIdeasQueueOverallStatus() {
    return this.queueService.getViralIdeasQueueOverallStatus();
  }

  /**
   * GET /api/viral-analysis/{queue_id}/results ⚡ NEW
   * Retrieves the final results of a viral analysis job with comprehensive analysis data, reels, and insights
   *
   * Description: This endpoint retrieves the complete, processed results of a viral ideas analysis job.
   * It serves as the primary data source for displaying comprehensive analysis results to users,
   * aggregating data from multiple database tables to provide a unified response.
   *
   * Key Features:
   * - Multi-table data aggregation from 7+ database tables
   * - Flexible JSONB analysis data supporting multiple workflow versions
   * - Real-time CDN URL generation for profile images
   * - Legacy compatibility for backward-compatible frontend integrations
   * - Enhanced content transformation using working endpoint patterns
   * - Performance-optimized queries with proper indexing
   *
   * Usage: Fetches the data to be displayed on the frontend once an analysis is complete.
   */
  @Get('/analysis/:queue_id/results')
  async getViralAnalysisResults(
    @Param('queue_id') queueId: string,
  ): Promise<ViralAnalysisResultsResponseDto> {
    return await this.viralAnalysisResultsService.getViralAnalysisResults(
      queueId,
    );
  }

  /**
   * GET /api/viral-analysis/{queue_id}/content ⚡ NEW
   * Description: Retrieves the content that was analyzed as part of a job.
   * Usage: To show the source content alongside the analysis results.
   */
  @Get('/analysis/:queue_id/content')
  getViralAnalysisContent(@Param('queue_id') queueId: string) {
    return this.analysisService.getViralAnalysisContent(queueId);
  }

  /**
   * GET /api/viral-ideas/queue-status ⚡ NEW
   * Gets comprehensive statistics and monitoring data for the viral ideas processing queue
   *
   * Description: This endpoint serves as the primary system monitoring and dashboard endpoint
   * for the viral ideas analysis pipeline. It provides real-time insights into queue health,
   * processing performance, and recent activity patterns.
   *
   * Key Features:
   * - Real-time queue statistics across all status categories
   * - Recent activity monitoring with the latest 10 submissions
   * - Performance metrics including progress tracking and timing
   * - Content strategy insights from form data aggregation
   * - System health indicators for operational monitoring
   *
   * Usage: Administrative dashboards, user status displays, performance analytics,
   * capacity planning, and error detection.
   */
  @Get('/ideas/queue-status')
  async getQueueStatus(): Promise<QueueStatusResponseDto> {
    return await this.overallQueueStatusService.getQueueStatus();
  }
}
