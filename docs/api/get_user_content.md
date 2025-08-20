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
# In backend_api.py

@app.get("/api/content/user/{username}")
async def get_user_content(
    username: str,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("recent", ...),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get user's own content for grid display"""
    # The implementation is identical to `get_competitor_content`
    # It queries the `content` table filtered by the `username`.
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

This endpoint's code is functionally identical to `get_competitor_content`. It queries the `content` table, filters by the `username` provided in the path, and applies sorting and pagination. The only difference is the default `sort_by` value.

### Nest.js (Mongoose)

```typescript
// In your content.controller.ts

@Get('/user/:username')
async getUserContent(
  @Param('username') username: string,
  @Query('limit') limit: number = 24,
  @Query('offset') offset: number = 0,
  @Query('sort_by') sortBy: string = 'recent',
) {
  // You can reuse the same service method as getCompetitorContent
  const result = await this.contentService.getCompetitorContent(username, limit, offset, sortBy);
  return { success: true, data: result };
}

// In your content.service.ts
// No new method is needed. The `getCompetitorContent` method can be reused
// as it already fetches content by username.
```

## Responses

### Success: 200 OK

Returns a paginated list of the user's own content.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "id": "user_reel_abc",
                "caption": "My latest creation!",
                "view_count": 15000,
                "like_count": 1500
                // ... other reel data
            }
        ],
        "total_count": 1,
        "has_more": false,
        "username": "current_user",
        "sort_by": "recent"
    }
}
```

### Error: 500 Internal Server Error

Returned if there is a failure to retrieve the content.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_user_content(username: str, limit: int, offset: int, sort_by: str)`
-   **Database Table:** `content`, with a join to `primary_profiles` to ensure consistent profile data is included.
-   **Transformation:** Uses the same `_transform_content_for_frontend` method as other content endpoints to format the data for the client.
