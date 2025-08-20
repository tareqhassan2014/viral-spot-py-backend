# POST `/api/profile/{primary_username}/add-competitor/{target_username}` ⚡

Adds a `target_username` as a competitor to a `primary_username`.

## Description

This endpoint is part of a new competitor analysis feature. It allows a user to manually add another profile as a competitor. The system will then fetch the basic information of the `target_username`, download their profile image to a local bucket, and store their profile in the `similar_profiles` table for fast access.

This is a key part of building a list of competitors for a user to track and analyze.

## Path Parameters

| Parameter          | Type   | Description                                          |
| :----------------- | :----- | :--------------------------------------------------- |
| `primary_username` | string | The username of the user who is adding a competitor. |
| `target_username`  | string | The username of the profile to add as a competitor.  |

## Execution Flow

1.  **Receive Request**: The endpoint receives a POST request with `primary_username` and `target_username` in the URL path.
2.  **Fetch Competitor Data**: It calls a helper module (`simple_similar_profiles_api`) to fetch the basic profile data for the `target_username` from an external API.
3.  **Handle Not Found**: If the `target_username` cannot be found by the external API, a `404 Not Found` error is returned.
4.  **Download Profile Image**: The system downloads the profile image of the `target_username` and stores it in a local storage bucket (e.g., Supabase Storage).
5.  **Add to Database**: It creates a new record in the `similar_profiles` table with the `primary_username`, `target_username`, and the path to the downloaded profile image.
6.  **Transform and Respond**: The data for the newly added competitor is formatted for the frontend and returned with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI & Helper Module)

```python
# In backend_api.py

@app.post("/api/profile/{primary_username}/add-competitor/{target_username}")
async def add_manual_competitor(primary_username: str, target_username: str):
    # ... error handling ...
    similar_api = get_similar_api()
    result = await similar_api.add_manual_profile(primary_username, target_username)
    # ... response handling ...

# In simple_similar_profiles_api.py

class SimpleSimilarProfilesAPI:
    async def add_manual_profile(self, primary_username: str, target_username: str) -> Dict:
        # ... check if profile already exists ...

        profile_data = await self._fetch_basic_profile_data(target_username)
        if not profile_data:
            # ... handle not found ...

        result = await self._process_single_similar_profile(
            primary_username, profile_data, 999, batch_id
        )
        # ... return success or error ...

    async def _process_single_similar_profile(self, primary_username: str, profile_raw: Dict, rank: int, batch_id: str) -> Dict:
        # ... download and upload image ...

        db_record = { ... }
        self.supabase.client.table('similar_profiles').upsert(db_record).execute()

        # ... return formatted response ...
```

**Line-by-Line Explanation:**

1.  **`add_manual_competitor(...)`**: The endpoint function which calls the helper module.
2.  **`add_manual_profile(...)`**: The main logic handler. It checks for an existing record, fetches the profile data from an external API, and then processes it.
3.  **`_fetch_basic_profile_data(...)`**: A helper method to call an external API to get the competitor's name and profile picture URL.
4.  **`_process_single_similar_profile(...)`**: This is where the core work happens. It downloads the profile image, uploads it to storage (like S3 or Supabase Storage), and then saves a record in the `similar_profiles` table with all the relevant info.

### Nest.js (Mongoose)

```typescript
// In your profile.controller.ts

@Post(':primary_username/add-competitor/:target_username')
async addManualCompetitor(
  @Param('primary_username') primaryUsername: string,
  @Param('target_username') targetUsername: string,
) {
  const result = await this.profileService.addManualCompetitor(primaryUsername, targetUsername);
  // ... handle success or errors ...
  return { success: true, data: result };
}

// In your profile.service.ts

async addManualCompetitor(primaryUsername: string, targetUsername: string): Promise<any> {
  const existing = await this.similarProfileModel.findOne({ primary_username: primaryUsername, similar_username: targetUsername }).exec();
  if (existing) {
    // Return existing data, maybe transformed
    return { ... };
  }

  // 1. Fetch from external API
  const externalProfile = await this.externalApiService.getProfile(targetUsername);
  if (!externalProfile) {
    throw new NotFoundException('Target profile not found');
  }

  // 2. Download and upload image to your storage (e.g., S3)
  const imageUrl = await this.storageService.upload(externalProfile.profile_pic_url);

  // 3. Save to database
  const newSimilarProfile = new this.similarProfileModel({
    primary_username: primaryUsername,
    similar_username: targetUsername,
    similar_name: externalProfile.full_name,
    profile_image_url: imageUrl,
    similarity_rank: 999, // High rank for manual adds
  });
  await newSimilarProfile.save();

  // 4. Return transformed data
  return { ... };
}
```

## Responses

### Success: 200 OK

Returns the profile data of the newly added competitor.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "username": "new_competitor",
        "profile_name": "New Competitor",
        "profile_image_url": "https://cdn.example.com/new_competitor.jpg"
        // ... other profile data
    },
    "message": "Successfully added @new_competitor to competitors for @primary_user"
}
```

### Error: 404 Not Found

Returned if the `target_username` cannot be found.

### Error: 503 Service Unavailable

Returned if the `simple_similar_profiles_api` module is not available.

### Error: 500 Internal Server Error

Returned for any other server-side errors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `add_manual_competitor(primary_username: str, target_username: str)`
-   **Helper Module:** `simple_similar_profiles_api.py` (uses the `add_manual_profile` method)
-   **Database Table:** `similar_profiles`
-   **Storage:** Profile images are downloaded and stored in a Supabase bucket, then served via a CDN.
