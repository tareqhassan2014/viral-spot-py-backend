import { Controller, Get, Param, Query } from '@nestjs/common';
import { ContentService } from './content.service';
import {
  GetCompetitorContentQueryDto,
  GetCompetitorContentResponseDto,
} from './dto/get-competitor-content.dto';
import { GetReelsQueryDto, GetReelsResponseDto } from './dto/get-reels.dto';
import {
  GetUserContentQueryDto,
  GetUserContentResponseDto,
} from './dto/get-user-content.dto';
import { CompetitorContentService } from './services/competitor-content.service';
import { ReelsService } from './services/reels.service';
import { UserContentService } from './services/user-content.service';

@Controller('/content')
export class ContentController {
  constructor(
    private readonly contentService: ContentService,
    private readonly userContentService: UserContentService,
    private readonly competitorContentService: CompetitorContentService,
    private readonly reelsService: ReelsService,
  ) {}

  /**
   * GET /api/content/reels ⚡
   * Comprehensive Reels Discovery with Advanced Filtering, Sorting, and Pagination
   *
   * Description: This is the main endpoint for browsing and discovering viral content in the ViralSpot platform.
   * It provides a powerful set of filters to allow users to narrow down the content they are interested in.
   * The results are paginated to ensure efficient loading and browsing.
   * Usage: Content discovery, viral content browsing, filtered content search, and trending content analysis.
   */
  @Get('/reels')
  async getReels(
    @Query() query: GetReelsQueryDto,
  ): Promise<GetReelsResponseDto> {
    return await this.reelsService.getReels(query);
  }

  /**
   * GET /api/content/posts
   * Description: Retrieves a list of posts, likely with filtering and pagination.
   * Usage: For browsing content that is not in video format.
   */
  @Get('/posts')
  getPosts(
    @Query('page') page?: number,
    @Query('limit') limit?: number,
    @Query('filter') filter?: string,
    @Query('sort') sort?: string,
  ) {
    return this.contentService.getPosts({
      page: page || 1,
      limit: limit || 20,
      filter,
      sort,
    });
  }

  /**
   * GET /api/content/competitor/{username} ⚡
   * Comprehensive Competitor Content Retrieval with Advanced Analytics and Performance Optimization
   *
   * Description: Fetches content from a competitor's profile for competitive analysis. This endpoint
   * is a key part of the competitor analysis feature, allowing users to retrieve and analyze competitor
   * content strategies, identify trends, and understand what performs well in their niche.
   * Usage: Competitor analysis, content strategy comparison, trend identification, and performance benchmarking.
   */
  @Get('/competitor/:username')
  async getCompetitorContent(
    @Param('username') username: string,
    @Query() query: GetCompetitorContentQueryDto,
  ): Promise<GetCompetitorContentResponseDto> {
    return await this.competitorContentService.getCompetitorContent(
      username,
      query.limit,
      query.offset,
      query.sort_by,
    );
  }

  /**
   * GET /api/content/user/{username} ⚡
   * Comprehensive User Content Retrieval with Advanced Analytics and Frontend Optimization
   *
   * Description: Fetches content from a user's own profile through the ViralSpot analysis pipeline
   * and interface. Supports pagination and sorting to make it easy for users to browse their own
   * content library and analyze their content strategy, performance, and viral potential.
   * Usage: Self-analysis, content strategy optimization, performance tracking, and content library browsing.
   */
  @Get('/user/:username')
  async getUserContent(
    @Param('username') username: string,
    @Query() query: GetUserContentQueryDto,
  ): Promise<GetUserContentResponseDto> {
    return await this.userContentService.getUserContent(
      username,
      query.limit,
      query.offset,
      query.sort_by,
    );
  }
}
