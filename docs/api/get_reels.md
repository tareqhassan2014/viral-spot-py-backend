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
