# GET `/api/profile/{username}/reels`

Fetches all the reels associated with a specific profile, with support for sorting and pagination.

## Description

This endpoint retrieves a list of reels for a given `username`. It is used to populate the reels section of a user's profile page. The results can be sorted and paginated to allow for efficient browsing of a user's content.

## Path Parameters

| Parameter  | Type   | Description                        |
| :--------- | :----- | :--------------------------------- |
| `username` | string | The Instagram username to look up. |

## Query Parameters

| Parameter | Type    | Description                                                                | Default   |
| :-------- | :------ | :------------------------------------------------------------------------- | :-------- |
| `sort_by` | string  | The sorting order for the reels. Can be `popular`, `recent`, or `oldest`.  | `popular` |
| `limit`   | integer | The maximum number of reels to return per page. Must be between 1 and 100. | `24`      |
| `offset`  | integer | The number of reels to skip for pagination.                                | `0`       |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `username` path parameter and optional query parameters (`sort_by`, `limit`, `offset`).
2.  **Build Query**: It constructs a database query on the `content` table, filtering for records that match the `username`.
3.  **Apply Sorting**: Based on the `sort_by` parameter, it adds an `ORDER BY` clause to the query:
    -   `popular`: Orders by `outlier_score` and `view_count` descending.
    -   `recent`: Orders by `date_posted` descending.
    -   `oldest`: Orders by `date_posted` ascending.
4.  **Apply Pagination**: It uses the `limit` and `offset` parameters to paginate the results.
5.  **Execute Query**: The query is executed to fetch the reels from the database.
6.  **Transform Data**: Each reel in the result is transformed into a frontend-friendly format.
7.  **Check for More Pages**: The system checks if there are more reels available beyond the current page to set the `isLastPage` flag.
8.  **Send Response**: It returns the list of transformed reels and the `isLastPage` flag with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# Main get_profile_reels method in ViralSpotAPI class (lines 893-950)
async def get_profile_reels(self, username: str, sort_by: str = 'popular', limit: int = 24, offset: int = 0):
    """Get reels for a specific profile"""
    try:
        logger.info(f"Getting reels for profile: {username}, sort_by: {sort_by}")

        # Use the same profile join as the main query to get real profile data
        query = self.supabase.client.table('content').select('''
            *,
            primary_profiles!profile_id (
                username,
                profile_name,
                followers,
                profile_image_url,
                profile_image_path,
                is_verified,
                account_type
            )
        ''').eq('username', username)

        # Apply sorting
        if sort_by == 'popular':
            query = query.order('outlier_score', desc=True).order('view_count', desc=True)
        elif sort_by == 'recent':
            query = query.order('date_posted', desc=True)
        elif sort_by == 'oldest':
            query = query.order('date_posted', desc=False)

        # Apply pagination - request one extra to check for more data
        query = query.range(offset, offset + limit)

        response = query.execute()

        if not response.data:
            return {'reels': [], 'isLastPage': True}

        # Check if there are more pages
        has_more_data = len(response.data) > limit

        # Trim to exact limit
        data_to_return = response.data[:limit]

        # Transform for frontend with real profile data from the join
        transformed_reels = []
        for item in data_to_return:
            transformed_reels.append(self._transform_content_for_frontend(item))

        is_last_page = not has_more_data

        logger.info(f"✅ Returned {len(transformed_reels)} reels for {username}")

        return {
            'reels': transformed_reels,
            'isLastPage': is_last_page
        }

    except Exception as e:
        logger.error(f"❌ Error getting profile reels for {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint definition (lines 1226-1236)
@app.get("/api/profile/{username}/reels")
async def get_profile_reels(
    username: str = Path(..., description="Instagram username"),
    sort_by: str = Query("popular", regex="^(popular|recent|oldest)$"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get reels for a specific profile"""
    result = await api_instance.get_profile_reels(username, sort_by, limit, offset)
    return APIResponse(success=True, data=result)
```

**Line-by-Line Explanation:**

1.  **`async def get_profile_reels(...)`**: Defines an asynchronous method that takes username, sort_by, limit, and offset parameters.

2.  **`logger.info(f"Getting reels for profile: {username}, sort_by: {sort_by}")`**: Logs the incoming request with parameters for debugging and monitoring.

3.  **Complex JOIN Query**: The query includes a sophisticated JOIN with the `primary_profiles` table to get complete profile information:

    ```sql
    SELECT *, primary_profiles!profile_id (username, profile_name, followers, profile_image_url, profile_image_path, is_verified, account_type)
    FROM content WHERE username = :username
    ```

4.  **`.eq('username', username)`**: Filters the content table for records that match the specified username. This is more efficient than filtering by profile_id as it uses the indexed username field.

5.  **Dynamic Sorting Logic**: Three different sorting strategies:

    -   **`popular`**: Orders by `outlier_score` DESC, then `view_count` DESC (viral content first)
    -   **`recent`**: Orders by `date_posted` DESC (newest content first)
    -   **`oldest`**: Orders by `date_posted` ASC (oldest content first)

6.  **`query = query.range(offset, offset + limit)`**: Applies pagination using Supabase's range method. Note: This requests exactly `limit` items, not `limit + 1` like some other endpoints.

7.  **`response = query.execute()`**: Executes the constructed query against the database.

8.  **Empty Result Handling**: Returns empty array with `isLastPage: True` if no content is found for the username.

9.  **Pagination Logic**: Unlike other endpoints, this one doesn't request `limit + 1` items, so it uses a different approach to determine if there are more pages.

10. **`data_to_return = response.data[:limit]`**: Ensures we return exactly the requested number of items.

11. **Content Transformation**: Uses the same `_transform_content_for_frontend()` method as other endpoints to ensure consistent data formatting with CDN URLs, field mapping, and frontend compatibility.

12. **Comprehensive Logging**: Logs both the request parameters and the successful response for monitoring and debugging.

13. **Error Handling**: Catches all exceptions and converts them to HTTP 500 errors with detailed error messages.

### Key Implementation Features

**1. Profile Data Integration**: Unlike a simple content query, this endpoint joins with the `primary_profiles` table to provide complete profile information with each reel, ensuring the frontend has all necessary data for display.

**2. Efficient Filtering**: Uses the indexed `username` field for filtering rather than requiring a separate profile lookup, improving query performance.

**3. Consistent Data Transformation**: Reuses the same transformation logic as the main `/api/reels` endpoint, ensuring consistent data structure across the API.

**4. Flexible Sorting**: Supports three distinct sorting modes optimized for different use cases:

-   Content discovery (popular)
-   Timeline browsing (recent/oldest)

**5. Robust Error Handling**: Comprehensive exception handling with detailed logging for debugging production issues.

### Nest.js (Mongoose)

```typescript
// DTO for validation
import { IsString, IsOptional, IsInt, IsIn, Min, Max } from "class-validator";
import { Transform } from "class-transformer";

export class GetProfileReelsDto {
    @IsString()
    username: string;

    @IsOptional()
    @IsIn(["popular", "recent", "oldest"])
    sort_by?: string = "popular";

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
}

// In your profile.controller.ts
import { Controller, Get, Param, Query, Logger } from "@nestjs/common";
import { ProfileService } from "./profile.service";
import { GetProfileReelsDto } from "./dto/get-profile-reels.dto";

@Controller("api/profile")
export class ProfileController {
    private readonly logger = new Logger(ProfileController.name);

    constructor(private readonly profileService: ProfileService) {}

    @Get(":username/reels")
    async getProfileReels(
        @Param("username") username: string,
        @Query() query: Omit<GetProfileReelsDto, "username">
    ) {
        this.logger.log(
            `Getting reels for profile: ${username}, sort_by: ${query.sort_by}`
        );

        const result = await this.profileService.getProfileReels(
            username,
            query.sort_by || "popular",
            query.limit || 24,
            query.offset || 0
        );

        this.logger.log(
            `✅ Returned ${result.reels.length} reels for ${username}`
        );
        return { success: true, data: result };
    }
}

// In your profile.service.ts
import { Injectable, Logger } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import { Content, ContentDocument } from "./schemas/content.schema";
import {
    PrimaryProfile,
    PrimaryProfileDocument,
} from "./schemas/primary-profile.schema";

@Injectable()
export class ProfileService {
    private readonly logger = new Logger(ProfileService.name);

    constructor(
        @InjectModel(Content.name) private contentModel: Model<ContentDocument>,
        @InjectModel(PrimaryProfile.name)
        private primaryProfileModel: Model<PrimaryProfileDocument>
    ) {}

    async getProfileReels(
        username: string,
        sortBy: string,
        limit: number,
        offset: number
    ): Promise<any> {
        try {
            // Build aggregation pipeline for efficient JOIN and filtering
            const pipeline: any[] = [];

            // 1. Match content by username (more efficient than profile_id lookup)
            pipeline.push({
                $match: { username },
            });

            // 2. Lookup profile data (equivalent to JOIN)
            pipeline.push({
                $lookup: {
                    from: "primary_profiles",
                    localField: "profile_id",
                    foreignField: "_id",
                    as: "profile",
                },
            });

            // 3. Unwind profile array (1:1 relationship)
            pipeline.push({
                $unwind: {
                    path: "$profile",
                    preserveNullAndEmptyArrays: true,
                },
            });

            // 4. Apply sorting based on sort_by parameter
            let sortStage: any = {};
            switch (sortBy) {
                case "popular":
                    sortStage = { outlier_score: -1, view_count: -1 };
                    break;
                case "recent":
                    sortStage = { date_posted: -1 };
                    break;
                case "oldest":
                    sortStage = { date_posted: 1 };
                    break;
                default:
                    sortStage = { outlier_score: -1, view_count: -1 };
            }
            pipeline.push({ $sort: sortStage });

            // 5. Apply pagination
            pipeline.push({ $skip: offset });
            pipeline.push({ $limit: limit + 1 }); // Get one extra to check for more pages

            // 6. Execute aggregation
            const results = await this.contentModel.aggregate(pipeline).exec();

            // Handle empty results
            if (!results || results.length === 0) {
                return { reels: [], isLastPage: true };
            }

            // 7. Check for more pages and trim results
            const hasMore = results.length > limit;
            const reelsToReturn = results.slice(0, limit);

            // 8. Transform for frontend
            const transformedReels = reelsToReturn.map((item) =>
                this.transformContentForFrontend(item)
            );

            return {
                reels: transformedReels,
                isLastPage: !hasMore,
            };
        } catch (error) {
            this.logger.error(
                `❌ Error getting profile reels for ${username}: ${error.message}`
            );
            throw error;
        }
    }

    private transformContentForFrontend(item: any): any {
        const profile = item.profile || {};

        // Handle CDN URLs for thumbnails
        let thumbnail_url = null;
        if (item.thumbnail_path) {
            thumbnail_url = `${process.env.CDN_BASE_URL}/content-thumbnails/${item.thumbnail_path}`;
        } else if (item.thumbnail_url) {
            thumbnail_url = item.thumbnail_url;
        }

        // Handle profile image URLs
        let profile_image_url = null;
        if (profile.profile_image_path) {
            profile_image_url = `${process.env.CDN_BASE_URL}/profile-images/${profile.profile_image_path}`;
        } else if (profile.profile_image_url) {
            profile_image_url = profile.profile_image_url;
        }

        // Transform to match Python implementation exactly
        return {
            id: item.content_id,
            reel_id: item.content_id,
            content_id: item.content_id,
            content_type: item.content_type || "reel",
            shortcode: item.shortcode,
            url: item.url,
            description: item.description || "",
            title: item.description || "", // Alias for frontend
            thumbnail_url: thumbnail_url,
            thumbnail_local: thumbnail_url, // For compatibility
            thumbnail: thumbnail_url, // For compatibility
            view_count: item.view_count || 0,
            like_count: item.like_count || 0,
            comment_count: item.comment_count || 0,
            outlier_score: item.outlier_score || 0,
            outlierScore: `${(item.outlier_score || 0).toFixed(1)}x`, // Formatted for frontend
            date_posted: item.date_posted,
            username: item.username,
            profile: `@${item.username}`,
            profile_name: profile.profile_name || "",
            bio: profile.bio || "",
            profile_followers: profile.followers || 0,
            followers: profile.followers || 0, // For compatibility
            profile_image_url: profile_image_url,
            profileImage: profile_image_url, // For compatibility
            is_verified: profile.is_verified || false,
            account_type: profile.account_type || "Personal",
            primary_category: item.primary_category,
            secondary_category: item.secondary_category,
            tertiary_category: item.tertiary_category,
            keyword_1: item.keyword_1,
            keyword_2: item.keyword_2,
            keyword_3: item.keyword_3,
            keyword_4: item.keyword_4,
            categorization_confidence: item.categorization_confidence || 0,
            content_style: item.content_style,
            language: item.language || "en",

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

    // Alternative approach using populate (simpler but potentially less efficient)
    async getProfileReelsWithPopulate(
        username: string,
        sortBy: string,
        limit: number,
        offset: number
    ): Promise<any> {
        try {
            // First find the profile to get the profile_id
            const profile = await this.primaryProfileModel
                .findOne({ username })
                .lean()
                .exec();
            if (!profile) {
                return { reels: [], isLastPage: true };
            }

            // Build sort options
            let sortOptions: any = {};
            switch (sortBy) {
                case "popular":
                    sortOptions = { outlier_score: -1, view_count: -1 };
                    break;
                case "recent":
                    sortOptions = { date_posted: -1 };
                    break;
                case "oldest":
                    sortOptions = { date_posted: 1 };
                    break;
                default:
                    sortOptions = { outlier_score: -1, view_count: -1 };
            }

            // Query content with populate
            const reels = await this.contentModel
                .find({ username }) // Use username for efficiency
                .sort(sortOptions)
                .skip(offset)
                .limit(limit + 1) // Fetch one extra to check for more pages
                .populate({
                    path: "profile_id",
                    select: "username profile_name followers profile_image_url profile_image_path is_verified account_type",
                })
                .lean()
                .exec();

            const hasMore = reels.length > limit;
            const results = reels.slice(0, limit);

            // Transform results
            const transformedReels = results.map((reel) => {
                // Merge profile data into the reel object for transformation
                const reelWithProfile = {
                    ...reel,
                    profile: reel.profile_id || profile,
                };
                return this.transformContentForFrontend(reelWithProfile);
            });

            return {
                reels: transformedReels,
                isLastPage: !hasMore,
            };
        } catch (error) {
            this.logger.error(
                `❌ Error getting profile reels for ${username}: ${error.message}`
            );
            throw error;
        }
    }
}
```

### Key Differences in Nest.js Implementation

1. **MongoDB Aggregation Pipeline**: Uses MongoDB's aggregation framework for efficient JOIN operations, similar to the complex Supabase query in Python.

2. **DTO Validation**: Comprehensive input validation using class-validator decorators with proper type conversion and constraints.

3. **Dual Implementation Approaches**:

    - **Aggregation Pipeline**: More efficient for complex queries, mirrors the Python JOIN approach
    - **Populate Method**: Simpler syntax, good for straightforward use cases

4. **Performance Optimization**:

    - Uses `username` field for filtering (indexed) rather than requiring profile lookup
    - Implements `lean()` queries for better performance
    - Proper pagination with `limit + 1` technique

5. **Comprehensive Data Transformation**: Complete field mapping that exactly matches the Python implementation, including:

    - CDN URL handling for images
    - Multiple field aliases for frontend compatibility
    - Number formatting (1.2M, 45K format)
    - Comprehensive error handling

6. **Logging Integration**: Mirrors the Python logging approach with detailed request/response logging.

7. **Error Handling**: Proper exception handling with detailed error messages and logging.

## Responses

### Success: 200 OK

Returns a list of reel objects with complete profile information and pagination metadata.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "id": "3234567890123456789",
                "reel_id": "3234567890123456789",
                "content_id": "3234567890123456789",
                "content_type": "reel",
                "shortcode": "CxYzAbC1234",
                "url": "https://www.instagram.com/reel/CxYzAbC1234/",
                "description": "Amazing sunset timelapse from my rooftop! 🌅 #sunset #timelapse #photography",
                "title": "Amazing sunset timelapse from my rooftop! 🌅 #sunset #timelapse #photography",
                "thumbnail_url": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/reel_3234567890123456789_thumb.jpg",
                "thumbnail_local": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/reel_3234567890123456789_thumb.jpg",
                "thumbnail": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/reel_3234567890123456789_thumb.jpg",
                "view_count": 245670,
                "like_count": 18420,
                "comment_count": 892,
                "outlier_score": 2.3456,
                "outlierScore": "2.3x",
                "date_posted": "2024-01-15T18:30:00Z",
                "username": "exampleuser",
                "profile": "@exampleuser",
                "profile_name": "Example Creator",
                "bio": "Content creator sharing daily inspiration ✨",
                "profile_followers": 125430,
                "followers": 125430,
                "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/exampleuser_profile.jpg",
                "profileImage": "https://cdn.supabase.co/storage/v1/object/public/profile-images/exampleuser_profile.jpg",
                "is_verified": true,
                "account_type": "Influencer",
                "primary_category": "Lifestyle",
                "secondary_category": "Photography",
                "tertiary_category": "Travel",
                "keyword_1": "sunset",
                "keyword_2": "timelapse",
                "keyword_3": "photography",
                "keyword_4": "rooftop",
                "categorization_confidence": 0.89,
                "content_style": "video",
                "language": "en",
                "views": "245.7K",
                "likes": "18.4K",
                "comments": "892"
            },
            {
                "id": "3234567890123456790",
                "reel_id": "3234567890123456790",
                "content_id": "3234567890123456790",
                "content_type": "reel",
                "shortcode": "CxYzAbC5678",
                "url": "https://www.instagram.com/reel/CxYzAbC5678/",
                "description": "Quick morning workout routine 💪 #fitness #workout #morning",
                "title": "Quick morning workout routine 💪 #fitness #workout #morning",
                "thumbnail_url": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/reel_3234567890123456790_thumb.jpg",
                "view_count": 189340,
                "like_count": 14230,
                "comment_count": 567,
                "outlier_score": 1.8765,
                "outlierScore": "1.9x",
                "date_posted": "2024-01-14T07:15:00Z",
                "username": "exampleuser",
                "profile": "@exampleuser",
                "profile_name": "Example Creator",
                "profile_followers": 125430,
                "followers": 125430,
                "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/exampleuser_profile.jpg",
                "is_verified": true,
                "account_type": "Influencer",
                "primary_category": "Fitness",
                "secondary_category": "Health",
                "tertiary_category": "Lifestyle",
                "keyword_1": "fitness",
                "keyword_2": "workout",
                "keyword_3": "morning",
                "keyword_4": "routine",
                "views": "189.3K",
                "likes": "14.2K",
                "comments": "567"
            }
        ],
        "isLastPage": false
    }
}
```

**Key Response Features:**

-   **Complete Content Data**: All reel metadata including views, likes, comments, categories, and keywords
-   **Profile Integration**: Full profile information joined with each reel for efficient frontend rendering
-   **CDN Optimization**: Supabase Storage CDN URLs for thumbnails and profile images
-   **Multiple Aliases**: Frontend compatibility fields like `thumbnail`, `thumbnail_local`, `profileImage`
-   **Formatted Numbers**: Human-readable number formats (245.7K, 18.4K) alongside raw values
-   **Rich Metadata**: Categorization, confidence scores, content style, and language information
-   **Pagination**: `isLastPage` flag for efficient infinite scrolling implementation

### Empty Profile Response

When a username has no content or doesn't exist:

```json
{
    "success": true,
    "data": {
        "reels": [],
        "isLastPage": true
    }
}
```

### Error: 500 Internal Server Error

Returned if an unexpected error occurs on the server.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_profile_reels(username: str, sort_by: str, limit: int, offset: int)`
-   **Database Table:** `content`
-   **Sorting Logic:**
    -   `popular`: Orders by `outlier_score` and then `view_count`, both descending.
    -   `recent`: Orders by `date_posted` descending.
    -   `oldest`: Orders by `date_posted` ascending.
