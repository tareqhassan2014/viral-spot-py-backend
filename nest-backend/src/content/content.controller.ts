import { Controller, Get, Param, Query } from '@nestjs/common';
import { ContentService } from './content.service';
import {
  GetUserContentQueryDto,
  GetUserContentResponseDto,
} from './dto/get-user-content.dto';
import { UserContentService } from './services/user-content.service';

@Controller('/content')
export class ContentController {
  constructor(
    private readonly contentService: ContentService,
    private readonly userContentService: UserContentService,
  ) {}

  /**
   * GET /api/content/reels
   * Description: Retrieves a list of reels, with support for filtering and pagination.
   * Usage: The main endpoint for browsing and discovering viral content.
   */
  @Get('/reels')
  getReels(
    @Query('page') page?: number,
    @Query('limit') limit?: number,
    @Query('filter') filter?: string,
    @Query('sort') sort?: string,
  ) {
    return this.contentService.getReels({
      page: page || 1,
      limit: limit || 20,
      filter,
      sort,
    });
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
   * GET /api/content/competitor/{username} ⚡ NEW
   * Description: Fetches content from a competitor's profile.
   * Usage: Used in the competitor analysis feature to compare content strategies.
   */
  @Get('/competitor/:username')
  getCompetitorContent(@Param('username') username: string) {
    return this.contentService.getCompetitorContent(username);
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
