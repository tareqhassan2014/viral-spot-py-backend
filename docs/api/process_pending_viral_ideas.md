# POST `/api/viral-ideas/process-pending` ⚡

Processes all pending items in the viral ideas queue.

## Description

This endpoint serves as a batch operation to process all viral ideas analysis jobs that are currently in a `pending` state. It is a powerful tool for clearing out the queue and ensuring that all submitted requests are processed.

This is likely used for administrative purposes or scheduled tasks to keep the analysis pipeline flowing smoothly.

## Execution Flow

1.  **Receive Request**: The endpoint receives a POST request.
2.  **Instantiate Queue Manager**: It creates an instance of a `ViralIdeasQueueManager` class.
3.  **Start Background Task**: It calls a method on the queue manager (e.g., `process_all_pending`) which is designed to run as a background task. This method fetches all pending jobs from the `viral_ideas_queue` table and processes them.
4.  **Send Response**: The endpoint immediately returns a confirmation that the batch processing has started in the background.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In backend_api.py
import asyncio
from viral_ideas_processor import ViralIdeasQueueManager

@app.post("/api/viral-ideas/process-pending")
async def process_pending_viral_ideas():
    """Process all pending viral ideas queue items"""
    try:
        queue_manager = ViralIdeasQueueManager()

        # Start the batch processing in a background task
        asyncio.create_task(queue_manager.process_pending_items())

        return APIResponse(
            success=True,
            data={'status': 'processing_started'},
            message="Processing of pending viral ideas queue items started"
        )
    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

1.  **`queue_manager = ViralIdeasQueueManager()`**: Instantiates the class responsible for managing the queue.
2.  **`asyncio.create_task(...)`**: Schedules the `process_pending_items` method to run in the background. This method would contain the logic to fetch all `pending` items from the database and process them one by one.
3.  **`return APIResponse(...)`**: The endpoint responds immediately, without waiting for the batch job to complete.

### Nest.js (Mongoose)

```typescript
// In your viral-ideas.controller.ts

@Post('/process-pending')
async processPending() {
  // This endpoint would typically be protected (e.g., admin only)
  await this.viralIdeasService.processPending();
  return { success: true, data: { status: 'processing_started' } };
}

// In your viral-ideas.service.ts
// This also uses a job queue system like BullMQ

async processPending(): Promise<void> {
  // Find all pending items
  const pendingItems = await this.viralIdeasQueueModel.find({ status: 'pending' }).exec();

  // Add each item to the queue for processing
  for (const item of pendingItems) {
    await this.viralIdeasQueue.add('process-item', {
      queueItem: item.toObject(),
    });
  }
}

// The same `viral-ideas.processor.ts` from the previous example
// would handle these jobs.
```

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
