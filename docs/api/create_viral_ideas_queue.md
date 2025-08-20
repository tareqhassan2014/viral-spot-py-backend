# POST `/api/viral-ideas/queue` ⚡

Creates a new viral ideas analysis job and adds it to the queue.

## Description

This endpoint is the trigger for the core AI-powered viral ideas pipeline. It allows a user to submit a request for a new analysis based on their content strategy and a selected list of competitors.

The endpoint creates a new entry in the `viral_ideas_queue` table and links the selected competitors in the `viral_ideas_competitors` table. This new job will then be picked up by the backend processors for analysis.

## Request Body

The endpoint expects a JSON request body with the following structure:

```json
{
    "session_id": "unique_session_id",
    "primary_username": "user_profile",
    "content_strategy": {
        "contentType": "Educational",
        "targetAudience": "Beginner developers",
        "goals": "Increase brand awareness"
    },
    "selected_competitors": ["competitor1", "competitor2"]
}
```

| Field                  | Type             | Description                                             |
| :--------------------- | :--------------- | :------------------------------------------------------ |
| `session_id`           | string           | A unique identifier for the user's session.             |
| `primary_username`     | string           | The username of the user requesting the analysis.       |
| `content_strategy`     | object           | An object describing the user's content strategy.       |
| `selected_competitors` | array of strings | A list of usernames for the competitors to be analyzed. |

## Execution Flow

1.  **Receive Request**: The endpoint receives a POST request with a JSON body containing the `session_id`, `primary_username`, `content_strategy`, and `selected_competitors`.
2.  **Validate Request Body**: The incoming JSON is validated against a predefined schema (e.g., a Pydantic model or a Nest.js DTO) to ensure all required fields are present and have the correct types.
3.  **Create Queue Entry**: A new record is created in the `viral_ideas_queue` table with the data from the request. The status is set to `pending`.
4.  **Link Competitors**: For each username in the `selected_competitors` array, a new record is created in the `viral_ideas_competitors` table, linking them to the new queue entry.
5.  **Send Response**: The endpoint returns a success message along with the ID of the newly created queue entry.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In backend_api.py

@app.post("/api/viral-ideas/queue")
async def create_viral_ideas_queue(request: ViralIdeasQueueRequest, api_instance: ViralSpotAPI = Depends(get_api)):
    """Create a new viral ideas analysis queue entry"""
    try:
        content_strategy_json = request.content_strategy.dict()

        queue_result = api_instance.supabase.client.table('viral_ideas_queue').insert({
            'session_id': request.session_id,
            'primary_username': request.primary_username,
            'content_strategy': content_strategy_json,
            'status': 'pending',
        }).execute()

        queue_id = queue_result.data[0]['id']

        if request.selected_competitors:
            competitor_records = [{'queue_id': queue_id, 'competitor_username': c} for c in request.selected_competitors]
            api_instance.supabase.client.table('viral_ideas_competitors').insert(competitor_records).execute()

        # ... construct and return response ...

    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

1.  **`request: ViralIdeasQueueRequest`**: The endpoint uses a Pydantic model `ViralIdeasQueueRequest` to automatically validate the incoming JSON body.
2.  **`api_instance.supabase.client.table('viral_ideas_queue').insert(...)`**: Inserts a new row into the `viral_ideas_queue` table with the main analysis job details.
3.  **`queue_id = queue_result.data[0]['id']`**: Retrieves the ID of the newly created queue entry.
4.  **`competitor_records = [...]`**: Creates a list of dictionary objects, one for each selected competitor.
5.  **`api_instance.supabase.client.table('viral_ideas_competitors').insert(...)`**: Performs a bulk insert into the `viral_ideas_competitors` table to link the competitors to the main job.

### Nest.js (Mongoose)

```typescript
// In your viral-ideas.controller.ts
import { CreateViralIdeasDto } from './dto/create-viral-ideas.dto';

@Post('/queue')
async createViralIdeasQueue(@Body() createDto: CreateViralIdeasDto) {
  const result = await this.viralIdeasService.createQueue(createDto);
  return { success: true, data: result };
}

// In your viral-ideas.service.ts
async createQueue(createDto: CreateViralIdeasDto): Promise<any> {
  // Create the main queue entry
  const newQueueItem = new this.viralIdeasQueueModel({
    session_id: createDto.session_id,
    primary_username: createDto.primary_username,
    content_strategy: createDto.content_strategy,
    status: 'pending',
  });
  const savedQueueItem = await newQueueItem.save();

  // Create the competitor links
  if (createDto.selected_competitors && createDto.selected_competitors.length > 0) {
    const competitorDocs = createDto.selected_competitors.map(username => ({
      queue_id: savedQueueItem._id,
      competitor_username: username,
    }));
    await this.viralIdeasCompetitorModel.insertMany(competitorDocs);
  }

  // Return the created queue item's data
  return {
    id: savedQueueItem._id,
    session_id: savedQueueItem.session_id,
    // ... other fields
  };
}
```

## Responses

### Success: 200 OK

Returns a confirmation object with the ID of the newly created queue entry.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "id": "queue_uuid_12345",
        "session_id": "unique_session_id",
        "primary_username": "user_profile",
        "status": "pending",
        "submitted_at": "2023-10-27T12:00:00Z"
    },
    "message": "Viral ideas analysis queued for @user_profile"
}
```

### Error: 500 Internal Server Error

Returned if there is a failure in creating the queue entry or linking the competitors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `create_viral_ideas_queue(request: ViralIdeasQueueRequest, ...)`
-   **Pydantic Model:** `ViralIdeasQueueRequest` is used to validate the incoming request body.
-   **Database Tables:**
    -   `viral_ideas_queue`: The main table for storing analysis jobs.
    -   `viral_ideas_competitors`: Stores the list of competitors for each analysis job.
