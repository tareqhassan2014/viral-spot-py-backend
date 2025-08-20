# POST `/api/viral-ideas/queue/{queue_id}/process` ⚡

Triggers the processing of a specific item in the queue.

## Description

This endpoint is intended for internal or manual use to trigger the processing of a specific viral ideas analysis job. It directly starts the analysis by fetching the job's details from the `viral_queue_summary` view, creating a `ViralIdeasQueueItem`, and then launching the `ViralIdeasProcessor` in a background task.

This provides a direct way to start the analysis for a single job, which can be useful for debugging, reprocessing failed jobs, or other administrative tasks.

## Path Parameters

| Parameter  | Type   | Description                            |
| :--------- | :----- | :------------------------------------- |
| `queue_id` | string | The ID of the analysis job to process. |

## Responses

### Success: 200 OK

Returns a confirmation that the processing has been initiated in a background task.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "queue_id": "queue_uuid_12345",
        "status": "processing_started"
    },
    "message": "Viral ideas processing started in background"
}
```

### Error: 404 Not Found

Returned if the `queue_id` does not correspond to an existing job.

### Error: 500 Internal Server Error

Returned if there is a failure in starting the processing task.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `trigger_viral_analysis_processing(queue_id: str, ...)`
-   **Background Processing:** The actual analysis is performed by the `ViralIdeasProcessor` class, which is run as an asynchronous background task using `asyncio.create_task`. This ensures that the API can respond quickly without waiting for the full analysis to complete.
-   **Helper Class:** `ViralIdeasQueueItem` is used to structure the data for the processor.
