import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  GetSecondaryProfileResponseDto,
  SecondaryProfileDto,
} from '../dto/secondary-profile.dto';
import {
  SecondaryProfile,
  SecondaryProfileDocument,
} from '../schemas/secondary-profile.schema';

@Injectable()
export class SecondaryProfileService {
  private readonly logger = new Logger(SecondaryProfileService.name);

  constructor(
    @InjectModel(SecondaryProfile.name)
    private secondaryProfileModel: Model<SecondaryProfileDocument>,
  ) {}

  /**
   * Retrieves secondary (discovered) profile data for loading states and previews
   *
   * Features:
   * - Quick profile previews while full data is being processed
   * - CDN-optimized image URLs with intelligent fallback
   * - Frontend interface compatibility matching primary profiles
   * - Secondary profile indicators for frontend logic
   * - Comprehensive error handling with detailed logging
   */
  async getSecondaryProfile(
    username: string,
  ): Promise<GetSecondaryProfileResponseDto> {
    this.logger.log(`🔍 Getting secondary profile: @${username}`);

    const startTime = Date.now();

    // Query MongoDB for the secondary profile
    const profile = await this.secondaryProfileModel
      .findOne({ username })
      .lean() // Use lean() for better performance when transforming data
      .exec();

    if (!profile) {
      this.logger.warn(`❌ Secondary profile not found: @${username}`);
      throw new NotFoundException('Secondary profile not found');
    }

    // Transform the profile data for frontend consumption
    const transformedProfile = this.transformSecondaryProfile(profile);

    const processingTime = Date.now() - startTime;

    this.logger.log(
      `✅ Successfully retrieved secondary profile: @${username} (${processingTime}ms)`,
    );

    return {
      success: true,
      data: transformedProfile,
    };
  }

  /**
   * Transform secondary profile data to match frontend interface
   * Implements smart image URL handling with CDN optimization and fallback strategy
   */
  private transformSecondaryProfile(
    profile: SecondaryProfileDocument,
  ): SecondaryProfileDto {
    // Smart image URL handling with fallback strategy
    let profile_image_url: string | null = null;
    let profile_image_local: string | null = null;

    if (profile.profile_pic_path) {
      // Convert to CDN URL (using environment variable for CDN base URL)
      const cdnBaseUrl = process.env.CDN_BASE_URL || '';
      profile_image_url = cdnBaseUrl
        ? `${cdnBaseUrl}/profile-images/${profile.profile_pic_path}`
        : profile.profile_pic_path;
      profile_image_local = profile_image_url;
    } else if (profile.profile_pic_url) {
      // Fallback to original Instagram URL
      profile_image_url = profile.profile_pic_url;
      profile_image_local = profile_image_url;
    }

    // Transform to match frontend interface (same structure as primary profiles)
    return {
      username: profile.username || '',
      profile_name: profile.full_name || profile.username || '',
      bio: profile.biography || '',
      followers: profile.followers_count || 0,
      profile_image_url,
      profile_image_local,
      is_verified: profile.is_verified || false,
      primary_category: profile.primary_category,
      secondary_category: profile.secondary_category,
      tertiary_category: profile.tertiary_category,
      account_type: profile.estimated_account_type || 'Personal',
      url: `https://instagram.com/${profile.username}`,

      // Secondary profile specific fields (distinguish from primary profiles)
      reels_count: 0, // Unknown for secondary profiles
      average_views: 0, // Unknown for secondary profiles
      is_secondary: true, // Flag to indicate this is secondary data
      created_at: profile.createdAt
        ? new Date(profile.createdAt).toISOString()
        : '',
      updated_at: profile.updatedAt
        ? new Date(profile.updatedAt).toISOString()
        : '',
    };
  }
}
