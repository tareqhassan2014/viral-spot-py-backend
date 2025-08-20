# POST `/api/profile/{primary_username}/add-competitor/{target_username}` ⚡

Adds a `target_username` as a competitor to a `primary_username`.

## Description

This endpoint is part of a new competitor analysis feature. It allows a user to manually add another profile as a competitor. The system will then fetch the basic information of the `target_username`, download their profile image to a local bucket, and store their profile in the `similar_profiles` table for fast access.

This is a key part of building a list of competitors for a user to track and analyze.

## Path Parameters

| Parameter          | Type   | Description                                          |
| :----------------- | :----- | :--------------------------------------------------- |
| `primary_username` | string | The username of the user who is adding a competitor. |
| `target_username`  | string | The username of the profile to add as a competitor.  |

## Execution Flow

1.  **Receive Request**: The endpoint receives a POST request with `primary_username` and `target_username` in the URL path.
2.  **Fetch Competitor Data**: It calls a helper module (`simple_similar_profiles_api`) to fetch the basic profile data for the `target_username` from an external API.
3.  **Handle Not Found**: If the `target_username` cannot be found by the external API, a `404 Not Found` error is returned.
4.  **Download Profile Image**: The system downloads the profile image of the `target_username` and stores it in a local storage bucket (e.g., Supabase Storage).
5.  **Add to Database**: It creates a new record in the `similar_profiles` table with the `primary_username`, `target_username`, and the path to the downloaded profile image.
6.  **Transform and Respond**: The data for the newly added competitor is formatted for the frontend and returned with a `200 OK` status.

## Responses

### Success: 200 OK

Returns the profile data of the newly added competitor.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "username": "new_competitor",
        "profile_name": "New Competitor",
        "profile_image_url": "https://cdn.example.com/new_competitor.jpg"
        // ... other profile data
    },
    "message": "Successfully added @new_competitor to competitors for @primary_user"
}
```

### Error: 404 Not Found

Returned if the `target_username` cannot be found.

### Error: 503 Service Unavailable

Returned if the `simple_similar_profiles_api` module is not available.

### Error: 500 Internal Server Error

Returned for any other server-side errors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `add_manual_competitor(primary_username: str, target_username: str)`
-   **Helper Module:** `simple_similar_profiles_api.py` (uses the `add_manual_profile` method)
-   **Database Table:** `similar_profiles`
-   **Storage:** Profile images are downloaded and stored in a Supabase bucket, then served via a CDN.
