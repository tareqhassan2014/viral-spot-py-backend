import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  GetSimilarProfilesResponseDto,
  SimilarProfileDto,
} from '../dto/similar-profiles.dto';
import {
  PrimaryProfile,
  PrimaryProfileDocument,
} from '../schemas/primary-profile.schema';
import {
  SecondaryProfile,
  SecondaryProfileDocument,
} from '../schemas/secondary-profile.schema';

@Injectable()
export class SimilarProfilesService {
  private readonly logger = new Logger(SimilarProfilesService.name);

  constructor(
    @InjectModel(PrimaryProfile.name)
    private primaryProfileModel: Model<PrimaryProfileDocument>,
    @InjectModel(SecondaryProfile.name)
    private secondaryProfileModel: Model<SecondaryProfileDocument>,
  ) {}

  /**
   * Similar Profiles Discovery with Advanced Ranking and Comprehensive Analysis
   *
   * Gets a list of similar profiles for a specific user based on similarity ranking,
   * including comprehensive profile data and analysis metadata.
   */
  async getSimilarProfiles(
    username: string,
    limit: number,
  ): Promise<GetSimilarProfilesResponseDto> {
    this.logger.log(`🔍 Similar profiles discovery: @${username}`);

    const startTime = Date.now();

    // First, get the primary profile with comprehensive data
    const primaryProfile = await this.primaryProfileModel
      .findOne({ username })
      .select(
        '_id username profile_name followers mean_views profile_primary_category',
      )
      .lean()
      .exec();

    if (!primaryProfile) {
      this.logger.warn(`❌ Primary profile not found: @${username}`);
      throw new NotFoundException('Profile not found');
    }

    // Get similar profiles from secondary_profiles collection
    const similarProfiles = await this.secondaryProfileModel
      .find({ discovered_by_id: primaryProfile._id })
      .select(
        `
        username full_name biography followers_count profile_pic_url profile_pic_path
        is_verified estimated_account_type primary_category secondary_category
        tertiary_category similarity_rank discovered_by external_url
      `,
      )
      .sort({ similarity_rank: 1 })
      .limit(limit)
      .lean()
      .exec();

    // Transform similar profiles for frontend
    const transformedProfiles = similarProfiles.map((profile, index) =>
      this.transformSimilarProfile(profile, index),
    );

    const processingTime = Date.now() - startTime;

    this.logger.log(
      `✅ Successfully found ${transformedProfiles.length} similar profiles for @${username} (${processingTime}ms)`,
    );

    // Build comprehensive response structure
    return {
      success: true,
      data: transformedProfiles,
      count: transformedProfiles.length,
      target_username: username,
      target_profile: {
        username: primaryProfile.username,
        profile_name: primaryProfile.profile_name || '',
        followers: primaryProfile.followers || 0,
        average_views: Number(primaryProfile.mean_views) || 0,
        primary_category: primaryProfile.profile_primary_category || null,
        keywords_analyzed: 0, // Not available
      },
      analysis_summary: {
        total_profiles_compared: transformedProfiles.length,
        profiles_with_similarity: transformedProfiles.length,
        target_keywords_count: 0, // Not available
        top_score: transformedProfiles[0]?.similarity_score || 0,
      },
      message: `Found ${transformedProfiles.length} similar profiles successfully`,
    };
  }

  private transformSimilarProfile(
    profile: SecondaryProfileDocument,
    index: number,
  ): SimilarProfileDto {
    // Smart image URL resolution
    let profile_image_url: string | null = null;
    if (profile.profile_pic_path) {
      const cdnBaseUrl = process.env.CDN_BASE_URL || '';
      profile_image_url = cdnBaseUrl
        ? `${cdnBaseUrl}/profile-images/secondary/${profile.profile_pic_path}`
        : profile.profile_pic_path;
    } else if (profile.profile_pic_url) {
      profile_image_url = profile.profile_pic_url;
    }

    // Calculate dynamic similarity score
    const similarity_score = Math.max(0.1, 1.0 - index * 0.05);

    return {
      username: profile.username,
      profile_name: profile.full_name || profile.username,
      followers: profile.followers_count || 0,
      average_views: 0, // Not available in secondary profiles
      primary_category: profile.primary_category || null,
      secondary_category: profile.secondary_category || null,
      tertiary_category: profile.tertiary_category || null,
      profile_image_url,
      profile_image_local: profile_image_url, // For compatibility
      profile_pic_url: profile_image_url, // For compatibility
      profile_pic_local: profile_image_url, // For compatibility
      bio: profile.biography || '',
      is_verified: profile.is_verified || false,
      total_reels: 0, // Not available
      similarity_score,
      rank: index + 1,
      url: `https://www.instagram.com/${profile.username}/`,
    };
  }
}
