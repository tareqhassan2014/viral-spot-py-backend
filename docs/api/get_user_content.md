# GET `/api/content/user/{username}` ⚡

Fetches content from a user's own profile.

## Description

This endpoint allows users to view their own content through the ViralSpot analysis pipeline and interface. It's useful for users who want to analyze their own content strategy, see how their posts and reels are performing, and get the same insights for their own profiles as they do for competitors.

The endpoint supports pagination and sorting to make it easy for users to browse their own content library.

## Path Parameters

| Parameter  | Type   | Description                                    |
| :--------- | :----- | :--------------------------------------------- |
| `username` | string | The username of the user to fetch content for. |

## Query Parameters

| Parameter | Type    | Description                                                        | Default  |
| :-------- | :------ | :----------------------------------------------------------------- | :------- |
| `limit`   | integer | The maximum number of content items to return per page (1-100).    | `24`     |
| `offset`  | integer | The number of content items to skip for pagination.                | `0`      |
| `sort_by` | string  | The sorting order. Options: `recent`, `popular`, `views`, `likes`. | `recent` |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `username` path parameter and optional query parameters for sorting and pagination.
2.  **Build Query**: It constructs a database query on the `content` table, filtering for records that match the `username`.
3.  **Apply Sorting**: The `sort_by` parameter is used to add an `ORDER BY` clause to the query.
4.  **Apply Pagination**: The `limit` and `offset` parameters are used for pagination.
5.  **Execute Query**: The query is executed to fetch the user's content.
6.  **Transform and Respond**: The results are transformed into a frontend-friendly format and returned with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# Complete get_user_content endpoint implementation (lines 2123-2181)
@app.get("/api/content/user/{username}")
async def get_user_content(
    username: str,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("recent", regex="^(recent|popular|views|likes)$"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get user's own content for grid display"""
    try:
        # Build query for user content with profile join for consistent profile data
        query = api_instance.supabase.client.table('content').select('''
            *,
            primary_profiles!profile_id (
                username,
                profile_name,
                bio,
                followers,
                profile_image_url,
                profile_image_path,
                is_verified,
                account_type
            )
        ''').eq('username', username)

        # Apply sorting
        if sort_by == "popular":
            query = query.order('outlier_score', desc=True)
        elif sort_by == "views":
            query = query.order('view_count', desc=True)
        elif sort_by == "likes":
            query = query.order('like_count', desc=True)
        else:  # recent (default)
            query = query.order('date_posted', desc=True)

        # Execute query with pagination
        result = query.range(offset, offset + limit - 1).execute()

        # Transform using the same method as working endpoints
        processed_reels = []
        for item in (result.data or []):
            transformed = api_instance._transform_content_for_frontend(item)
            if transformed:
                processed_reels.append(transformed)

        return APIResponse(
            success=True,
            data={
                'reels': processed_reels,
                'total_count': len(processed_reels),
                'has_more': len(result.data) == limit if result.data else False,
                'username': username,
                'sort_by': sort_by
            }
        )

    except Exception as e:
        logger.error(f"Error getting user content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user content")
```

**Line-by-Line Explanation:**

1.  **Endpoint Definition**:

    ```python
    @app.get("/api/content/user/{username}")
    async def get_user_content(username: str, limit: int = Query(24, ge=1, le=100), ...)
    ```

    Defines the FastAPI endpoint with comprehensive parameter validation and regex constraints for `sort_by`.

2.  **Comprehensive Content Query**:

    ```python
    query = api_instance.supabase.client.table('content').select('''
        *,
        primary_profiles!profile_id (
            username, profile_name, bio, followers, profile_image_url,
            profile_image_path, is_verified, account_type
        )
    ''').eq('username', username)
    ```

    Fetches all content fields plus 8 essential profile fields via JOIN for rich display data.

3.  **Dynamic Sorting Logic**:

    ```python
    if sort_by == "popular":
        query = query.order('outlier_score', desc=True)
    elif sort_by == "views":
        query = query.order('view_count', desc=True)
    elif sort_by == "likes":
        query = query.order('like_count', desc=True)
    else:  # recent (default)
        query = query.order('date_posted', desc=True)
    ```

    Implements 4 different sorting strategies with "recent" as the default for user content.

4.  **Pagination Execution**:

    ```python
    result = query.range(offset, offset + limit - 1).execute()
    ```

    Applies efficient database-level pagination using Supabase's range method.

5.  **Content Transformation**:

    ```python
    processed_reels = []
    for item in (result.data or []):
        transformed = api_instance._transform_content_for_frontend(item)
        if transformed:
            processed_reels.append(transformed)
    ```

    Uses the same `_transform_content_for_frontend` method as other endpoints for consistency.

6.  **Rich Response Structure**:
    ```python
    return APIResponse(success=True, data={
        'reels': processed_reels,
        'total_count': len(processed_reels),
        'has_more': len(result.data) == limit if result.data else False,
        'username': username,
        'sort_by': sort_by
    })
    ```
    Returns comprehensive metadata including pagination info and sorting context.

### Key Implementation Features

**1. Profile Data Integration**: Joins with `primary_profiles` table to include essential profile information with each content item.

**2. User-Centric Sorting**: Default sorting is "recent" (vs "popular" for competitors) to show users their latest content first.

**3. Comprehensive Field Selection**: Fetches all content fields plus 8 profile fields for rich frontend display.

**4. Consistent Transformation**: Uses the same `_transform_content_for_frontend` method as other content endpoints.

**5. Efficient Pagination**: Database-level pagination with `has_more` indicator for infinite scroll support.

**6. Regex Validation**: Strict validation of `sort_by` parameter to prevent invalid sorting options.

**7. Error Resilience**: Comprehensive error handling with detailed logging for debugging.

### Nest.js (Mongoose)

```typescript
// DTO for validation
import { IsOptional, IsInt, IsString, Min, Max } from "class-validator";
import { Transform } from "class-transformer";

export class GetUserContentDto {
    @IsOptional()
    @Transform(({ value }) => parseInt(value))
    @IsInt()
    @Min(1)
    @Max(100)
    limit?: number = 24;

    @IsOptional()
    @Transform(({ value }) => parseInt(value))
    @IsInt()
    @Min(0)
    offset?: number = 0;

    @IsOptional()
    @IsString()
    @Transform(({ value }) => value?.toLowerCase())
    sort_by?: string = "recent";
}

// In your content.controller.ts
import { Controller, Get, Param, Query, Logger } from "@nestjs/common";
import { ContentService } from "./content.service";
import { GetUserContentDto } from "./dto/get-user-content.dto";

@Controller("api/content")
export class ContentController {
    private readonly logger = new Logger(ContentController.name);

    constructor(private readonly contentService: ContentService) {}

    @Get("user/:username")
    async getUserContent(
        @Param("username") username: string,
        @Query() queryParams: GetUserContentDto
    ) {
        this.logger.log(`Getting user content for: ${username}`);

        // Validate sort_by parameter
        const validSortOptions = ["recent", "popular", "views", "likes"];
        const sortBy = validSortOptions.includes(
            queryParams.sort_by || "recent"
        )
            ? queryParams.sort_by || "recent"
            : "recent";

        const result = await this.contentService.getUserContent(
            username,
            queryParams.limit || 24,
            queryParams.offset || 0,
            sortBy
        );

        this.logger.log(
            `✅ Found ${result.reels.length} content items for ${username}`
        );
        return {
            success: true,
            data: result,
        };
    }
}

// In your content.service.ts
import { Injectable, Logger } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import { Content, ContentDocument } from "./schemas/content.schema";
import {
    PrimaryProfile,
    PrimaryProfileDocument,
} from "./schemas/primary-profile.schema";

@Injectable()
export class ContentService {
    private readonly logger = new Logger(ContentService.name);

    constructor(
        @InjectModel(Content.name) private contentModel: Model<ContentDocument>,
        @InjectModel(PrimaryProfile.name)
        private primaryProfileModel: Model<PrimaryProfileDocument>
    ) {}

    async getUserContent(
        username: string,
        limit: number,
        offset: number,
        sortBy: string
    ): Promise<any> {
        try {
            // Build sort criteria based on sort_by parameter
            let sortCriteria: any = {};
            switch (sortBy) {
                case "popular":
                    sortCriteria = { outlier_score: -1 };
                    break;
                case "views":
                    sortCriteria = { view_count: -1 };
                    break;
                case "likes":
                    sortCriteria = { like_count: -1 };
                    break;
                default: // recent
                    sortCriteria = { date_posted: -1 };
                    break;
            }

            // Fetch content with profile data using aggregation for better performance
            const contentItems = await this.contentModel
                .aggregate([
                    // Match content by username
                    { $match: { username: username } },

                    // Lookup profile data
                    {
                        $lookup: {
                            from: "primary_profiles",
                            localField: "profile_id",
                            foreignField: "_id",
                            as: "primary_profiles",
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
                    },

                    // Unwind the profile array (should be single item)
                    {
                        $unwind: {
                            path: "$primary_profiles",
                            preserveNullAndEmptyArrays: true,
                        },
                    },

                    // Sort by specified criteria
                    { $sort: sortCriteria },

                    // Apply pagination
                    { $skip: offset },
                    { $limit: limit },
                ])
                .exec();

            // Transform content for frontend using the same logic as other endpoints
            const transformedContent = contentItems
                .map((item) => this.transformContentForFrontend(item))
                .filter((item) => item !== null);

            // Determine if there are more items
            const totalCount = await this.contentModel
                .countDocuments({ username })
                .exec();
            const hasMore = offset + limit < totalCount;

            return {
                reels: transformedContent,
                total_count: transformedContent.length,
                has_more: hasMore,
                username: username,
                sort_by: sortBy,
            };
        } catch (error) {
            this.logger.error(
                `❌ Error getting user content for ${username}: ${error.message}`
            );
            throw error;
        }
    }

    // Alternative implementation using populate for simpler queries
    async getUserContentSimple(
        username: string,
        limit: number,
        offset: number,
        sortBy: string
    ): Promise<any> {
        try {
            // Build sort criteria
            let sortCriteria: any = {};
            switch (sortBy) {
                case "popular":
                    sortCriteria = { outlier_score: -1 };
                    break;
                case "views":
                    sortCriteria = { view_count: -1 };
                    break;
                case "likes":
                    sortCriteria = { like_count: -1 };
                    break;
                default: // recent
                    sortCriteria = { date_posted: -1 };
                    break;
            }

            // Fetch content with profile data using populate
            const contentItems = await this.contentModel
                .find({ username })
                .populate({
                    path: "profile_id",
                    model: "PrimaryProfile",
                    select: "username profile_name bio followers profile_image_url profile_image_path is_verified account_type",
                })
                .sort(sortCriteria)
                .skip(offset)
                .limit(limit)
                .lean()
                .exec();

            // Transform content for frontend
            const transformedContent = contentItems
                .map((item) => this.transformContentForFrontend(item))
                .filter((item) => item !== null);

            // Check for more items
            const hasMore = contentItems.length === limit;

            return {
                reels: transformedContent,
                total_count: transformedContent.length,
                has_more: hasMore,
                username: username,
                sort_by: sortBy,
            };
        } catch (error) {
            this.logger.error(
                `❌ Error in simple user content query: ${error.message}`
            );
            throw error;
        }
    }

    private transformContentForFrontend(item: any): any {
        if (!item) return null;

        try {
            // Get profile data (either from aggregation or populate)
            const profile = item.primary_profiles || item.profile_id;

            // Smart image URL resolution
            let profile_image_url = null;
            if (profile?.profile_image_path) {
                profile_image_url = `https://cdn.supabase.co/storage/v1/object/public/profile-images/${profile.profile_image_path}`;
            } else if (profile?.profile_image_url) {
                profile_image_url = profile.profile_image_url;
            }

            // Transform content item with profile data
            return {
                id: item._id?.toString() || item.id,
                username: item.username,
                caption: item.caption || "",
                view_count: this.formatNumber(item.view_count || 0),
                like_count: this.formatNumber(item.like_count || 0),
                comment_count: this.formatNumber(item.comment_count || 0),
                share_count: this.formatNumber(item.share_count || 0),
                date_posted: item.date_posted,
                content_type: item.content_type || "reel",
                thumbnail_url: item.thumbnail_url,
                video_url: item.video_url,
                outlier_score: item.outlier_score || 0,

                // Profile information
                profile: {
                    username: profile?.username || item.username,
                    profile_name: profile?.profile_name || "",
                    bio: profile?.bio || "",
                    followers: this.formatNumber(profile?.followers || 0),
                    profile_image_url: profile_image_url,
                    is_verified: profile?.is_verified || false,
                    account_type: profile?.account_type || "Personal",
                },

                // Additional metadata
                engagement_rate: this.calculateEngagementRate(item, profile),
                performance_score: this.calculatePerformanceScore(item),
                content_url: `https://www.instagram.com/p/${
                    item.shortcode || item.id
                }/`,
            };
        } catch (error) {
            this.logger.error(
                `❌ Error transforming content item: ${error.message}`
            );
            return null;
        }
    }

    private formatNumber(num: number): string {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + "M";
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + "K";
        }
        return num.toString();
    }

    private calculateEngagementRate(content: any, profile: any): number {
        if (!profile?.followers || profile.followers === 0) return 0;
        const totalEngagement =
            (content.like_count || 0) + (content.comment_count || 0);
        return (
            Math.round((totalEngagement / profile.followers) * 100 * 100) / 100
        ); // Round to 2 decimal places
    }

    private calculatePerformanceScore(content: any): number {
        // Simple performance score based on engagement metrics
        const views = content.view_count || 0;
        const likes = content.like_count || 0;
        const comments = content.comment_count || 0;
        const shares = content.share_count || 0;

        // Weighted score calculation
        return Math.round(
            views * 0.1 + likes * 0.4 + comments * 0.3 + shares * 0.2
        );
    }
}
```

### Key Differences in Nest.js Implementation

1. **DTO Validation**: Comprehensive input validation with proper type conversion and constraints for all parameters.

2. **MongoDB Aggregation**: Provides an optimized implementation using MongoDB's aggregation pipeline for better performance with JOINs.

3. **Populate Alternative**: Includes a simpler implementation using Mongoose's `populate` method for easier understanding.

4. **User-Centric Sorting**: Default sorting is "recent" to show users their latest content first, matching the Python implementation.

5. **Smart Image URL Resolution**:

    - **CDN Priority**: Supabase Storage CDN URLs for optimized delivery
    - **Fallback Strategy**: Original profile URLs when CDN paths aren't available

6. **Rich Content Transformation**:

    - **Profile Integration**: Includes complete profile data with each content item
    - **Engagement Metrics**: Calculates engagement rate and performance scores
    - **Number Formatting**: Formats large numbers (1.2K, 1.5M) for better display
    - **Content URLs**: Generates direct Instagram links for each content item

7. **Performance Optimization**:

    - **Lean Queries**: Uses `.lean()` for better performance when transforming data
    - **Strategic Field Selection**: Only fetches required profile fields to minimize data transfer
    - **Aggregation Pipeline**: Efficient JOINs using MongoDB aggregation

8. **Error Resilience**: Comprehensive error handling with detailed logging and graceful degradation when transformation fails.

## Responses

### Success: 200 OK

Returns a comprehensive paginated list of the user's own content with rich metadata and profile integration.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "id": "64f8a9b2c1d2e3f4a5b6c7d8",
                "username": "fitness_creator_alex",
                "caption": "Morning workout routine that changed my life! 💪 Who's ready to transform? #fitness #motivation #workout",
                "view_count": "125.3K",
                "like_count": "8.2K",
                "comment_count": "342",
                "share_count": "156",
                "date_posted": "2024-01-15T08:30:00Z",
                "content_type": "reel",
                "thumbnail_url": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/fitness_creator_alex/reel_001_thumb.jpg",
                "video_url": "https://cdn.supabase.co/storage/v1/object/public/content-videos/fitness_creator_alex/reel_001.mp4",
                "outlier_score": 8.7,
                "profile": {
                    "username": "fitness_creator_alex",
                    "profile_name": "Alex Rodriguez - Fitness Coach",
                    "bio": "Certified Personal Trainer 💪 Helping you reach your fitness goals | Online coaching available",
                    "followers": "125.8K",
                    "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/fitness_creator_alex_profile.jpg",
                    "is_verified": true,
                    "account_type": "Business Page"
                },
                "engagement_rate": 6.85,
                "performance_score": 18750,
                "content_url": "https://www.instagram.com/p/C2Abc123Def/"
            },
            {
                "id": "64f8a9b2c1d2e3f4a5b6c7d9",
                "username": "fitness_creator_alex",
                "caption": "Quick 5-minute ab workout you can do anywhere! No equipment needed 🔥 Save this for later!",
                "view_count": "89.7K",
                "like_count": "5.4K",
                "comment_count": "198",
                "share_count": "89",
                "date_posted": "2024-01-12T15:45:00Z",
                "content_type": "reel",
                "thumbnail_url": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/fitness_creator_alex/reel_002_thumb.jpg",
                "video_url": "https://cdn.supabase.co/storage/v1/object/public/content-videos/fitness_creator_alex/reel_002.mp4",
                "outlier_score": 7.2,
                "profile": {
                    "username": "fitness_creator_alex",
                    "profile_name": "Alex Rodriguez - Fitness Coach",
                    "bio": "Certified Personal Trainer 💪 Helping you reach your fitness goals | Online coaching available",
                    "followers": "125.8K",
                    "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/fitness_creator_alex_profile.jpg",
                    "is_verified": true,
                    "account_type": "Business Page"
                },
                "engagement_rate": 4.45,
                "performance_score": 13280,
                "content_url": "https://www.instagram.com/p/C2Xyz789Ghi/"
            },
            {
                "id": "64f8a9b2c1d2e3f4a5b6c7da",
                "username": "fitness_creator_alex",
                "caption": "Meal prep Sunday! Here's my go-to high-protein breakfast prep 🍳 Recipe in comments!",
                "view_count": "67.2K",
                "like_count": "4.1K",
                "comment_count": "267",
                "share_count": "124",
                "date_posted": "2024-01-10T12:20:00Z",
                "content_type": "reel",
                "thumbnail_url": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/fitness_creator_alex/reel_003_thumb.jpg",
                "video_url": "https://cdn.supabase.co/storage/v1/object/public/content-videos/fitness_creator_alex/reel_003.mp4",
                "outlier_score": 6.8,
                "profile": {
                    "username": "fitness_creator_alex",
                    "profile_name": "Alex Rodriguez - Fitness Coach",
                    "bio": "Certified Personal Trainer 💪 Helping you reach your fitness goals | Online coaching available",
                    "followers": "125.8K",
                    "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/fitness_creator_alex_profile.jpg",
                    "is_verified": true,
                    "account_type": "Business Page"
                },
                "engagement_rate": 3.48,
                "performance_score": 10890,
                "content_url": "https://www.instagram.com/p/C2Mno456Jkl/"
            }
        ],
        "total_count": 3,
        "has_more": true,
        "username": "fitness_creator_alex",
        "sort_by": "recent"
    }
}
```

**Key Response Features:**

-   **Rich Content Data**: Complete content information including captions, engagement metrics, and performance scores
-   **Profile Integration**: Full profile data included with each content item for consistent display
-   **CDN-Optimized Media**: Supabase Storage CDN URLs for thumbnails and videos for fast loading
-   **Formatted Numbers**: Human-readable number formatting (125.3K, 8.2M) for better UX
-   **Engagement Analytics**: Calculated engagement rates and performance scores for content analysis
-   **Direct Links**: Instagram content URLs for easy navigation to original posts
-   **User-Centric Sorting**: Default "recent" sorting to show users their latest content first

### Response Field Details:

**Content Items (`reels`):**

-   **`id`**: Unique content identifier (MongoDB ObjectId)
-   **`username`**: Content creator's username
-   **`caption`**: Full content caption with hashtags and mentions
-   **`view_count`**: Formatted view count (e.g., "125.3K")
-   **`like_count`**: Formatted like count (e.g., "8.2K")
-   **`comment_count`**: Formatted comment count (e.g., "342")
-   **`share_count`**: Formatted share count (e.g., "156")
-   **`date_posted`**: ISO timestamp of when content was posted
-   **`content_type`**: Type of content ("reel", "post", "story")
-   **`thumbnail_url`**: CDN-optimized thumbnail image URL
-   **`video_url`**: CDN-optimized video file URL (for video content)
-   **`outlier_score`**: Viral potential score (0-10 scale)
-   **`engagement_rate`**: Calculated engagement rate as percentage
-   **`performance_score`**: Weighted performance score based on all metrics
-   **`content_url`**: Direct Instagram link to the original content

**Profile Data (`profile`):**

-   **`username`**: Profile username
-   **`profile_name`**: Display name or business name
-   **`bio`**: Profile biography/description
-   **`followers`**: Formatted follower count
-   **`profile_image_url`**: CDN-optimized profile image URL
-   **`is_verified`**: Instagram verification status
-   **`account_type`**: Account classification (Personal, Business Page, Creator, etc.)

**Metadata:**

-   **`total_count`**: Number of content items in current response
-   **`has_more`**: Boolean indicating if more content is available for pagination
-   **`username`**: Target username for the content query
-   **`sort_by`**: Applied sorting method ("recent", "popular", "views", "likes")

### Sorting Options:

-   **`recent`** (default): Sorts by `date_posted` descending - shows newest content first
-   **`popular`**: Sorts by `outlier_score` descending - shows highest viral potential first
-   **`views`**: Sorts by `view_count` descending - shows most viewed content first
-   **`likes`**: Sorts by `like_count` descending - shows most liked content first

### User Experience Benefits:

-   **Self-Analysis**: Users can analyze their own content performance and engagement patterns
-   **Content Strategy**: Identify which content types and topics perform best
-   **Performance Tracking**: Monitor engagement rates and viral potential over time
-   **Content Library**: Easy browsing of personal content with rich metadata
-   **Optimization Insights**: Compare performance across different sorting methods

### Error: 500 Internal Server Error

Returned if there is a failure to retrieve the content.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_user_content(username: str, limit: int, offset: int, sort_by: str)`
-   **Database Table:** `content`, with a join to `primary_profiles` to ensure consistent profile data is included.
-   **Transformation:** Uses the same `_transform_content_for_frontend` method as other content endpoints to format the data for the client.
