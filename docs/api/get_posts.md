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
# In backend_api.py

@app.get("/api/posts")
async def get_posts(
    # ... all the query parameters, same as /api/reels ...
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get posts with filtering and pagination"""
    filters = ReelFilter(
        # ... copies all query params ...
        content_types='post' # Hardcodes the content type
    )
    result = await api_instance.get_reels(filters, limit, offset)
    return APIResponse(success=True, data=result)
```

**Line-by-Line Explanation:**

1.  **`@app.get("/api/posts")`**: The endpoint definition. It accepts the same filters as `/api/reels`.
2.  **`filters = ReelFilter(...)`**: It creates the same filter object that `/api/reels` uses.
3.  **`content_types='post'`**: This is the key line. It hardcodes the content type to `'post'`, ensuring that only posts are fetched.
4.  **`result = await api_instance.get_reels(...)`**: It calls the exact same `get_reels` method from the API class, passing the modified filter object. This is a great example of code reuse.

### Nest.js (Mongoose)

```typescript
// In your content.controller.ts

@Get('/posts')
async getPosts(@Query() queryParams: any) {
  const { limit = 24, offset = 0, ...filters } = queryParams;
  // Add the hardcoded filter
  filters.content_types = 'post';
  const result = await this.contentService.getReels(filters, limit, offset);
  return { success: true, data: result };
}

// In your content.service.ts

// No new method needed! The `getReels` service method can handle this.
// You would just need to make sure your `getReels` method can handle
// the `content_types` filter.

async getReels(filters: any, limit: number, offset: number): Promise<any> {
  const query = {};
  // ...
  if (filters.content_types) {
    query['content_type'] = { $in: filters.content_types.split(',') };
  }
  // ... rest of the method
}
```

## Responses

### Success: 200 OK

Returns a paginated list of post objects.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "id": "post_abc",
                "caption": "A beautiful photo!",
                "like_count": 12345,
                "comment_count": 1234,
                "media_type": "IMAGE"
                // ... other post data
            }
        ],
        "isLastPage": true
    }
}
```

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_posts(...)`
-   **Reusability:** This endpoint cleverly reuses the `api_instance.get_reels` function by passing a `ReelFilter` with `content_types='post'`. This is a great example of DRY (Don't Repeat Yourself) principles.
