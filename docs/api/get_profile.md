# GET `/api/profile/{username}`

Retrieves detailed data for a specific user profile.

## Description

This endpoint fetches the profile information for a given username from the database. It is the primary way to get all the necessary data to display a user's profile page on the frontend. The data is transformed to a frontend-friendly format before being returned.

## Path Parameters

| Parameter  | Type   | Description                        |
| :--------- | :----- | :--------------------------------- |
| `username` | string | The Instagram username to look up. |

## Execution Flow

1.  **Receive Request**: The endpoint receives an HTTP GET request with a `username` in the URL path.
2.  **Query Database**: It queries the `primary_profiles` table to find a record where the `username` column matches the one from the request.
3.  **Handle Not Found**: If no record is found, the endpoint returns a `404 Not Found` error.
4.  **Transform Data**: If a profile is found, the raw data from the database is passed to a transformation function (`_transform_profile_for_frontend`). This function formats the data into a frontend-friendly structure, which might involve renaming fields, calculating new values, or nesting related data.
5.  **Send Response**: The transformed profile data is returned in the response with a `200 OK` status.

## Responses

### Success: 200 OK

Returns the profile data in a structured format.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "username": "exampleuser",
        "profile_name": "Example User",
        "bio": "This is an example bio.",
        "follower_count": 12345,
        "profile_image_url": "https://example.com/profile.jpg",
        "is_verified": false,
        "account_type": "Public",
        "recent_reels": [
            // ... array of reel objects
        ]
    }
}
```

### Error: 404 Not Found

Returned if the requested `username` does not exist in the database.

**Example Response:**

```json
{
    "detail": "Profile not found"
}
```

### Error: 500 Internal Server Error

Returned if an unexpected error occurs on the server while processing the request.

**Example Response:**

```json
{
    "detail": "Internal server error message"
}
```

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_profile(username: str)`
-   **Database Table:** `primary_profiles`

The backend function `_transform_profile_for_frontend` is used to process the raw data from the database before it is sent to the client. This ensures that the data is in a consistent and easy-to-use format.
