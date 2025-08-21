import { Controller, Delete, Get, Param, Post, Query } from '@nestjs/common';
import { CacheClearingResponseDto } from './dto/cache-clearing-response.dto';
import { CompetitorAdditionResponseDto } from './dto/competitor-response.dto';
import {
  GetProfileReelsQueryDto,
  GetProfileReelsResponseDto,
} from './dto/profile-reels.dto';
import { GetProfileResponseDto } from './dto/profile-response.dto';
import { ProfileStatusResponseDto } from './dto/profile-status-response.dto';
import { GetSecondaryProfileResponseDto } from './dto/secondary-profile.dto';
import {
  GetSimilarProfilesFastQueryDto,
  GetSimilarProfilesFastResponseDto,
} from './dto/similar-profiles-fast.dto';
import {
  GetSimilarProfilesQueryDto,
  GetSimilarProfilesResponseDto,
} from './dto/similar-profiles.dto';
import { ProfileService } from './profile.service';
import { CompetitorService } from './services/competitor.service';
import { ProfileReelsService } from './services/profile-reels.service';
import { ProfileRetrievalService } from './services/profile-retrieval.service';
import { ProfileStatusService } from './services/profile-status.service';
import { SecondaryProfileService } from './services/secondary-profile.service';
import { SimilarProfilesCacheService } from './services/similar-profiles-cache.service';
import { SimilarProfilesFastService } from './services/similar-profiles-fast.service';
import { SimilarProfilesService } from './services/similar-profiles.service';

@Controller('/profile')
export class ProfileController {
  constructor(
    private readonly profileService: ProfileService,
    private readonly competitorService: CompetitorService,
    private readonly profileRetrievalService: ProfileRetrievalService,
    private readonly profileReelsService: ProfileReelsService,
    private readonly similarProfilesService: SimilarProfilesService,
    private readonly similarProfilesFastService: SimilarProfilesFastService,
    private readonly profileStatusService: ProfileStatusService,
    private readonly cacheService: SimilarProfilesCacheService,
    private readonly secondaryProfileService: SecondaryProfileService,
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
   * GET /api/profile/{username}/reels 🎬
   * Advanced Profile Reels Retrieval with Intelligent Sorting and Pagination
   *
   * Description: Fetches all reels associated with a specific profile with comprehensive
   * sorting options, pagination support, and complete profile data integration. Supports
   * popular, recent, and oldest sorting with efficient MongoDB aggregation pipeline.
   * Usage: Profile reels display, content browsing, timeline navigation, and viral content discovery.
   */
  @Get('/:username/reels')
  async getProfileReels(
    @Param('username') username: string,
    @Query() query: GetProfileReelsQueryDto,
  ): Promise<GetProfileReelsResponseDto> {
    return await this.profileReelsService.getProfileReels(
      username,
      query.sort_by,
      query.limit,
      query.offset,
    );
  }

  /**
   * GET /api/profile/{username}/similar 🎯
   * Advanced Similar Profiles Discovery with Intelligent Ranking and Comprehensive Analysis
   *
   * Description: Gets a list of similar profiles for a specific user based on sophisticated similarity
   * ranking algorithms, including comprehensive profile data, multi-level categorization, and detailed
   * analysis metadata. Provides intelligent profile recommendations for content discovery and competitive analysis.
   * Usage: Profile recommendations, content discovery, competitive intelligence, and audience expansion.
   */
  @Get('/:username/similar')
  async getSimilarProfiles(
    @Param('username') username: string,
    @Query() query: GetSimilarProfilesQueryDto,
  ): Promise<GetSimilarProfilesResponseDto> {
    return await this.similarProfilesService.getSimilarProfiles(
      username,
      query.limit,
    );
  }

  /**
   * GET /api/profile/{username}/similar-fast ⚡
   * High-Performance Similar Profiles with Advanced Caching and CDN Optimization
   *
   * Description: Optimized endpoint for retrieving similar profiles with 24-hour caching,
   * CDN-delivered images, and intelligent fallback strategies. Supports up to 80 profiles
   * per request with lightning-fast cached responses and comprehensive retry logic.
   * Usage: High-performance profile recommendations, cached content discovery, and optimized user experience.
   */
  @Get('/:username/similar-fast')
  async getSimilarProfilesFast(
    @Param('username') username: string,
    @Query() query: GetSimilarProfilesFastQueryDto,
  ): Promise<GetSimilarProfilesFastResponseDto> {
    return await this.similarProfilesFastService.getSimilarProfilesFast(
      username,
      query.limit,
      query.force_refresh,
    );
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
    return await this.cacheService.clearCacheForProfile(username);
  }

  /**
   * GET /api/profile/{username}/secondary
   * Retrieves Secondary (Discovered) Profile Data for Loading States and Previews
   *
   * Description: Fetches data for a secondary profile, which is a profile that has been discovered
   * through the analysis of a primary profile. Primarily intended for displaying loading states
   * or profile previews before full data is fetched.
   * Usage: Loading states, profile previews, quick profile cards, profile discovery, competitor research.
   */
  @Get('/:username/secondary')
  async getSecondaryProfile(
    @Param('username') username: string,
  ): Promise<GetSecondaryProfileResponseDto> {
    return await this.secondaryProfileService.getSecondaryProfile(username);
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
    return await this.profileStatusService.checkProfileStatus(username);
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
