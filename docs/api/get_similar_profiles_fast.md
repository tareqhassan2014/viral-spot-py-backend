# GET `/api/profile/{username}/similar-fast` ⚡

A new, faster endpoint for retrieving similar profiles.

## Description

This endpoint is an optimized alternative to the standard `/similar` endpoint. It is designed for high performance, using a dedicated caching layer and a streamlined database table (`similar_profiles`) to deliver results quickly. Profile images are served from a CDN for an even faster user experience.

## Path Parameters

| Parameter  | Type   | Description                                          |
| :--------- | :----- | :--------------------------------------------------- |
| `username` | string | The Instagram username to find similar profiles for. |

## Query Parameters

| Parameter       | Type    | Description                                                        | Default |
| :-------------- | :------ | :----------------------------------------------------------------- | :------ |
| `limit`         | integer | The number of similar profiles to return (between 1 and 80).       | `20`    |
| `force_refresh` | boolean | If `true`, bypasses the cache and fetches fresh data from the API. | `false` |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `username` path parameter and optional `limit` and `force_refresh` query parameters.
2.  **Check Cache**: It first checks an in-memory cache (or a dedicated caching service like Redis) for the requested `username` and `limit`. If `force_refresh` is `true`, this step is skipped.
3.  **Return Cached Data**: If a valid, non-expired cache entry is found, the data is returned directly with a message indicating it was cached.
4.  **Query Database**: If the data is not in the cache or `force_refresh` is true, it queries the `similar_profiles` table. It filters for records matching the `primary_username` and limits the results.
5.  **Fetch from External API (if needed)**: If the `similar_profiles` table is empty or the data is stale, the system may call an external API to fetch a new list of similar profiles.
6.  **Update Database and Cache**: The new data is used to update the `similar_profiles` table and is stored in the cache with a 24-hour expiration.
7.  **Transform and Respond**: The data is formatted for the frontend and returned with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI & Helper Module)

```python
# Complete get_similar_profiles_fast endpoint implementation (lines 1289-1330)
@app.get("/api/profile/{username}/similar-fast")
async def get_similar_profiles_fast(
    username: str = Path(..., description="Instagram username"),
    limit: int = Query(20, description="Number of similar profiles to return", ge=1, le=80),
    force_refresh: bool = Query(False, description="Force refresh from API")
):
    """
    Get similar profiles with fast caching (new optimized endpoint)

    This endpoint uses the new similar_profiles table for lightning-fast loading.
    Images are stored in Supabase bucket and served via CDN.

    Features:
    - Returns cached results instantly (24hr cache)
    - Supports 20-80 similar profiles per request
    - Optimized for batch operations
    - CDN-delivered profile images
    """
    if not SIMPLE_SIMILAR_API_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Simple similar profiles API not available"
        )

    try:
        similar_api = get_similar_api()
        result = await similar_api.get_similar_profiles(username, limit, force_refresh)

        if result['success']:
            return APIResponse(
                success=True,
                data=result['data'],
                message=f"Found {result['total']} similar profiles ({'cached' if result.get('cached') else 'fresh'})"
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in similar profiles fast endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Complete SimpleSimilarProfilesAPI class implementation (lines 32-536)
class SimpleSimilarProfilesAPI:
    """Lightweight API for similar profiles with fast caching"""

    def __init__(self):
        """Initialize with Supabase and API clients"""
        if not SUPABASE_AVAILABLE:
            raise RuntimeError("Required dependencies not available")

        self.supabase = SupabaseManager()
        self.api_client = RapidAPIClient()

        # Cache settings
        self.cache_duration_hours = 24  # Cache similar profiles for 24 hours
        self.max_similar_profiles = 80  # Support up to 80 similar profiles

        logger.info("✅ Simple Similar Profiles API initialized")

    async def get_similar_profiles(self, username: str, limit: int = 20, force_refresh: bool = False) -> Dict:
        """
        Get similar profiles for a username - returns cached or fetches new

        Args:
            username: Target username to find similar profiles for
            limit: Number of profiles to return (max 80)
            force_refresh: Force refresh from API even if cached

        Returns:
            Dict with success, data (list of profiles), and metadata
        """
        try:
            username = username.lower().replace('@', '')
            limit = min(limit, self.max_similar_profiles)

            logger.info(f"🔍 Getting similar profiles for @{username} (limit: {limit})")

            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_profiles = await self._get_cached_similar_profiles(username, limit)
                if cached_profiles:
                    logger.info(f"✅ Returning {len(cached_profiles)} cached similar profiles")
                    return {
                        'success': True,
                        'data': cached_profiles,
                        'cached': True,
                        'total': len(cached_profiles),
                        'username': username
                    }

            # Fetch fresh data if no cache or force refresh
            logger.info(f"🚀 Fetching fresh similar profiles for @{username}")
            fresh_profiles = await self._fetch_and_cache_similar_profiles(username, limit)

            return {
                'success': True,
                'data': fresh_profiles,
                'cached': False,
                'total': len(fresh_profiles),
                'username': username
            }

        except Exception as e:
            logger.error(f"❌ Error getting similar profiles for @{username}: {e}")
            return {
                'success': False,
                'data': [],
                'error': str(e),
                'username': username
            }

    async def _get_cached_similar_profiles(self, username: str, limit: int) -> Optional[List[Dict]]:
        """Get similar profiles from cache if recent enough"""
        try:
            # Check for recent cached profiles
            cutoff_time = datetime.now() - timedelta(hours=self.cache_duration_hours)

            response = self.supabase.client.table('similar_profiles').select('''
                similar_username,
                similar_name,
                profile_image_path,
                profile_image_url,
                similarity_rank,
                image_downloaded,
                created_at
            ''').eq('primary_username', username).eq('image_downloaded', True).gte('created_at', cutoff_time.isoformat()).order('similarity_rank').limit(limit).execute()

            if not response.data:
                logger.info(f"📭 No recent cached similar profiles found for @{username}")
                return None

            # Convert to API format
            profiles = []
            for profile in response.data:
                # Get CDN URL for profile image
                profile_image_url = None
                if profile.get('profile_image_path'):
                    profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_image_path'])
                elif profile.get('profile_image_url'):
                    profile_image_url = profile['profile_image_url']

                profiles.append({
                    'username': profile['similar_username'],
                    'name': profile.get('similar_name', profile['similar_username']),
                    'profile_image_url': profile_image_url,
                    'rank': profile.get('similarity_rank', 0)
                })

            logger.info(f"📋 Found {len(profiles)} cached similar profiles for @{username}")
            return profiles

        except Exception as e:
            logger.error(f"❌ Error getting cached similar profiles: {e}")
            return None

    async def _fetch_and_cache_similar_profiles(self, username: str, limit: int) -> List[Dict]:
        """Fetch similar profiles from API and cache with images - with enhanced retry logic"""
        try:
            batch_id = str(uuid.uuid4())
            logger.info(f"🔄 Starting fresh fetch for @{username} (batch: {batch_id[:8]})")

            # Step 1: Fetch similar profiles from API with enhanced retry logic
            similar_profiles_raw = await self._fetch_similar_profiles_with_retry(username, limit)

            if not similar_profiles_raw:
                logger.warning(f"⚠️ No similar profiles returned from API for @{username} after all retry attempts")
                return []

            logger.info(f"📥 API returned {len(similar_profiles_raw)} similar profiles")

            # Step 2: Process each profile and download images in parallel
            processed_profiles = await self._process_similar_profiles_batch(
                username, similar_profiles_raw, batch_id
            )

            logger.info(f"✅ Successfully processed {len(processed_profiles)} similar profiles")
            return processed_profiles

        except Exception as e:
            logger.error(f"❌ Error fetching and caching similar profiles: {e}")
            return []
```

**Line-by-Line Explanation:**

1.  **`@app.get("/api/profile/{username}/similar-fast")`**: Defines the FastAPI endpoint with comprehensive parameter validation and detailed documentation.

2.  **Service Availability Check**:

    ```python
    if not SIMPLE_SIMILAR_API_AVAILABLE:
        raise HTTPException(status_code=503, detail="Simple similar profiles API not available")
    ```

    Ensures the helper module is available before proceeding.

3.  **`similar_api = get_similar_api()`**: Gets a singleton instance of the `SimpleSimilarProfilesAPI` class for efficient resource usage.

4.  **Main Logic Handler**: `get_similar_profiles()` method implements the core caching strategy:

    -   **Cache Check**: First checks for cached data unless `force_refresh` is true
    -   **Fresh Fetch**: Falls back to API fetch if no cache or force refresh requested
    -   **Error Handling**: Comprehensive error handling with detailed logging

5.  **Smart Cache Strategy**: `_get_cached_similar_profiles()` method:

    -   **24-Hour Cache**: Uses `cutoff_time = datetime.now() - timedelta(hours=24)`
    -   **Image Validation**: Only returns profiles where `image_downloaded = True`
    -   **CDN URL Generation**: Converts storage paths to public CDN URLs
    -   **Similarity Ranking**: Orders results by `similarity_rank` for consistent ordering

6.  **Enhanced Retry Logic**: `_fetch_similar_profiles_with_retry()` implements multiple strategies:

    -   **Progressive Delays**: 2s, 4s delays between retries
    -   **Username Variations**: Tries variations if original username fails
    -   **Fallback Strategies**: Multiple approaches to maximize success rate

7.  **Parallel Processing**: `_process_similar_profiles_batch()` method:

    -   **Batch Processing**: Processes profiles in batches of 10 for performance
    -   **Parallel Downloads**: Uses `asyncio.gather()` for concurrent image downloads
    -   **Error Resilience**: Continues processing even if individual profiles fail

8.  **Image Management**: Sophisticated image handling:
    -   **Download to Temp**: Downloads images to temporary files
    -   **Supabase Storage**: Uploads to `profile-images` bucket with organized paths
    -   **CDN URLs**: Generates public CDN URLs for fast delivery
    -   **Cleanup**: Removes temporary files after processing

### Key Implementation Features

**1. High-Performance Caching**: 24-hour cache with instant retrieval for subsequent requests.

**2. CDN-Optimized Images**: All profile images stored in Supabase Storage with CDN delivery.

**3. Enhanced Retry Logic**: Multiple strategies including username variations and progressive delays.

**4. Parallel Processing**: Concurrent image downloads and database operations for speed.

**5. Comprehensive Error Handling**: Graceful degradation with detailed logging throughout.

**6. Batch Operations**: Efficient processing of multiple profiles simultaneously.

**7. Resource Management**: Proper cleanup of temporary files and singleton API instance.

### Nest.js (Mongoose)

```typescript
// DTO for validation
import {
    IsString,
    IsOptional,
    IsInt,
    IsBoolean,
    Min,
    Max,
} from "class-validator";
import { Transform } from "class-transformer";

export class GetSimilarProfilesFastDto {
    @IsOptional()
    @Transform(({ value }) => parseInt(value))
    @IsInt()
    @Min(1)
    @Max(80)
    limit?: number = 20;

    @IsOptional()
    @Transform(({ value }) => value === "true")
    @IsBoolean()
    force_refresh?: boolean = false;
}

// In your profile.controller.ts
import {
    Controller,
    Get,
    Param,
    Query,
    Logger,
    Inject,
    CACHE_MANAGER,
} from "@nestjs/common";
import { Cache } from "cache-manager";
import { ProfileService } from "./profile.service";
import { GetSimilarProfilesFastDto } from "./dto/get-similar-profiles-fast.dto";

@Controller("api/profile")
export class ProfileController {
    private readonly logger = new Logger(ProfileController.name);

    constructor(
        private readonly profileService: ProfileService,
        @Inject(CACHE_MANAGER) private cacheManager: Cache
    ) {}

    @Get(":username/similar-fast")
    async getSimilarProfilesFast(
        @Param("username") username: string,
        @Query() queryParams: GetSimilarProfilesFastDto
    ) {
        const cleanUsername = username.toLowerCase().replace("@", "");
        const limit = Math.min(queryParams.limit || 20, 80);

        this.logger.log(
            `🔍 Getting similar profiles for @${cleanUsername} (limit: ${limit})`
        );

        const result = await this.profileService.getSimilarProfilesFast(
            cleanUsername,
            limit,
            queryParams.force_refresh || false
        );

        const message = `Found ${result.data.length} similar profiles (${
            result.cached ? "cached" : "fresh"
        })`;
        this.logger.log(`✅ ${message}`);

        return {
            success: true,
            data: result.data,
            message: message,
        };
    }
}

// In your profile.service.ts
import { Injectable, Logger, Inject, CACHE_MANAGER } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import { Cache } from "cache-manager";
import {
    SimilarProfile,
    SimilarProfileDocument,
} from "./schemas/similar-profile.schema";
import { ExternalApiService } from "./external-api.service";
import { StorageService } from "./storage.service";

@Injectable()
export class ProfileService {
    private readonly logger = new Logger(ProfileService.name);
    private readonly CACHE_DURATION_HOURS = 24;
    private readonly MAX_SIMILAR_PROFILES = 80;

    constructor(
        @InjectModel(SimilarProfile.name)
        private similarProfileModel: Model<SimilarProfileDocument>,
        @Inject(CACHE_MANAGER) private cacheManager: Cache,
        private externalApiService: ExternalApiService,
        private storageService: StorageService
    ) {}

    async getSimilarProfilesFast(
        username: string,
        limit: number,
        forceRefresh: boolean
    ): Promise<{ data: any[]; cached: boolean }> {
        try {
            const cleanUsername = username.toLowerCase().replace("@", "");
            const effectiveLimit = Math.min(limit, this.MAX_SIMILAR_PROFILES);

            // Check cache first (unless force refresh)
            if (!forceRefresh) {
                const cached = await this.getCachedSimilarProfiles(
                    cleanUsername,
                    effectiveLimit
                );
                if (cached && cached.length > 0) {
                    this.logger.log(
                        `✅ Returning ${cached.length} cached similar profiles`
                    );
                    return { data: cached, cached: true };
                }
            }

            // Fetch fresh data
            this.logger.log(
                `🚀 Fetching fresh similar profiles for @${cleanUsername}`
            );
            const fresh = await this.fetchAndCacheSimilarProfiles(
                cleanUsername,
                effectiveLimit
            );

            return { data: fresh, cached: false };
        } catch (error) {
            this.logger.error(
                `❌ Error getting similar profiles for @${username}: ${error.message}`
            );
            return { data: [], cached: false };
        }
    }

    private async getCachedSimilarProfiles(
        username: string,
        limit: number
    ): Promise<any[] | null> {
        try {
            // Check for recent cached profiles (24-hour cache)
            const cutoffTime = new Date();
            cutoffTime.setHours(
                cutoffTime.getHours() - this.CACHE_DURATION_HOURS
            );

            const cachedProfiles = await this.similarProfileModel
                .find({
                    primary_username: username,
                    image_downloaded: true,
                    createdAt: { $gte: cutoffTime },
                })
                .sort({ similarity_rank: 1 })
                .limit(limit)
                .lean()
                .exec();

            if (cachedProfiles.length === 0) {
                this.logger.log(
                    `📭 No recent cached similar profiles found for @${username}`
                );
                return null;
            }

            // Transform to API format with CDN URLs
            const profiles = cachedProfiles.map((profile) => {
                let profile_image_url = null;

                if (profile.profile_image_path) {
                    // Generate CDN URL for Supabase Storage
                    profile_image_url = `https://cdn.supabase.co/storage/v1/object/public/profile-images/${profile.profile_image_path}`;
                } else if (profile.profile_image_url) {
                    profile_image_url = profile.profile_image_url;
                }

                return {
                    username: profile.similar_username,
                    name: profile.similar_name || profile.similar_username,
                    profile_image_url: profile_image_url,
                    rank: profile.similarity_rank || 0,
                };
            });

            this.logger.log(
                `📋 Found ${profiles.length} cached similar profiles for @${username}`
            );
            return profiles;
        } catch (error) {
            this.logger.error(
                `❌ Error getting cached similar profiles: ${error.message}`
            );
            return null;
        }
    }

    private async fetchAndCacheSimilarProfiles(
        username: string,
        limit: number
    ): Promise<any[]> {
        try {
            const batchId = this.generateBatchId();
            this.logger.log(
                `🔄 Starting fresh fetch for @${username} (batch: ${batchId.substring(
                    0,
                    8
                )})`
            );

            // Step 1: Fetch similar profiles from external API with retry logic
            const similarProfilesRaw = await this.fetchSimilarProfilesWithRetry(
                username,
                limit
            );

            if (!similarProfilesRaw || similarProfilesRaw.length === 0) {
                this.logger.warn(
                    `⚠️ No similar profiles returned from API for @${username}`
                );
                return [];
            }

            this.logger.log(
                `📥 API returned ${similarProfilesRaw.length} similar profiles`
            );

            // Step 2: Process profiles in parallel batches
            const processedProfiles = await this.processSimilarProfilesBatch(
                username,
                similarProfilesRaw,
                batchId
            );

            this.logger.log(
                `✅ Successfully processed ${processedProfiles.length} similar profiles`
            );
            return processedProfiles;
        } catch (error) {
            this.logger.error(
                `❌ Error fetching and caching similar profiles: ${error.message}`
            );
            return [];
        }
    }

    private async fetchSimilarProfilesWithRetry(
        username: string,
        limit: number,
        maxRetries: number = 2
    ): Promise<any[]> {
        // Enhanced retry logic with username variations
        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                if (attempt > 0) {
                    const delay = Math.min(5000, Math.pow(2, attempt) * 1000); // 2s, 4s
                    this.logger.log(
                        `🔄 Retry attempt ${
                            attempt + 1
                        }/${maxRetries} after ${delay}ms delay`
                    );
                    await new Promise((resolve) => setTimeout(resolve, delay));
                }

                const profiles =
                    await this.externalApiService.getSimilarProfiles(
                        username,
                        limit
                    );

                if (profiles && profiles.length > 0) {
                    this.logger.log(
                        `✅ Successfully fetched ${
                            profiles.length
                        } profiles on attempt ${attempt + 1}`
                    );
                    return profiles;
                }
            } catch (error) {
                this.logger.error(
                    `❌ Error on attempt ${attempt + 1} for @${username}: ${
                        error.message
                    }`
                );
                if (attempt === maxRetries - 1) {
                    this.logger.error(
                        `❌ All attempts failed for @${username}`
                    );
                }
            }
        }

        // Try username variations as fallback
        const variations = this.getUsernameVariations(username);
        for (const variation of variations) {
            try {
                this.logger.log(`🔄 Trying username variation: @${variation}`);
                const profiles =
                    await this.externalApiService.getSimilarProfiles(
                        variation,
                        limit
                    );

                if (profiles && profiles.length > 0) {
                    this.logger.log(
                        `✅ Success with variation @${variation}: ${profiles.length} profiles`
                    );
                    return profiles;
                }
            } catch (error) {
                this.logger.warn(
                    `⚠️ Variation @${variation} failed: ${error.message}`
                );
            }
        }

        return [];
    }

    private async processSimilarProfilesBatch(
        primaryUsername: string,
        profilesRaw: any[],
        batchId: string
    ): Promise<any[]> {
        const processedProfiles = [];
        const batchSize = 10;

        // Process in smaller batches for better performance
        for (let i = 0; i < profilesRaw.length; i += batchSize) {
            const batch = profilesRaw.slice(i, i + batchSize);

            // Process batch in parallel
            const batchPromises = batch.map((profile, index) =>
                this.processSingleSimilarProfile(
                    primaryUsername,
                    profile,
                    i + index + 1,
                    batchId
                )
            );

            const batchResults = await Promise.allSettled(batchPromises);

            // Collect successful results
            for (const result of batchResults) {
                if (result.status === "fulfilled" && result.value.success) {
                    processedProfiles.push(result.value.data);
                }
            }
        }

        return processedProfiles;
    }

    private async processSingleSimilarProfile(
        primaryUsername: string,
        profileRaw: any,
        rank: number,
        batchId: string
    ): Promise<{ success: boolean; data?: any; error?: string }> {
        try {
            const similarUsername = profileRaw.username?.replace("@", "") || "";
            const similarName =
                profileRaw.full_name || profileRaw.name || similarUsername;
            const profilePicUrl = profileRaw.profile_pic_url || "";

            if (!similarUsername) {
                return { success: false, error: "No username" };
            }

            this.logger.log(`🔄 Processing @${similarUsername} (rank ${rank})`);

            // Download and upload profile image
            let profileImagePath = null;
            let profileImageUrl = null;
            let imageDownloaded = false;

            if (profilePicUrl) {
                try {
                    // Download and upload to storage
                    const bucketPath = `similar/${primaryUsername}/${similarUsername}_profile.jpg`;
                    profileImagePath =
                        await this.storageService.uploadImageFromUrl(
                            profilePicUrl,
                            "profile-images",
                            bucketPath
                        );

                    if (profileImagePath) {
                        profileImageUrl = `https://cdn.supabase.co/storage/v1/object/public/profile-images/${profileImagePath}`;
                        imageDownloaded = true;
                        this.logger.log(
                            `✅ Image uploaded for @${similarUsername}`
                        );
                    }
                } catch (error) {
                    this.logger.warn(
                        `⚠️ Failed to download image for @${similarUsername}: ${error.message}`
                    );
                }
            }

            // Save to database using upsert
            const dbRecord = {
                primary_username: primaryUsername,
                similar_username: similarUsername,
                similar_name: similarName,
                profile_image_path: profileImagePath,
                profile_image_url: profileImageUrl,
                similarity_rank: rank,
                batch_id: batchId,
                image_downloaded: imageDownloaded,
                fetch_failed: !imageDownloaded && !!profilePicUrl,
            };

            await this.similarProfileModel.findOneAndUpdate(
                {
                    primary_username: primaryUsername,
                    similar_username: similarUsername,
                },
                dbRecord,
                { upsert: true, new: true }
            );

            return {
                success: true,
                data: {
                    username: similarUsername,
                    name: similarName,
                    profile_image_url: profileImageUrl,
                    rank: rank,
                },
            };
        } catch (error) {
            this.logger.error(
                `❌ Error processing similar profile: ${error.message}`
            );
            return { success: false, error: error.message };
        }
    }

    private getUsernameVariations(username: string): string[] {
        const variations = [];
        const cleanUsername = username.toLowerCase().replace("@", "").trim();

        if (cleanUsername.length > 3) {
            // Remove numbers at the end
            const withoutNumbers = cleanUsername.replace(/\d+$/, "");
            if (withoutNumbers !== cleanUsername && withoutNumbers.length > 2) {
                variations.push(withoutNumbers);
            }

            // Remove special characters
            const withoutSpecial = cleanUsername.replace(/[_.]/g, "");
            if (withoutSpecial !== cleanUsername && withoutSpecial.length > 2) {
                variations.push(withoutSpecial);
            }
        }

        return variations.slice(0, 2); // Limit to 2 variations
    }

    private generateBatchId(): string {
        return (
            Math.random().toString(36).substring(2, 15) +
            Math.random().toString(36).substring(2, 15)
        );
    }
}

// Similar Profile Mongoose Schema
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document } from "mongoose";

export type SimilarProfileDocument = SimilarProfile & Document;

@Schema({ timestamps: true, collection: "similar_profiles" })
export class SimilarProfile {
    @Prop({ required: true, index: true })
    primary_username: string;

    @Prop({ required: true, index: true })
    similar_username: string;

    @Prop()
    similar_name?: string;

    @Prop()
    profile_image_path?: string;

    @Prop()
    profile_image_url?: string;

    @Prop({ type: Number, default: 0 })
    similarity_rank: number;

    @Prop()
    batch_id?: string;

    @Prop({ type: Boolean, default: false })
    image_downloaded: boolean;

    @Prop({ type: Boolean, default: false })
    fetch_failed: boolean;

    @Prop({ type: Date, default: Date.now })
    created_at: Date;
}

export const SimilarProfileSchema =
    SchemaFactory.createForClass(SimilarProfile);

// Create compound indexes for efficient querying
SimilarProfileSchema.index(
    { primary_username: 1, similar_username: 1 },
    { unique: true }
);
SimilarProfileSchema.index({ primary_username: 1, similarity_rank: 1 });
SimilarProfileSchema.index({
    primary_username: 1,
    image_downloaded: 1,
    created_at: -1,
});
SimilarProfileSchema.index({ batch_id: 1 });
```

### Key Differences in Nest.js Implementation

1. **DTO Validation**: Comprehensive input validation with proper type conversion and constraints for limit (1-80) and force_refresh parameters.

2. **Enhanced Caching Strategy**:

    - **24-Hour Cache**: Configurable cache duration with time-based filtering
    - **Image Validation**: Only returns profiles with successfully downloaded images
    - **CDN URL Generation**: Automatic conversion of storage paths to CDN URLs

3. **Robust Retry Logic**:

    - **Progressive Delays**: Exponential backoff with 2s, 4s delays
    - **Username Variations**: Fallback strategies with username modifications
    - **Error Resilience**: Continues processing even if individual profiles fail

4. **Parallel Processing**:

    - **Batch Operations**: Processes profiles in batches of 10 for optimal performance
    - **Promise.allSettled**: Ensures all profiles are processed even if some fail
    - **Concurrent Downloads**: Parallel image downloads and database operations

5. **Comprehensive Schema**: Complete Mongoose schema with strategic indexing:

    - **Compound Indexes**: Efficient querying on primary_username + similar_username
    - **Performance Indexes**: Optimized for cache lookups and ranking
    - **Unique Constraints**: Prevents duplicate similar profile entries

6. **Storage Integration**: Seamless integration with storage services for image management:

    - **CDN Optimization**: Automatic CDN URL generation for fast image delivery
    - **Organized Storage**: Structured bucket paths for easy management
    - **Error Handling**: Graceful degradation when image downloads fail

7. **Production-Ready Features**:
    - **Comprehensive Logging**: Detailed logging with emojis for easy monitoring
    - **Batch Tracking**: UUID-based batch tracking for debugging
    - **Resource Management**: Proper error handling and resource cleanup

## Responses

### Success: 200 OK

Returns a list of similar profiles with CDN-optimized images and metadata indicating cache status.

**Example Response (Cached):**

```json
{
    "success": true,
    "data": [
        {
            "username": "marketing_expert_sarah",
            "name": "Sarah Johnson - Marketing Expert",
            "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/similar/tech_entrepreneur/marketing_expert_sarah_profile.jpg",
            "rank": 1
        },
        {
            "username": "startup_founder_mike",
            "name": "Mike Chen | Startup Founder",
            "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/similar/tech_entrepreneur/startup_founder_mike_profile.jpg",
            "rank": 2
        },
        {
            "username": "business_coach_alex",
            "name": "Alex Rodriguez - Business Coach",
            "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/similar/tech_entrepreneur/business_coach_alex_profile.jpg",
            "rank": 3
        },
        {
            "username": "digital_nomad_lisa",
            "name": "Lisa Park | Digital Nomad",
            "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/similar/tech_entrepreneur/digital_nomad_lisa_profile.jpg",
            "rank": 4
        },
        {
            "username": "growth_hacker_james",
            "name": "James Wilson - Growth Hacker",
            "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/similar/tech_entrepreneur/growth_hacker_james_profile.jpg",
            "rank": 5
        }
    ],
    "message": "Found 5 similar profiles (cached)"
}
```

**Example Response (Fresh):**

```json
{
    "success": true,
    "data": [
        {
            "username": "ai_researcher_emma",
            "name": "Emma Thompson - AI Researcher",
            "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/similar/tech_entrepreneur/ai_researcher_emma_profile.jpg",
            "rank": 1
        },
        {
            "username": "blockchain_dev_carlos",
            "name": "Carlos Martinez | Blockchain Developer",
            "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/similar/tech_entrepreneur/blockchain_dev_carlos_profile.jpg",
            "rank": 2
        }
    ],
    "message": "Found 2 similar profiles (fresh)"
}
```

**Key Response Features:**

-   **CDN-Optimized Images**: All profile images served from Supabase Storage CDN for fast loading
-   **Similarity Ranking**: Profiles ordered by similarity rank for relevance
-   **Cache Status Indication**: Message clearly indicates whether results are cached or fresh
-   **Structured Profile Data**: Complete profile information including username, display name, and image
-   **Organized Storage Paths**: Images stored in organized bucket structure for easy management
-   **High Limit Support**: Supports up to 80 similar profiles per request for comprehensive analysis

### Response Field Details:

-   **`username`**: Instagram username of the similar profile
-   **`name`**: Display name or full name from Instagram profile
-   **`profile_image_url`**: CDN-optimized URL for profile image (Supabase Storage)
-   **`rank`**: Similarity ranking (1 = most similar)
-   **`message`**: Descriptive message indicating count and cache status
-   **`success`**: Always true for successful responses

### Cache Behavior:

-   **24-Hour Cache**: Results cached for 24 hours for lightning-fast subsequent requests
-   **Image Validation**: Only returns profiles with successfully downloaded images
-   **Force Refresh**: `force_refresh=true` bypasses cache and fetches fresh data
-   **Automatic Expiration**: Cache automatically expires after 24 hours

### Error: 503 Service Unavailable

Returned if the `simple_similar_profiles_api` module is not available.

### Error: 500 Internal Server Error

Returned for any other server-side errors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_similar_profiles_fast(username: str, limit: int, force_refresh: bool)`
-   **Helper Module:** `simple_similar_profiles_api.py`
-   **Caching:** Results are cached for 24 hours to ensure fast subsequent requests.
