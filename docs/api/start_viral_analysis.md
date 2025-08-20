# POST `/api/viral-ideas/queue/{queue_id}/start` ⚡

Starts a queued analysis job.

## Description

This endpoint is used to manually trigger the processing of a specific viral ideas analysis job that is already in the queue. It serves as a signal to the backend that the job is ready to be picked up by a processor.

It's important to note that this endpoint does not immediately change the status of the job to `processing`. The backend `viral_processor` is responsible for updating the status when it actually begins the analysis. This endpoint simply ensures the job is in a `pending` state and ready to go.

## Path Parameters

| Parameter  | Type   | Description                          |
| :--------- | :----- | :----------------------------------- |
| `queue_id` | string | The ID of the analysis job to start. |

## Execution Flow

1.  **Receive Request**: The endpoint receives a POST request with a `queue_id` in the URL path.
2.  **Verify Job Status**: It queries the `viral_ideas_queue` table to find the job with the given `queue_id`. It verifies that the job exists and its status is `pending`.
3.  **Handle Invalid State**: If the job is not found or is not in a `pending` state, it returns an appropriate error (e.g., `404 Not Found` or `409 Conflict`).
4.  **Signal for Processing**: This endpoint does not directly start the processing. Instead, it acts as a signal to the backend worker processes that the job is ready to be picked up. The worker is responsible for changing the status to `processing`.
5.  **Send Response**: It returns a confirmation message that the job has been queued and will be processed shortly.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In backend_api.py

@app.post("/api/viral-ideas/queue/{queue_id}/start")
async def start_viral_analysis(queue_id: str, api_instance: ViralSpotAPI = Depends(get_api)):
    """Mark viral ideas analysis as ready to be picked up by processor"""
    try:
        # This endpoint just verifies the job exists.
        # The actual status update is handled by the separate worker process.
        check_result = api_instance.supabase.client.table('viral_ideas_queue').select('*').eq('id', queue_id).execute()

        if not check_result.data:
            raise HTTPException(status_code=404, detail="Queue entry not found")

        queue_item = check_result.data[0]

        return APIResponse(
            success=True,
            data={'queue_id': queue_id, 'status': queue_item['status']},
            message="Analysis queued successfully - processor will start shortly"
        )
    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

1.  **`check_result = ...`**: The code simply checks if a queue entry with the given `queue_id` exists.
2.  **`if not check_result.data:`**: If it doesn't exist, it returns a 404 error.
3.  **`return APIResponse(...)`**: It returns a success message. It does **not** change the status of the job. This is because a separate, long-running worker process is responsible for polling the queue for `pending` jobs and updating their status to `processing` when it begins working on them. This endpoint is just a signal that the user has confirmed they want to start.

### Nest.js (Mongoose)

```typescript
// In your viral-ideas.controller.ts

@Post('/queue/:queueId/start')
async startViralAnalysis(@Param('queueId') queueId: string) {
  const result = await this.viralIdeasService.startAnalysis(queueId);
  if (!result) {
    throw new NotFoundException('Queue entry not found');
  }
  return { success: true, data: result, message: "Analysis queued successfully" };
}

// In your viral-ideas.service.ts

async startAnalysis(queueId: string): Promise<any> {
  const queueItem = await this.viralIdeasQueueModel.findById(queueId).exec();

  if (!queueItem) {
    return null;
  }

  // In a robust system, you would emit an event here to a job queue
  // processor (like BullMQ) to signal it can start.
  // For simplicity, we just check for existence and return the status.
  // The worker would be responsible for updating the status from 'pending' to 'processing'.

  return {
    queue_id: queueItem._id,
    status: queueItem.status,
  };
}
```

## Responses

### Success: 200 OK

Returns a confirmation that the job has been successfully queued for processing.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "queue_id": "queue_uuid_12345",
        "status": "pending"
    },
    "message": "Analysis queued successfully - processor will start shortly"
}
```

### Error: 404 Not Found

Returned if the `queue_id` does not correspond to an existing job.

### Error: 500 Internal Server Error

Returned for any other server-side errors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `start_viral_analysis(queue_id: str, ...)`
-   **Workflow:** This endpoint verifies that the queue entry exists and is in a `pending` state. The actual processing is handled asynchronously by a separate worker process, which will then update the job's status.
