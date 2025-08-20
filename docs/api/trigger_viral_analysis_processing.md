# POST `/api/viral-ideas/queue/{queue_id}/process` ⚡

Triggers the processing of a specific item in the queue.

## Description

This endpoint is intended for internal or manual use to trigger the processing of a specific viral ideas analysis job. It directly starts the analysis by fetching the job's details from the `viral_queue_summary` view, creating a `ViralIdeasQueueItem`, and then launching the `ViralIdeasProcessor` in a background task.

This provides a direct way to start the analysis for a single job, which can be useful for debugging, reprocessing failed jobs, or other administrative tasks.

## Path Parameters

| Parameter  | Type   | Description                            |
| :--------- | :----- | :------------------------------------- |
| `queue_id` | string | The ID of the analysis job to process. |

## Execution Flow

1.  **Receive Request**: The endpoint receives a POST request with a `queue_id` in the URL path.
2.  **Fetch Job Data**: It queries the `viral_queue_summary` view to get all the necessary data for the job, including the content strategy and competitor list.
3.  **Handle Not Found**: If the job is not found, a `404 Not Found` error is returned.
4.  **Instantiate Processor**: The application creates an instance of a `ViralIdeasProcessor` class, passing the job data to its constructor.
5.  **Start Background Task**: The main processing logic of the `ViralIdeasProcessor` is started as a background task (e.g., using `asyncio.create_task` or a job queue like BullMQ). This allows the API to respond immediately without waiting for the analysis to complete.
6.  **Send Response**: The endpoint returns a confirmation that the processing has started in the background.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In backend_api.py
import asyncio
from viral_ideas_processor import ViralIdeasProcessor, ViralIdeasQueueItem

@app.post("/api/viral-ideas/queue/{queue_id}/process")
async def trigger_viral_analysis_processing(queue_id: str, ...):
    """Trigger the actual viral ideas processing for a queue entry"""
    try:
        # Get all job details from the `viral_queue_summary` view
        queue_result = api_instance.supabase.client.table('viral_queue_summary')...

        # ... create a ViralIdeasQueueItem object from the data ...

        processor = ViralIdeasProcessor()

        # Run the long-running analysis in a background task
        asyncio.create_task(processor.process_queue_item(queue_item))

        return APIResponse(
            success=True,
            data={'queue_id': queue_id, 'status': 'processing_started'},
            message="Viral ideas processing started in background"
        )
    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

1.  **`queue_result = ...`**: Fetches all the necessary data for the job from the database.
2.  **`processor = ViralIdeasProcessor()`**: Instantiates the class that contains the core analysis logic.
3.  **`asyncio.create_task(...)`**: This is the key part. It schedules the `process_queue_item` method to run in the background. This allows the API to immediately send a response to the client without waiting for the entire analysis (which could take minutes) to complete.
4.  **`return APIResponse(...)`**: The endpoint immediately returns a `processing_started` status.

### Nest.js (Mongoose)

```typescript
// In your viral-ideas.controller.ts

@Post('/queue/:queueId/process')
async triggerProcessing(@Param('queueId') queueId: string) {
  // This endpoint would typically be protected (e.g., admin only)
  await this.viralIdeasService.triggerProcessing(queueId);
  return { success: true, data: { status: 'processing_started' } };
}

// In your viral-ideas.service.ts
// This requires a job queue system like BullMQ

import { InjectQueue } from '@nestjs/bull';
import { Queue } from 'bull';

@Injectable()
export class ViralIdeasService {
  constructor(
    @InjectQueue('viral-ideas') private readonly viralIdeasQueue: Queue,
    // ... other models
  ) {}

  async triggerProcessing(queueId: string): Promise<void> {
    const queueItem = await this.viralIdeasQueueModel.findById(queueId).exec();
    if (!queueItem) {
      throw new NotFoundException('Queue entry not found');
    }

    // Add the job to the BullMQ queue.
    // A separate "processor" file will listen for jobs on this queue.
    await this.viralIdeasQueue.add('process-item', {
      queueItem: queueItem.toObject(),
    });
  }
}

// In a separate file: viral-ideas.processor.ts
@Processor('viral-ideas')
export class ViralIdeasProcessor {
  @Process('process-item')
  async handleProcessItem(job: Job) {
    const { queueItem } = job.data;
    // ...
    // This is where the long-running analysis logic would live.
    // It would update the database with progress and final results.
    // ...
  }
}
```

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
