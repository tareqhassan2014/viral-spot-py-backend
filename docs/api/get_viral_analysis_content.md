# GET `/api/viral-analysis/{queue_id}/content` ⚡

Retrieves the content that was analyzed as part of a job.

## Description

This endpoint is designed to be used in conjunction with the analysis results from `GET /api/viral-analysis/{queue_id}/results`. It fetches the source content (reels and posts) that was used in a specific analysis job.

This is essential for the frontend to be able to display the original content alongside the AI-generated insights, giving users a complete picture and context for the analysis. The endpoint allows for filtering to retrieve content from just the primary user, just the competitors, or all content included in the analysis.

## Path Parameters

| Parameter  | Type   | Description                 |
| :--------- | :----- | :-------------------------- |
| `queue_id` | string | The ID of the analysis job. |

## Query Parameters

| Parameter      | Type    | Description                                                                | Default |
| :------------- | :------ | :------------------------------------------------------------------------- | :------ |
| `content_type` | string  | The type of content to retrieve. Can be `all`, `primary`, or `competitor`. | `all`   |
| `limit`        | integer | The maximum number of content items to return (1-200).                     | `100`   |
| `offset`       | integer | The number of content items to skip for pagination.                        | `0`     |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `queue_id` path parameter and optional query parameters (`content_type`, `limit`, `offset`).
2.  **Find Analysis Reels**: It first queries the `viral_analysis_reels` table to get the list of `content_id`s that were part of the analysis for the given `queue_id`.
3.  **Build Content Query**: It then constructs a query on the `content` table, filtering for records where the `content_id` is in the list retrieved in the previous step.
4.  **Apply Content Type Filter**: If the `content_type` parameter is `primary` or `competitor`, it adds a `WHERE` clause to filter the results based on the `username` of the content's author.
5.  **Apply Pagination**: The `limit` and `offset` parameters are used for pagination.
6.  **Execute and Respond**: The query is executed, the results are transformed, and the paginated list of content is returned with a `200 OK` status.

## Database Schema Details

### Primary Tables Used

This endpoint retrieves analyzed content through a two-step database query process.

#### 1. `viral_analysis_reels` Table

Tracks exactly which reels were used in the specific analysis. **[View Complete Documentation](../database/viral_analysis_reels.md)**

```sql
-- Step 1: Get content IDs that were part of the analysis
SELECT content_id, reel_type, username, rank_in_selection,
       view_count_at_analysis, like_count_at_analysis, comment_count_at_analysis,
       transcript_completed, hook_text, power_words, analysis_metadata
FROM viral_analysis_reels
WHERE analysis_id = ?
ORDER BY reel_type, rank_in_selection;
```

-   **Purpose**: Identifies which specific reels contributed to the analysis insights
-   **Key Fields**: `content_id`, `reel_type`, `username`, performance metrics at analysis time
-   **Usage**: Source of truth for which content was actually analyzed

#### 2. `content` Table

Full reel/post content data with profile relationships.

```sql
-- Step 2: Get full content data for analyzed reels
SELECT c.*,
       p.username, p.profile_name, p.followers, p.profile_image_url,
       p.profile_image_path, p.is_verified, p.account_type
FROM content c
JOIN primary_profiles p ON c.profile_id = p.id
WHERE c.content_id IN (analyzed_content_ids)
AND (? = 'all' OR
     (? = 'primary' AND c.username = primary_username) OR
     (? = 'competitor' AND c.username != primary_username))
ORDER BY c.view_count DESC
LIMIT ? OFFSET ?;
```

-   **Purpose**: Complete content data with profile context for analyzed reels
-   **Filtering**: Supports primary-only, competitor-only, or all content filtering
-   **Pagination**: Implements limit/offset pagination for large result sets

### Query Flow Strategy

1. **Analysis Verification**: Verify the analysis exists and get primary username
2. **Content Discovery**: Query `viral_analysis_reels` to find analyzed content IDs
3. **Content Enrichment**: Query `content` table with profile JOINs for full data
4. **Type Filtering**: Apply content_type filter (all/primary/competitor)
5. **Pagination**: Apply limit/offset for manageable response sizes

## Detailed Implementation Guide

### Python (FastAPI)

```python
# Complete get_viral_analysis_content endpoint implementation (lines 1946-2061)
@app.get("/api/viral-analysis/{queue_id}/content")
async def get_viral_analysis_content(
    queue_id: str,
    content_type: str = Query("all", regex="^(all|primary|competitor)$"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get content/reels from viral analysis for grid display"""
    try:
        # Get the queue and analysis info
        queue_result = api_instance.supabase.client.table('viral_ideas_queue').select(
            'primary_username'
        ).eq('id', queue_id).execute()

        if not queue_result.data:
            raise HTTPException(status_code=404, detail="Queue not found")

        primary_username = queue_result.data[0]['primary_username']

        # Get the latest analysis for this queue
        analysis_result = api_instance.supabase.client.table('viral_analysis_results').select(
            'id'
        ).eq('queue_id', queue_id).order('analysis_run', desc=True).limit(1).execute()

        if not analysis_result.data:
            raise HTTPException(status_code=404, detail="Analysis not found")

        analysis_id = analysis_result.data[0]['id']

        if content_type == "primary":
            # Get all reels from the primary user
            query = api_instance.supabase.client.table('content').select(
                'content_id, shortcode, url, description, view_count, like_count, comment_count, '
                'date_posted, username, outlier_score, transcript, transcript_language, transcript_available'
            ).eq('username', primary_username)

            # Order by view count descending to show best performing first
            result = query.order('view_count', desc=True).range(offset, offset + limit - 1).execute()

            # Add reel_type for consistency
            reels = []
            for reel in result.data or []:
                reel['reel_type'] = 'primary'
                reels.append(reel)

        elif content_type == "competitor":
            # Get all competitor usernames for this queue
            competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').select(
                'competitor_username'
            ).eq('queue_id', queue_id).eq('is_active', True).execute()

            competitor_usernames = [comp['competitor_username'] for comp in competitors_result.data or []]

            if not competitor_usernames:
                reels = []
            else:
                query = api_instance.supabase.client.table('content').select(
                    'content_id, shortcode, url, description, view_count, like_count, comment_count, '
                    'date_posted, username, outlier_score, transcript, transcript_language, transcript_available'
                ).in_('username', competitor_usernames)

                result = query.order('outlier_score', desc=True).range(offset, offset + limit - 1).execute()

                # Add reel_type for consistency
                reels = []
                for reel in result.data or []:
                    reel['reel_type'] = 'competitor'
                    reels.append(reel)

        else:  # "all"
            # Get both primary and competitor reels
            competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').select(
                'competitor_username'
            ).eq('queue_id', queue_id).eq('is_active', True).execute()

            competitor_usernames = [comp['competitor_username'] for comp in competitors_result.data or []]
            all_usernames = [primary_username] + competitor_usernames

            query = api_instance.supabase.client.table('content').select(
                'content_id, shortcode, url, description, view_count, like_count, comment_count, '
                'date_posted, username, outlier_score, transcript, transcript_language, transcript_available'
            ).in_('username', all_usernames)

            result = query.order('outlier_score', desc=True).range(offset, offset + limit - 1).execute()

            # Add reel_type based on username
            reels = []
            for reel in result.data or []:
                reel['reel_type'] = 'primary' if reel['username'] == primary_username else 'competitor'
                reels.append(reel)

        return APIResponse(
            success=True,
            data={
                'reels': reels,
                'total_count': len(reels),
                'has_more': len(reels) == limit,
                'primary_username': primary_username
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting viral analysis content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis content")
```

**Line-by-Line Explanation:**

1.  **Queue Information Retrieval**:

    ```python
    queue_result = api_instance.supabase.client.table('viral_ideas_queue').select(
        'primary_username'
    ).eq('id', queue_id).execute()
    ```

    Fetches the primary username associated with the queue to distinguish between primary and competitor content.

2.  **Queue Validation**:

    ```python
    if not queue_result.data:
        raise HTTPException(status_code=404, detail="Queue not found")
    ```

    Ensures the queue exists before proceeding with content retrieval.

3.  **Latest Analysis Lookup**:

    ```python
    analysis_result = api_instance.supabase.client.table('viral_analysis_results').select(
        'id'
    ).eq('queue_id', queue_id).order('analysis_run', desc=True).limit(1).execute()
    ```

    Gets the most recent analysis for the queue, supporting multiple analysis runs per queue.

4.  **Primary Content Strategy**:

    ```python
    if content_type == "primary":
        query = api_instance.supabase.client.table('content').select(
            'content_id, shortcode, url, description, view_count, like_count, comment_count, '
            'date_posted, username, outlier_score, transcript, transcript_language, transcript_available'
        ).eq('username', primary_username)
        result = query.order('view_count', desc=True).range(offset, offset + limit - 1).execute()
    ```

    Fetches comprehensive content fields for the primary user, ordered by view count for performance insights.

5.  **Competitor Content Strategy**:

    ```python
    elif content_type == "competitor":
        competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').select(
            'competitor_username'
        ).eq('queue_id', queue_id).eq('is_active', True).execute()

        competitor_usernames = [comp['competitor_username'] for comp in competitors_result.data or []]
        query = api_instance.supabase.client.table('content').select(...).in_('username', competitor_usernames)
        result = query.order('outlier_score', desc=True).range(offset, offset + limit - 1).execute()
    ```

    Dynamically fetches active competitors for the queue and retrieves their content, ordered by viral potential.

6.  **Combined Content Strategy**:

    ```python
    else:  # "all"
        all_usernames = [primary_username] + competitor_usernames
        query = api_instance.supabase.client.table('content').select(...).in_('username', all_usernames)
        result = query.order('outlier_score', desc=True).range(offset, offset + limit - 1).execute()
    ```

    Combines primary and competitor content, ordered by outlier score for comprehensive viral analysis.

7.  **Content Type Classification**:

    ```python
    for reel in result.data or []:
        reel['reel_type'] = 'primary' if reel['username'] == primary_username else 'competitor'
        reels.append(reel)
    ```

    Dynamically classifies content as primary or competitor based on username comparison.

8.  **Rich Response Structure**:
    ```python
    return APIResponse(success=True, data={
        'reels': reels,
        'total_count': len(reels),
        'has_more': len(reels) == limit,
        'primary_username': primary_username
    })
    ```
    Returns comprehensive metadata including pagination info and primary username context.

### Key Implementation Features

**1. Dynamic Content Filtering**: Supports three distinct content filtering strategies (all, primary, competitor) with optimized queries for each.

**2. Comprehensive Field Selection**: Fetches 11 essential content fields including engagement metrics, transcripts, and viral scores.

**3. Smart Sorting Strategies**:

-   **Primary Content**: Sorted by `view_count` descending (performance focus)
-   **Competitor Content**: Sorted by `outlier_score` descending (viral potential focus)
-   **All Content**: Sorted by `outlier_score` descending (comprehensive viral analysis)

**4. Active Competitor Filtering**: Only includes active competitors (`is_active = True`) for accurate analysis scope.

**5. Multiple Analysis Support**: Handles multiple analysis runs per queue by selecting the latest analysis.

**6. Content Type Classification**: Automatically classifies content as primary or competitor for frontend display.

**7. Comprehensive Error Handling**: Proper HTTP status codes and detailed error messages for debugging.

### Nest.js (Mongoose)

```typescript
// DTO for validation
import { IsOptional, IsString, IsInt, Min, Max } from "class-validator";
import { Transform } from "class-transformer";

export class GetViralAnalysisContentDto {
    @IsOptional()
    @IsString()
    @Transform(({ value }) => value?.toLowerCase())
    content_type?: string = "all";

    @IsOptional()
    @Transform(({ value }) => parseInt(value))
    @IsInt()
    @Min(1)
    @Max(200)
    limit?: number = 100;

    @IsOptional()
    @Transform(({ value }) => parseInt(value))
    @IsInt()
    @Min(0)
    offset?: number = 0;
}

// In your viral-ideas.controller.ts
import {
    Controller,
    Get,
    Param,
    Query,
    Logger,
    NotFoundException,
} from "@nestjs/common";
import { ViralIdeasService } from "./viral-ideas.service";
import { GetViralAnalysisContentDto } from "./dto/get-viral-analysis-content.dto";

@Controller("api/viral-analysis")
export class ViralIdeasController {
    private readonly logger = new Logger(ViralIdeasController.name);

    constructor(private readonly viralIdeasService: ViralIdeasService) {}

    @Get(":queueId/content")
    async getAnalysisContent(
        @Param("queueId") queueId: string,
        @Query() queryParams: GetViralAnalysisContentDto
    ) {
        this.logger.log(`Getting analysis content for queue: ${queueId}`);

        // Validate content_type parameter
        const validContentTypes = ["all", "primary", "competitor"];
        const contentType = validContentTypes.includes(
            queryParams.content_type || "all"
        )
            ? queryParams.content_type || "all"
            : "all";

        const result = await this.viralIdeasService.getAnalysisContent(
            queueId,
            contentType,
            queryParams.limit || 100,
            queryParams.offset || 0
        );

        this.logger.log(
            `✅ Found ${result.reels.length} content items for analysis ${queueId}`
        );
        return {
            success: true,
            data: result,
        };
    }
}

// In your viral-ideas.service.ts
import { Injectable, Logger, NotFoundException } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import {
    ViralIdeasQueue,
    ViralIdeasQueueDocument,
} from "./schemas/viral-ideas-queue.schema";
import {
    ViralIdeasCompetitor,
    ViralIdeasCompetitorDocument,
} from "./schemas/viral-ideas-competitor.schema";
import {
    ViralAnalysisResult,
    ViralAnalysisResultDocument,
} from "./schemas/viral-analysis-result.schema";
import { Content, ContentDocument } from "./schemas/content.schema";

@Injectable()
export class ViralIdeasService {
    private readonly logger = new Logger(ViralIdeasService.name);

    constructor(
        @InjectModel(ViralIdeasQueue.name)
        private viralIdeasQueueModel: Model<ViralIdeasQueueDocument>,
        @InjectModel(ViralIdeasCompetitor.name)
        private viralIdeasCompetitorModel: Model<ViralIdeasCompetitorDocument>,
        @InjectModel(ViralAnalysisResult.name)
        private viralAnalysisResultModel: Model<ViralAnalysisResultDocument>,
        @InjectModel(Content.name) private contentModel: Model<ContentDocument>
    ) {}

    async getAnalysisContent(
        queueId: string,
        contentType: string,
        limit: number,
        offset: number
    ): Promise<any> {
        try {
            // 1. Get queue information and validate existence
            const queue = await this.viralIdeasQueueModel
                .findById(queueId)
                .select("primary_username")
                .lean()
                .exec();

            if (!queue) {
                throw new NotFoundException("Queue not found");
            }

            const primaryUsername = queue.primary_username;

            // 2. Get the latest analysis for this queue
            const analysis = await this.viralAnalysisResultModel
                .findOne({ queue_id: queueId })
                .sort({ analysis_run: -1 })
                .select("_id")
                .lean()
                .exec();

            if (!analysis) {
                throw new NotFoundException("Analysis not found");
            }

            let reels = [];

            if (contentType === "primary") {
                // Get primary user content ordered by view count
                reels = await this.getPrimaryContent(
                    primaryUsername,
                    limit,
                    offset
                );
            } else if (contentType === "competitor") {
                // Get competitor content ordered by outlier score
                reels = await this.getCompetitorContent(queueId, limit, offset);
            } else {
                // Get all content (primary + competitors) ordered by outlier score
                reels = await this.getAllContent(
                    queueId,
                    primaryUsername,
                    limit,
                    offset
                );
            }

            return {
                reels: reels,
                total_count: reels.length,
                has_more: reels.length === limit,
                primary_username: primaryUsername,
            };
        } catch (error) {
            if (error instanceof NotFoundException) {
                throw error;
            }
            this.logger.error(
                `❌ Error getting analysis content: ${error.message}`
            );
            throw error;
        }
    }

    private async getPrimaryContent(
        primaryUsername: string,
        limit: number,
        offset: number
    ): Promise<any[]> {
        const content = await this.contentModel
            .find({ username: primaryUsername })
            .select(
                "content_id shortcode url description view_count like_count comment_count " +
                    "date_posted username outlier_score transcript transcript_language transcript_available"
            )
            .sort({ view_count: -1 })
            .skip(offset)
            .limit(limit)
            .lean()
            .exec();

        return content.map((item) => ({
            ...item,
            reel_type: "primary",
        }));
    }

    private async getCompetitorContent(
        queueId: string,
        limit: number,
        offset: number
    ): Promise<any[]> {
        // Get active competitors for this queue
        const competitors = await this.viralIdeasCompetitorModel
            .find({ queue_id: queueId, is_active: true })
            .select("competitor_username")
            .lean()
            .exec();

        const competitorUsernames = competitors.map(
            (comp) => comp.competitor_username
        );

        if (competitorUsernames.length === 0) {
            return [];
        }

        const content = await this.contentModel
            .find({ username: { $in: competitorUsernames } })
            .select(
                "content_id shortcode url description view_count like_count comment_count " +
                    "date_posted username outlier_score transcript transcript_language transcript_available"
            )
            .sort({ outlier_score: -1 })
            .skip(offset)
            .limit(limit)
            .lean()
            .exec();

        return content.map((item) => ({
            ...item,
            reel_type: "competitor",
        }));
    }

    private async getAllContent(
        queueId: string,
        primaryUsername: string,
        limit: number,
        offset: number
    ): Promise<any[]> {
        // Get active competitors for this queue
        const competitors = await this.viralIdeasCompetitorModel
            .find({ queue_id: queueId, is_active: true })
            .select("competitor_username")
            .lean()
            .exec();

        const competitorUsernames = competitors.map(
            (comp) => comp.competitor_username
        );
        const allUsernames = [primaryUsername, ...competitorUsernames];

        const content = await this.contentModel
            .find({ username: { $in: allUsernames } })
            .select(
                "content_id shortcode url description view_count like_count comment_count " +
                    "date_posted username outlier_score transcript transcript_language transcript_available"
            )
            .sort({ outlier_score: -1 })
            .skip(offset)
            .limit(limit)
            .lean()
            .exec();

        return content.map((item) => ({
            ...item,
            reel_type:
                item.username === primaryUsername ? "primary" : "competitor",
        }));
    }

    // Alternative implementation using aggregation for better performance
    async getAnalysisContentOptimized(
        queueId: string,
        contentType: string,
        limit: number,
        offset: number
    ): Promise<any> {
        try {
            const pipeline = [
                // Match the queue
                { $match: { _id: queueId } },

                // Lookup competitors
                {
                    $lookup: {
                        from: "viral_ideas_competitors",
                        localField: "_id",
                        foreignField: "queue_id",
                        as: "competitors",
                        pipeline: [
                            { $match: { is_active: true } },
                            { $project: { competitor_username: 1 } },
                        ],
                    },
                },

                // Project usernames based on content_type
                {
                    $project: {
                        primary_username: 1,
                        target_usernames: {
                            $switch: {
                                branches: [
                                    {
                                        case: { $eq: [contentType, "primary"] },
                                        then: ["$primary_username"],
                                    },
                                    {
                                        case: {
                                            $eq: [contentType, "competitor"],
                                        },
                                        then: "$competitors.competitor_username",
                                    },
                                ],
                                default: {
                                    $concatArrays: [
                                        ["$primary_username"],
                                        "$competitors.competitor_username",
                                    ],
                                },
                            },
                        },
                    },
                },

                // Lookup content
                {
                    $lookup: {
                        from: "content",
                        localField: "target_usernames",
                        foreignField: "username",
                        as: "content",
                        pipeline: [
                            {
                                $project: {
                                    content_id: 1,
                                    shortcode: 1,
                                    url: 1,
                                    description: 1,
                                    view_count: 1,
                                    like_count: 1,
                                    comment_count: 1,
                                    date_posted: 1,
                                    username: 1,
                                    outlier_score: 1,
                                    transcript: 1,
                                    transcript_language: 1,
                                    transcript_available: 1,
                                },
                            },
                            {
                                $sort:
                                    contentType === "primary"
                                        ? { view_count: -1 }
                                        : { outlier_score: -1 },
                            },
                            { $skip: offset },
                            { $limit: limit },
                        ],
                    },
                },
            ];

            const result = await this.viralIdeasQueueModel
                .aggregate(pipeline)
                .exec();

            if (!result || result.length === 0) {
                throw new NotFoundException("Queue not found");
            }

            const queueData = result[0];
            const content = queueData.content || [];

            // Add reel_type classification
            const reels = content.map((item) => ({
                ...item,
                reel_type:
                    item.username === queueData.primary_username
                        ? "primary"
                        : "competitor",
            }));

            return {
                reels: reels,
                total_count: reels.length,
                has_more: reels.length === limit,
                primary_username: queueData.primary_username,
            };
        } catch (error) {
            this.logger.error(
                `❌ Error in optimized analysis content query: ${error.message}`
            );
            throw error;
        }
    }
}
```

### Key Differences in Nest.js Implementation

1. **DTO Validation**: Comprehensive input validation with proper type conversion and constraints for all parameters.

2. **Modular Content Strategies**: Separate methods for different content types (`getPrimaryContent`, `getCompetitorContent`, `getAllContent`) for better maintainability.

3. **MongoDB Aggregation Alternative**: Provides an optimized implementation using MongoDB's aggregation pipeline for complex queries.

4. **Smart Sorting Logic**:

    - **Primary Content**: Sorted by `view_count` descending for performance insights
    - **Competitor Content**: Sorted by `outlier_score` descending for viral potential
    - **All Content**: Sorted by `outlier_score` descending for comprehensive analysis

5. **Active Competitor Filtering**: Only includes active competitors (`is_active: true`) for accurate analysis scope.

6. **Content Type Classification**: Automatic classification based on username comparison with primary user.

7. **Performance Optimization**:

    - **Lean Queries**: Uses `.lean()` for better performance when transforming data
    - **Strategic Field Selection**: Only fetches required fields to minimize data transfer
    - **Aggregation Pipeline**: Alternative implementation for complex queries on large datasets

8. **Error Handling**: Comprehensive error handling with proper HTTP status codes and detailed logging.

## Responses

### Success: 200 OK

Returns a comprehensive paginated list of the content that was part of the viral analysis, with rich metadata for frontend display.

**Example Response (content_type="all"):**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "content_id": "64f8a9b2c1d2e3f4a5b6c7d8",
                "shortcode": "CzX8vQrP2mK",
                "url": "https://instagram.com/p/CzX8vQrP2mK/",
                "description": "🔥 5 VIRAL Content Ideas That Actually Work! Which one will you try first? 👇 #contentcreator #viralcontent #socialmediatips",
                "view_count": 2847593,
                "like_count": 156842,
                "comment_count": 3247,
                "date_posted": "2024-01-12T18:30:00Z",
                "username": "marketing_guru_sarah",
                "outlier_score": 8.7,
                "transcript": "Hey creators! Today I'm sharing 5 viral content ideas that have generated millions of views...",
                "transcript_language": "en",
                "transcript_available": true,
                "reel_type": "competitor"
            },
            {
                "content_id": "64f8a9b2c1d2e3f4a5b6c7d9",
                "shortcode": "CzY1mNpQ8rL",
                "url": "https://instagram.com/p/CzY1mNpQ8rL/",
                "description": "My morning routine that changed everything ✨ Save this for later! #morningroutine #productivity #selfcare",
                "view_count": 1923847,
                "like_count": 89234,
                "comment_count": 2156,
                "date_posted": "2024-01-10T09:15:00Z",
                "username": "fitness_creator_alex",
                "outlier_score": 7.9,
                "transcript": "Good morning everyone! Let me walk you through my 5-step morning routine...",
                "transcript_language": "en",
                "transcript_available": true,
                "reel_type": "primary"
            },
            {
                "content_id": "64f8a9b2c1d2e3f4a5b6c7da",
                "shortcode": "CzZ4pQsR9tM",
                "url": "https://instagram.com/p/CzZ4pQsR9tM/",
                "description": "POV: You finally understand compound interest 💰 #financetips #investing #moneymindset",
                "view_count": 1456789,
                "like_count": 67823,
                "comment_count": 1834,
                "date_posted": "2024-01-08T14:45:00Z",
                "username": "finance_coach_mike",
                "outlier_score": 7.2,
                "transcript": "Let me explain compound interest in the simplest way possible...",
                "transcript_language": "en",
                "transcript_available": true,
                "reel_type": "competitor"
            }
        ],
        "total_count": 3,
        "has_more": true,
        "primary_username": "fitness_creator_alex"
    }
}
```

**Example Response (content_type="primary"):**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "content_id": "64f8a9b2c1d2e3f4a5b6c7d9",
                "shortcode": "CzY1mNpQ8rL",
                "url": "https://instagram.com/p/CzY1mNpQ8rL/",
                "description": "My morning routine that changed everything ✨ Save this for later! #morningroutine #productivity #selfcare",
                "view_count": 1923847,
                "like_count": 89234,
                "comment_count": 2156,
                "date_posted": "2024-01-10T09:15:00Z",
                "username": "fitness_creator_alex",
                "outlier_score": 7.9,
                "transcript": "Good morning everyone! Let me walk you through my 5-step morning routine...",
                "transcript_language": "en",
                "transcript_available": true,
                "reel_type": "primary"
            },
            {
                "content_id": "64f8a9b2c1d2e3f4a5b6c7db",
                "shortcode": "CzA2nOpS1uN",
                "url": "https://instagram.com/p/CzA2nOpS1uN/",
                "description": "3 exercises that will transform your core 💪 Try this workout! #fitness #core #workout",
                "view_count": 847293,
                "like_count": 42156,
                "comment_count": 987,
                "date_posted": "2024-01-05T16:20:00Z",
                "username": "fitness_creator_alex",
                "outlier_score": 6.4,
                "transcript": "Today we're focusing on core strength with these 3 powerful exercises...",
                "transcript_language": "en",
                "transcript_available": true,
                "reel_type": "primary"
            }
        ],
        "total_count": 2,
        "has_more": false,
        "primary_username": "fitness_creator_alex"
    }
}
```

**Key Response Features:**

-   **Rich Content Data**: Complete content information including captions, engagement metrics, and viral scores
-   **Content Classification**: Each item includes `reel_type` ("primary" or "competitor") for frontend filtering
-   **Transcript Integration**: Full transcript data with language detection for AI analysis context
-   **Engagement Metrics**: Comprehensive view, like, and comment counts for performance analysis
-   **Direct Links**: Instagram URLs for easy navigation to original content
-   **Viral Scoring**: `outlier_score` indicating viral potential (0-10 scale)
-   **Pagination Support**: `has_more` flag and `total_count` for infinite scroll implementation

### Response Field Details:

**Content Items (`reels`):**

-   **`content_id`**: Unique content identifier (MongoDB ObjectId)
-   **`shortcode`**: Instagram shortcode for URL construction
-   **`url`**: Direct Instagram link to the original content
-   **`description`**: Full content caption with hashtags and mentions
-   **`view_count`**: Raw view count for performance analysis
-   **`like_count`**: Raw like count for engagement analysis
-   **`comment_count`**: Raw comment count for engagement analysis
-   **`date_posted`**: ISO timestamp of when content was posted
-   **`username`**: Content creator's username
-   **`outlier_score`**: Viral potential score (0-10 scale, higher = more viral)
-   **`transcript`**: Full content transcript for AI analysis
-   **`transcript_language`**: Detected language code (e.g., "en", "es", "fr")
-   **`transcript_available`**: Boolean indicating if transcript is available
-   **`reel_type`**: Content classification ("primary" or "competitor")

**Metadata:**

-   **`total_count`**: Number of content items in current response
-   **`has_more`**: Boolean indicating if more content is available for pagination
-   **`primary_username`**: Username of the primary user for context

### Content Type Filtering:

-   **`all`** (default): Returns both primary and competitor content, sorted by `outlier_score` descending for comprehensive viral analysis
-   **`primary`**: Returns only primary user content, sorted by `view_count` descending for performance insights
-   **`competitor`**: Returns only competitor content, sorted by `outlier_score` descending for viral potential analysis

### Sorting Strategies:

**Primary Content (`content_type="primary"`):**

-   Sorted by `view_count` descending
-   Focus on performance analysis and user's best-performing content
-   Helps identify what works for the primary user

**Competitor Content (`content_type="competitor"`):**

-   Sorted by `outlier_score` descending
-   Focus on viral potential and trending content from competitors
-   Helps identify viral patterns and opportunities

**All Content (`content_type="all"`):**

-   Sorted by `outlier_score` descending
-   Comprehensive view prioritizing viral potential across all sources
-   Optimal for discovering trending content patterns

### Use Cases:

1. **Content Grid Display**: Frontend can display content in a responsive grid with thumbnails and basic metrics
2. **Viral Analysis Context**: Provides source content alongside AI-generated insights for complete analysis
3. **Performance Comparison**: Compare primary user content performance against competitors
4. **Content Inspiration**: Discover high-performing content patterns from competitors
5. **Transcript Analysis**: AI can analyze transcript data for content themes and viral patterns

### Error: 404 Not Found

Returned if the `queue_id` is not found, or if the analysis for that job is not found.

### Error: 500 Internal Server Error

Returned for any other server-side errors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_viral_analysis_content(queue_id: str, ...)`
-   **Database Interaction:** The function first retrieves the `primary_username` and `analysis_id` from the `viral_ideas_queue` and `viral_analysis_results` tables. Based on the `content_type`, it then queries the `content` table to get the relevant reels for the primary user and/or the competitors.
