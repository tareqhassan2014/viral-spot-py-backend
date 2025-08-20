# GET `/api/posts`

Retrieves a list of posts, with support for filtering and pagination.

## Description

This endpoint is used for browsing content that is not in video format, such as single images or carousels. It functions very similarly to the `/api/reels` endpoint and reuses the same underlying logic. The main difference is that it is hardcoded to only return content of the `post` type.

## Query Parameters

The filtering and sorting options for this endpoint are a subset of those available for `/api/reels`.

### General

| Parameter | Type    | Description                                                         | Default |
| :-------- | :------ | :------------------------------------------------------------------ | :------ |
| `search`  | string  | A search term to match against post captions and other text fields. | `null`  |
| `limit`   | integer | The maximum number of posts to return per page (1-100).             | `24`    |
| `offset`  | integer | The number of posts to skip for pagination.                         | `0`     |

### Filtering

| Parameter              | Type    | Description                                                    | Default |
| :--------------------- | :------ | :------------------------------------------------------------- | :------ |
| `primary_categories`   | string  | Comma-separated list of primary categories to filter by.       | `null`  |
| `secondary_categories` | string  | Comma-separated list of secondary categories to filter by.     | `null`  |
| `keywords`             | string  | Comma-separated list of keywords to filter by.                 | `null`  |
| `min_outlier_score`    | float   | Minimum outlier score.                                         | `null`  |
| `max_outlier_score`    | float   | Maximum outlier score.                                         | `null`  |
| `min_likes`            | integer | Minimum like count.                                            | `null`  |
| `max_likes`            | integer | Maximum like count.                                            | `null`  |
| `min_comments`         | integer | Minimum comment count.                                         | `null`  |
| `max_comments`         | integer | Maximum comment count.                                         | `null`  |
| `date_range`           | string  | A predefined date range to filter by (e.g., `last_7_days`).    | `null`  |
| `is_verified`          | boolean | Filter for content from verified or non-verified accounts.     | `null`  |
| `excluded_usernames`   | string  | Comma-separated list of usernames to exclude from the results. | `null`  |

### Sorting & Ordering

| Parameter      | Type    | Description                                                                     | Default |
| :------------- | :------ | :------------------------------------------------------------------------------ | :------ |
| `sort_by`      | string  | The sorting order. Options: `popular`, `likes`, `comments`, `recent`, `oldest`. | `null`  |
| `random_order` | boolean | If `true`, returns the results in a random order for the given `session_id`.    | `false` |
| `session_id`   | string  | A unique ID for the user's session, used for consistent random ordering.        | `null`  |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with various optional query parameters.
2.  **Set Content Type Filter**: It internally sets a filter to only include content where `content_type` is `'post'`.
3.  **Call Reels Logic**: Instead of duplicating code, it calls the same underlying function that the `/api/reels` endpoint uses, passing along all the query parameters and the hardcoded `content_type` filter.
4.  **Execute and Respond**: The reels logic then handles the query building, execution, transformation, and response, just as it would for reels, but only returning posts.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# Complete get_posts endpoint implementation (lines 1166-1209)
@app.get("/api/posts")
async def get_posts(
    search: Optional[str] = Query(None),
    primary_categories: Optional[str] = Query(None),
    secondary_categories: Optional[str] = Query(None),
    keywords: Optional[str] = Query(None),
    min_outlier_score: Optional[float] = Query(None),
    max_outlier_score: Optional[float] = Query(None),
    min_likes: Optional[int] = Query(None),
    max_likes: Optional[int] = Query(None),
    min_comments: Optional[int] = Query(None),
    max_comments: Optional[int] = Query(None),
    date_range: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    random_order: Optional[bool] = Query(False),
    session_id: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, regex="^(popular|likes|comments|recent|oldest)$"),
    excluded_usernames: Optional[str] = Query(None),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get posts with filtering and pagination (likes-based)"""
    filters = ReelFilter(
        search=search,
        primary_categories=primary_categories,
        secondary_categories=secondary_categories,
        keywords=keywords,
        min_outlier_score=min_outlier_score,
        max_outlier_score=max_outlier_score,
        min_likes=min_likes,
        max_likes=max_likes,
        min_comments=min_comments,
        max_comments=max_comments,
        date_range=date_range,
        is_verified=is_verified,
        random_order=random_order,
        session_id=session_id,
        sort_by=sort_by,
        excluded_usernames=excluded_usernames,
        content_types='post'  # Key difference: hardcoded to 'post'
    )
    result = await api_instance.get_reels(filters, limit, offset)
    return APIResponse(success=True, data=result)
```

**Line-by-Line Explanation:**

1.  **`@app.get("/api/posts")`**: The endpoint definition that accepts a subset of the `/api/reels` parameters, specifically excluding view-related filters since posts don't have view counts.

2.  **Parameter Differences from `/api/reels`**:

    -   **Missing**: `min_views`, `max_views`, `min_followers`, `max_followers`, `account_types`, `content_types`, `languages`, `content_styles`, `min_account_engagement_rate`, `max_account_engagement_rate`
    -   **Different Regex**: `sort_by` regex is more restrictive: `"^(popular|likes|comments|recent|oldest)$"` (excludes view-based and engagement-based sorting)

3.  **`filters = ReelFilter(...)`**: Creates the same filter object that `/api/reels` uses, but with a crucial difference in the `content_types` parameter.

4.  **`content_types='post'`**: This is the key line that differentiates this endpoint. It hardcodes the content type to `'post'`, ensuring that only posts (images, carousels) are fetched, not reels (videos).

5.  **`result = await api_instance.get_reels(filters, limit, offset)`**: Calls the exact same `get_reels` method from the API class, demonstrating excellent code reuse. The method name is `get_reels` but it actually handles all content types based on the filter.

6.  **Complete Parameter Mapping**: Unlike the simplified version in the original documentation, this shows all 17 parameters that are explicitly passed to the `ReelFilter` constructor.

### Key Implementation Insights

**1. Smart Code Reuse**: Instead of duplicating the complex filtering, sorting, and pagination logic, this endpoint leverages the existing `get_reels` infrastructure by simply changing the content type filter.

**2. Parameter Subset Strategy**: The endpoint accepts only parameters that make sense for posts:

-   **Excluded View Filters**: Since posts don't have view counts, `min_views` and `max_views` are not available
-   **Simplified Sorting**: Removes view-based sorting options like `views`, `followers`, `account_engagement`, `content_engagement`
-   **Focused on Engagement**: Emphasizes like and comment-based metrics which are more relevant for posts

**3. Consistent Data Structure**: Since it uses the same underlying `get_reels` method and `_transform_content_for_frontend` transformation, the response structure is identical to reels, ensuring frontend consistency.

**4. Efficient Database Querying**: The `content_types='post'` filter is processed by the `_build_content_query` method, which adds a `WHERE content_type = 'post'` clause to the database query, making it efficient.

### Nest.js (Mongoose)

```typescript
// DTO for validation (subset of GetReelsDto)
import {
    IsString,
    IsOptional,
    IsInt,
    IsIn,
    IsBoolean,
    Min,
    Max,
} from "class-validator";
import { Transform } from "class-transformer";

export class GetPostsDto {
    @IsOptional()
    @IsString()
    search?: string;

    @IsOptional()
    @IsString()
    primary_categories?: string;

    @IsOptional()
    @IsString()
    secondary_categories?: string;

    @IsOptional()
    @IsString()
    keywords?: string;

    @IsOptional()
    @Transform(({ value }) => parseFloat(value))
    @Min(0)
    min_outlier_score?: number;

    @IsOptional()
    @Transform(({ value }) => parseFloat(value))
    @Min(0)
    max_outlier_score?: number;

    @IsOptional()
    @Transform(({ value }) => parseInt(value))
    @IsInt()
    @Min(0)
    min_likes?: number;

    @IsOptional()
    @Transform(({ value }) => parseInt(value))
    @IsInt()
    @Min(0)
    max_likes?: number;

    @IsOptional()
    @Transform(({ value }) => parseInt(value))
    @IsInt()
    @Min(0)
    min_comments?: number;

    @IsOptional()
    @Transform(({ value }) => parseInt(value))
    @IsInt()
    @Min(0)
    max_comments?: number;

    @IsOptional()
    @IsString()
    date_range?: string;

    @IsOptional()
    @IsBoolean()
    @Transform(({ value }) => value === "true")
    is_verified?: boolean;

    @IsOptional()
    @IsBoolean()
    @Transform(({ value }) => value === "true")
    random_order?: boolean = false;

    @IsOptional()
    @IsString()
    session_id?: string;

    @IsOptional()
    @IsIn(["popular", "likes", "comments", "recent", "oldest"])
    sort_by?: string;

    @IsOptional()
    @IsString()
    excluded_usernames?: string;

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

// In your content.controller.ts
import { Controller, Get, Query, Logger } from "@nestjs/common";
import { ContentService } from "./content.service";
import { GetPostsDto } from "./dto/get-posts.dto";

@Controller("api")
export class ContentController {
    private readonly logger = new Logger(ContentController.name);

    constructor(private readonly contentService: ContentService) {}

    @Get("/posts")
    async getPosts(@Query() queryParams: GetPostsDto) {
        this.logger.log(
            `Getting posts with filters: ${JSON.stringify(queryParams)}`
        );

        const { limit = 24, offset = 0, ...filters } = queryParams;

        // Add the hardcoded content type filter
        const postsFilters = {
            ...filters,
            content_types: "post", // Key difference from reels endpoint
        };

        const result = await this.contentService.getReels(
            postsFilters,
            limit,
            offset
        );

        this.logger.log(`✅ Returned ${result.reels.length} posts`);
        return { success: true, data: result };
    }
}

// In your content.service.ts - Enhanced getReels method to handle posts

@Injectable()
export class ContentService {
    private readonly logger = new Logger(ContentService.name);

    constructor(
        @InjectModel(Content.name) private contentModel: Model<ContentDocument>,
        @InjectModel(PrimaryProfile.name)
        private primaryProfileModel: Model<PrimaryProfileDocument>
    ) {}

    async getReels(filters: any, limit: number, offset: number): Promise<any> {
        const { limit: queryLimit = 24, offset: queryOffset = 0 } = filters;

        // Build MongoDB aggregation pipeline
        const pipeline: any[] = [];

        // 1. Match stage - build query conditions
        const matchConditions: any = {};

        // Content type filter - crucial for posts endpoint
        if (filters.content_types) {
            if (typeof filters.content_types === "string") {
                // Handle single content type (like 'post')
                matchConditions.content_type = filters.content_types;
            } else {
                // Handle multiple content types
                const types = filters.content_types
                    .split(",")
                    .map((t) => t.trim());
                matchConditions.content_type = { $in: types };
            }
        }

        // Search filter
        if (filters.search) {
            matchConditions.$or = [
                { description: { $regex: filters.search, $options: "i" } },
                { username: { $regex: filters.search, $options: "i" } },
            ];
        }

        // Category filters
        if (filters.primary_categories) {
            const categories = filters.primary_categories
                .split(",")
                .map((c) => c.trim());
            matchConditions.primary_category = { $in: categories };
        }

        if (filters.secondary_categories) {
            const categories = filters.secondary_categories
                .split(",")
                .map((c) => c.trim());
            matchConditions.secondary_category = { $in: categories };
        }

        // Keyword search across multiple fields
        if (filters.keywords) {
            const keywords = filters.keywords.split(",").map((k) => k.trim());
            const keywordConditions = [];

            keywords.forEach((keyword) => {
                const regex = { $regex: keyword, $options: "i" };
                keywordConditions.push(
                    { keyword_1: regex },
                    { keyword_2: regex },
                    { keyword_3: regex },
                    { keyword_4: regex },
                    { description: regex }
                );
            });

            if (keywordConditions.length > 0) {
                matchConditions.$or = matchConditions.$or
                    ? [...matchConditions.$or, ...keywordConditions]
                    : keywordConditions;
            }
        }

        // Numeric range filters (posts don't have views, so skip view-related filters)
        if (filters.min_likes !== undefined) {
            matchConditions.like_count = {
                ...matchConditions.like_count,
                $gte: filters.min_likes,
            };
        }
        if (filters.max_likes !== undefined) {
            matchConditions.like_count = {
                ...matchConditions.like_count,
                $lte: filters.max_likes,
            };
        }

        if (filters.min_comments !== undefined) {
            matchConditions.comment_count = {
                ...matchConditions.comment_count,
                $gte: filters.min_comments,
            };
        }
        if (filters.max_comments !== undefined) {
            matchConditions.comment_count = {
                ...matchConditions.comment_count,
                $lte: filters.max_comments,
            };
        }

        // Outlier score filters
        if (filters.min_outlier_score !== undefined) {
            matchConditions.outlier_score = {
                ...matchConditions.outlier_score,
                $gte: filters.min_outlier_score,
            };
        }
        if (filters.max_outlier_score !== undefined) {
            matchConditions.outlier_score = {
                ...matchConditions.outlier_score,
                $lte: filters.max_outlier_score,
            };
        }

        // Exclusion filters
        if (filters.excluded_usernames) {
            const excludedUsers = filters.excluded_usernames
                .split(",")
                .map((u) => u.trim());
            matchConditions.username = { $nin: excludedUsers };
        }

        // Add match stage if we have conditions
        if (Object.keys(matchConditions).length > 0) {
            pipeline.push({ $match: matchConditions });
        }

        // 2. Lookup stage (JOIN with primary_profiles)
        pipeline.push({
            $lookup: {
                from: "primary_profiles",
                localField: "profile_id",
                foreignField: "_id",
                as: "profile",
            },
        });

        // Unwind the profile array
        pipeline.push({
            $unwind: {
                path: "$profile",
                preserveNullAndEmptyArrays: true,
            },
        });

        // 3. Additional filtering based on profile data
        const profileMatchConditions: any = {};

        if (filters.is_verified !== undefined) {
            profileMatchConditions["profile.is_verified"] = filters.is_verified;
        }

        // Add profile-based filtering
        if (Object.keys(profileMatchConditions).length > 0) {
            pipeline.push({ $match: profileMatchConditions });
        }

        // 4. Sorting (posts-specific sorting options)
        let sortStage: any = {};

        switch (filters.sort_by) {
            case "likes":
                sortStage = { like_count: -1 };
                break;
            case "comments":
                sortStage = { comment_count: -1 };
                break;
            case "recent":
                sortStage = { date_posted: -1 };
                break;
            case "oldest":
                sortStage = { date_posted: 1 };
                break;
            default: // 'popular'
                sortStage = { outlier_score: -1, like_count: -1 };
        }

        pipeline.push({ $sort: sortStage });

        // 5. Pagination
        pipeline.push({ $skip: offset });
        pipeline.push({ $limit: limit + 1 }); // Get one extra to check for more pages

        // 6. Execute aggregation
        const results = await this.contentModel.aggregate(pipeline).exec();

        // 7. Handle random ordering if requested
        let processedResults = results;
        if (filters.random_order && filters.session_id) {
            processedResults = await this.applyRandomOrdering(
                results,
                filters.session_id,
                limit
            );
        } else {
            processedResults = results.slice(0, limit);
        }

        // 8. Check for more pages
        const hasMore = results.length > limit;

        // 9. Transform results for frontend (same transformation as reels)
        const transformedPosts = processedResults.map((item) =>
            this.transformContentForFrontend(item)
        );

        return {
            reels: transformedPosts, // Note: still called 'reels' for frontend compatibility
            isLastPage: !hasMore,
        };
    }

    // Same transformation method as reels - ensures consistent data structure
    private transformContentForFrontend(item: any): any {
        // ... same implementation as in get_reels.md
        // This ensures posts and reels have identical response structure
    }
}
```

### Key Differences in Nest.js Implementation

1. **Specialized DTO**: `GetPostsDto` contains only the parameters relevant to posts, excluding view-related filters and advanced engagement metrics.

2. **Content Type Filtering**: The crucial line `content_types: 'post'` is added to the filters before calling the `getReels` method.

3. **Posts-Specific Sorting**: The sorting logic excludes view-based options (`views`, `followers`, `account_engagement`, `content_engagement`) and focuses on like/comment-based metrics.

4. **Code Reuse Strategy**: Leverages the existing `getReels` service method by adding the content type filter, demonstrating excellent DRY principles.

5. **Consistent Response Structure**: Uses the same transformation method as reels, ensuring the frontend can handle both content types identically.

6. **MongoDB Query Optimization**: The `content_type` filter is applied early in the aggregation pipeline for efficient database querying.

## Responses

### Success: 200 OK

Returns a paginated list of post objects with the same structure as reels, ensuring frontend consistency.

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
                "content_type": "post",
                "shortcode": "CxYzAbC1234",
                "url": "https://www.instagram.com/p/CxYzAbC1234/",
                "description": "Beautiful sunset from my latest photoshoot 📸✨ #photography #sunset #portrait",
                "title": "Beautiful sunset from my latest photoshoot 📸✨ #photography #sunset #portrait",
                "thumbnail_url": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/post_3234567890123456789_thumb.jpg",
                "thumbnail_local": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/post_3234567890123456789_thumb.jpg",
                "thumbnail": "https://cdn.supabase.co/storage/v1/object/public/content-thumbnails/post_3234567890123456789_thumb.jpg",
                "view_count": 0,
                "like_count": 15420,
                "comment_count": 234,
                "outlier_score": 1.8765,
                "outlierScore": "1.9x",
                "date_posted": "2024-01-15T16:45:00Z",
                "username": "photographyuser",
                "profile": "@photographyuser",
                "profile_name": "Photography Studio",
                "bio": "Professional photographer capturing life's moments 📷",
                "profile_followers": 89340,
                "followers": 89340,
                "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/photographyuser_profile.jpg",
                "profileImage": "https://cdn.supabase.co/storage/v1/object/public/profile-images/photographyuser_profile.jpg",
                "is_verified": false,
                "account_type": "Business Page",
                "primary_category": "Photography",
                "secondary_category": "Art",
                "tertiary_category": "Lifestyle",
                "keyword_1": "photography",
                "keyword_2": "sunset",
                "keyword_3": "portrait",
                "keyword_4": "photoshoot",
                "categorization_confidence": 0.92,
                "content_style": "image",
                "language": "en",
                "views": "0",
                "likes": "15.4K",
                "comments": "234"
            },
            {
                "id": "3234567890123456790",
                "content_id": "3234567890123456790",
                "content_type": "post",
                "shortcode": "CxYzAbC5678",
                "url": "https://www.instagram.com/p/CxYzAbC5678/",
                "description": "Recipe carousel: 5 easy breakfast ideas 🥞 Swipe for ingredients! #cooking #breakfast #recipes",
                "like_count": 8930,
                "comment_count": 156,
                "outlier_score": 1.2345,
                "outlierScore": "1.2x",
                "date_posted": "2024-01-14T09:30:00Z",
                "username": "cookingwithsarah",
                "profile": "@cookingwithsarah",
                "profile_name": "Sarah's Kitchen",
                "primary_category": "Food",
                "secondary_category": "Cooking",
                "tertiary_category": "Lifestyle",
                "keyword_1": "cooking",
                "keyword_2": "breakfast",
                "keyword_3": "recipes",
                "keyword_4": "healthy",
                "content_style": "carousel",
                "likes": "8.9K",
                "comments": "156"
            }
        ],
        "isLastPage": false
    }
}
```

**Key Response Features:**

-   **Identical Structure to Reels**: Posts use the same response format as reels for frontend consistency
-   **Content Type Distinction**: `content_type: "post"` clearly identifies the content type
-   **No View Counts**: Posts have `view_count: 0` since Instagram posts don't track views
-   **Image-Focused Metadata**: `content_style` shows "image" or "carousel" instead of "video"
-   **Like/Comment Emphasis**: Metrics focus on likes and comments rather than views
-   **Same Transformation**: Uses identical field mapping and CDN URL handling as reels
-   **Frontend Compatibility**: Response key is still "reels" to maintain frontend compatibility

### Key Differences from Reels Response:

1. **`content_type`**: Always "post" instead of "reel"
2. **`view_count`**: Always 0 (posts don't have view metrics)
3. **`content_style`**: Typically "image" or "carousel" instead of "video"
4. **URL Pattern**: Uses `/p/` instead of `/reel/` in Instagram URLs
5. **Engagement Focus**: Emphasizes like/comment ratios over view-based metrics

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_posts(...)`
-   **Reusability:** This endpoint cleverly reuses the `api_instance.get_reels` function by passing a `ReelFilter` with `content_types='post'`. This is a great example of DRY (Don't Repeat Yourself) principles.
