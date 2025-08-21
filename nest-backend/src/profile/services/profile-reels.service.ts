import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { Content, ContentDocument } from '../../content/schemas/content.schema';
import {
  GetProfileReelsResponseDto,
  ProfileReelDto,
} from '../dto/profile-reels.dto';
import { PrimaryProfileDocument } from '../schemas/primary-profile.schema';

@Injectable()
export class ProfileReelsService {
  private readonly logger = new Logger(ProfileReelsService.name);

  constructor(
    @InjectModel(Content.name)
    private contentModel: Model<ContentDocument>,
  ) {}

  /**
   * Profile Reels Retrieval with Advanced Sorting and Pagination
   *
   * Fetches all reels associated with a specific profile with support for sorting
   * and pagination, including complete profile data integration.
   */
  async getProfileReels(
    username: string,
    sortBy: string,
    limit: number,
    offset: number,
  ): Promise<GetProfileReelsResponseDto> {
    this.logger.log(
      `🎬 Profile reels retrieval: @${username}, sort_by: ${sortBy}`,
    );

    const startTime = Date.now();

    // Build aggregation pipeline for efficient JOIN and filtering
    const pipeline: any[] = [];

    // 1. Match content by username (more efficient than profile_id lookup)
    pipeline.push({
      $match: { username },
    });

    // 2. Lookup profile data (equivalent to JOIN)
    pipeline.push({
      $lookup: {
        from: 'primary_profiles',
        localField: 'profile_id',
        foreignField: '_id',
        as: 'profile',
      },
    });

    // 3. Unwind profile array (1:1 relationship)
    pipeline.push({
      $unwind: {
        path: '$profile',
        preserveNullAndEmptyArrays: true,
      },
    });

    // 4. Apply sorting based on sort_by parameter
    const sortStage = this.buildSortStage(sortBy);
    pipeline.push({ $sort: sortStage });

    // 5. Apply pagination
    pipeline.push({ $skip: offset });
    pipeline.push({ $limit: limit + 1 }); // Get one extra to check for more pages

    // 6. Execute aggregation
    const results = await this.contentModel.aggregate(pipeline).exec();

    // Handle empty results
    if (!results || results.length === 0) {
      const processingTime = Date.now() - startTime;
      this.logger.log(
        `✅ No reels found for @${username} (${processingTime}ms)`,
      );
      return {
        success: true,
        data: { reels: [], isLastPage: true },
        message: 'No reels found for this profile',
      };
    }

    // 7. Check for more pages and trim results
    const hasMore = results.length > limit;
    const reelsToReturn = results.slice(0, limit);

    // 8. Transform for frontend
    const transformedReels = reelsToReturn.map((item) =>
      this.transformContentForFrontend(
        item as ContentDocument & { profile?: PrimaryProfileDocument },
      ),
    );

    const processingTime = Date.now() - startTime;

    this.logger.log(
      `✅ Successfully retrieved ${transformedReels.length} reels for @${username} (${processingTime}ms)`,
    );

    return {
      success: true,
      data: {
        reels: transformedReels,
        isLastPage: !hasMore,
      },
      message: `Retrieved ${transformedReels.length} reels successfully`,
    };
  }

  private buildSortStage(sortBy: string): Record<string, number> {
    switch (sortBy) {
      case 'popular':
        return { outlier_score: -1, view_count: -1 };
      case 'recent':
        return { date_posted: -1 };
      case 'oldest':
        return { date_posted: 1 };
      default:
        return { outlier_score: -1, view_count: -1 };
    }
  }

  private transformContentForFrontend(
    item: ContentDocument & { profile?: PrimaryProfileDocument },
  ): ProfileReelDto {
    const profile = item.profile || ({} as Partial<PrimaryProfileDocument>);

    // Handle CDN URLs for thumbnails
    let thumbnail_url: string | null = null;
    if (item.thumbnail_path) {
      const cdnBaseUrl = process.env.CDN_BASE_URL || '';
      thumbnail_url = cdnBaseUrl
        ? `${cdnBaseUrl}/content-thumbnails/${item.thumbnail_path}`
        : item.thumbnail_path;
    } else if (item.thumbnail_url) {
      thumbnail_url = item.thumbnail_url;
    }

    // Handle profile image URLs
    let profile_image_url: string | null = null;
    if (profile.profile_image_path) {
      const cdnBaseUrl = process.env.CDN_BASE_URL || '';
      profile_image_url = cdnBaseUrl
        ? `${cdnBaseUrl}/profile-images/${profile.profile_image_path}`
        : profile.profile_image_path;
    } else if (profile.profile_image_url) {
      profile_image_url = profile.profile_image_url;
    }

    // Transform to match Python implementation exactly
    return {
      id: item.content_id,
      reel_id: item.content_id,
      content_id: item.content_id,
      content_type: item.content_type || 'reel',
      shortcode: item.shortcode,
      url: item.url,
      description: item.description || '',
      title: item.description || '', // Alias for frontend
      thumbnail_url,
      thumbnail_local: thumbnail_url, // For compatibility
      thumbnail: thumbnail_url, // For compatibility
      view_count: item.view_count || 0,
      like_count: item.like_count || 0,
      comment_count: item.comment_count || 0,
      outlier_score: Number(item.outlier_score) || 0,
      outlierScore: `${(Number(item.outlier_score) || 0).toFixed(1)}x`, // Formatted for frontend
      date_posted: item.date_posted,
      username: item.username,
      profile: `@${item.username}`,
      profile_name: profile.profile_name || '',
      bio: profile.bio || '',
      profile_followers: profile.followers || 0,
      followers: profile.followers || 0, // For compatibility
      profile_image_url,
      profileImage: profile_image_url, // For compatibility
      is_verified: profile.is_verified || false,
      account_type: profile.account_type || 'Personal',
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
  }

  private formatNumber(num: number): string {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  }
}
