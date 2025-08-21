import { Controller, Delete, Get, Param, Post } from '@nestjs/common';
import { CacheClearingResponseDto } from './dto/cache-clearing-response.dto';
import { CompetitorAdditionResponseDto } from './dto/competitor-response.dto';
import { GetProfileResponseDto } from './dto/profile-response.dto';
import { ProfileStatusResponseDto } from './dto/profile-status-response.dto';
import { ProfileService } from './profile.service';
import { CompetitorService } from './services/competitor.service';
import { ProfileRetrievalService } from './services/profile-retrieval.service';
import { ProfileStatusService } from './services/profile-status.service';
import { SimilarProfilesCacheService } from './services/similar-profiles-cache.service';

@Controller('/profile')
export class ProfileController {
  constructor(
    private readonly profileService: ProfileService,
    private readonly competitorService: CompetitorService,
    private readonly profileRetrievalService: ProfileRetrievalService,
    private readonly profileStatusService: ProfileStatusService,
    private readonly cacheService: SimilarProfilesCacheService,
  ) {}

  /**
   * GET /api/profile/{username} 🔍
   * Comprehensive Profile Data Retrieval with Advanced Analytics and Frontend Optimization
   *
   * Description: Retrieves detailed profile data for a specific Instagram username with comprehensive
   * analytics, categorization, and frontend-optimized data transformation. Serves as the primary
   * profile data endpoint with intelligent CDN image handling and performance optimization.
   * Usage: Profile page display, analytics dashboard, competitive analysis, and user profile management.
   */
  @Get('/:username')
  async getProfile(
    @Param('username') username: string,
  ): Promise<GetProfileResponseDto> {
    return await this.profileRetrievalService.getProfile(username);
  }

  /**
   * GET /api/profile/{username}/reels
   * Description: Fetches all the reels associated with a specific profile.
   * Usage: Populates the reels section of a profile's page.
   */
  @Get('/:username/reels')
  getProfileReels(@Param('username') username: string) {
    return this.profileService.getProfileReels(username);
  }

  /**
   * GET /api/profile/{username}/similar
   * Description: Gets a list of similar profiles. This is the standard endpoint for similarity checks.
   * Usage: Suggests other profiles to the user.
   */
  @Get('/:username/similar')
  getSimilarProfiles(@Param('username') username: string) {
    return this.profileService.getSimilarProfiles(username);
  }

  /**
   * GET /api/profile/{username}/similar-fast ⚡ NEW
   * Description: A new, faster endpoint for retrieving similar profiles with 24hr caching.
   * Usage: An optimized alternative to the standard /similar endpoint with CDN-delivered images.
   */
  @Get('/:username/similar-fast')
  getSimilarProfilesFast(@Param('username') username: string) {
    return this.profileService.getSimilarProfilesFast(username);
  }

  /**
   * DELETE /api/profile/{username}/similar-cache ⚡
   * Advanced Cache Management for Similar Profiles with Performance Optimization
   *
   * Description: Provides comprehensive cache management capabilities for similar profiles data
   * with intelligent performance optimization. Serves as a critical cache invalidation tool that
   * enables real-time cache refresh for similar profiles optimization.
   * Usage: Cache refresh, administrative management, development testing, and data consistency.
   */
  @Delete('/:username/similar-cache')
  async clearSimilarProfilesCache(
    @Param('username') username: string,
  ): Promise<CacheClearingResponseDto> {
    return this.cacheService.clearCacheForProfile(username);
  }

  /**
   * GET /api/profile/{username}/secondary
   * Description: Retrieves secondary (discovered) profiles associated with a primary profile.
   * Usage: Can be used to show how the network of profiles is expanding.
   */
  @Get('/:username/secondary')
  getSecondaryProfiles(@Param('username') username: string) {
    return this.profileService.getSecondaryProfiles(username);
  }

  /**
   * GET /api/profile/{username}/status 🔍
   * Comprehensive Real-time Profile Processing Status Tracking
   *
   * Description: Provides comprehensive real-time profile processing status tracking with advanced
   * state monitoring and intelligent polling optimization. Serves as the primary status monitoring
   * interface for profile processing workflows.
   * Usage: Real-time status updates, progress monitoring, queue management, and error detection.
   */
  @Get('/:username/status')
  async checkProfileStatus(
    @Param('username') username: string,
  ): Promise<ProfileStatusResponseDto> {
    return this.profileStatusService.checkProfileStatus(username);
  }

  /**
   * POST /api/profile/{username}/request
   * Description: Submits a request to scrape and analyze a new profile.
   * Usage: The primary way for users to add new profiles to the system.
   */
  @Post('/:username/request')
  requestProfileProcessing(@Param('username') username: string) {
    return this.profileService.requestProfileProcessing(username);
  }

  /**
   * POST /api/profile/{primary_username}/add-competitor/{target_username} ⚡
   * Manual Competitor Addition with Intelligent Profile Processing and Storage Management
   *
   * Description: Adds a target_username as a competitor to a primary_username with comprehensive
   * profile data fetching, duplicate prevention, and intelligent fallback handling.
   * Usage: Strategic competitor tracking, custom competitor lists, and competitive intelligence.
   */
  @Post('/:primary_username/add-competitor/:target_username')
  async addManualCompetitor(
    @Param('primary_username') primaryUsername: string,
    @Param('target_username') targetUsername: string,
  ): Promise<CompetitorAdditionResponseDto> {
    return await this.competitorService.addManualCompetitor(
      primaryUsername,
      targetUsername,
    );
  }
}
