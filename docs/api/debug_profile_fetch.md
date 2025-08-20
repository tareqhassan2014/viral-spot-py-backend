# GET `/api/debug/profile/{username}` 🐛

A debug endpoint to get raw or extended data for a profile.

## Description

This endpoint is intended for internal testing and development purposes only. It provides a way to directly test the profile fetching functionality of the `simple_similar_profiles_api` module.

It calls the internal `_fetch_basic_profile_data` method, which is responsible for fetching the basic data of a profile. This is useful for quickly verifying that the profile fetching mechanism is working as expected without having to go through the full application flow.

**Note:** This endpoint should not be used by the frontend in a production environment.

## Path Parameters

| Parameter  | Type   | Description                          |
| :--------- | :----- | :----------------------------------- |
| `username` | string | The username of the profile to test. |

## Responses

### Success: 200 OK

Returns the raw profile data fetched by the underlying API.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "username": "testuser",
        "profile_data": {
            "full_name": "Test User",
            "follower_count": 100,
            "biography": "This is a test account."
            // ... other raw profile data
        },
        "api_available": true
    },
    "message": "Debug fetch for @testuser"
}
```

### Error: 503 Service Unavailable

Returned if the `simple_similar_profiles_api` module is not available.

### Error: 500 Internal Server Error

Returned for any other server-side errors during the fetch process.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `debug_profile_fetch(username: str)`
-   **Internal Method:** This endpoint directly calls the `_fetch_basic_profile_data` method of the `similar_api` object.
