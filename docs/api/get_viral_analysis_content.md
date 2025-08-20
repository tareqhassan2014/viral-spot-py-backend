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
