# GET `/api/viral-ideas/queue-status` ⚡

Gets overall statistics for the viral ideas queue.

## Description

This endpoint provides a high-level, dashboard-like view of the health and status of the viral ideas processing queue. It is useful for monitoring the overall system, understanding the current workload, and quickly identifying any potential issues.

The endpoint returns two main pieces of information:

1.  **Statistics:** A count of jobs in each status category (pending, processing, completed, failed).
2.  **Recent Items:** A list of the 10 most recently submitted jobs, providing a snapshot of the latest activity.

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request.
2.  **Get Statistics**: It performs several `COUNT` queries on the `viral_ideas_queue` table to get the number of jobs in each status category (pending, processing, completed, failed).
3.  **Get Recent Items**: It queries the `viral_queue_summary` view, ordering by the submission date descending and limiting the result to 10 to get the most recent jobs.
4.  **Combine and Respond**: The statistics and the list of recent items are combined into a single JSON object and returned with a `200 OK` status.

## Responses

### Success: 200 OK

Returns an object with queue statistics and a list of recent items.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "statistics": {
            "pending": 5,
            "processing": 2,
            "completed": 150,
            "failed": 1,
            "total": 158
        },
        "recent_items": [
            {
                "id": "queue_uuid_abc",
                "primary_username": "user1",
                "status": "completed",
                "progress_percentage": 100,
                "submitted_at": "2023-10-27T14:00:00Z"
            },
            {
                "id": "queue_uuid_def",
                "primary_username": "user2",
                "status": "processing",
                "progress_percentage": 75,
                "submitted_at": "2023-10-27T14:05:00Z"
            }
        ]
    }
}
```

### Error: 500 Internal Server Error

Returned if there is a failure in retrieving the queue status.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_viral_ideas_queue_status(...)`
-   **Database Interaction:**
    -   The statistics are gathered by performing `count` queries on the `viral_ideas_queue` table for each status.
    -   The recent items are fetched from the `viral_queue_summary` view to efficiently get the necessary data.
