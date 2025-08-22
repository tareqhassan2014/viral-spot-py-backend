import { Controller, Get, Param, Query } from '@nestjs/common';
import {
  GetCompetitorContentQueryDto,
  GetCompetitorContentResponseDto,
} from './dto/get-competitor-content.dto';
import { GetFilterOptionsResponseDto } from './dto/get-filter-options.dto';
import { GetPostsQueryDto, GetPostsResponseDto } from './dto/get-posts.dto';
import { GetReelsQueryDto, GetReelsResponseDto } from './dto/get-reels.dto';
import {
  GetUserContentQueryDto,
  GetUserContentResponseDto,
} from './dto/get-user-content.dto';
import { CompetitorContentService } from './services/competitor-content.service';
import { FilterOptionsService } from './services/filter-options.service';
import { PostsService } from './services/posts.service';
import { ReelsService } from './services/reels.service';
import { UserContentService } from './services/user-content.service';

@Controller('/content')
export class ContentController {
  constructor(
    private readonly userContentService: UserContentService,
    private readonly competitorContentService: CompetitorContentService,
    private readonly reelsService: ReelsService,
    private readonly postsService: PostsService,
    private readonly filterOptionsService: FilterOptionsService,
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
   * GET /api/content/posts ⚡
   * Posts Discovery with Advanced Filtering and Pagination
   *
   * Description: This endpoint is used for browsing content that is not in video format, such as single images or carousels.
   * It functions very similarly to the /api/reels endpoint and reuses the same underlying logic.
   * The main difference is that it is hardcoded to only return content of the 'post' type.
   * Usage: Image content discovery, carousel browsing, photo-based content analysis.
   */
  @Get('/posts')
  async getPosts(
    @Query() query: GetPostsQueryDto,
  ): Promise<GetPostsResponseDto> {
    return await this.postsService.getPosts(query);
  }

  /**
   * GET /api/content/filter ⚡
   * Dynamic Filter Options Retrieval
   *
   * Description: This is a utility endpoint designed to populate the filter dropdowns and selection menus on the frontend.
   * It dynamically queries the database to find all unique values for the various filterable fields,
   * such as categories, content types, languages, and keywords.
   * Usage: Frontend filter population, dynamic UI generation, database-synced filter options.
   */
  @Get('/filter')
  async getFilterOptions(): Promise<GetFilterOptionsResponseDto> {
    return await this.filterOptionsService.getFilterOptions();
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
