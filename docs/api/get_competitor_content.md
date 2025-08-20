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
# In backend_api.py

@app.get("/api/content/competitor/{username}")
async def get_competitor_content(
    username: str,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("popular", ...),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get competitor content for grid display"""
    try:
        query = api_instance.supabase.client.table('content').select(
            '*, primary_profiles!profile_id (*)'
        ).eq('username', username)

        # ... apply sorting ...

        result = query.range(offset, offset + limit - 1).execute()
        # ... transform results ...
        return APIResponse(success=True, data={...})

    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

1.  **`query = api_instance.supabase.client.table('content')...`**: Builds the query on the `content` table.
2.  **`select('*, primary_profiles!profile_id (*)')`**: Selects all columns from `content` and joins the related `primary_profiles` record.
3.  **`.eq('username', username)`**: Filters the content to the specified competitor's username.
4.  The rest of the logic for sorting, pagination, and transformation is very similar to the `get_profile_reels` endpoint.

### Nest.js (Mongoose)

```typescript
// In your content.controller.ts

@Get('/competitor/:username')
async getCompetitorContent(
  @Param('username') username: string,
  @Query('limit') limit: number = 24,
  @Query('offset') offset: number = 0,
  @Query('sort_by') sortBy: string = 'popular',
) {
  const result = await this.contentService.getCompetitorContent(username, limit, offset, sortBy);
  return { success: true, data: result };
}

// In your content.service.ts

async getCompetitorContent(username: string, limit: number, offset: number, sortBy: string): Promise<any> {
  const profile = await this.primaryProfileModel.findOne({ username }).exec();
  if (!profile) {
    // Or handle as an error
    return { reels: [], total_count: 0, has_more: false };
  }

  const sortOptions = {};
  // ... build sortOptions based on sortBy ...

  const reels = await this.contentModel
    .find({ profile_id: profile._id })
    .sort(sortOptions)
    .skip(offset)
    .limit(limit)
    .populate('profile_id')
    .exec();

  // ... transform and return ...
}
```

## Responses

### Success: 200 OK

Returns a paginated list of the competitor's content.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "id": "competitor_reel_1",
                "caption": "A viral reel from a competitor.",
                "view_count": 2000000,
                "like_count": 200000
                // ... other reel data
            }
        ],
        "total_count": 1,
        "has_more": false,
        "username": "competitor_username",
        "sort_by": "popular"
    }
}
```

### Error: 500 Internal Server Error

Returned if there is a failure to retrieve the content.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_competitor_content(username: str, limit: int, offset: int, sort_by: str)`
-   **Database Table:** `content`, with a join to `primary_profiles` to include full profile data with each content item.
-   **Transformation:** The `_transform_content_for_frontend` method is used to ensure the data is in a consistent format for the client.
