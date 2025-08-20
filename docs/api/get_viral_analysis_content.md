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

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In backend_api.py

@app.get("/api/viral-analysis/{queue_id}/content")
async def get_viral_analysis_content(
    queue_id: str,
    content_type: str = Query("all", ...),
    ...
):
    """Get content/reels from viral analysis for grid display"""
    try:
        # 1. Get the analysis ID and primary username
        analysis_id, primary_username = get_analysis_info(queue_id)

        # 2. Get list of content_ids that were part of the analysis
        reels_info = api_instance.supabase.client.table('viral_analysis_reels').select('content_id').eq('analysis_id', analysis_id).execute()
        content_ids = [r['content_id'] for r in reels_info.data]

        # 3. Build the main query on the `content` table
        query = api_instance.supabase.client.table('content').select(...).in_('content_id', content_ids)

        # 4. Apply filtering based on `content_type`
        if content_type == "primary":
            query = query.eq('username', primary_username)
        elif content_type == "competitor":
            query = query.not_.eq('username', primary_username)

        # 5. Apply pagination, execute, and transform
        # ...

    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

1.  The code first fetches the `analysis_id` and the `primary_username` associated with the `queue_id`.
2.  It then gets a list of all the `content_id`s that were part of that specific analysis from the `viral_analysis_reels` table.
3.  It builds a query on the main `content` table, filtering for all the content that matches the retrieved `content_id`s.
4.  It applies an additional filter based on whether the user wants to see content from the primary user, the competitors, or all of them.

### Nest.js (Mongoose)

```typescript
// In your viral-ideas.controller.ts

@Get('/analysis/:queueId/content')
async getAnalysisContent(
  @Param('queueId') queueId: string,
  @Query('content_type') contentType: string = 'all',
  // ... other query params
) {
  const result = await this.viralIdeasService.getAnalysisContent(queueId, contentType, ...);
  return { success: true, data: result };
}

// In your viral-ideas.service.ts

async getAnalysisContent(queueId: string, contentType: string, ...): Promise<any> {
  // 1. Find the analysis result and populate the associated reels
  const analysis = await this.viralAnalysisResultModel
    .findOne({ queue_id: queueId })
    .populate('reels') // Assumes `reels` is an array of `content` refs
    .populate({ path: 'queue_id', select: 'primary_username' })
    .exec();

  if (!analysis) {
    throw new NotFoundException('Analysis not found');
  }

  // 2. Filter the populated reels based on the content_type
  let filteredReels = analysis.reels;
  const primaryUsername = analysis.queue_id.primary_username;

  if (contentType === 'primary') {
    filteredReels = analysis.reels.filter(reel => reel.username === primaryUsername);
  } else if (contentType === 'competitor') {
    filteredReels = analysis.reels.filter(reel => reel.username !== primaryUsername);
  }

  // 3. Apply pagination and transformation to the filtered array
  // ...

  return { reels: transformedReels, ... };
}
```

## Responses

### Success: 200 OK

Returns a paginated list of the content that was part of the analysis.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "content_id": "reel_abc",
                "username": "primary_user",
                "reel_type": "primary",
                "view_count": 500000
                // ... other content data
            },
            {
                "content_id": "reel_xyz",
                "username": "competitor1",
                "reel_type": "competitor",
                "view_count": 2500000
                // ... other content data
            }
        ],
        "total_count": 2,
        "has_more": false,
        "primary_username": "primary_user"
    }
}
```

### Error: 404 Not Found

Returned if the `queue_id` is not found, or if the analysis for that job is not found.

### Error: 500 Internal Server Error

Returned for any other server-side errors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_viral_analysis_content(queue_id: str, ...)`
-   **Database Interaction:** The function first retrieves the `primary_username` and `analysis_id` from the `viral_ideas_queue` and `viral_analysis_results` tables. Based on the `content_type`, it then queries the `content` table to get the relevant reels for the primary user and/or the competitors.
