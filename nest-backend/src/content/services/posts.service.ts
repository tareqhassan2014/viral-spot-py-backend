import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  PrimaryProfile,
  PrimaryProfileDocument,
} from '../../profile/schemas/primary-profile.schema';
import { GetPostsQueryDto, GetPostsResponseDto } from '../dto/get-posts.dto';
import { GetReelsQueryDto } from '../dto/get-reels.dto';
import { Content, ContentDocument } from '../schemas/content.schema';
import { ReelsService } from './reels.service';

@Injectable()
export class PostsService {
  private readonly logger = new Logger(PostsService.name);

  constructor(
    @InjectModel(Content.name)
    private contentModel: Model<ContentDocument>,
    @InjectModel(PrimaryProfile.name)
    private primaryProfileModel: Model<PrimaryProfileDocument>,
    private readonly reelsService: ReelsService,
  ) {}

  /**
   * GET /api/content/posts ⚡
   * Posts Discovery with Advanced Filtering and Pagination
   *
   * Description: This endpoint is used for browsing content that is not in video format, such as single images or carousels.
   * It functions very similarly to the /api/reels endpoint and reuses the same underlying logic.
   * The main difference is that it is hardcoded to only return content of the 'post' type.
   * Usage: Image content discovery, carousel browsing, photo-based content analysis.
   */
  async getPosts(filters: GetPostsQueryDto): Promise<GetPostsResponseDto> {
    this.logger.log(
      `⚡ Getting posts with filters: search=${filters.search}, sort_by=${filters.sort_by}, limit=${filters.limit}`,
    );

    const startTime = Date.now();

    try {
      // Convert posts filters to reels filters and add content_type filter
      const reelsFilters: GetReelsQueryDto = {
        ...filters,
        content_types: 'post', // Key difference: hardcoded to 'post'
        // Posts don't have view-related filters, so we don't include them
        min_views: undefined,
        max_views: undefined,
        min_followers: undefined,
        max_followers: undefined,
        account_types: undefined,
        languages: undefined,
        content_styles: undefined,
        min_account_engagement_rate: undefined,
        max_account_engagement_rate: undefined,
        tertiary_categories: undefined, // Posts have fewer category levels in the docs
      };

      // Reuse the reels service logic with posts-specific filters
      const reelsResponse = await this.reelsService.getReels(reelsFilters);

      // Transform the response to posts format
      const postsResponse: GetPostsResponseDto = {
        success: reelsResponse.success,
        data: {
          reels: reelsResponse.data.reels, // Note: still called 'reels' for frontend compatibility
          isLastPage: reelsResponse.data.isLastPage,
        },
        message: reelsResponse.message?.replace('reels', 'posts'),
      };

      const processingTime = Date.now() - startTime;

      this.logger.log(
        `✅ Returned ${postsResponse.data.reels.length} posts, isLastPage: ${postsResponse.data.isLastPage} (${processingTime}ms)`,
      );

      return postsResponse;
    } catch (error) {
      this.logger.error(
        `❌ Error getting posts: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
      throw error;
    }
  }
}
