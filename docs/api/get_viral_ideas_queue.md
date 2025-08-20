# GET `/api/viral-ideas/queue/{session_id}` ⚡

Retrieves the status of a specific viral ideas analysis job from the queue.

## Description

After creating a new viral ideas analysis job with the `POST /api/viral-ideas/queue` endpoint, the frontend can use this endpoint to poll for status updates. This allows for real-time feedback to the user, showing the progress of the analysis as it moves through the pipeline.

The endpoint returns a comprehensive status object, including the current stage of the analysis, the progress percentage, and the content strategy that was submitted.

## Path Parameters

| Parameter    | Type   | Description                                                                        |
| :----------- | :----- | :--------------------------------------------------------------------------------- |
| `session_id` | string | The unique identifier for the user's session, which is linked to the analysis job. |

## Responses

### Success: 200 OK

Returns a detailed status object for the analysis job.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "id": "queue_uuid_12345",
        "session_id": "unique_session_id",
        "primary_username": "user_profile",
        "status": "processing",
        "progress_percentage": 50,
        "content_type": "Educational",
        "target_audience": "Beginner developers",
        "main_goals": "Increase brand awareness",
        "competitors": ["competitor1", "competitor2"],
        "submitted_at": "2023-10-27T12:00:00Z",
        "started_processing_at": "2023-10-27T12:01:00Z",
        "completed_at": null
    }
}
```

### Error: 404 Not Found

Returned if no queue entry is found for the given `session_id`.

### Error: 500 Internal Server Error

Returned for any other server-side errors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_viral_ideas_queue(session_id: str, ...)`
-   **Database View:** `viral_queue_summary` is used to efficiently retrieve the status and related data for the queue entry. This view likely joins the `viral_ideas_queue` and `viral_ideas_competitors` tables.
