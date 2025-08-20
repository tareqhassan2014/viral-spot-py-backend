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
# In ViralSpotAPI class in backend_api.py

async def get_profile_reels(self, username: str, sort_by: str = 'popular', limit: int = 24, offset: int = 0):
    """Get reels for a specific profile"""
    try:
        logger.info(f"Getting reels for profile: {username}, sort_by: {sort_by}")

        query = self.supabase.client.table('content').select('''
            *,
            primary_profiles!profile_id (
                username, profile_name, followers,
                profile_image_url, profile_image_path,
                is_verified, account_type
            )
        ''').eq('username', username)

        if sort_by == 'popular':
            query = query.order('outlier_score', desc=True).order('view_count', desc=True)
        elif sort_by == 'recent':
            query = query.order('date_posted', desc=True)
        elif sort_by == 'oldest':
            query = query.order('date_posted', desc=False)

        query = query.range(offset, offset + limit)
        response = query.execute()

        if not response.data:
            return {'reels': [], 'isLastPage': True}

        has_more_data = len(response.data) > limit
        data_to_return = response.data[:limit]

        transformed_reels = [self._transform_content_for_frontend(item) for item in data_to_return]

        is_last_page = not has_more_data

        logger.info(f"✅ Returned {len(transformed_reels)} reels for {username}")

        return { 'reels': transformed_reels, 'isLastPage': is_last_page }

    except Exception as e:
        logger.error(f"❌ Error getting profile reels for {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint definition
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

1.  **`query = self.supabase.client.table('content').select(...)`**: Builds a query to select content, joining with `primary_profiles` to get author information.
2.  **`.eq('username', username)`**: Filters the content for the specified `username`.
3.  **`if sort_by == 'popular': ...`**: Applies sorting based on the `sort_by` parameter.
4.  **`query = query.range(offset, offset + limit)`**: Applies pagination. It fetches one extra item to check if there are more pages.
5.  **`has_more_data = len(response.data) > limit`**: Determines if there is a next page.
6.  **`data_to_return = response.data[:limit]`**: Slices the list to the requested limit.
7.  **`transformed_reels = [...]`**: Transforms each item for the frontend.

### Nest.js (Mongoose)

```typescript
// In your profile.controller.ts

@Get(':username/reels')
async getProfileReels(
  @Param('username') username: string,
  @Query('sort_by') sortBy: string = 'popular',
  @Query('limit') limit: number = 24,
  @Query('offset') offset: number = 0,
) {
  const result = await this.profileService.getProfileReels(username, sortBy, limit, offset);
  return { success: true, data: result };
}

// In your profile.service.ts

async getProfileReels(username: string, sortBy: string, limit: number, offset: number): Promise<any> {
  const profile = await this.primaryProfileModel.findOne({ username }).exec();
  if (!profile) {
    return { reels: [], isLastPage: true };
  }

  let sortOptions = {};
  if (sortBy === 'popular') {
    sortOptions = { outlier_score: -1, view_count: -1 };
  } else if (sortBy === 'recent') {
    sortOptions = { date_posted: -1 };
  } else if (sortBy === 'oldest') {
    sortOptions = { date_posted: 1 };
  }

  const reels = await this.contentModel
    .find({ profile_id: profile._id })
    .sort(sortOptions)
    .skip(offset)
    .limit(limit + 1) // Fetch one extra
    .exec();

  const hasMore = reels.length > limit;
  const results = reels.slice(0, limit);

  // You would have a `transformContentForFrontend` method here
  const transformedReels = results.map(reel => this.transformContentForFrontend(reel, profile));

  return {
    reels: transformedReels,
    isLastPage: !hasMore,
  };
}
```

## Responses

### Success: 200 OK

Returns a list of reel objects and a flag indicating if there are more pages.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "id": "reel123",
                "thumbnail_url": "https://example.com/thumb.jpg",
                "view_count": 123456,
                "like_count": 12345,
                "comment_count": 123
                // ... other reel properties
            }
        ],
        "isLastPage": false
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
