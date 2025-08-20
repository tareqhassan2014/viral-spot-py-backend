# POST `/api/reset-session`

Resets the user's random session.

## Description

This is a utility endpoint used for debugging or clearing session-specific data. It specifically targets the "random session" feature, which is used to provide a consistent, shuffled order of content when the `random_order=true` parameter is used in the `/api/reels` or `/api/posts` endpoints.

Calling this endpoint will clear the stored random seed for a given `session_id`, causing a new random order to be generated on the next request.

## Query Parameters

| Parameter    | Type   | Description                     |
| :----------- | :----- | :------------------------------ |
| `session_id` | string | The ID of the session to reset. |

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
