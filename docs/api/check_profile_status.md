# GET `/api/profile/{username}/status`

Checks the processing status of a profile.

## Description

After a new profile is requested for analysis via the `POST /api/profile/{username}/request` endpoint, this endpoint can be used to poll for updates on its processing status. It allows the frontend to know whether the profile is still in the queue, being processed, or if it is complete and ready to be viewed.

## Path Parameters

| Parameter  | Type   | Description                           |
| :--------- | :----- | :------------------------------------ |
| `username` | string | The username of the profile to check. |

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
