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
