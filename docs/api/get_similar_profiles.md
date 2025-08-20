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

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In ViralSpotAPI class in backend_api.py

async def get_similar_profiles(self, username: str, limit: int = 20):
    """Get similar profiles for a username"""
    try:
        logger.info(f"Getting similar profiles for: {username}")

        primary_response = self.supabase.client.table('primary_profiles').select('id').eq('username', username).execute()

        if not primary_response.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        primary_id = primary_response.data[0]['id']

        similar_response = self.supabase.client.table('secondary_profiles').select(
            'username, full_name, followers_count, profile_pic_url, profile_pic_path, similarity_rank'
        ).eq('discovered_by_id', primary_id).order('similarity_rank').limit(limit).execute()

        similar_profiles = []
        for profile in similar_response.data:
            # ... transformation logic for each similar profile ...
            similar_profiles.append({ ... })

        # ... logic to build the final response object ...

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting similar profiles for {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint definition
@app.get("/api/profile/{username}/similar")
async def get_similar_profiles(
    username: str = Path(..., description="Instagram username"),
    limit: int = Query(20, ge=1, le=100),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get similar profiles for a username"""
    result = await api_instance.get_similar_profiles(username, limit)
    return result
```

**Line-by-Line Explanation:**

1.  **`primary_response = ...`**: Finds the primary profile to get its `id`.
2.  **`similar_response = ...`**: Queries the `secondary_profiles` table for all profiles that were `discovered_by_id` of the primary profile.
3.  **`.order('similarity_rank').limit(limit)`**: Sorts the results by rank and limits them.
4.  **`for profile in similar_response.data:`**: Loops through the results to transform each one.

### Nest.js (Mongoose)

```typescript
// In your profile.controller.ts

@Get(':username/similar')
async getSimilarProfiles(
  @Param('username') username: string,
  @Query('limit') limit: number = 20,
) {
  const result = await this.profileService.getSimilarProfiles(username, limit);
  if (!result) {
    throw new NotFoundException('Primary profile not found');
  }
  return { success: true, data: result };
}

// In your profile.service.ts

async getSimilarProfiles(username: string, limit: number): Promise<any> {
  const primaryProfile = await this.primaryProfileModel.findOne({ username }).exec();
  if (!primaryProfile) {
    return null;
  }

  const similarProfiles = await this.secondaryProfileModel
    .find({ discovered_by_id: primaryProfile._id })
    .sort({ similarity_rank: 1 })
    .limit(limit)
    .exec();

  // You would have a transformation method for secondary profiles
  const transformedProfiles = similarProfiles.map(p => this.transformSecondaryProfile(p));

  return {
      similar_profiles: transformedProfiles,
      // ... other data for the response
  };
}
```

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
