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

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `username` path parameter and optional `limit` and `force_refresh` query parameters.
2.  **Check Cache**: It first checks an in-memory cache (or a dedicated caching service like Redis) for the requested `username` and `limit`. If `force_refresh` is `true`, this step is skipped.
3.  **Return Cached Data**: If a valid, non-expired cache entry is found, the data is returned directly with a message indicating it was cached.
4.  **Query Database**: If the data is not in the cache or `force_refresh` is true, it queries the `similar_profiles` table. It filters for records matching the `primary_username` and limits the results.
5.  **Fetch from External API (if needed)**: If the `similar_profiles` table is empty or the data is stale, the system may call an external API to fetch a new list of similar profiles.
6.  **Update Database and Cache**: The new data is used to update the `similar_profiles` table and is stored in the cache with a 24-hour expiration.
7.  **Transform and Respond**: The data is formatted for the frontend and returned with a `200 OK` status.

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
