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

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In ViralSpotAPI class in backend_api.py

async def get_secondary_profile(self, username: str):
    """Get secondary profile data for loading state"""
    try:
        response = self.supabase.client.table('secondary_profiles').select(
            'username, full_name, biography, followers_count, profile_pic_url, ...'
        ).eq('username', username).execute()

        if not response.data:
            return None

        profile = response.data[0]
        # ... transformation logic to format for frontend ...
        return transformed_profile

    except Exception as e:
        logger.error(f"❌ Error getting secondary profile {username}: {e}")
        return None

# FastAPI endpoint definition
@app.get("/api/profile/{username}/secondary")
async def get_secondary_profile(
    username: str = Path(..., description="Instagram username"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get secondary profile data for loading state"""
    result = await api_instance.get_secondary_profile(username)
    if result:
        return APIResponse(success=True, data=result)
    else:
        raise HTTPException(status_code=404, detail="Secondary profile not found")
```

**Line-by-Line Explanation:**

1.  **`response = self.supabase.client.table('secondary_profiles')...`**: Queries the `secondary_profiles` table for a record matching the `username`.
2.  **`if not response.data: return None`**: If no profile is found, it returns `None`. The endpoint handler will turn this into a 404.
3.  **`profile = response.data[0]`**: Gets the first record.
4.  **`return transformed_profile`**: Returns the formatted data.

### Nest.js (Mongoose)

```typescript
// In your profile.controller.ts

@Get(':username/secondary')
async getSecondaryProfile(@Param('username') username: string) {
  const profile = await this.profileService.getSecondaryProfile(username);
  if (!profile) {
    throw new NotFoundException('Secondary profile not found');
  }
  return { success: true, data: profile };
}

// In your profile.service.ts

async getSecondaryProfile(username: string): Promise<any> {
  const profile = await this.secondaryProfileModel.findOne({ username }).exec();
  if (!profile) {
    return null;
  }
  return this.transformSecondaryProfile(profile);
}

private transformSecondaryProfile(profile: SecondaryProfileDocument): any {
  // Transformation logic similar to the other profile types
  return {
    username: profile.username,
    profile_name: profile.full_name || '',
    // ... etc.
  };
}
```

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
