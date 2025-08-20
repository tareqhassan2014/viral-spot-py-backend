# GET `/api/profile/{username}/similar-fast` ⚡

A new, faster endpoint for retrieving similar profiles.

## Description

This endpoint is an optimized alternative to the standard `/similar` endpoint. It is designed for high performance, using a dedicated caching layer and a streamlined database table (`similar_profiles`) to deliver results quickly. Profile images are served from a CDN for an even faster user experience.

## Path Parameters

| Parameter  | Type   | Description                                          |
| :--------- | :----- | :--------------------------------------------------- |
| `username` | string | The Instagram username to find similar profiles for. |

## Query Parameters

| Parameter       | Type    | Description                                                        | Default |
| :-------------- | :------ | :----------------------------------------------------------------- | :------ |
| `limit`         | integer | The number of similar profiles to return (between 1 and 80).       | `20`    |
| `force_refresh` | boolean | If `true`, bypasses the cache and fetches fresh data from the API. | `false` |

## Responses

### Success: 200 OK

Returns a list of similar profiles and a message indicating if the results were cached.

**Example Response:**

```json
{
    "success": true,
    "data": [
        {
            "username": "fastsimilaruser",
            "profile_name": "Fast Similar User"
            // ... other profile properties
        }
    ],
    "message": "Found 1 similar profiles (cached)"
}
```

### Error: 503 Service Unavailable

Returned if the `simple_similar_profiles_api` module is not available.

### Error: 500 Internal Server Error

Returned for any other server-side errors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_similar_profiles_fast(username: str, limit: int, force_refresh: bool)`
-   **Helper Module:** `simple_similar_profiles_api.py`
-   **Caching:** Results are cached for 24 hours to ensure fast subsequent requests.
