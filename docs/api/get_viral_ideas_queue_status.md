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

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In backend_api.py

@app.get("/api/viral-ideas/queue-status")
async def get_viral_ideas_queue_status(api_instance: ViralSpotAPI = Depends(get_api)):
    """Get overall viral ideas queue status and statistics"""
    try:
        # Get queue statistics by counting items for each status
        pending_result = api_instance.supabase.client.table('viral_ideas_queue').select('id', count='exact').eq('status', 'pending').execute()
        # ... repeat for processing, completed, failed ...

        # Get recent items from the summary view
        recent_result = api_instance.supabase.client.table('viral_queue_summary').select(...).order('submitted_at', desc=True).limit(10).execute()

        # ... combine and return the response ...

    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

1.  **`pending_result = ...`**: It runs a `COUNT` query for each status. This is simple but can be inefficient if the table is very large.
2.  **`recent_result = ...`**: It fetches the 10 most recent items from the `viral_queue_summary` view for a quick overview of recent activity.

### Nest.js (Mongoose)

```typescript
// In your viral-ideas.controller.ts

@Get('/queue-status')
async getQueueStatus() {
  const result = await this.viralIdeasService.getQueueStatus();
  return { success: true, data: result };
}

// In your viral-ideas.service.ts

async getQueueStatus(): Promise<any> {
  // Use `countDocuments` for efficiency
  const pending = await this.viralIdeasQueueModel.countDocuments({ status: 'pending' });
  const processing = await this.viralIdeasQueueModel.countDocuments({ status: 'processing' });
  const completed = await this.viralIdeasQueueModel.countDocuments({ status: 'completed' });
  const failed = await this.viralIdeasQueueModel.countDocuments({ status: 'failed' });

  // Fetch recent items
  const recentItems = await this.viralIdeasQueueModel
    .find()
    .sort({ createdAt: -1 })
    .limit(10)
    .exec();

  // You might need to populate competitor data here as well if needed for the summary

  return {
    statistics: {
      pending,
      processing,
      completed,
      failed,
      total: pending + processing + completed + failed,
    },
    recent_items: recentItems.map(item => ({ /* transform item */ })),
  };
}
```

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
