# POST `/api/reset-session`

Resets the user's random session.

## Description

This is a utility endpoint used for debugging or clearing session-specific data. It specifically targets the "random session" feature, which is used to provide a consistent, shuffled order of content when the `random_order=true` parameter is used in the `/api/reels` or `/api/posts` endpoints.

Calling this endpoint will clear the stored random seed for a given `session_id`, causing a new random order to be generated on the next request.

## Query Parameters

| Parameter    | Type   | Description                     |
| :----------- | :----- | :------------------------------ |
| `session_id` | string | The ID of the session to reset. |

## Execution Flow

1.  **Receive Request**: The endpoint receives a POST request with a `session_id` as a query parameter.
2.  **Access In-Memory Storage**: It accesses an in-memory dictionary or hash map (`session_storage`) that stores the random seeds for user sessions.
3.  **Delete Session Data**: If an entry exists for the given `session_id`, it is deleted from the in-memory storage.
4.  **Send Response**: It returns a confirmation message, indicating whether the session was found and reset or not found.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In backend_api.py
# `session_storage` is a simple in-memory dictionary defined at the module level.
session_storage = {}

# In ViralSpotAPI class in backend_api.py
async def reset_session(self, session_id: str):
    """Reset random session"""
    try:
        if session_id in session_storage:
            del session_storage[session_id]
            return {'message': 'Session reset successfully'}
        else:
            return {'message': 'Session not found'}
    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

1.  **`session_storage = {}`**: A simple Python dictionary is used as an in-memory store. **Note:** This is not a scalable solution for production, as the session data will be lost on server restart and will not be shared across multiple server instances.
2.  **`if session_id in session_storage:`**: Checks if the key exists in the dictionary.
3.  **`del session_storage[session_id]`**: If it exists, it's deleted.

### Nest.js (Mongoose)

```typescript
// In your utility.controller.ts

@Post('/reset-session')
async resetSession(@Query('session_id') sessionId: string) {
  const result = await this.utilityService.resetSession(sessionId);
  return { success: true, data: result };
}

// In your utility.service.ts
// This should be implemented with a proper caching service like Redis.

import { Injectable } from '@nestjs/common';
import { Cache } from 'cache-manager';
import { Inject } from '@nestjs/common';

@Injectable()
export class UtilityService {
  constructor(@Inject('CACHE_MANAGER') private cacheManager: Cache) {}

  async resetSession(sessionId: string): Promise<{ message: string }> {
    // Construct the key used for storing session data
    const cacheKey = `random_session:${sessionId}`;

    // Check if the key exists before deleting
    const sessionData = await this.cacheManager.get(cacheKey);

    if (sessionData) {
      await this.cacheManager.del(cacheKey);
      return { message: 'Session reset successfully' };
    } else {
      return { message: 'Session not found' };
    }
  }
}
```

## Responses

### Success: 200 OK

Returns a confirmation message.

**Example Response (Session Found and Reset):**

```json
{
    "success": true,
    "data": {
        "message": "Session reset successfully"
    }
}
```

**Example Response (Session Not Found):**

```json
{
    "success": true,
    "data": {
        "message": "Session not found"
    }
}
```

### Error: 500 Internal Server Error

Returned if there is an unexpected error during the session reset process.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `reset_session(session_id: str)`
-   **Session Storage:** The random session data is stored in an in-memory Python dictionary called `session_storage`. This endpoint simply deletes the entry for the given `session_id`.
