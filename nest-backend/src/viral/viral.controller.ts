import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { ViralService } from './viral.service';

@Controller('api')
export class ViralController {
  constructor(private readonly viralService: ViralService) {}

  /**
   * POST /api/viral-ideas/queue ⚡ NEW
   * Description: Creates a new viral ideas analysis job and adds it to the queue.
   * Usage: Kicks off the AI pipeline to find viral trends.
   */
  @Post('viral-ideas/queue')
  createViralIdeasQueue(@Body() queueData: any) {
    return this.viralService.createViralIdeasQueue(queueData);
  }

  /**
   * GET /api/viral-ideas/queue/{session_id} ⚡ NEW
   * Description: Retrieves the status of a specific viral ideas analysis job from the queue.
   * Usage: Polling for real-time updates on the analysis progress.
   */
  @Get('viral-ideas/queue/:session_id')
  getViralIdeasQueueStatus(@Param('session_id') sessionId: string) {
    return this.viralService.getViralIdeasQueueStatus(sessionId);
  }

  /**
   * GET /api/viral-ideas/check-existing/{username} ⚡ NEW
   * Description: Checks if there's already an existing analysis (completed or active) for a profile with intelligent duplicate prevention.
   * Usage: Prevents duplicate analysis creation, enables immediate access to existing results, and optimizes resource utilization.
   */
  @Get('viral-ideas/check-existing/:username')
  checkExistingViralAnalysis(@Param('username') username: string) {
    return this.viralService.checkExistingViralAnalysis(username);
  }

  /**
   * POST /api/viral-ideas/queue/{queue_id}/start ⚡ NEW
   * Description: Signals a queued analysis job as ready for background worker processing.
   * Usage: Queue signaling and worker coordination for viral analysis jobs.
   */
  @Post('viral-ideas/queue/:queue_id/start')
  startViralAnalysisProcessing(@Param('queue_id') queueId: string) {
    return this.viralService.startViralAnalysisProcessing(queueId);
  }

  /**
   * POST /api/viral-ideas/queue/{queue_id}/process ⚡ NEW
   * Description: Immediately triggers the processing of a specific item in the queue.
   * Usage: Administrative tool for immediate processing, debugging, and manual intervention.
   */
  @Post('viral-ideas/queue/:queue_id/process')
  processViralAnalysisQueue(@Param('queue_id') queueId: string) {
    return this.viralService.processViralAnalysisQueue(queueId);
  }

  /**
   * POST /api/viral-ideas/process-pending ⚡ NEW
   * Description: Processes all pending items in the viral ideas queue.
   * Usage: A batch operation to clear the queue and process multiple jobs.
   */
  @Post('viral-ideas/process-pending')
  processPendingViralIdeas() {
    return this.viralService.processPendingViralIdeas();
  }

  /**
   * GET /api/viral-ideas/queue-status ⚡ NEW
   * Description: Gets overall statistics for the viral ideas queue.
   * Usage: A dashboard-like feature to monitor the health of the processing queue.
   */
  @Get('viral-ideas/queue-status')
  getViralIdeasQueueOverallStatus() {
    return this.viralService.getViralIdeasQueueOverallStatus();
  }

  /**
   * GET /api/viral-analysis/{queue_id}/results ⚡ NEW
   * Description: Retrieves the final results of a viral analysis job.
   * Usage: Fetches the data to be displayed on the frontend once an analysis is complete.
   */
  @Get('viral-analysis/:queue_id/results')
  getViralAnalysisResults(@Param('queue_id') queueId: string) {
    return this.viralService.getViralAnalysisResults(queueId);
  }

  /**
   * GET /api/viral-analysis/{queue_id}/content ⚡ NEW
   * Description: Retrieves the content that was analyzed as part of a job.
   * Usage: To show the source content alongside the analysis results.
   */
  @Get('viral-analysis/:queue_id/content')
  getViralAnalysisContent(@Param('queue_id') queueId: string) {
    return this.viralService.getViralAnalysisContent(queueId);
  }
}
