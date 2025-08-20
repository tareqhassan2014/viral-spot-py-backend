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

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `username` in the URL path.
2.  **Call Internal Method**: It directly calls an internal, private method (`_fetch_basic_profile_data`) from a helper module. This method is likely responsible for fetching raw data from an external API.
3.  **Bypass Transformations**: This endpoint intentionally bypasses the standard data transformation and validation layers of the main application.
4.  **Send Raw Response**: It returns the raw, untransformed data directly from the internal method, which is useful for debugging the underlying data source.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In backend_api.py

@app.get("/api/debug/profile/{username}")
async def debug_profile_fetch(username: str):
    """Debug endpoint to test profile fetching directly"""
    try:
        similar_api = get_similar_api()
        # Call the internal method directly for debugging
        profile_data = await similar_api._fetch_basic_profile_data(username)

        return APIResponse(
            success=True,
            data={ 'username': username, 'profile_data': profile_data, ... },
            message=f"Debug fetch for @{username}"
        )

    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

1.  **`similar_api = get_similar_api()`**: Gets an instance of the helper class.
2.  **`await similar_api._fetch_basic_profile_data(username)`**: The key part is that it calls a private internal method (`_fetch_basic_profile_data`). This method is responsible for making the raw call to the external Instagram API. The endpoint then returns this raw data directly, bypassing any of the usual transformation, validation, or database interaction logic.

### Nest.js (Mongoose)

```typescript
// In your debug.controller.ts

@Get('/profile/:username')
async debugProfileFetch(@Param('username') username: string) {
  // Inject the external API service directly
  const rawData = await this.externalApiService.getProfile(username);
  return { success: true, data: rawData, message: `Debug fetch for @${username}` };
}

// In your external-api.service.ts

async getProfile(username: string): Promise<any> {
  // This method would contain the logic to call the third-party
  // Instagram scraper API and return the raw JSON response.
  const response = await this.httpService.post(...).toPromise();
  return response.data;
}
```

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
