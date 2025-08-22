import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  PrimaryProfile,
  PrimaryProfileDocument,
} from '../../profile/schemas/primary-profile.schema';
import {
  GetReelsQueryDto,
  GetReelsResponseDto,
  ReelItemDto,
} from '../dto/get-reels.dto';
import { Content, ContentDocument } from '../schemas/content.schema';

@Injectable()
export class ReelsService {
  private readonly logger = new Logger(ReelsService.name);
  private readonly sessionStorage = new Map<string, Set<string>>(); // Simple in-memory session storage

  constructor(
    @InjectModel(Content.name)
    private contentModel: Model<ContentDocument>,
    @InjectModel(PrimaryProfile.name)
    private primaryProfileModel: Model<PrimaryProfileDocument>,
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
  async getReels(filters: GetReelsQueryDto): Promise<GetReelsResponseDto> {
    this.logger.log(
      `⚡ Getting reels with filters: search=${filters.search}, sort_by=${filters.sort_by}, limit=${filters.limit}`,
    );

    const startTime = Date.now();
    const { limit = 24, offset = 0 } = filters;

    try {
      // Build MongoDB aggregation pipeline for complex filtering
      const pipeline: any[] = [];

      // 1. Build match conditions for content filtering
      const matchConditions = this.buildContentMatchConditions(filters);
      if (Object.keys(matchConditions).length > 0) {
        pipeline.push({ $match: matchConditions });
      }

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

      // 4. Apply profile-based filtering
      const profileMatchConditions = this.buildProfileMatchConditions(filters);
      if (Object.keys(profileMatchConditions).length > 0) {
        pipeline.push({ $match: profileMatchConditions });
      }

      // 5. Apply sorting
      const sortStage = this.buildSortStage(filters.sort_by);
      pipeline.push({ $sort: sortStage });

      // 6. Apply pagination
      pipeline.push({ $skip: offset });
      pipeline.push({ $limit: limit + 1 }); // Get one extra to check for more pages

      // 7. Execute aggregation
      const results = await this.contentModel.aggregate(pipeline).exec();

      // Handle empty results
      if (!results || results.length === 0) {
        const processingTime = Date.now() - startTime;
        this.logger.log(
          `📭 No reels found for the given filters (${processingTime}ms)`,
        );
        return {
          success: true,
          data: {
            reels: [],
            isLastPage: true,
          },
          message: 'No reels found for the given filters',
        };
      }

      // 8. Check for more pages and trim results
      const hasMore = results.length > limit;
      let itemsToReturn = results.slice(0, limit);

      // 9. Apply random ordering if requested
      if (filters.random_order && filters.session_id) {
        itemsToReturn = this.applyRandomOrdering(
          itemsToReturn as (ContentDocument & {
            primary_profiles?: PrimaryProfileDocument;
          })[],
          filters.session_id,
          limit,
        );
      }

      // 10. Transform content for frontend
      const transformedReels = itemsToReturn
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
        `✅ Returned ${transformedReels.length} reels, isLastPage: ${!hasMore} (${processingTime}ms)`,
      );

      return {
        success: true,
        data: {
          reels: transformedReels,
          isLastPage: !hasMore,
        },
        message: `Retrieved ${transformedReels.length} reels successfully`,
      };
    } catch (error) {
      this.logger.error(
        `❌ Error getting reels: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
      throw error;
    }
  }

  private buildContentMatchConditions(
    filters: GetReelsQueryDto,
  ): Record<string, any> {
    const matchConditions: Record<string, any> = {};

    // Search filter (searches description and username)
    if (filters.search) {
      matchConditions.$or = [
        { description: { $regex: filters.search, $options: 'i' } },
        { username: { $regex: filters.search, $options: 'i' } },
      ];
    }

    // Category filters
    if (filters.primary_categories) {
      const categories = filters.primary_categories
        .split(',')
        .map((c) => c.trim());
      matchConditions.primary_category = { $in: categories };
    }

    if (filters.secondary_categories) {
      const categories = filters.secondary_categories
        .split(',')
        .map((c) => c.trim());
      matchConditions.secondary_category = { $in: categories };
    }

    if (filters.tertiary_categories) {
      const categories = filters.tertiary_categories
        .split(',')
        .map((c) => c.trim());
      matchConditions.tertiary_category = { $in: categories };
    }

    // Keyword search across multiple fields
    if (filters.keywords) {
      const keywords = filters.keywords.split(',').map((k) => k.trim());
      const keywordConditions: any[] = [];

      keywords.forEach((keyword) => {
        const regex = { $regex: keyword, $options: 'i' };
        keywordConditions.push(
          { keyword_1: regex },
          { keyword_2: regex },
          { keyword_3: regex },
          { keyword_4: regex },
          { description: regex },
        );
      });

      if (keywordConditions.length > 0) {
        const existingOr = matchConditions.$or as
          | Record<string, any>[]
          | undefined;
        matchConditions.$or = existingOr
          ? [...existingOr, ...(keywordConditions as Record<string, any>[])]
          : keywordConditions;
      }
    }

    // Numeric range filters
    if (filters.min_outlier_score !== undefined) {
      const existing =
        (matchConditions.outlier_score as Record<string, any>) || {};
      matchConditions.outlier_score = {
        ...existing,
        $gte: filters.min_outlier_score,
      };
    }
    if (filters.max_outlier_score !== undefined) {
      const existing =
        (matchConditions.outlier_score as Record<string, any>) || {};
      matchConditions.outlier_score = {
        ...existing,
        $lte: filters.max_outlier_score,
      };
    }

    if (filters.min_views !== undefined) {
      const existing =
        (matchConditions.view_count as Record<string, any>) || {};
      matchConditions.view_count = {
        ...existing,
        $gte: filters.min_views,
      };
    }
    if (filters.max_views !== undefined) {
      const existing =
        (matchConditions.view_count as Record<string, any>) || {};
      matchConditions.view_count = {
        ...existing,
        $lte: filters.max_views,
      };
    }

    if (filters.min_likes !== undefined) {
      const existing =
        (matchConditions.like_count as Record<string, any>) || {};
      matchConditions.like_count = {
        ...existing,
        $gte: filters.min_likes,
      };
    }
    if (filters.max_likes !== undefined) {
      const existing =
        (matchConditions.like_count as Record<string, any>) || {};
      matchConditions.like_count = {
        ...existing,
        $lte: filters.max_likes,
      };
    }

    if (filters.min_comments !== undefined) {
      const existing =
        (matchConditions.comment_count as Record<string, any>) || {};
      matchConditions.comment_count = {
        ...existing,
        $gte: filters.min_comments,
      };
    }
    if (filters.max_comments !== undefined) {
      const existing =
        (matchConditions.comment_count as Record<string, any>) || {};
      matchConditions.comment_count = {
        ...existing,
        $lte: filters.max_comments,
      };
    }

    // Content type filter
    if (filters.content_types) {
      const types = filters.content_types.split(',').map((t) => t.trim());
      matchConditions.content_type = { $in: types };
    }

    // Language filter
    if (filters.languages) {
      const languages = filters.languages.split(',').map((l) => l.trim());
      matchConditions.language = { $in: languages };
    }

    // Content style filter
    if (filters.content_styles) {
      const styles = filters.content_styles.split(',').map((s) => s.trim());
      matchConditions.content_style = { $in: styles };
    }

    // Date range filter (simplified implementation)
    if (filters.date_range) {
      const dateCondition = this.buildDateRangeCondition(filters.date_range);
      if (dateCondition) {
        matchConditions.date_posted = dateCondition;
      }
    }

    // Exclusion filters
    if (filters.excluded_usernames) {
      const excludedUsers = filters.excluded_usernames
        .split(',')
        .map((u) => u.trim());
      matchConditions.username = { $nin: excludedUsers };
    }

    return matchConditions;
  }

  private buildProfileMatchConditions(
    filters: GetReelsQueryDto,
  ): Record<string, any> {
    const profileMatchConditions: Record<string, any> = {};

    // Follower count filters
    if (filters.min_followers !== undefined) {
      const existing =
        (profileMatchConditions['primary_profiles.followers'] as Record<
          string,
          any
        >) || {};
      profileMatchConditions['primary_profiles.followers'] = {
        ...existing,
        $gte: filters.min_followers,
      };
    }
    if (filters.max_followers !== undefined) {
      const existing =
        (profileMatchConditions['primary_profiles.followers'] as Record<
          string,
          any
        >) || {};
      profileMatchConditions['primary_profiles.followers'] = {
        ...existing,
        $lte: filters.max_followers,
      };
    }

    // Verification filter
    if (filters.is_verified !== undefined) {
      profileMatchConditions['primary_profiles.is_verified'] =
        filters.is_verified;
    }

    // Account type filter
    if (filters.account_types) {
      const types = filters.account_types.split(',').map((t) => t.trim());
      profileMatchConditions['primary_profiles.account_type'] = { $in: types };
    }

    return profileMatchConditions;
  }

  private buildDateRangeCondition(
    dateRange: string,
  ): Record<string, any> | null {
    const now = new Date();
    let startDate: Date;

    switch (dateRange) {
      case 'last_7_days':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case 'last_30_days':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case 'last_90_days':
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        break;
      default:
        return null;
    }

    return { $gte: startDate };
  }

  private buildSortStage(sortBy?: string): Record<string, number> {
    switch (sortBy) {
      case 'views':
        return { view_count: -1 };
      case 'likes':
        return { like_count: -1 };
      case 'comments':
        return { comment_count: -1 };
      case 'recent':
        return { date_posted: -1 };
      case 'oldest':
        return { date_posted: 1 };
      case 'followers':
        return { 'primary_profiles.followers': -1 };
      case 'account_engagement':
      case 'content_engagement':
        // Simplified engagement calculation
        return { like_count: -1, comment_count: -1 };
      default: // 'popular'
        return { outlier_score: -1, view_count: -1 };
    }
  }

  private applyRandomOrdering(
    data: (ContentDocument & { primary_profiles?: PrimaryProfileDocument })[],
    sessionId: string,
    limit: number,
  ): (ContentDocument & { primary_profiles?: PrimaryProfileDocument })[] {
    // Create consistent seed from session ID
    const seed = this.createHashSeed(sessionId);

    // Get seen items from session storage
    const seenIds = this.sessionStorage.get(sessionId) || new Set<string>();

    // Filter out seen items
    const unseenData = data.filter(
      (item) => !seenIds.has(item.content_id || (item._id?.toString() ?? '')),
    );

    // Shuffle with consistent seed
    const shuffled = this.shuffleWithSeed(unseenData, seed);

    // Take only what we need
    const result = shuffled.slice(0, limit);

    // Update seen items in session storage
    result.forEach((item) => {
      seenIds.add(item.content_id || (item._id?.toString() ?? ''));
    });
    this.sessionStorage.set(sessionId, seenIds);

    return result;
  }

  private createHashSeed(sessionId: string): number {
    // Simple hash function to create consistent seed
    let hash = 0;
    for (let i = 0; i < sessionId.length; i++) {
      const char = sessionId.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  private shuffleWithSeed(
    array: (ContentDocument & { primary_profiles?: PrimaryProfileDocument })[],
    seed: number,
  ): (ContentDocument & { primary_profiles?: PrimaryProfileDocument })[] {
    const shuffled = [...array];
    let currentIndex = shuffled.length;

    // Use seed to create predictable randomness
    let random = seed;

    while (currentIndex !== 0) {
      // Generate pseudo-random number
      random = (random * 9301 + 49297) % 233280;
      const randomIndex = Math.floor((random / 233280) * currentIndex);
      currentIndex--;

      // Swap elements
      [shuffled[currentIndex], shuffled[randomIndex]] = [
        shuffled[randomIndex],
        shuffled[currentIndex],
      ];
    }

    return shuffled;
  }

  private transformContentForFrontend(
    item: ContentDocument & {
      primary_profiles?: PrimaryProfileDocument;
    },
  ): ReelItemDto | null {
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

      // Transform content item with profile data
      return {
        id: item.content_id || '',
        content_id: item.content_id || '',
        shortcode: item.shortcode || '',
        url: item.url || '',
        description: item.description || '',
        title: item.description || '', // Alias for frontend
        thumbnail_url,
        thumbnail_local: thumbnail_url, // For compatibility
        thumbnail: thumbnail_url, // For compatibility
        view_count: item.view_count || 0,
        like_count: item.like_count || 0,
        comment_count: item.comment_count || 0,
        outlier_score: Number(item.outlier_score) || 0,
        outlierScore: this.formatOutlierScore(Number(item.outlier_score) || 0),
        date_posted: item.date_posted || new Date(),
        username: item.username || '',
        profile: `@${item.username || ''}`,
        profile_name: profile?.profile_name || '',
        bio: profile?.bio || '',
        followers: profile?.followers || 0,
        profile_followers: profile?.followers || 0, // For compatibility
        profile_image_url,
        profileImage: profile_image_url, // For compatibility
        is_verified: profile?.is_verified || false,
        account_type: profile?.account_type || 'Personal',
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
        views: this.formatNumber(item.view_count || 0),
        likes: this.formatNumber(item.like_count || 0),
        comments: this.formatNumber(item.comment_count || 0),
      };
    } catch (error) {
      this.logger.error(
        `❌ Error transforming reel item: ${error instanceof Error ? error.message : 'Unknown error'}`,
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
