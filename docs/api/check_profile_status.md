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
