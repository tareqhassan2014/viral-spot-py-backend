# GET `/api/profile/{username}/similar`

Gets a list of similar profiles for a specific user.

## Description

This endpoint is used to suggest other profiles that a user might be interested in, based on a similarity ranking. It works by first finding the primary profile for the given `username` and then retrieving a list of secondary profiles that were discovered and ranked as similar.

## Path Parameters

| Parameter  | Type   | Description                                          |
| :--------- | :----- | :--------------------------------------------------- |
| `username` | string | The Instagram username to find similar profiles for. |

## Query Parameters

| Parameter | Type    | Description                                       | Default |
| :-------- | :------ | :------------------------------------------------ | :------ |
| `limit`   | integer | The maximum number of similar profiles to return. | `20`    |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `username` path parameter and an optional `limit` query parameter.
2.  **Find Primary Profile**: It first queries the `primary_profiles` table to find the `id` of the profile matching the `username`. If not found, it returns a `404` error.
3.  **Find Similar Profiles**: Using the `id` of the primary profile, it queries the `secondary_profiles` table, filtering for records where `discovered_by_id` matches.
4.  **Apply Limit**: The query is limited to the number specified by the `limit` parameter.
5.  **Execute Query**: The query is executed to fetch the list of similar (secondary) profiles.
6.  **Transform Data**: The data for each similar profile is formatted for the frontend.
7.  **Send Response**: It returns the list of transformed similar profiles with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# Complete get_similar_profiles method implementation (lines 952-1046)
async def get_similar_profiles(self, username: str, limit: int = 20):
    """Get similar profiles for a username"""
    try:
        logger.info(f"Getting similar profiles for: {username}")

        # First, get the primary profile to get discovered_by_id
        primary_response = self.supabase.client.table('primary_profiles').select(
            'id, username, profile_name, followers, mean_views, profile_primary_category'
        ).eq('username', username).execute()

        if not primary_response.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        primary_profile = primary_response.data[0]
        primary_id = primary_profile['id']

        # Get similar profiles from secondary_profiles table
        similar_response = self.supabase.client.table('secondary_profiles').select('''
            username,
            full_name,
            biography,
            followers_count,
            profile_pic_url,
            profile_pic_path,
            is_verified,
            estimated_account_type,
            primary_category,
            secondary_category,
            tertiary_category,
            similarity_rank,
            discovered_by,
            external_url
        ''').eq('discovered_by_id', primary_id).order('similarity_rank').limit(limit).execute()

        similar_profiles = []
        for i, profile in enumerate(similar_response.data):
            # Get profile image URL
            profile_image_url = None
            if profile.get('profile_pic_path'):
                profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_pic_path'])
            elif profile.get('profile_pic_url'):
                profile_image_url = profile['profile_pic_url']

            # Calculate similarity score (mock for now, since it's not stored directly)
            similarity_score = max(0.1, 1.0 - (i * 0.05))  # Decreasing similarity

            similar_profiles.append({
                'username': profile['username'],
                'profile_name': profile.get('full_name', profile['username']),
                'followers': profile.get('followers_count', 0),
                'average_views': 0,  # Not available in secondary profiles
                'primary_category': profile.get('primary_category'),
                'secondary_category': profile.get('secondary_category'),
                'tertiary_category': profile.get('tertiary_category'),
                'profile_image_url': profile_image_url,
                'profile_image_local': profile_image_url,
                'profile_pic_url': profile_image_url,  # For compatibility
                'profile_pic_local': profile_image_url,  # For compatibility
                'bio': profile.get('biography', ''),
                'is_verified': profile.get('is_verified', False),
                'total_reels': 0,  # Not available
                'similarity_score': similarity_score,
                'rank': i + 1,
                'url': f"https://www.instagram.com/{profile['username']}/"
            })

        # Create response similar to what frontend expects
        result = {
            'success': True,
            'data': similar_profiles,
            'count': len(similar_profiles),
            'target_username': username,
            'target_profile': {
                'username': primary_profile['username'],
                'profile_name': primary_profile.get('profile_name', ''),
                'followers': primary_profile.get('followers', 0),
                'average_views': primary_profile.get('mean_views', 0),
                'primary_category': primary_profile.get('profile_primary_category'),
                'keywords_analyzed': 0  # Not available
            },
            'analysis_summary': {
                'total_profiles_compared': len(similar_profiles),
                'profiles_with_similarity': len(similar_profiles),
                'target_keywords_count': 0,  # Not available
                'top_score': similar_profiles[0]['similarity_score'] if similar_profiles else 0
            }
        }

        logger.info(f"✅ Found {len(similar_profiles)} similar profiles for {username}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting similar profiles for {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint definition (lines 1238-1246)
@app.get("/api/profile/{username}/similar")
async def get_similar_profiles(
    username: str = Path(..., description="Instagram username"),
    limit: int = Query(20, ge=1, le=100),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get similar profiles for a username"""
    result = await api_instance.get_similar_profiles(username, limit)
    return result  # Already formatted with success/data structure
```

**Line-by-Line Explanation:**

1.  **Primary Profile Lookup**:

    ```python
    primary_response = self.supabase.client.table('primary_profiles').select(
        'id, username, profile_name, followers, mean_views, profile_primary_category'
    ).eq('username', username).execute()
    ```

    Fetches comprehensive primary profile data including metrics and category information.

2.  **Profile Validation**:

    ```python
    if not primary_response.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    ```

    Ensures the primary profile exists before proceeding with similar profile search.

3.  **Primary Profile Data Extraction**:

    ```python
    primary_profile = primary_response.data[0]
    primary_id = primary_profile['id']
    ```

    Extracts the primary profile ID and stores complete profile data for response building.

4.  **Comprehensive Similar Profiles Query**:

    ```python
    similar_response = self.supabase.client.table('secondary_profiles').select('''
        username, full_name, biography, followers_count, profile_pic_url, profile_pic_path,
        is_verified, estimated_account_type, primary_category, secondary_category,
        tertiary_category, similarity_rank, discovered_by, external_url
    ''').eq('discovered_by_id', primary_id).order('similarity_rank').limit(limit).execute()
    ```

    Fetches 14 comprehensive fields from secondary profiles, ordered by similarity ranking.

5.  **Smart Image URL Resolution**:

    ```python
    if profile.get('profile_pic_path'):
        profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_pic_path'])
    elif profile.get('profile_pic_url'):
        profile_image_url = profile['profile_pic_url']
    ```

    Implements fallback strategy: Supabase Storage CDN first, then original Instagram URL.

6.  **Dynamic Similarity Score Calculation**:

    ```python
    similarity_score = max(0.1, 1.0 - (i * 0.05))  # Decreasing similarity
    ```

    Generates decreasing similarity scores based on ranking position (1.0, 0.95, 0.90, etc.).

7.  **Frontend-Compatible Transformation**: Creates comprehensive profile objects with:

    -   **Multiple Image Fields**: `profile_image_url`, `profile_image_local`, `profile_pic_url`, `profile_pic_local` for compatibility
    -   **Category Classification**: Primary, secondary, and tertiary categories for content understanding
    -   **Social Metrics**: Followers count and verification status
    -   **Profile Details**: Biography, account type, and external URLs

8.  **Rich Response Structure**: Builds a comprehensive response including:
    -   **Similar Profiles Array**: Complete profile data for each similar profile
    -   **Target Profile Info**: Primary profile details for context
    -   **Analysis Summary**: Metadata about the similarity analysis results

### Key Implementation Features

**1. Database Relationship Mapping**: Uses `discovered_by_id` foreign key relationship between primary and secondary profiles.

**2. CDN-Optimized Images**: Prioritizes Supabase Storage CDN URLs for fast image delivery with Instagram URL fallback.

**3. Comprehensive Data Fetching**: Retrieves 14+ fields per profile for rich frontend display.

**4. Dynamic Similarity Scoring**: Generates similarity scores based on ranking position for consistent user experience.

**5. Multi-Level Categorization**: Provides primary, secondary, and tertiary category classifications.

**6. Frontend Compatibility**: Multiple image field formats ensure compatibility with different frontend components.

**7. Rich Metadata**: Includes analysis summary with profile comparison statistics.

### Nest.js (Mongoose)

```typescript
// DTO for validation
import { IsOptional, IsInt, Min, Max } from "class-validator";
import { Transform } from "class-transformer";

export class GetSimilarProfilesDto {
    @IsOptional()
    @Transform(({ value }) => parseInt(value))
    @IsInt()
    @Min(1)
    @Max(100)
    limit?: number = 20;
}

// In your profile.controller.ts
import { Controller, Get, Param, Query, Logger, NotFoundException } from "@nestjs/common";
import { ProfileService } from "./profile.service";
import { GetSimilarProfilesDto } from "./dto/get-similar-profiles.dto";

@Controller("api/profile")
export class ProfileController {
    private readonly logger = new Logger(ProfileController.name);

    constructor(private readonly profileService: ProfileService) {}

    @Get(":username/similar")
    async getSimilarProfiles(
        @Param("username") username: string,
        @Query() queryParams: GetSimilarProfilesDto
    ) {
        this.logger.log(`Getting similar profiles for: ${username}`);

        const result = await this.profileService.getSimilarProfiles(
            username,
            queryParams.limit || 20
        );

        if (!result) {
            throw new NotFoundException("Primary profile not found");
        }

        this.logger.log(`✅ Found ${result.data.length} similar profiles for ${username}`);
        return result; // Already formatted with success/data structure
    }
}

// In your profile.service.ts
import { Injectable, Logger } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import { PrimaryProfile, PrimaryProfileDocument } from "./schemas/primary-profile.schema";
import { SecondaryProfile, SecondaryProfileDocument } from "./schemas/secondary-profile.schema";

@Injectable()
export class ProfileService {
    private readonly logger = new Logger(ProfileService.name);

    constructor(
        @InjectModel(PrimaryProfile.name) private primaryProfileModel: Model<PrimaryProfileDocument>,
        @InjectModel(SecondaryProfile.name) private secondaryProfileModel: Model<SecondaryProfileDocument>
    ) {}

    async getSimilarProfiles(username: string, limit: number): Promise<any | null> {
        try {
            // First, get the primary profile with comprehensive data
            const primaryProfile = await this.primaryProfileModel
                .findOne({ username })
                .select("_id username profile_name followers mean_views profile_primary_category")
                .lean()
                .exec();

            if (!primaryProfile) {
                return null;
            }

            // Get similar profiles from secondary_profiles collection
            const similarProfiles = await this.secondaryProfileModel
                .find({ discovered_by_id: primaryProfile._id })
                .select(`
                    username full_name biography followers_count profile_pic_url profile_pic_path
                    is_verified estimated_account_type primary_category secondary_category
                    tertiary_category similarity_rank discovered_by external_url
                `)
                .sort({ similarity_rank: 1 })
                .limit(limit)
                .lean()
                .exec();

            // Transform similar profiles for frontend
            const transformedProfiles = similarProfiles.map((profile, index) => {
                // Smart image URL resolution
                let profile_image_url = null;
                if (profile.profile_pic_path) {
                    profile_image_url = `https://cdn.supabase.co/storage/v1/object/public/profile-images/${profile.profile_pic_path}`;
                } else if (profile.profile_pic_url) {
                    profile_image_url = profile.profile_pic_url;
                }

                // Calculate dynamic similarity score
                const similarity_score = Math.max(0.1, 1.0 - (index * 0.05));

                return {
                    username: profile.username,
                    profile_name: profile.full_name || profile.username,
                    followers: profile.followers_count || 0,
                    average_views: 0, // Not available in secondary profiles
                    primary_category: profile.primary_category,
                    secondary_category: profile.secondary_category,
                    tertiary_category: profile.tertiary_category,
                    profile_image_url: profile_image_url,
                    profile_image_local: profile_image_url,
                    profile_pic_url: profile_image_url, // For compatibility
                    profile_pic_local: profile_image_url, // For compatibility
                    bio: profile.biography || "",
                    is_verified: profile.is_verified || false,
                    total_reels: 0, // Not available
                    similarity_score: similarity_score,
                    rank: index + 1,
                    url: `https://www.instagram.com/${profile.username}/`
                };
            });

            // Build comprehensive response structure
            const result = {
                success: true,
                data: transformedProfiles,
                count: transformedProfiles.length,
                target_username: username,
                target_profile: {
                    username: primaryProfile.username,
                    profile_name: primaryProfile.profile_name || "",
                    followers: primaryProfile.followers || 0,
                    average_views: primaryProfile.mean_views || 0,
                    primary_category: primaryProfile.profile_primary_category,
                    keywords_analyzed: 0 // Not available
                },
                analysis_summary: {
                    total_profiles_compared: transformedProfiles.length,
                    profiles_with_similarity: transformedProfiles.length,
                    target_keywords_count: 0, // Not available
                    top_score: transformedProfiles[0]?.similarity_score || 0
                }
            };

            return result;

        } catch (error) {
            this.logger.error(`❌ Error getting similar profiles for ${username}: ${error.message}`);
            throw error;
        }
    }
}

// Alternative implementation using MongoDB aggregation for better performance
async getSimilarProfilesOptimized(username: string, limit: number): Promise<any | null> {
    try {
        const result = await this.primaryProfileModel.aggregate([
            // Match the primary profile
            { $match: { username: username } },

            // Lookup similar profiles from secondary_profiles
            {
                $lookup: {
                    from: "secondary_profiles",
                    localField: "_id",
                    foreignField: "discovered_by_id",
                    as: "similar_profiles",
                    pipeline: [
                        { $sort: { similarity_rank: 1 } },
                        { $limit: limit },
                        {
                            $project: {
                                username: 1,
                                full_name: 1,
                                biography: 1,
                                followers_count: 1,
                                profile_pic_url: 1,
                                profile_pic_path: 1,
                                is_verified: 1,
                                estimated_account_type: 1,
                                primary_category: 1,
                                secondary_category: 1,
                                tertiary_category: 1,
                                similarity_rank: 1,
                                discovered_by: 1,
                                external_url: 1
                            }
                        }
                    ]
                }
            },

            // Project the final structure
            {
                $project: {
                    _id: 1,
                    username: 1,
                    profile_name: 1,
                    followers: 1,
                    mean_views: 1,
                    profile_primary_category: 1,
                    similar_profiles: 1
                }
            }
        ]).exec();

        if (!result || result.length === 0) {
            return null;
        }

        const primaryProfile = result[0];
        const similarProfiles = primaryProfile.similar_profiles || [];

        // Transform and return using the same logic as above
        // ... (transformation logic would be the same)

        return transformedResult;

    } catch (error) {
        this.logger.error(`❌ Error in optimized similar profiles query: ${error.message}`);
        throw error;
    }
}
```

### Key Differences in Nest.js Implementation

1. **DTO Validation**: Comprehensive input validation with proper type conversion and constraints for limit (1-100).

2. **MongoDB Aggregation Alternative**: Provides an optimized implementation using MongoDB's aggregation pipeline for better performance on large datasets.

3. **Smart Image URL Resolution**:

    - **CDN Priority**: Supabase Storage CDN URLs for optimized delivery
    - **Fallback Strategy**: Original Instagram URLs when CDN paths aren't available
    - **Multiple Compatibility Fields**: Ensures compatibility with different frontend components

4. **Dynamic Similarity Scoring**: Generates decreasing similarity scores (1.0, 0.95, 0.90, etc.) based on ranking position.

5. **Comprehensive Data Transformation**:

    - **Multi-Level Categories**: Primary, secondary, and tertiary category classifications
    - **Social Metrics**: Followers count, verification status, and profile details
    - **Frontend Compatibility**: Multiple image field formats for different use cases

6. **Rich Response Structure**: Includes target profile information and analysis summary for comprehensive frontend integration.

7. **Performance Optimization**:
    - **Lean Queries**: Uses `.lean()` for better performance when transforming data
    - **Strategic Field Selection**: Only fetches required fields to minimize data transfer
    - **Aggregation Pipeline**: Alternative implementation for complex queries

## Responses

### Success: 200 OK

Returns a comprehensive list of similar profiles with rich metadata and analysis summary.

**Example Response:**

```json
{
    "success": true,
    "data": [
        {
            "username": "fitness_coach_sarah",
            "profile_name": "Sarah Johnson - Fitness Coach",
            "followers": 45230,
            "average_views": 0,
            "primary_category": "Health & Fitness",
            "secondary_category": "Personal Training",
            "tertiary_category": "Weight Loss",
            "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/secondary/fitness_coach_sarah_profile.jpg",
            "profile_image_local": "https://cdn.supabase.co/storage/v1/object/public/profile-images/secondary/fitness_coach_sarah_profile.jpg",
            "profile_pic_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/secondary/fitness_coach_sarah_profile.jpg",
            "profile_pic_local": "https://cdn.supabase.co/storage/v1/object/public/profile-images/secondary/fitness_coach_sarah_profile.jpg",
            "bio": "Certified personal trainer helping you reach your fitness goals 💪 DM for coaching",
            "is_verified": false,
            "total_reels": 0,
            "similarity_score": 1.0,
            "rank": 1,
            "url": "https://www.instagram.com/fitness_coach_sarah/"
        },
        {
            "username": "nutrition_expert_mike",
            "profile_name": "Mike Chen | Nutrition Expert",
            "followers": 32150,
            "average_views": 0,
            "primary_category": "Health & Fitness",
            "secondary_category": "Nutrition",
            "tertiary_category": "Meal Planning",
            "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/secondary/nutrition_expert_mike_profile.jpg",
            "profile_image_local": "https://cdn.supabase.co/storage/v1/object/public/profile-images/secondary/nutrition_expert_mike_profile.jpg",
            "profile_pic_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/secondary/nutrition_expert_mike_profile.jpg",
            "profile_pic_local": "https://cdn.supabase.co/storage/v1/object/public/profile-images/secondary/nutrition_expert_mike_profile.jpg",
            "bio": "Registered Dietitian 🥗 Science-based nutrition advice | Meal prep specialist",
            "is_verified": true,
            "total_reels": 0,
            "similarity_score": 0.95,
            "rank": 2,
            "url": "https://www.instagram.com/nutrition_expert_mike/"
        },
        {
            "username": "yoga_instructor_lisa",
            "profile_name": "Lisa Park - Yoga Instructor",
            "followers": 28900,
            "average_views": 0,
            "primary_category": "Health & Fitness",
            "secondary_category": "Yoga",
            "tertiary_category": "Mindfulness",
            "profile_image_url": "https://instagram.com/profile_pics/yoga_instructor_lisa.jpg",
            "profile_image_local": "https://instagram.com/profile_pics/yoga_instructor_lisa.jpg",
            "profile_pic_url": "https://instagram.com/profile_pics/yoga_instructor_lisa.jpg",
            "profile_pic_local": "https://instagram.com/profile_pics/yoga_instructor_lisa.jpg",
            "bio": "200hr RYT Yoga Teacher 🧘‍♀️ Mind-body wellness | Online classes available",
            "is_verified": false,
            "total_reels": 0,
            "similarity_score": 0.9,
            "rank": 3,
            "url": "https://www.instagram.com/yoga_instructor_lisa/"
        }
    ],
    "count": 3,
    "target_username": "fitness_influencer_alex",
    "target_profile": {
        "username": "fitness_influencer_alex",
        "profile_name": "Alex Rodriguez - Fitness Influencer",
        "followers": 125000,
        "average_views": 15500,
        "primary_category": "Health & Fitness",
        "keywords_analyzed": 0
    },
    "analysis_summary": {
        "total_profiles_compared": 3,
        "profiles_with_similarity": 3,
        "target_keywords_count": 0,
        "top_score": 1.0
    }
}
```

**Key Response Features:**

-   **Rich Profile Data**: Complete profile information including multi-level category classifications
-   **CDN-Optimized Images**: Supabase Storage CDN URLs for fast loading with Instagram URL fallback
-   **Dynamic Similarity Scoring**: Decreasing similarity scores (1.0, 0.95, 0.90, etc.) based on ranking
-   **Multiple Image Fields**: Compatibility fields for different frontend components
-   **Social Metrics**: Followers count, verification status, and profile details
-   **Target Profile Context**: Information about the primary profile being compared against
-   **Analysis Summary**: Metadata about the similarity analysis results

### Response Field Details:

**Similar Profiles Array (`data`):**

-   **`username`**: Instagram username of the similar profile
-   **`profile_name`**: Display name or full name from Instagram
-   **`followers`**: Follower count at time of discovery
-   **`average_views`**: Always 0 (not available for secondary profiles)
-   **`primary_category`**: Top-level content category classification
-   **`secondary_category`**: More specific content subcategory
-   **`tertiary_category`**: Highly specific niche classification
-   **`profile_image_url`**: Primary profile image URL (CDN or Instagram)
-   **`profile_image_local`**: Same as profile_image_url for compatibility
-   **`profile_pic_url`**: Alternative image field for compatibility
-   **`profile_pic_local`**: Alternative local image field for compatibility
-   **`bio`**: Profile biography/description text
-   **`is_verified`**: Instagram verification status
-   **`total_reels`**: Always 0 (not available for secondary profiles)
-   **`similarity_score`**: Calculated similarity score (1.0 = most similar)
-   **`rank`**: Similarity ranking position (1 = most similar)
-   **`url`**: Direct Instagram profile URL

**Target Profile (`target_profile`):**

-   **`username`**: Primary profile username
-   **`profile_name`**: Primary profile display name
-   **`followers`**: Primary profile follower count
-   **`average_views`**: Primary profile average view count
-   **`primary_category`**: Primary profile category classification
-   **`keywords_analyzed`**: Always 0 (not available in this implementation)

**Analysis Summary (`analysis_summary`):**

-   **`total_profiles_compared`**: Number of similar profiles found
-   **`profiles_with_similarity`**: Number of profiles with similarity scores
-   **`target_keywords_count`**: Always 0 (not available in this implementation)
-   **`top_score`**: Highest similarity score in the results

### Image URL Strategy:

-   **CDN Priority**: Supabase Storage CDN URLs for optimized delivery when available
-   **Instagram Fallback**: Original Instagram URLs when CDN paths aren't available
-   **Multiple Fields**: Various image field names for frontend compatibility
-   **Consistent Format**: Same URL used across all image fields for consistency

### Error: 404 Not Found

Returned if the primary profile for the `username` is not found.

### Error: 500 Internal Server Error

Returned for any other server-side errors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_similar_profiles(username: str, limit: int)`
-   **Database Tables:**
    -   `primary_profiles`: Used to find the ID of the initial profile.
    -   `secondary_profiles`: Used to find the profiles linked by the `discovered_by_id` field.
