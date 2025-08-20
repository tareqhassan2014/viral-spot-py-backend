# GET `/api/viral-ideas/queue/{session_id}` ⚡

Retrieves the status of a specific viral ideas analysis job from the queue.

## Description

After creating a new viral ideas analysis job with the `POST /api/viral-ideas/queue` endpoint, the frontend can use this endpoint to poll for status updates. This allows for real-time feedback to the user, showing the progress of the analysis as it moves through the pipeline.

The endpoint returns a comprehensive status object, including the current stage of the analysis, the progress percentage, and the content strategy that was submitted.

## Path Parameters

| Parameter    | Type   | Description                                                                        |
| :----------- | :----- | :--------------------------------------------------------------------------------- |
| `session_id` | string | The unique identifier for the user's session, which is linked to the analysis job. |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `session_id` in the URL path.
2.  **Query Database View**: It queries a database view called `viral_queue_summary`. This view is a pre-joined and aggregated representation of the `viral_ideas_queue` and `viral_ideas_competitors` tables, designed for efficient status lookups.
3.  **Handle Not Found**: If no record is found for the given `session_id`, a `404 Not Found` error is returned.
4.  **Send Response**: If a record is found, the data from the view is returned as the response with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In backend_api.py

@app.get("/api/viral-ideas/queue/{session_id}")
async def get_viral_ideas_queue(session_id: str, api_instance: ViralSpotAPI = Depends(get_api)):
    """Get viral ideas queue status by session ID"""
    try:
        # The Python code uses a database VIEW called `viral_queue_summary`
        # This view pre-joins the queue and competitor tables for efficiency
        result = api_instance.supabase.client.table('viral_queue_summary').select('*').eq('session_id', session_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Queue entry not found")

        # ... construct and return response from view data ...

    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

1.  **`api_instance.supabase.client.table('viral_queue_summary')...`**: Instead of querying and joining multiple tables in the code, the logic queries a pre-defined database view. This is a common performance optimization. The view handles the complexity of joining `viral_ideas_queue` and `viral_ideas_competitors`.
2.  **`.eq('session_id', session_id)`**: It filters the view to find the record for the specific session.

### Nest.js (Mongoose)

```typescript
// In your viral-ideas.controller.ts

@Get('/queue/:session_id')
async getViralIdeasQueue(@Param('session_id') sessionId: string) {
  const result = await this.viralIdeasService.getQueueBySessionId(sessionId);
  if (!result) {
    throw new NotFoundException('Queue entry not found');
  }
  return { success: true, data: result };
}

// In your viral-ideas.service.ts

async getQueueBySessionId(sessionId: string): Promise<any> {
  // In Mongoose, we achieve the same result as a view using `.populate()`
  const queueItem = await this.viralIdeasQueueModel
    .findOne({ session_id: sessionId })
    .exec();

  if (!queueItem) {
    return null;
  }

  const competitors = await this.viralIdeasCompetitorModel
    .find({ queue_id: queueItem._id })
    .exec();

  // Combine and transform the data to match the expected response
  return {
    id: queueItem._id,
    session_id: queueItem.session_id,
    competitors: competitors.map(c => c.competitor_username),
    // ... other fields from both collections
  };
}
```

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
