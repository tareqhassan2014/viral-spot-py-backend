# GET `/api/reels`

Retrieves a list of reels, with extensive support for filtering, sorting, and pagination.

## Description

This is the main endpoint for browsing and discovering viral content in the ViralSpot platform. It provides a powerful set of filters to allow users to narrow down the content they are interested in. The results are paginated to ensure efficient loading and browsing.

## Query Parameters

This endpoint accepts a wide range of query parameters to customize the results.

### General

| Parameter | Type    | Description                                                                       | Default |
| :-------- | :------ | :-------------------------------------------------------------------------------- | :------ |
| `search`  | string  | A search term to match against reel captions, transcripts, and other text fields. | `null`  |
| `limit`   | integer | The maximum number of reels to return per page (1-100).                           | `24`    |
| `offset`  | integer | The number of reels to skip for pagination.                                       | `0`     |

### Filtering

| Parameter                     | Type    | Description                                                    | Default |
| :---------------------------- | :------ | :------------------------------------------------------------- | :------ |
| `primary_categories`          | string  | Comma-separated list of primary categories to filter by.       | `null`  |
| `secondary_categories`        | string  | Comma-separated list of secondary categories to filter by.     | `null`  |
| `tertiary_categories`         | string  | Comma-separated list of tertiary categories to filter by.      | `null`  |
| `keywords`                    | string  | Comma-separated list of keywords to filter by.                 | `null`  |
| `min_outlier_score`           | float   | Minimum outlier score.                                         | `null`  |
| `max_outlier_score`           | float   | Maximum outlier score.                                         | `null`  |
| `min_views`                   | integer | Minimum view count.                                            | `null`  |
| `max_views`                   | integer | Maximum view count.                                            | `null`  |
| `min_likes`                   | integer | Minimum like count.                                            | `null`  |
| `max_likes`                   | integer | Maximum like count.                                            | `null`  |
| `min_comments`                | integer | Minimum comment count.                                         | `null`  |
| `max_comments`                | integer | Maximum comment count.                                         | `null`  |
| `min_followers`               | integer | Minimum follower count for the reel's creator.                 | `null`  |
| `max_followers`               | integer | Maximum follower count for the reel's creator.                 | `null`  |
| `date_range`                  | string  | A predefined date range to filter by (e.g., `last_7_days`).    | `null`  |
| `is_verified`                 | boolean | Filter for content from verified or non-verified accounts.     | `null`  |
| `account_types`               | string  | Comma-separated list of account types to filter by.            | `null`  |
| `content_types`               | string  | Comma-separated list of content types to filter by.            | `null`  |
| `languages`                   | string  | Comma-separated list of languages to filter by.                | `null`  |
| `content_styles`              | string  | Comma-separated list of content styles to filter by.           | `null`  |
| `min_account_engagement_rate` | float   | Minimum account engagement rate (0-100).                       | `null`  |
| `max_account_engagement_rate` | float   | Maximum account engagement rate (0-100).                       | `null`  |
| `excluded_usernames`          | string  | Comma-separated list of usernames to exclude from the results. | `null`  |

### Sorting & Ordering

| Parameter      | Type    | Description                                                                                                                                       | Default |
| :------------- | :------ | :------------------------------------------------------------------------------------------------------------------------------------------------ | :------ |
| `sort_by`      | string  | The sorting order. Options: `popular`, `views`, `likes`, `comments`, `recent`, `oldest`, `followers`, `account_engagement`, `content_engagement`. | `null`  |
| `random_order` | boolean | If `true`, returns the results in a random order for the given `session_id`.                                                                      | `false` |
| `session_id`   | string  | A unique ID for the user's session, used for consistent random ordering.                                                                          | `null`  |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a wide range of optional query parameters for filtering, sorting, and pagination.
2.  **Parse and Validate Filters**: The query parameters are parsed and validated, often using a Pydantic-like model (`ReelFilter`) to ensure data integrity.
3.  **Build Dynamic Query**: A flexible database query is constructed on the `content` table. Each filter parameter adds a `WHERE` clause to the query. This includes filtering by categories, keywords, performance metrics (views, likes), and account metrics (followers).
4.  **Apply Sorting**: The `sort_by` parameter determines the `ORDER BY` clause. If `random_order` is `true`, it uses a `session_id` to create a consistent random sort for that user's session.
5.  **Apply Pagination**: The `limit` and `offset` parameters are used to paginate the results.
6.  **Execute Query**: The complex, dynamically built query is executed against the database.
7.  **Transform Data**: The results are transformed into a frontend-friendly format.
8.  **Send Response**: The paginated and transformed list of reels is returned with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In ViralSpotAPI class in backend_api.py

async def get_reels(self, filters: ReelFilter, limit: int = 24, offset: int = 0):
    """Get reels with filtering and pagination"""
    try:
        # Build and execute query - request one extra to check if there's more data
        query = self._build_content_query(filters, limit + 1, offset)
        response = query.execute()

        if not response or not hasattr(response, 'data') or response.data is None:
            return {'reels': [], 'isLastPage': True}

        data = response.data
        has_more_data = len(data) > limit

        # Apply random ordering if needed
        if filters.random_order and filters.session_id:
            data = self._apply_random_ordering(data, filters.session_id, limit)
        else:
            data = data[:limit]

        transformed_reels = [self._transform_content_for_frontend(item) for item in data if item]
        is_last_page = not has_more_data

        return { 'reels': transformed_reels, 'isLastPage': is_last_page }

    except Exception as e:
        logger.error(f"❌ Error getting reels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint definition
@app.get("/api/reels")
async def get_reels(
    # ... all the query parameters ...
    filters: ReelFilter = Depends(get_filters), # Depends on a function that gathers filters
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    result = await api_instance.get_reels(filters, limit, offset)
    return APIResponse(success=True, data=result)
```

**Line-by-Line Explanation:**

1.  **`_build_content_query(...)`**: This is a crucial helper method that dynamically constructs the database query. It takes all the filter parameters and adds the appropriate `WHERE` clauses, `ORDER BY` clauses, and pagination (`range`).
2.  **`query.execute()`**: Runs the final query against the database.
3.  **`has_more_data = len(data) > limit`**: Because `limit + 1` items were requested, this check determines if there is another page of results.
4.  **`_apply_random_ordering(...)`**: If random ordering is requested, this helper shuffles the results consistently based on the `session_id`.
5.  **`_transform_content_for_frontend(...)`**: Loops through the results and formats each one into the structure the frontend expects.
6.  **`@app.get("/api/reels")`**: The endpoint definition. It uses a dependency `get_filters` to gather all the optional query parameters into a single `ReelFilter` object, which keeps the endpoint signature clean.

### Nest.js (Mongoose)

```typescript
// In your content.controller.ts

@Get('/reels')
async getReels(@Query() queryParams: any) {
  const { limit = 24, offset = 0, ...filters } = queryParams;
  const result = await this.contentService.getReels(filters, limit, offset);
  return { success: true, data: result };
}

// In your content.service.ts

async getReels(filters: any, limit: number, offset: number): Promise<any> {
  const query = {};
  const sort = {};

  // 1. Build the query object dynamically based on filters
  if (filters.primary_categories) {
    query['primary_category'] = { $in: filters.primary_categories.split(',') };
  }
  if (filters.min_views) {
    query['view_count'] = { $gte: Number(filters.min_views) };
  }
  // ... and so on for all other filters

  // 2. Build the sort object
  if (filters.sort_by === 'views') {
    sort['view_count'] = -1;
  } else { // Default to 'popular'
    sort['outlier_score'] = -1;
    sort['view_count'] = -1;
  }

  // 3. Execute query
  const reels = await this.contentModel
    .find(query)
    .sort(sort)
    .skip(offset)
    .limit(limit + 1) // Fetch one extra to check for next page
    .populate('profile_id') // Equivalent to the JOIN in Python
    .exec();

  // 4. Handle pagination and transform
  const hasMore = reels.length > limit;
  const results = reels.slice(0, limit);
  const transformedReels = results.map(r => this.transformContentForFrontend(r));

  return {
    reels: transformedReels,
    isLastPage: !hasMore,
  };
}
```

## Responses

### Success: 200 OK

Returns a paginated list of reel objects.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "id": "reel_xyz",
                "caption": "Check out this amazing reel!",
                "view_count": 987654,
                "like_count": 98765
                // ... other reel data
            }
        ],
        "isLastPage": false
    }
}
```

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_reels(filters: ReelFilter, limit: int, offset: int)`
-   **Pydantic Model:** `ReelFilter` is used to manage the large number of filter parameters.
-   **Database Table:** `content`, with joins to `primary_profiles`.
