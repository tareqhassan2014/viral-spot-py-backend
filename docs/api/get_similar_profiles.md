# GET `/api/profile/{username}/similar`

Gets a list of similar profiles for a specific user.

## Description

This endpoint is used to suggest other profiles that a user might be interested in, based on a similarity ranking. It works by first finding the primary profile for the given `username` and then retrieving a list of secondary profiles that were discovered and ranked as similar.

## Path Parameters

| Parameter  | Type   | Description                                          |
| :--------- | :----- | :--------------------------------------------------- |
| `username` | string | The Instagram username to find similar profiles for. |

## Query Parameters

| Parameter | Type    | Description                                       | Default |
| :-------- | :------ | :------------------------------------------------ | :------ |
| `limit`   | integer | The maximum number of similar profiles to return. | `20`    |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `username` path parameter and an optional `limit` query parameter.
2.  **Find Primary Profile**: It first queries the `primary_profiles` table to find the `id` of the profile matching the `username`. If not found, it returns a `404` error.
3.  **Find Similar Profiles**: Using the `id` of the primary profile, it queries the `secondary_profiles` table, filtering for records where `discovered_by_id` matches.
4.  **Apply Limit**: The query is limited to the number specified by the `limit` parameter.
5.  **Execute Query**: The query is executed to fetch the list of similar (secondary) profiles.
6.  **Transform Data**: The data for each similar profile is formatted for the frontend.
7.  **Send Response**: It returns the list of transformed similar profiles with a `200 OK` status.

## Responses

### Success: 200 OK

Returns a list of similar profiles, ordered by their similarity rank.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "primary_profile": {
            // ... data for the primary profile
        },
        "similar_profiles": [
            {
                "username": "similaruser1",
                "full_name": "Similar User One",
                "followers_count": 54321,
                "similarity_rank": 1
                // ... other profile properties
            }
        ],
        "total": 1,
        "limit": 20
    }
}
```

### Error: 404 Not Found

Returned if the primary profile for the `username` is not found.

### Error: 500 Internal Server Error

Returned for any other server-side errors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_similar_profiles(username: str, limit: int)`
-   **Database Tables:**
    -   `primary_profiles`: Used to find the ID of the initial profile.
    -   `secondary_profiles`: Used to find the profiles linked by the `discovered_by_id` field.
