import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { ViralDiscoveryResponseDto } from './dto/viral-discovery-response.dto';
import { GetViralIdeasQueueStatusResponseDto } from './dto/viral-ideas-queue-status.dto';
import {
  CreateViralIdeasQueueDto,
  CreateViralIdeasQueueResponseDto,
} from './dto/viral-ideas-queue.dto';
import { ViralAnalysisService } from './services/viral-analysis.service';
import { ViralDiscoveryService } from './services/viral-discovery.service';
import { ViralIdeasQueueCreationService } from './services/viral-ideas-queue-creation.service';
import { ViralIdeasQueueStatusService } from './services/viral-ideas-queue-status.service';
import { ViralQueueService } from './services/viral-queue.service';

@Controller('/viral')
export class ViralController {
  constructor(
    private readonly discoveryService: ViralDiscoveryService,
    private readonly queueService: ViralQueueService,
    private readonly analysisService: ViralAnalysisService,
    private readonly queueCreationService: ViralIdeasQueueCreationService,
    private readonly queueStatusService: ViralIdeasQueueStatusService,
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
   * POST /api/viral-ideas/queue/{queue_id}/start ⚡ NEW
   * Description: Signals a queued analysis job as ready for background worker processing.
   * Usage: Queue signaling and worker coordination for viral analysis jobs.
   */
  @Post('/ideas/queue/:queue_id/start')
  startViralAnalysisProcessing(@Param('queue_id') queueId: string) {
    return this.queueService.startViralAnalysisProcessing(queueId);
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
   * POST /api/viral-ideas/process-pending ⚡ NEW
   * Description: Processes all pending items in the viral ideas queue.
   * Usage: A batch operation to clear the queue and process multiple jobs.
   */
  @Post('/ideas/process-pending')
  processPendingViralIdeas() {
    return this.queueService.processPendingViralIdeas();
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
   * Description: Retrieves the final results of a viral analysis job.
   * Usage: Fetches the data to be displayed on the frontend once an analysis is complete.
   */
  @Get('/analysis/:queue_id/results')
  getViralAnalysisResults(@Param('queue_id') queueId: string) {
    return this.analysisService.getViralAnalysisResults(queueId);
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
}
