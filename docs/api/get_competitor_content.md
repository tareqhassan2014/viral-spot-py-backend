# GET `/api/content/competitor/{username}` ⚡

Fetches content from a competitor's profile.

## Description

This endpoint is a key part of the competitor analysis feature. It allows the frontend to retrieve and display the content (reels, posts, etc.) from a specific competitor. This is useful for comparing content strategies, identifying trends, and understanding what is performing well for other profiles in the same niche.

The endpoint supports pagination and several sorting options to help users analyze the competitor's content effectively.

## Path Parameters

| Parameter  | Type   | Description                                           |
| :--------- | :----- | :---------------------------------------------------- |
| `username` | string | The username of the competitor to fetch content from. |

## Query Parameters

| Parameter | Type    | Description                                                        | Default   |
| :-------- | :------ | :----------------------------------------------------------------- | :-------- |
| `limit`   | integer | The maximum number of content items to return per page (1-100).    | `24`      |
| `offset`  | integer | The number of content items to skip for pagination.                | `0`       |
| `sort_by` | string  | The sorting order. Options: `popular`, `recent`, `views`, `likes`. | `popular` |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `username` path parameter and optional query parameters for sorting and pagination.
2.  **Build Query**: It constructs a database query on the `content` table, filtering for records that match the `username`.
3.  **Apply Sorting**: The `sort_by` parameter is used to add an `ORDER BY` clause to the query.
4.  **Apply Pagination**: The `limit` and `offset` parameters are used for pagination.
5.  **Execute Query**: The query is executed to fetch the competitor's content.
6.  **Transform and Respond**: The results are transformed into a frontend-friendly format and returned with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# Complete get_competitor_content endpoint implementation (lines 2063-2121)
@app.get("/api/content/competitor/{username}")
async def get_competitor_content(
    username: str,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("popular", regex="^(popular|recent|views|likes)$"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get competitor content for grid display"""
    try:
        # Use the same JOIN as main reels endpoint to provide full profile data
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
        if sort_by == "recent":
            query = query.order('date_posted', desc=True)
        elif sort_by == "views":
            query = query.order('view_count', desc=True)
        elif sort_by == "likes":
            query = query.order('like_count', desc=True)
        else:  # popular (default)
            query = query.order('outlier_score', desc=True)

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
        logger.error(f"Error getting competitor content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get competitor content")
```

**Line-by-Line Explanation:**

1.  **`@app.get("/api/content/competitor/{username}")`**: Defines the FastAPI endpoint with a path parameter for the competitor's username and query parameter validation.

2.  **Parameter Validation**:

    -   `username`: Path parameter (required)
    -   `limit`: Query parameter with range validation (1-100, default 24)
    -   `offset`: Query parameter for pagination (≥0, default 0)
    -   `sort_by`: Query parameter with regex validation for 4 sorting options

3.  **Complex JOIN Query**: Uses the same sophisticated JOIN as the main reels endpoint:

    ```sql
    SELECT *, primary_profiles!profile_id (username, profile_name, bio, followers, profile_image_url, profile_image_path, is_verified, account_type)
    FROM content
    WHERE username = ?
    ```

    This ensures complete profile data is included with each content item.

4.  **`.eq('username', username)`**: Filters content to only include items from the specified competitor's username.

5.  **Dynamic Sorting Logic**: Four different sorting strategies based on the `sort_by` parameter:

    -   **`recent`**: Orders by `date_posted` DESC (newest content first)
    -   **`views`**: Orders by `view_count` DESC (most viewed content first)
    -   **`likes`**: Orders by `like_count` DESC (most liked content first)
    -   **`popular`** (default): Orders by `outlier_score` DESC (viral content first)

6.  **`query.range(offset, offset + limit - 1)`**: Applies pagination using Supabase's range method with inclusive end index.

7.  **Content Transformation**: Uses the same `_transform_content_for_frontend` method as other endpoints:

    -   Ensures consistent data structure across all endpoints
    -   Handles CDN URLs for thumbnails and profile images
    -   Formats numbers (1.2M, 45K format)
    -   Includes all necessary frontend compatibility fields

8.  **Response Structure**: Returns a comprehensive response object with:

    -   `reels`: Array of transformed content items
    -   `total_count`: Number of items returned (for frontend display)
    -   `has_more`: Boolean indicating if more pages are available
    -   `username`: Echo of the requested username
    -   `sort_by`: Echo of the applied sorting method

9.  **Error Handling**: Comprehensive exception handling with detailed logging and HTTP 500 error response.

### Key Implementation Features

**1. Profile Data Integration**: Uses the same JOIN strategy as main endpoints to include complete profile information with each content item.

**2. Flexible Sorting Options**: Supports 4 different sorting methods optimized for competitor analysis:

-   Viral content discovery (`popular`)
-   Timeline analysis (`recent`)
-   Performance analysis (`views`, `likes`)

**3. Consistent Data Transformation**: Uses the same transformation method as other endpoints, ensuring frontend compatibility and consistent data structure.

**4. Efficient Pagination**: Uses Supabase's range method for efficient database pagination.

**5. Comprehensive Response**: Includes metadata like `total_count`, `has_more`, and echoed parameters for frontend state management.

**6. Robust Error Handling**: Detailed error logging and proper HTTP status codes for debugging and monitoring.

### Nest.js (Mongoose)

```typescript
// DTO for validation
import { IsString, IsOptional, IsInt, IsIn, Min, Max } from "class-validator";
import { Transform } from "class-transformer";

export class GetCompetitorContentDto {
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
    @IsIn(["popular", "recent", "views", "likes"])
    sort_by?: string = "popular";
}

// In your content.controller.ts
import { Controller, Get, Param, Query, Logger } from "@nestjs/common";
import { ContentService } from "./content.service";
import { GetCompetitorContentDto } from "./dto/get-competitor-content.dto";

@Controller("api/content")
export class ContentController {
    private readonly logger = new Logger(ContentController.name);

    constructor(private readonly contentService: ContentService) {}

    @Get("/competitor/:username")
    async getCompetitorContent(
        @Param("username") username: string,
        @Query() queryParams: GetCompetitorContentDto
    ) {
        this.logger.log(
            `Getting competitor content for: ${username}, sort_by: ${queryParams.sort_by}`
        );

        const result = await this.contentService.getCompetitorContent(
            username,
            queryParams.limit || 24,
            queryParams.offset || 0,
            queryParams.sort_by || "popular"
        );

        this.logger.log(
            `✅ Returned ${result.reels.length} content items for ${username}`
        );
        return { success: true, data: result };
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

    async getCompetitorContent(
        username: string,
        limit: number,
        offset: number,
        sortBy: string
    ): Promise<any> {
        try {
            // Build MongoDB aggregation pipeline for efficient JOIN and filtering
            const pipeline: any[] = [];

            // 1. Match content by username
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
                case "recent":
                    sortStage = { date_posted: -1 };
                    break;
                case "views":
                    sortStage = { view_count: -1 };
                    break;
                case "likes":
                    sortStage = { like_count: -1 };
                    break;
                default: // "popular"
                    sortStage = { outlier_score: -1 };
            }

            pipeline.push({ $sort: sortStage });

            // 5. Pagination
            pipeline.push({ $skip: offset });
            pipeline.push({ $limit: limit });

            // 6. Execute aggregation
            const results = await this.contentModel.aggregate(pipeline).exec();

            // 7. Transform results for frontend (same transformation as other endpoints)
            const transformedContent = results.map((item) =>
                this.transformContentForFrontend(item)
            );

            return {
                reels: transformedContent,
                total_count: transformedContent.length,
                has_more: results.length === limit, // Simple check for more pages
                username: username,
                sort_by: sortBy,
            };
        } catch (error) {
            this.logger.error(
                `❌ Error getting competitor content for ${username}: ${error.message}`
            );
            throw error;
        }
    }

    // Alternative implementation using populate (simpler but potentially less efficient)
    async getCompetitorContentWithPopulate(
        username: string,
        limit: number,
        offset: number,
        sortBy: string
    ): Promise<any> {
        try {
            // Build sort options
            let sortOptions: any = {};
            switch (sortBy) {
                case "recent":
                    sortOptions = { date_posted: -1 };
                    break;
                case "views":
                    sortOptions = { view_count: -1 };
                    break;
                case "likes":
                    sortOptions = { like_count: -1 };
                    break;
                default: // "popular"
                    sortOptions = { outlier_score: -1 };
            }

            // Query content by username with profile population
            const content = await this.contentModel
                .find({ username })
                .sort(sortOptions)
                .skip(offset)
                .limit(limit)
                .populate({
                    path: "profile_id",
                    select: "username profile_name bio followers profile_image_url profile_image_path is_verified account_type",
                })
                .lean()
                .exec();

            // Transform results
            const transformedContent = content.map((item) => {
                // Merge profile data into the content object for transformation
                const contentWithProfile = {
                    ...item,
                    profile: item.profile_id,
                };
                return this.transformContentForFrontend(contentWithProfile);
            });

            return {
                reels: transformedContent,
                total_count: transformedContent.length,
                has_more: content.length === limit,
                username: username,
                sort_by: sortBy,
            };
        } catch (error) {
            this.logger.error(
                `❌ Error getting competitor content for ${username}: ${error.message}`
            );
            throw error;
        }
    }

    private transformContentForFrontend(item: any): any {
        const profile = item.profile || {};

        // Handle CDN URLs for thumbnails
        let thumbnail_url = null;
        if (item.thumbnail_path) {
            thumbnail_url = `https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/${item.thumbnail_path}`;
        }

        // Handle CDN URLs for profile images
        let profile_image_url = null;
        if (profile.profile_image_path) {
            profile_image_url = `https://cdn.supabase.co/storage/v1/object/public/profile-images/${profile.profile_image_path}`;
        } else if (profile.profile_image_url) {
            profile_image_url = profile.profile_image_url;
        }

        return {
            // Content identifiers
            id: item.content_id,
            reel_id: item.content_id,
            content_id: item.content_id,
            content_type: item.content_type || "reel",
            shortcode: item.shortcode,
            url: item.url,
            description: item.description || "",
            title: item.description || "", // Alias for frontend

            // Media
            thumbnail_url: thumbnail_url,
            thumbnail_local: thumbnail_url, // For compatibility
            thumbnail: thumbnail_url, // For compatibility

            // Metrics
            view_count: item.view_count || 0,
            like_count: item.like_count || 0,
            comment_count: item.comment_count || 0,
            outlier_score: item.outlier_score || 0,
            outlierScore: this.formatOutlierScore(item.outlier_score || 0),

            // Dates
            date_posted: item.date_posted,

            // Profile information
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

            // Content categorization
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
            return (num / 1000000).toFixed(1) + "M";
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + "K";
        }
        return num.toString();
    }

    private formatOutlierScore(score: number): string {
        return score.toFixed(1) + "x";
    }
}
```

### Key Differences in Nest.js Implementation

1. **DTO Validation**: Comprehensive input validation using class-validator decorators with proper type conversion and constraints.

2. **Dual Implementation Approaches**:

    - **Aggregation Pipeline**: More efficient for complex queries, mirrors the Python JOIN approach
    - **Populate Method**: Simpler syntax, good for straightforward use cases

3. **MongoDB Aggregation Pipeline**: Efficient JOIN operation using `$lookup` and `$unwind` stages, exactly mirroring the Python Supabase JOIN.

4. **Flexible Sorting**: Four sorting strategies optimized for competitor analysis:

    - **Popular**: `outlier_score` DESC (viral content discovery)
    - **Recent**: `date_posted` DESC (timeline analysis)
    - **Views**: `view_count` DESC (performance analysis)
    - **Likes**: `like_count` DESC (engagement analysis)

5. **Comprehensive Data Transformation**: Complete field mapping that exactly matches the Python implementation, including:

    - CDN URL handling for images
    - Multiple field aliases for frontend compatibility
    - Number formatting (1.2M, 45K format)
    - Outlier score formatting (1.5x format)

6. **Performance Optimization**: Uses `lean()` queries for better performance and proper indexing on `username` field.

7. **Error Handling**: Comprehensive exception handling with detailed logging for debugging production issues.

## Responses

### Success: 200 OK

Returns a paginated list of the competitor's content with complete profile data and performance metrics.

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
                "description": "🔥 This marketing strategy got me 10M views! Here's how you can do it too... #marketing #viral #entrepreneur",
                "title": "🔥 This marketing strategy got me 10M views! Here's how you can do it too... #marketing #viral #entrepreneur",
                "thumbnail_url": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/reel_3234567890123456789_thumb.jpg",
                "thumbnail_local": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/reel_3234567890123456789_thumb.jpg",
                "thumbnail": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/reel_3234567890123456789_thumb.jpg",
                "view_count": 10500000,
                "like_count": 245700,
                "comment_count": 18400,
                "outlier_score": 3.2456,
                "outlierScore": "3.2x",
                "date_posted": "2024-01-10T14:30:00Z",
                "username": "marketing_guru_alex",
                "profile": "@marketing_guru_alex",
                "profile_name": "Alex - Marketing Expert",
                "bio": "🚀 Helping entrepreneurs scale with proven marketing strategies | 500K+ students taught",
                "profile_followers": 1200000,
                "followers": 1200000,
                "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/marketing_guru_alex_profile.jpg",
                "profileImage": "https://cdn.supabase.co/storage/v1/object/public/profile-images/marketing_guru_alex_profile.jpg",
                "is_verified": true,
                "account_type": "Business Page",
                "primary_category": "Business & Finance",
                "secondary_category": "Digital Marketing",
                "tertiary_category": "Social Media Marketing",
                "keyword_1": "marketing",
                "keyword_2": "viral",
                "keyword_3": "entrepreneur",
                "keyword_4": "strategy",
                "categorization_confidence": 0.95,
                "content_style": "talking head",
                "language": "en",
                "views": "10.5M",
                "likes": "245.7K",
                "comments": "18.4K"
            },
            {
                "id": "3234567890123456790",
                "content_id": "3234567890123456790",
                "content_type": "reel",
                "shortcode": "CxYzAbC5678",
                "url": "https://www.instagram.com/reel/CxYzAbC5678/",
                "description": "3 mistakes that are killing your conversion rates (and how to fix them) 📈 #marketing #conversion #business",
                "view_count": 2800000,
                "like_count": 89300,
                "comment_count": 5600,
                "outlier_score": 2.1234,
                "outlierScore": "2.1x",
                "date_posted": "2024-01-08T10:15:00Z",
                "username": "marketing_guru_alex",
                "profile": "@marketing_guru_alex",
                "profile_name": "Alex - Marketing Expert",
                "primary_category": "Business & Finance",
                "secondary_category": "Digital Marketing",
                "tertiary_category": "Conversion Optimization",
                "keyword_1": "marketing",
                "keyword_2": "conversion",
                "keyword_3": "business",
                "keyword_4": "optimization",
                "content_style": "tutorial",
                "views": "2.8M",
                "likes": "89.3K",
                "comments": "5.6K"
            }
        ],
        "total_count": 2,
        "has_more": true,
        "username": "marketing_guru_alex",
        "sort_by": "popular"
    }
}
```

**Key Response Features:**

-   **Complete Content Data**: All content metadata including views, likes, comments, categories, and keywords
-   **Profile Integration**: Full competitor profile information joined with each content item
-   **Performance Metrics**: Outlier scores and formatted engagement numbers for easy analysis
-   **CDN Optimization**: Supabase Storage CDN URLs for thumbnails and profile images
-   **Competitor Analysis Focus**: Data structured for comparing content strategies and performance
-   **Multiple Aliases**: Frontend compatibility fields like `thumbnail`, `thumbnail_local`, `profileImage`
-   **Rich Metadata**: Categorization, confidence scores, content style, and language information
-   **Pagination Support**: `total_count`, `has_more`, and echoed parameters for frontend state management

### Response Metadata:

-   **`total_count`**: Number of content items returned in this page
-   **`has_more`**: Boolean indicating if more pages are available for pagination
-   **`username`**: Echo of the requested competitor's username
-   **`sort_by`**: Echo of the applied sorting method for frontend state consistency

### Competitor Analysis Use Cases:

1. **Content Strategy Analysis**: Compare content types, styles, and topics
2. **Performance Benchmarking**: Analyze engagement rates and viral content patterns
3. **Trend Identification**: Discover what content performs well in your niche
4. **Timing Analysis**: Study posting patterns and optimal timing strategies
5. **Format Optimization**: Understand which content formats drive the most engagement

### Error: 500 Internal Server Error

Returned if there is a failure to retrieve the content.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_competitor_content(username: str, limit: int, offset: int, sort_by: str)`
-   **Database Table:** `content`, with a join to `primary_profiles` to include full profile data with each content item.
-   **Transformation:** The `_transform_content_for_frontend` method is used to ensure the data is in a consistent format for the client.
