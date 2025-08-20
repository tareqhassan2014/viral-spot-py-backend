# GET `/api/profile/{username}/secondary`

Retrieves secondary (discovered) profile data.

## Description

This endpoint is used to fetch data for a secondary profile, which is a profile that has been discovered through the analysis of a primary profile. It's primarily intended to be used for displaying a loading state or a preview of a profile before the full data is fetched.

## Path Parameters

| Parameter  | Type   | Description                                     |
| :--------- | :----- | :---------------------------------------------- |
| `username` | string | The username of the secondary profile to fetch. |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a `username` in the URL path.
2.  **Query Database**: It queries the `secondary_profiles` table to find a record where the `username` column matches the one from the request.
3.  **Handle Not Found**: If no record is found, the endpoint returns a `404 Not Found` error.
4.  **Transform Data**: If a profile is found, the data is transformed into a frontend-friendly format.
5.  **Send Response**: The transformed profile data is returned in the response with a `200 OK` status.

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
