import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model, Types } from 'mongoose';
import { Content, ContentDocument } from '../../content/schemas/content.schema';
import {
  PrimaryProfile,
  PrimaryProfileDocument,
} from '../../profile/schemas/primary-profile.schema';
import {
  SecondaryProfile,
  SecondaryProfileDocument,
} from '../../profile/schemas/secondary-profile.schema';
import {
  GetViralAnalysisContentQueryDto,
  ViralAnalysisContentResponseDto,
} from '../dto/viral-analysis-content.dto';
import {
  ViralAnalysisReels,
  ViralAnalysisReelsDocument,
} from '../entities/viral-analysis-reels.schema';
import {
  ViralAnalysisResults,
  ViralAnalysisResultsDocument,
} from '../entities/viral-analysis-results.schema';
import {
  ViralIdeasQueue,
  ViralIdeasQueueDocument,
} from '../entities/viral-ideas-queue.schema';

interface ContentAggregationResult {
  _id: Types.ObjectId;
  content_id: string;
  username: string;
  description?: string;
  transcript?: string;
  view_count?: number;
  like_count?: number;
  comment_count?: number;
  date_posted?: Date;
  content_type?: string;
  primary_category?: string;
  secondary_category?: string;
  content_style?: string;
  outlier_score?: number;
  primary_profile?: {
    username: string;
    profile_name?: string;
    profile_image_url?: string;
    followers?: number;
    account_type?: string;
  };
}

@Injectable()
export class ViralAnalysisContentService {
  private readonly logger = new Logger(ViralAnalysisContentService.name);

  constructor(
    @InjectModel(ViralIdeasQueue.name)
    private viralQueueModel: Model<ViralIdeasQueueDocument>,
    @InjectModel(ViralAnalysisResults.name)
    private viralAnalysisResultsModel: Model<ViralAnalysisResultsDocument>,
    @InjectModel(ViralAnalysisReels.name)
    private viralAnalysisReelsModel: Model<ViralAnalysisReelsDocument>,
    @InjectModel(Content.name)
    private contentModel: Model<ContentDocument>,
    @InjectModel(PrimaryProfile.name)
    private primaryProfileModel: Model<PrimaryProfileDocument>,
    @InjectModel(SecondaryProfile.name)
    private secondaryProfileModel: Model<SecondaryProfileDocument>,
  ) {}

  /**
   * GET /api/viral-analysis/{queue_id}/content ⚡
   * Retrieves the content that was analyzed as part of a job
   *
   * Description: This endpoint is designed to be used in conjunction with the analysis results.
   * It fetches the source content (reels and posts) that was used in a specific analysis job.
   * This is essential for the frontend to display the original content alongside AI-generated insights.
   *
   * Key Features:
   * - Dynamic content filtering (all, primary, competitor)
   * - Comprehensive field selection with engagement metrics
   * - Smart sorting strategies based on content type
   * - Active competitor filtering for accurate analysis scope
   * - Multiple analysis support with latest analysis selection
   * - Content type classification for frontend display
   */
  async getViralAnalysisContent(
    queueId: string,
    query: GetViralAnalysisContentQueryDto,
  ): Promise<ViralAnalysisContentResponseDto> {
    this.logger.log(
      `🔍 Fetching viral analysis content for queue: ${queueId}, type: ${query.content_type}, limit: ${query.limit}, offset: ${query.offset}`,
    );

    const startTime = Date.now();

    try {
      // Step 1: Request Validation
      if (!queueId) {
        throw new Error('queue_id parameter is required');
      }

      // Validate content_type parameter
      const validContentTypes = ['all', 'primary', 'competitor'];
      if (!validContentTypes.includes(query.content_type || 'all')) {
        throw new Error(
          `Invalid content_type. Must be one of: ${validContentTypes.join(', ')}`,
        );
      }

      // Step 2: Analysis Verification - Verify the analysis exists and get primary username
      const queueEntry = await this.viralQueueModel
        .findById(queueId)
        .select('primary_username status')
        .lean()
        .exec();

      if (!queueEntry) {
        this.logger.warn(`❌ Queue entry not found: ${queueId}`);
        throw new NotFoundException('Queue entry not found');
      }

      const primaryUsername = queueEntry.primary_username;
      this.logger.log(
        `📊 Queue entry found - Status: ${queueEntry.status}, User: @${primaryUsername}`,
      );

      // Step 3: Get Latest Analysis Results
      const analysisResults = await this.viralAnalysisResultsModel
        .findOne({ queue_id: queueId })
        .select('_id')
        .sort({ analysis_run: -1 })
        .lean()
        .exec();

      if (!analysisResults) {
        this.logger.warn(`❌ Analysis results not found for queue: ${queueId}`);
        throw new NotFoundException('Analysis results not found');
      }

      const analysisId = analysisResults._id;
      this.logger.log(
        `📈 Analysis found with ID: ${(analysisId as Types.ObjectId)?.toString()}`,
      );

      // Step 4: Content Discovery - Query viral_analysis_reels to find analyzed content IDs
      let reelTypeFilter: Record<string, any> = {};
      if (query.content_type === 'primary') {
        reelTypeFilter = { reel_type: 'primary' };
      } else if (query.content_type === 'competitor') {
        reelTypeFilter = { reel_type: 'competitor' };
      }

      const analyzedReels = await this.viralAnalysisReelsModel
        .find({
          analysis_id: analysisId,
          ...reelTypeFilter,
        })
        .select('content_id reel_type username')
        .lean()
        .exec();

      if (analyzedReels.length === 0) {
        this.logger.warn(
          `❌ No analyzed reels found for queue: ${queueId}, type: ${query.content_type}`,
        );
        return {
          success: true,
          data: {
            content: [],
            isLastPage: true,
            totalCount: 0,
            currentPage: 1,
            pageSize: query.limit || 100,
          },
          message: 'No content found for the specified criteria',
        };
      }

      const contentIds = analyzedReels.map((reel) => reel.content_id);
      this.logger.log(
        `🎬 Found ${analyzedReels.length} analyzed reels with ${contentIds.length} content IDs`,
      );

      // Step 5: Content Enrichment - Query content table with profile JOINs for full data
      const pipeline: any[] = [];

      // Match content IDs
      pipeline.push({
        $match: {
          content_id: { $in: contentIds },
        },
      });

      // Join with primary profiles
      pipeline.push({
        $lookup: {
          from: 'primary_profiles',
          localField: 'profile_id',
          foreignField: '_id',
          as: 'primary_profile',
          pipeline: [
            {
              $project: {
                username: 1,
                profile_name: 1,
                profile_image_url: 1,
                followers: 1,
                account_type: 1,
              },
            },
          ],
        },
      });

      pipeline.push({
        $unwind: {
          path: '$primary_profile',
          preserveNullAndEmptyArrays: true,
        },
      });

      // Step 6: Apply Smart Sorting Strategies
      let sortStage: Record<string, any> = {};
      if (query.content_type === 'primary') {
        // Primary Content: Sorted by view_count descending (performance focus)
        sortStage = { view_count: -1 };
      } else if (query.content_type === 'competitor') {
        // Competitor Content: Sorted by outlier_score descending (viral potential focus)
        sortStage = { outlier_score: -1 };
      } else {
        // All Content: Sorted by outlier_score descending (comprehensive viral analysis)
        sortStage = { outlier_score: -1 };
      }

      pipeline.push({ $sort: sortStage });

      // Step 7: Pagination
      pipeline.push({ $skip: query.offset || 0 });
      pipeline.push({ $limit: (query.limit || 100) + 1 }); // +1 to check if there are more items

      // Execute aggregation
      const contentResults = await this.contentModel
        .aggregate<ContentAggregationResult>(pipeline)
        .exec();

      // Check if there are more items (for pagination)
      const hasMore = contentResults.length > (query.limit || 100);
      if (hasMore) {
        contentResults.pop(); // Remove the extra item
      }

      // Step 8: Transform and Structure Data
      const transformedContent = contentResults.map((content) => {
        // Find the corresponding analyzed reel to get reel_type
        const analyzedReel = analyzedReels.find(
          (reel) => reel.content_id === content.content_id,
        );

        return {
          id: content._id?.toString() || '',
          content_id: content.content_id,
          username: content.username,
          description: content.description,
          transcript: content.transcript,
          view_count: content.view_count,
          like_count: content.like_count,
          comment_count: content.comment_count,
          posted_at: content.date_posted?.toISOString(),
          content_type: content.content_type,
          primary_category: content.primary_category,
          secondary_category: content.secondary_category,
          content_style: content.content_style,
          outlier_score: content.outlier_score,
          reel_type: analyzedReel?.reel_type || 'unknown',
          // Profile information
          profile_name: content.primary_profile?.profile_name,
          profile_image_url: content.primary_profile?.profile_image_url,
          followers: content.primary_profile?.followers,
          account_type: content.primary_profile?.account_type,
        };
      });

      const processingTime = Date.now() - startTime;
      const currentPage =
        Math.floor((query.offset || 0) / (query.limit || 100)) + 1;

      this.logger.log(
        `✅ Viral analysis content retrieved successfully - ${transformedContent.length} items, page ${currentPage} (${processingTime}ms)`,
      );

      // Step 9: Assemble Response
      return {
        success: true,
        data: {
          content: transformedContent,
          isLastPage: !hasMore,
          totalCount: analyzedReels.length, // Total available items
          currentPage,
          pageSize: query.limit || 100,
        },
        message: `Content retrieved successfully - ${transformedContent.length} items from ${query.content_type} analysis`,
      };
    } catch (error) {
      const processingTime = Date.now() - startTime;
      this.logger.error(
        `❌ Error fetching viral analysis content for queue ${queueId}: ${error instanceof Error ? error.message : 'Unknown error'} (${processingTime}ms)`,
      );
      throw error;
    }
  }
}
