import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  PrimaryProfile,
  PrimaryProfileDocument,
} from '../../profile/schemas/primary-profile.schema';
import {
  FilterOptionsDataDto,
  GetFilterOptionsResponseDto,
  UsernameOptionDto,
} from '../dto/get-filter-options.dto';
import { Content, ContentDocument } from '../schemas/content.schema';

@Injectable()
export class FilterOptionsService {
  private readonly logger = new Logger(FilterOptionsService.name);

  constructor(
    @InjectModel(Content.name)
    private contentModel: Model<ContentDocument>,
    @InjectModel(PrimaryProfile.name)
    private primaryProfileModel: Model<PrimaryProfileDocument>,
  ) {}

  /**
   * GET /api/content/filter ⚡
   * Dynamic Filter Options Retrieval
   *
   * Description: This is a utility endpoint designed to populate the filter dropdowns and selection menus on the frontend.
   * It dynamically queries the database to find all unique values for the various filterable fields,
   * such as categories, content types, languages, and keywords.
   * Usage: Frontend filter population, dynamic UI generation, database-synced filter options.
   */
  async getFilterOptions(): Promise<GetFilterOptionsResponseDto> {
    this.logger.log('⚡ Getting filter options from database');

    const startTime = Date.now();

    try {
      // Use parallel execution for better performance
      const [
        primaryCategories,
        secondaryCategories,
        tertiaryCategories,
        contentTypes,
        languages,
        contentStyles,
        accountTypes,
        usernames,
        keywords,
      ] = await Promise.all([
        // Content metadata queries - using distinct for efficiency
        this.contentModel.distinct('primary_category').exec(),
        this.contentModel.distinct('secondary_category').exec(),
        this.contentModel.distinct('tertiary_category').exec(),
        this.contentModel.distinct('content_type').exec(),
        this.contentModel.distinct('language').exec(),
        this.contentModel.distinct('content_style').exec(),

        // Profile queries
        this.primaryProfileModel.distinct('account_type').exec(),
        this.primaryProfileModel
          .find()
          .select('username profile_name')
          .lean()
          .exec(),

        // Keywords aggregation query
        this.getUniqueKeywords(),
      ]);

      // Process and filter the results
      const filterOptions: FilterOptionsDataDto = {
        primary_categories: this.filterAndSort(primaryCategories),
        secondary_categories: this.filterAndSort(secondaryCategories),
        tertiary_categories: this.filterAndSort(tertiaryCategories),
        keywords: this.filterAndSort(keywords),
        usernames: usernames.map(
          (user): UsernameOptionDto => ({
            username: user.username,
            profile_name: user.profile_name || '',
          }),
        ),
        account_types: this.filterAndSort(accountTypes),
        content_types: this.filterAndSort(contentTypes),
        languages: this.filterAndSort(languages),
        content_styles: this.filterAndSort(contentStyles),
      };

      const processingTime = Date.now() - startTime;

      this.logger.log(
        `✅ Filter options retrieved: ${filterOptions.primary_categories.length} primary categories, ${filterOptions.keywords.length} keywords, ${filterOptions.usernames.length} usernames (${processingTime}ms)`,
      );

      return {
        success: true,
        data: filterOptions,
        message: `Retrieved filter options successfully`,
      };
    } catch (error) {
      this.logger.error(
        `❌ Error getting filter options: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
      throw error;
    }
  }

  /**
   * Extract unique keywords from all 4 keyword fields using MongoDB aggregation
   */
  private async getUniqueKeywords(): Promise<string[]> {
    try {
      // MongoDB aggregation pipeline to extract unique keywords from all 4 keyword fields
      const keywordPipeline = [
        {
          $project: {
            keywords: ['$keyword_1', '$keyword_2', '$keyword_3', '$keyword_4'],
          },
        },
        {
          $unwind: '$keywords',
        },
        {
          $match: {
            keywords: { $nin: [null, '', undefined], $exists: true },
          },
        },
        {
          $group: {
            _id: '$keywords',
          },
        },
        {
          $sort: { _id: 1 },
        },
      ];

      const keywordsResult = await this.contentModel
        .aggregate<{ _id: string }>(keywordPipeline as any)
        .exec();

      return keywordsResult
        .map((k) => k._id)
        .filter((keyword): keyword is string => Boolean(keyword))
        .map((keyword) => keyword.toString().trim())
        .filter((keyword) => keyword.length > 0);
    } catch (error) {
      this.logger.error(
        `❌ Error getting unique keywords: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
      return []; // Return empty array on error to prevent breaking the main response
    }
  }

  /**
   * Filter out null, undefined, and empty values, then sort alphabetically
   */
  private filterAndSort(array: any[]): string[] {
    return array
      .filter((item) => {
        try {
          return Boolean(
            item && typeof item === 'string'
              ? item.trim()
              : String(item).trim(),
          );
        } catch {
          return false;
        }
      })
      .map((item) => (typeof item === 'string' ? item : String(item)).trim())
      .sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
  }

  /**
   * Alternative optimized implementation using fewer aggregation queries
   * Better for large datasets but more complex
   */
  async getFilterOptionsOptimized(): Promise<GetFilterOptionsResponseDto> {
    this.logger.log('⚡ Getting optimized filter options from database');

    const startTime = Date.now();

    try {
      // Single aggregation pipeline to get all content metadata
      const contentMetadataPipeline = [
        {
          $group: {
            _id: null,
            primary_categories: { $addToSet: '$primary_category' },
            secondary_categories: { $addToSet: '$secondary_category' },
            tertiary_categories: { $addToSet: '$tertiary_category' },
            content_types: { $addToSet: '$content_type' },
            languages: { $addToSet: '$language' },
            content_styles: { $addToSet: '$content_style' },
            keywords: {
              $addToSet: {
                $concatArrays: [
                  [{ $ifNull: ['$keyword_1', null] }],
                  [{ $ifNull: ['$keyword_2', null] }],
                  [{ $ifNull: ['$keyword_3', null] }],
                  [{ $ifNull: ['$keyword_4', null] }],
                ],
              },
            },
          },
        },
        {
          $project: {
            _id: 0,
            primary_categories: 1,
            secondary_categories: 1,
            tertiary_categories: 1,
            content_types: 1,
            languages: 1,
            content_styles: 1,
            keywords: {
              $reduce: {
                input: '$keywords',
                initialValue: [],
                in: { $concatArrays: ['$$value', '$$this'] },
              },
            },
          },
        },
      ];

      // Single aggregation pipeline for profile metadata
      const profileMetadataPipeline = [
        {
          $group: {
            _id: null,
            account_types: { $addToSet: '$account_type' },
            usernames: {
              $push: {
                username: '$username',
                profile_name: { $ifNull: ['$profile_name', ''] },
              },
            },
          },
        },
        {
          $project: {
            _id: 0,
            account_types: 1,
            usernames: 1,
          },
        },
      ];

      interface ContentMetadata {
        primary_categories: string[];
        secondary_categories: string[];
        tertiary_categories: string[];
        content_types: string[];
        languages: string[];
        content_styles: string[];
        keywords: string[];
      }

      interface ProfileMetadata {
        account_types: string[];
        usernames: UsernameOptionDto[];
      }

      const [contentMetadata, profileMetadata] = await Promise.all([
        this.contentModel
          .aggregate<ContentMetadata>(contentMetadataPipeline as any)
          .exec(),
        this.primaryProfileModel
          .aggregate<ProfileMetadata>(profileMetadataPipeline as any)
          .exec(),
      ]);

      const content = contentMetadata[0] || ({} as ContentMetadata);
      const profile = profileMetadata[0] || ({} as ProfileMetadata);

      const filterOptions: FilterOptionsDataDto = {
        primary_categories: this.filterAndSort(
          content.primary_categories || [],
        ),
        secondary_categories: this.filterAndSort(
          content.secondary_categories || [],
        ),
        tertiary_categories: this.filterAndSort(
          content.tertiary_categories || [],
        ),
        keywords: this.filterAndSort(content.keywords || []),
        usernames: profile.usernames || [],
        account_types: this.filterAndSort(profile.account_types || []),
        content_types: this.filterAndSort(content.content_types || []),
        languages: this.filterAndSort(content.languages || []),
        content_styles: this.filterAndSort(content.content_styles || []),
      };

      const processingTime = Date.now() - startTime;

      this.logger.log(
        `✅ Optimized filter options retrieved: ${filterOptions.primary_categories.length} primary categories, ${filterOptions.keywords.length} keywords (${processingTime}ms)`,
      );

      return {
        success: true,
        data: filterOptions,
        message: `Retrieved optimized filter options successfully`,
      };
    } catch (error) {
      this.logger.error(
        `❌ Error getting optimized filter options: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
      throw error;
    }
  }
}
