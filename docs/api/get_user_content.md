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
