# GET `/api/profile/{username}/secondary`

Retrieves secondary (discovered) profile data.

## Description

This endpoint is used to fetch data for a secondary profile, which is a profile that has been discovered through the analysis of a primary profile. It's primarily intended to be used for displaying a loading state or a preview of a profile before the full data is fetched.

## Path Parameters

| Parameter  | Type   | Description                                     |
| :--------- | :----- | :---------------------------------------------- |
| `username` | string | The username of the secondary profile to fetch. |

## Responses

### Success: 200 OK

Returns a transformed profile object with key information.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "username": "secondaryuser",
        "profile_name": "Secondary User",
        "bio": "A discovered profile.",
        "follower_count": 9876,
        "profile_image_url": "https://example.com/secondary.jpg",
        "is_verified": true
    }
}
```

### Error: 404 Not Found

Returned if the secondary profile with the given `username` is not found.

**Example Response:**

```json
{
    "detail": "Secondary profile not found"
}
```

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_secondary_profile(username: str)`
-   **Database Table:** `secondary_profiles`
