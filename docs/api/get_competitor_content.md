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
