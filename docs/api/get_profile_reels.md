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
