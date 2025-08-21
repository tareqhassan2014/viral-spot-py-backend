import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  GetProfileResponseDto,
  ProfileResponseDto,
} from '../dto/profile-response.dto';
import {
  PrimaryProfile,
  PrimaryProfileDocument,
} from '../schemas/primary-profile.schema';

@Injectable()
export class ProfileRetrievalService {
  private readonly logger = new Logger(ProfileRetrievalService.name);

  constructor(
    @InjectModel(PrimaryProfile.name)
    private primaryProfileModel: Model<PrimaryProfileDocument>,
  ) {}

  /**
   * Comprehensive Profile Data Retrieval with Advanced Analytics and Frontend Optimization
   *
   * Retrieves detailed profile data for a specific Instagram username with comprehensive
   * analytics, categorization, and frontend-optimized data transformation.
   */
  async getProfile(username: string): Promise<GetProfileResponseDto> {
    this.logger.log(`🔍 Profile data retrieval: @${username}`);

    const startTime = Date.now();

    // Query MongoDB for the profile
    const profile = await this.primaryProfileModel
      .findOne({ username })
      .lean() // Use lean() for better performance when we don't need Mongoose document features
      .exec();

    if (!profile) {
      this.logger.warn(`❌ Profile not found: @${username}`);
      throw new NotFoundException('Profile not found');
    }

    // Transform the profile data for frontend consumption
    const transformedProfile = this.transformProfileForFrontend(profile);

    const processingTime = Date.now() - startTime;

    this.logger.log(
      `✅ Successfully retrieved profile: @${username} (${processingTime}ms)`,
    );

    return {
      success: true,
      data: transformedProfile,
      message: 'Profile retrieved successfully',
    };
  }

  /**
   * Transform profile data for frontend consumption with intelligent CDN handling
   */
  private transformProfileForFrontend(
    profile: PrimaryProfileDocument,
  ): ProfileResponseDto {
    // Handle profile image URL - prioritize CDN URLs
    let profile_image_url: string | null = null;
    if (profile.profile_image_path) {
      // If using a CDN service like AWS CloudFront, Cloudinary, etc.
      const cdnBaseUrl = process.env.CDN_BASE_URL || '';
      profile_image_url = cdnBaseUrl
        ? `${cdnBaseUrl}/profile-images/${profile.profile_image_path}`
        : profile.profile_image_path;
    } else if (profile.profile_image_url) {
      profile_image_url = profile.profile_image_url;
    }

    // Transform to match the Python implementation exactly
    return {
      username: profile.username,
      profile_name: profile.profile_name || '',
      followers: profile.followers || 0,
      profile_image_url,
      profile_image_local: profile_image_url, // Alias for compatibility
      bio: profile.bio || '',
      is_verified: profile.is_verified || false,
      is_business_account: profile.is_business_account || false,
      reels_count: profile.total_reels || 0,
      average_views: Number(profile.mean_views) || 0,
      primary_category: profile.profile_primary_category || null,
      profile_type: 'primary',
      url: `https://www.instagram.com/${profile.username}/`,

      // Additional fields that might be useful for the frontend
      posts_count: profile.posts_count || 0,
      account_type: profile.account_type || 'Personal',
      language: profile.language || 'en',
      content_type: profile.content_type || 'entertainment',

      // Analytics data
      median_views: profile.median_views || 0,
      total_views: profile.total_views || 0,
      total_likes: profile.total_likes || 0,
      total_comments: profile.total_comments || 0,

      // Categorization
      secondary_category: profile.profile_secondary_category || null,
      tertiary_category: profile.profile_tertiary_category || null,
      categorization_confidence:
        Number(profile.profile_categorization_confidence) || 0.5,

      // Similar accounts (first 10 for performance)
      similar_accounts: [
        profile.similar_account1,
        profile.similar_account2,
        profile.similar_account3,
        profile.similar_account4,
        profile.similar_account5,
        profile.similar_account6,
        profile.similar_account7,
        profile.similar_account8,
        profile.similar_account9,
        profile.similar_account10,
      ].filter((account): account is string => Boolean(account)), // Remove null/undefined values

      // Timestamps
      last_full_scrape: profile.last_full_scrape || null,
      analysis_timestamp: profile.analysis_timestamp || null,
      created_at: this.getTimestamp(profile, 'createdAt', 'created_at'),
      updated_at: this.getTimestamp(profile, 'updatedAt', 'updated_at'),
    };
  }

  /**
   * Helper method to safely get timestamp from profile
   */
  private getTimestamp(
    profile: PrimaryProfileDocument,
    mongooseField: keyof PrimaryProfileDocument,
    customField: string,
  ): Date | null {
    // Safely access mongoose timestamp fields
    const mongooseValue = profile[mongooseField] as Date | undefined;

    // Safely access custom timestamp fields
    const profileAny = profile as unknown as Record<string, unknown>;
    const customValue = profileAny[customField] as Date | undefined;

    return mongooseValue || customValue || null;
  }
}
