# POST `/api/profile/{username}/request`

Submits a request to scrape and analyze a new profile.

## Description

This is the primary endpoint for adding new profiles to the ViralSpot system. When a username is submitted, this endpoint adds it to a high-priority processing queue. The backend workers will then pick up this request and begin the process of scraping, analyzing, and storing the profile's data.

The endpoint includes logic to prevent duplicate processing. If a profile has already been successfully processed or is already in the queue, it will not be added again.

## Path Parameters

| Parameter  | Type   | Description                             |
| :--------- | :----- | :-------------------------------------- |
| `username` | string | The username of the profile to process. |

## Query Parameters

| Parameter | Type   | Description                           | Default    |
| :-------- | :----- | :------------------------------------ | :--------- |
| `source`  | string | The source of the processing request. | `frontend` |

## Execution Flow

1.  **Receive Request**: The endpoint receives a POST request with a `username` path parameter and an optional `source` query parameter.
2.  **Check if Already Processed**: It first queries the `primary_profiles` table to see if the profile already exists and has been fully processed. If so, it returns a message indicating that the profile is already complete.
3.  **Check if Already in Queue**: If the profile is not in `primary_profiles`, it then checks the `queue` table to see if there is already a pending or processing job for that `username`. If so, it returns a message indicating it's already in the queue.
4.  **Add to Queue**: If the profile is not in either table, it creates a new entry in the `queue` table with the `username`, `source`, and a `HIGH` priority.
5.  **Send Response**: It returns a success message indicating that the profile has been added to the queue, along with an estimated processing time.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In ViralSpotAPI class in backend_api.py

async def request_profile_processing(self, username: str, source: str = "frontend"):
    """Request high priority processing for a profile"""
    try:
        primary_response = self.supabase.client.table('primary_profiles').select('username').eq('username', username).execute()
        if primary_response.data:
            return { 'queued': False, 'message': f'Profile {username} is already fully processed', ... }

        queue_response = self.supabase.client.table('queue').select('*').eq('username', username).in_('status', ['PENDING', 'PROCESSING']).execute()
        if queue_response.data:
            return { 'queued': True, 'message': f'Profile {username} is already in queue', ... }

        queue_data = { 'username': username, 'source': source, 'priority': 'HIGH', ... }
        await self.supabase.save_queue_item(queue_data)
        return { 'queued': True, 'message': f'Profile {username} added to high priority queue', ... }

    except Exception as e:
        # ... error handling ...

# FastAPI endpoint definition
@app.post("/api/profile/{username}/request")
async def request_profile_processing(...):
    result = await api_instance.request_profile_processing(username, source)
    return APIResponse(success=True, data=result)
```

**Line-by-Line Explanation:**

1.  **`primary_response = ...`**: Checks if the profile already exists in `primary_profiles`. If so, it returns a message and does not queue.
2.  **`queue_response = ...`**: Checks if the profile is already in the `queue` with a pending or processing status.
3.  **`queue_data = { ... }`**: If the profile is not found in either table, it creates a new dictionary for the queue record.
4.  **`await self.supabase.save_queue_item(queue_data)`**: Saves the new record to the `queue` table.

### Nest.js (Mongoose)

```typescript
// In your profile.controller.ts

@Post(':username/request')
async requestProfileProcessing(
  @Param('username') username: string,
  @Query('source') source: string = 'frontend',
) {
  const result = await this.profileService.requestProfileProcessing(username, source);
  return { success: true, data: result };
}

// In your profile.service.ts

async requestProfileProcessing(username: string, source: string): Promise<any> {
  const existingProfile = await this.primaryProfileModel.findOne({ username }).exec();
  if (existingProfile) {
    return { queued: false, message: 'Profile is already fully processed' };
  }

  const existingQueueItem = await this.queueModel.findOne({
    username,
    status: { $in: ['PENDING', 'PROCESSING'] },
  }).exec();
  if (existingQueueItem) {
    return { queued: false, message: 'Profile is already in the queue' };
  }

  const newQueueItem = new this.queueModel({
    username,
    source,
    priority: 'HIGH',
    status: 'PENDING',
    attempts: 0,
  });
  await newQueueItem.save();

  return {
    queued: true,
    message: 'Profile has been added to the high priority queue',
    estimated_time: '1-3 minutes',
  };
}
```

## Responses

### Success: 200 OK

Returns an object indicating the result of the request.

**Example Response (Queued):**

```json
{
    "success": true,
    "data": {
        "queued": true,
        "message": "Profile user_to_process has been added to the high priority queue",
        "estimated_time": "1-3 minutes"
    }
}
```

**Example Response (Already Processed):**

```json
{
    "success": true,
    "data": {
        "queued": false,
        "message": "Profile existing_user is already fully processed",
        "estimated_time": "complete"
    }
}
```

**Example Response (Already in Queue):**

```json
{
    "success": true,
    "data": {
        "queued": false,
        "message": "Profile user_in_queue is already in the high priority queue"
    }
}
```

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `request_profile_processing(username: str, source: str)`
-   **Database Tables:**
    -   `primary_profiles`: Checked to see if the profile already exists.
    -   `queue`: Checked for existing entries and where the new request is added.
-   **Priority:** Requests from this endpoint are added to the queue with `HIGH` priority.
