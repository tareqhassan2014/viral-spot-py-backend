import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  PrimaryProfile,
  PrimaryProfileDocument,
} from '../../profile/schemas/primary-profile.schema';
import {
  GetUserContentResponseDto,
  UserContentItemDto,
} from '../dto/get-user-content.dto';
import { Content, ContentDocument } from '../schemas/content.schema';

@Injectable()
export class UserContentService {
  private readonly logger = new Logger(UserContentService.name);

  constructor(
    @InjectModel(Content.name)
    private contentModel: Model<ContentDocument>,
    @InjectModel(PrimaryProfile.name)
    private primaryProfileModel: Model<PrimaryProfileDocument>,
  ) {}

  /**
   * GET /api/content/user/{username} ⚡
   * Comprehensive User Content Retrieval with Advanced Analytics and Frontend Optimization
   *
   * Description: Fetches content from a user's own profile through the ViralSpot analysis pipeline
   * and interface. Supports pagination and sorting to make it easy for users to browse their own
   * content library and analyze their content strategy, performance, and viral potential.
   * Usage: Self-analysis, content strategy optimization, performance tracking, and content library browsing.
   */
  async getUserContent(
    username: string,
    limit: number = 24,
    offset: number = 0,
    sortBy: string = 'recent',
  ): Promise<GetUserContentResponseDto> {
    this.logger.log(
      `⚡ Getting user content for: ${username}, limit: ${limit}, offset: ${offset}, sort_by: ${sortBy}`,
    );

    const startTime = Date.now();

    try {
      // Validate sort_by parameter
      const validSortOptions = ['recent', 'popular', 'views', 'likes'];
      const validatedSortBy = validSortOptions.includes(sortBy)
        ? sortBy
        : 'recent';

      // Build aggregation pipeline for efficient JOIN and filtering
      const pipeline: any[] = [];

      // 1. Match content by username
      pipeline.push({
        $match: { username },
      });

      // 2. Lookup profile data (equivalent to JOIN)
      pipeline.push({
        $lookup: {
          from: 'primary_profiles',
          localField: 'profile_id',
          foreignField: '_id',
          as: 'primary_profiles',
          pipeline: [
            {
              $project: {
                username: 1,
                profile_name: 1,
                bio: 1,
                followers: 1,
                profile_image_url: 1,
                profile_image_path: 1,
                is_verified: 1,
                account_type: 1,
              },
            },
          ],
        },
      });

      // 3. Unwind the profile array (should be single item)
      pipeline.push({
        $unwind: {
          path: '$primary_profiles',
          preserveNullAndEmptyArrays: true,
        },
      });

      // 4. Apply sorting based on sort_by parameter
      const sortStage = this.buildSortStage(validatedSortBy);
      pipeline.push({ $sort: sortStage });

      // 5. Apply pagination
      pipeline.push({ $skip: offset });
      pipeline.push({ $limit: limit + 1 }); // Get one extra to check for more pages

      // 6. Execute aggregation
      const contentItems = await this.contentModel.aggregate(pipeline).exec();

      // Handle empty results
      if (!contentItems || contentItems.length === 0) {
        const processingTime = Date.now() - startTime;
        this.logger.log(
          `✅ No content found for @${username} (${processingTime}ms)`,
        );
        return {
          success: true,
          data: {
            reels: [],
            total_count: 0,
            has_more: false,
            username,
            sort_by: validatedSortBy,
          },
          message: 'No content found for this user',
        };
      }

      // 7. Check for more pages and trim results
      const hasMore = contentItems.length > limit;
      const itemsToReturn = contentItems.slice(0, limit);

      // 8. Transform content for frontend using the same logic as other endpoints
      const transformedContent = itemsToReturn
        .map((item) =>
          this.transformContentForFrontend(
            item as ContentDocument & {
              primary_profiles?: PrimaryProfileDocument;
            },
          ),
        )
        .filter((item) => item !== null);

      const processingTime = Date.now() - startTime;

      this.logger.log(
        `✅ Found ${transformedContent.length} content items for ${username} (${processingTime}ms)`,
      );

      return {
        success: true,
        data: {
          reels: transformedContent,
          total_count: transformedContent.length,
          has_more: hasMore,
          username,
          sort_by: validatedSortBy,
        },
        message: `Retrieved ${transformedContent.length} content items successfully`,
      };
    } catch (error) {
      this.logger.error(
        `❌ Error getting user content for ${username}: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
      throw error;
    }
  }

  private buildSortStage(sortBy: string): Record<string, number> {
    switch (sortBy) {
      case 'popular':
        return { outlier_score: -1 };
      case 'views':
        return { view_count: -1 };
      case 'likes':
        return { like_count: -1 };
      default: // recent
        return { date_posted: -1 };
    }
  }

  private transformContentForFrontend(
    item: ContentDocument & {
      primary_profiles?: PrimaryProfileDocument;
    },
  ): UserContentItemDto | null {
    if (!item) return null;

    try {
      // Get profile data (from aggregation)
      const profile = item.primary_profiles;

      // Smart image URL resolution
      let profile_image_url: string | null = null;
      if (profile?.profile_image_path) {
        const cdnBaseUrl = process.env.CDN_BASE_URL || '';
        profile_image_url = cdnBaseUrl
          ? `${cdnBaseUrl}/profile-images/${profile.profile_image_path}`
          : profile.profile_image_path;
      } else if (profile?.profile_image_url) {
        profile_image_url = profile.profile_image_url;
      }

      // Handle content thumbnail URLs
      let thumbnail_url: string | null = null;
      if (item.thumbnail_path) {
        const cdnBaseUrl = process.env.CDN_BASE_URL || '';
        thumbnail_url = cdnBaseUrl
          ? `${cdnBaseUrl}/content-thumbnails/${item.thumbnail_path}`
          : item.thumbnail_path;
      } else if (item.thumbnail_url) {
        thumbnail_url = item.thumbnail_url;
      }

      // Handle video URLs
      let video_url: string | null = null;
      if (item.display_url_path) {
        const cdnBaseUrl = process.env.CDN_BASE_URL || '';
        video_url = cdnBaseUrl
          ? `${cdnBaseUrl}/content-videos/${item.display_url_path}`
          : item.display_url_path;
      } else if (item.url) {
        video_url = item.url;
      }

      // Transform content item with profile data
      return {
        id: item._id?.toString() || item.content_id || '',
        username: item.username || '',
        caption: item.description || '',
        view_count: this.formatNumber(item.view_count || 0),
        like_count: this.formatNumber(item.like_count || 0),
        comment_count: this.formatNumber(item.comment_count || 0),
        share_count: '0', // Not available in current schema
        date_posted: item.date_posted || new Date(),
        content_type: item.content_type || 'reel',
        thumbnail_url,
        video_url,
        outlier_score: Number(item.outlier_score) || 0,

        // Profile information
        profile: {
          username: profile?.username || item.username || '',
          profile_name: profile?.profile_name || '',
          bio: profile?.bio || '',
          followers: this.formatNumber(profile?.followers || 0),
          profile_image_url,
          is_verified: profile?.is_verified || false,
          account_type: profile?.account_type || 'Personal',
        },

        // Additional metadata
        engagement_rate: this.calculateEngagementRate(item, profile),
        performance_score: this.calculatePerformanceScore(item),
        content_url: `https://www.instagram.com/p/${
          item.shortcode || item.content_id || ''
        }/`,
      };
    } catch (error) {
      this.logger.error(
        `❌ Error transforming content item: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
      return null;
    }
  }

  private formatNumber(num: number): string {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }

  private calculateEngagementRate(
    content: ContentDocument,
    profile?: PrimaryProfileDocument,
  ): number {
    if (!profile?.followers || profile.followers === 0) return 0;
    const totalEngagement =
      (content.like_count || 0) + (content.comment_count || 0);
    return Math.round((totalEngagement / profile.followers) * 100 * 100) / 100; // Round to 2 decimal places
  }

  private calculatePerformanceScore(content: ContentDocument): number {
    // Simple performance score based on engagement metrics
    const views = content.view_count || 0;
    const likes = content.like_count || 0;
    const comments = content.comment_count || 0;

    // Weighted score calculation (no shares in current schema)
    return Math.round(views * 0.1 + likes * 0.5 + comments * 0.4);
  }
}
