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

## Detailed Implementation Guide

### Python (FastAPI & Helper Module)

```python
# In backend_api.py

@app.get("/api/profile/{username}/similar-fast")
async def get_similar_profiles_fast(
    username: str = Path(..., description="Instagram username"),
    limit: int = Query(20, ...),
    force_refresh: bool = Query(False, ...)
):
    # ... error handling ...
    similar_api = get_similar_api()
    result = await similar_api.get_similar_profiles(username, limit, force_refresh)
    # ... response handling ...

# In simple_similar_profiles_api.py

class SimpleSimilarProfilesAPI:
    async def get_similar_profiles(self, username: str, limit: int = 20, force_refresh: bool = False) -> Dict:
        if not force_refresh:
            cached_profiles = await self._get_cached_similar_profiles(username, limit)
            if cached_profiles:
                return { 'success': True, 'data': cached_profiles, 'cached': True, ... }

        fresh_profiles = await self._fetch_and_cache_similar_profiles(username, limit)
        return { 'success': True, 'data': fresh_profiles, 'cached': False, ... }

    async def _get_cached_similar_profiles(self, username: str, limit: int) -> Optional[List[Dict]]:
        cutoff_time = datetime.now() - timedelta(hours=self.cache_duration_hours)
        response = self.supabase.client.table('similar_profiles').select(...)
            .eq('primary_username', username)
            .gte('created_at', cutoff_time.isoformat())
            .order('similarity_rank').limit(limit).execute()
        # ... transformation logic ...

    async def _fetch_and_cache_similar_profiles(self, username: str, limit: int) -> List[Dict]:
        similar_profiles_raw = await self._fetch_similar_profiles_with_retry(username, limit)
        processed_profiles = await self._process_similar_profiles_batch(...)
        return processed_profiles
```

**Line-by-Line Explanation:**

1.  **`get_similar_profiles_fast(...)`**: The main endpoint function in `backend_api.py`. It gets an instance of the `SimpleSimilarProfilesAPI` and calls its `get_similar_profiles` method.
2.  **`get_similar_profiles(...)` (in helper)**: This is the main logic handler. It first checks for cached data unless `force_refresh` is true.
3.  **`_get_cached_similar_profiles(...)`**: Queries the `similar_profiles` table for data that is newer than the `cache_duration_hours`.
4.  **`_fetch_and_cache_similar_profiles(...)`**: If no cache is found, this method is called. It fetches data from an external API, processes it (including downloading images), and saves it to the `similar_profiles` table for future requests.

### Nest.js (Mongoose)

```typescript
// In your profile.controller.ts

@Get(':username/similar-fast')
async getSimilarProfilesFast(
  @Param('username') username: string,
  @Query('limit') limit: number = 20,
  @Query('force_refresh') forceRefresh: boolean = false,
) {
  const result = await this.profileService.getSimilarProfilesFast(username, limit, forceRefresh);
  return { success: true, data: result.data, message: result.message };
}

// In your profile.service.ts

async getSimilarProfilesFast(username: string, limit: number, forceRefresh: boolean): Promise<any> {
  if (!forceRefresh) {
    const cached = await this.getCachedSimilarProfiles(username, limit);
    if (cached) {
      return { data: cached, message: 'Found cached profiles' };
    }
  }

  const fresh = await this.fetchAndCacheSimilarProfiles(username, limit);
  return { data: fresh, message: 'Found fresh profiles' };
}

private async getCachedSimilarProfiles(username: string, limit: number): Promise<any[] | null> {
  const cutoff = new Date();
  cutoff.setHours(cutoff.getHours() - 24); // 24-hour cache

  const cachedProfiles = await this.similarProfileModel
    .find({ primary_username: username, createdAt: { $gte: cutoff } })
    .sort({ similarity_rank: 1 })
    .limit(limit)
    .exec();

  if (cachedProfiles.length > 0) {
    // Transform data for frontend
    return cachedProfiles.map(p => ({ /* ... */ }));
  }
  return null;
}

private async fetchAndCacheSimilarProfiles(username: string, limit: number): Promise<any[]> {
  // 1. Call your external API to get a list of similar usernames
  const externalProfiles = await this.externalApiService.getSimilar(username, limit);

  // 2. Process in parallel: download images, save to your storage (e.g., S3),
  //    and create records in the `similar_profiles` collection.
  const processedProfiles = await Promise.all(
    externalProfiles.map(async (p, index) => {
      const imageUrl = await this.storageService.upload(p.profile_pic_url);
      const newProfile = new this.similarProfileModel({
        primary_username: username,
        similar_username: p.username,
        similar_name: p.full_name,
        profile_image_url: imageUrl,
        similarity_rank: index + 1,
      });
      return await newProfile.save();
    })
  );

  // 3. Transform and return
  return processedProfiles.map(p => ({ /* ... */ }));
}
```

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
