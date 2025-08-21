import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  PrimaryProfile,
  PrimaryProfileDocument,
} from '../../profile/schemas/primary-profile.schema';
import {
  CompetitorContentItemDto,
  GetCompetitorContentResponseDto,
} from '../dto/get-competitor-content.dto';
import { Content, ContentDocument } from '../schemas/content.schema';

@Injectable()
export class CompetitorContentService {
  private readonly logger = new Logger(CompetitorContentService.name);

  constructor(
    @InjectModel(Content.name)
    private contentModel: Model<ContentDocument>,
    @InjectModel(PrimaryProfile.name)
    private primaryProfileModel: Model<PrimaryProfileDocument>,
  ) {}

  /**
   * GET /api/content/competitor/{username} ⚡
   * Comprehensive Competitor Content Retrieval with Advanced Analytics and Performance Optimization
   *
   * Description: Fetches content from a competitor's profile for competitive analysis. This endpoint
   * is a key part of the competitor analysis feature, allowing users to retrieve and analyze competitor
   * content strategies, identify trends, and understand what performs well in their niche.
   * Usage: Competitor analysis, content strategy comparison, trend identification, and performance benchmarking.
   */
  async getCompetitorContent(
    username: string,
    limit: number = 24,
    offset: number = 0,
    sortBy: string = 'popular',
  ): Promise<GetCompetitorContentResponseDto> {
    this.logger.log(
      `⚡ Getting competitor content for: ${username}, limit: ${limit}, offset: ${offset}, sort_by: ${sortBy}`,
    );

    const startTime = Date.now();

    try {
      // Validate sort_by parameter
      const validSortOptions = ['popular', 'recent', 'views', 'likes'];
      const validatedSortBy = validSortOptions.includes(sortBy)
        ? sortBy
        : 'popular';

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
          `✅ No content found for competitor @${username} (${processingTime}ms)`,
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
          message: 'No content found for this competitor',
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
        `✅ Found ${transformedContent.length} content items for competitor ${username} (${processingTime}ms)`,
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
        message: `Retrieved ${transformedContent.length} competitor content items successfully`,
      };
    } catch (error) {
      this.logger.error(
        `❌ Error getting competitor content for ${username}: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
      throw error;
    }
  }

  private buildSortStage(sortBy: string): Record<string, number> {
    switch (sortBy) {
      case 'recent':
        return { date_posted: -1 };
      case 'views':
        return { view_count: -1 };
      case 'likes':
        return { like_count: -1 };
      default: // popular
        return { outlier_score: -1 };
    }
  }

  private transformContentForFrontend(
    item: ContentDocument & {
      primary_profiles?: PrimaryProfileDocument;
    },
  ): CompetitorContentItemDto | null {
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

      // Transform content item with profile data (matching ProfileReelsService structure)
      return {
        // Content identifiers
        id: item.content_id || '',
        reel_id: item.content_id || '',
        content_id: item.content_id || '',
        content_type: item.content_type || 'reel',
        shortcode: item.shortcode || '',
        url: item.url || '',
        description: item.description || '',
        title: item.description || '', // Alias for frontend

        // Media
        thumbnail_url,
        thumbnail_local: thumbnail_url, // For compatibility
        thumbnail: thumbnail_url, // For compatibility

        // Metrics
        view_count: item.view_count || 0,
        like_count: item.like_count || 0,
        comment_count: item.comment_count || 0,
        outlier_score: Number(item.outlier_score) || 0,
        outlierScore: this.formatOutlierScore(Number(item.outlier_score) || 0),

        // Dates
        date_posted: item.date_posted || new Date(),

        // Profile information
        username: item.username || '',
        profile: `@${item.username || ''}`,
        profile_name: profile?.profile_name || '',
        bio: profile?.bio || '',
        profile_followers: profile?.followers || 0,
        followers: profile?.followers || 0, // For compatibility
        profile_image_url,
        profileImage: profile_image_url, // For compatibility
        is_verified: profile?.is_verified || false,
        account_type: profile?.account_type || 'Personal',

        // Content categorization
        primary_category: item.primary_category || null,
        secondary_category: item.secondary_category || null,
        tertiary_category: item.tertiary_category || null,
        keyword_1: item.keyword_1 || null,
        keyword_2: item.keyword_2 || null,
        keyword_3: item.keyword_3 || null,
        keyword_4: item.keyword_4 || null,
        categorization_confidence: Number(item.categorization_confidence) || 0,
        content_style: item.content_style || 'video',
        language: item.language || 'en',

        // Formatted numbers for display
        views: this.formatNumber(item.view_count || 0),
        likes: this.formatNumber(item.like_count || 0),
        comments: this.formatNumber(item.comment_count || 0),
      };
    } catch (error) {
      this.logger.error(
        `❌ Error transforming competitor content item: ${error instanceof Error ? error.message : 'Unknown error'}`,
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

  private formatOutlierScore(score: number): string {
    return score.toFixed(1) + 'x';
  }
}
