# GET `/api/profile/{username}/status`

Checks the processing status of a profile.

## Description

After a new profile is requested for analysis via the `POST /api/profile/{username}/request` endpoint, this endpoint can be used to poll for updates on its processing status. It allows the frontend to know whether the profile is still in the queue, being processed, or if it is complete and ready to be viewed.

## Path Parameters

| Parameter  | Type   | Description                           |
| :--------- | :----- | :------------------------------------ |
| `username` | string | The username of the profile to check. |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `username` in the URL path.
2.  **Check `primary_profiles` Table**: It first queries the `primary_profiles` table to see if a record with the given `username` exists.
3.  **Return Completed Status**: If a record is found in `primary_profiles`, it means the processing is complete. The endpoint returns a response with `completed: true`.
4.  **Check `queue` Table**: If the profile is not in `primary_profiles`, it then queries the `queue` table to find the status of the job for that `username`.
5.  **Return Queue Status**: If a record is found in the `queue`, it returns a response with `completed: false` and the current `status` from the queue (e.g., `PENDING`, `PROCESSING`).
6.  **Return Not Found**: If the profile is not found in either table, it returns a response with `completed: false` and a `status` of `NOT_FOUND`.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In ViralSpotAPI class in backend_api.py

async def check_profile_status(self, username: str):
    """Check if profile processing is complete"""
    try:
        response = self.supabase.client.table('primary_profiles').select('username, created_at').eq('username', username).execute()

        if response.data:
            return { 'completed': True, 'message': 'Profile processing completed', ... }
        else:
            queue_response = self.supabase.client.table('queue').select('*').eq('username', username).order('timestamp', desc=True).limit(1).execute()

            if queue_response.data:
                queue_item = queue_response.data[0]
                return { 'completed': False, 'status': queue_item['status'], ... }

            return { 'completed': False, 'status': 'NOT_FOUND', ... }

    except Exception as e:
        # ... error handling ...

# FastAPI endpoint definition
@app.get("/api/profile/{username}/status")
async def check_profile_status(
    username: str = Path(..., description="Instagram username"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Check profile processing status"""
    result = await api_instance.check_profile_status(username)
    return APIResponse(success=True, data=result)
```

**Line-by-Line Explanation:**

1.  **`response = self.supabase.client.table('primary_profiles')...`**: First, it checks the `primary_profiles` table.
2.  **`if response.data:`**: If a record is found, it means processing is complete, and it returns a `completed: true` status.
3.  **`else: queue_response = ...`**: If not found in `primary_profiles`, it checks the `queue` table.
4.  **`if queue_response.data:`**: If a record is found in the queue, it returns `completed: false` along with the current status from the queue record.
5.  **`return { 'completed': False, 'status': 'NOT_FOUND', ... }`**: If the profile is in neither table, it returns a `NOT_FOUND` status.

### Nest.js (Mongoose)

```typescript
// In your profile.controller.ts

@Get(':username/status')
async checkProfileStatus(@Param('username') username: string) {
  const result = await this.profileService.checkProfileStatus(username);
  return { success: true, data: result };
}

// In your profile.service.ts

async checkProfileStatus(username: string): Promise<any> {
  const primaryProfile = await this.primaryProfileModel.findOne({ username }).exec();
  if (primaryProfile) {
    return {
      completed: true,
      message: 'Profile processing completed',
      created_at: primaryProfile.createdAt,
    };
  }

  const queueItem = await this.queueModel
    .findOne({ username })
    .sort({ createdAt: -1 })
    .exec();

  if (queueItem) {
    return {
      completed: false,
      status: queueItem.status,
      message: `Profile is ${queueItem.status.toLowerCase()}`,
      attempts: queueItem.attempts,
    };
  }

  return {
    completed: false,
    status: 'NOT_FOUND',
    message: 'Profile not found in queue or database',
  };
}
```

## Responses

### Success: 200 OK

Returns a status object indicating the current state of the profile processing.

**Example Response (Completed):**

```json
{
    "success": true,
    "data": {
        "completed": true,
        "message": "Profile processing completed",
        "created_at": "2023-10-27T10:00:00Z"
    }
}
```

**Example Response (In Queue):**

```json
{
    "success": true,
    "data": {
        "completed": false,
        "status": "PENDING",
        "message": "Profile is pending",
        "attempts": 0
    }
}
```

**Example Response (Not Found):**

```json
{
    "success": true,
    "data": {
        "completed": false,
        "status": "NOT_FOUND",
        "message": "Profile not found in queue or database"
    }
}
```

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `check_profile_status(username: str)`
-   **Database Tables:**
    -   `primary_profiles`: Checked first to see if the profile has been successfully processed.
    -   `queue`: Checked if the profile is not yet in `primary_profiles` to determine its queue status.
