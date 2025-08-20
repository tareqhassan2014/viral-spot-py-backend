# POST `/api/viral-ideas/process-pending` ⚡

Processes all pending items in the viral ideas queue.

## Description

This endpoint serves as a batch operation to process all viral ideas analysis jobs that are currently in a `pending` state. It is a powerful tool for clearing out the queue and ensuring that all submitted requests are processed.

This is likely used for administrative purposes or scheduled tasks to keep the analysis pipeline flowing smoothly.

## Responses

### Success: 200 OK

Returns a confirmation that the batch processing has been initiated.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "status": "processing_started"
    },
    "message": "Processing of pending viral ideas queue items started"
}
```

### Error: 500 Internal Server Error

Returned if there is a failure in initiating the batch processing.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `process_pending_viral_ideas()`
-   **Background Processing:** The endpoint uses the `ViralIdeasQueueManager` class to handle the processing of all pending items. This is run as an asynchronous background task to prevent the API request from timing out.
