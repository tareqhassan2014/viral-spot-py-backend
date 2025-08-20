# GET `/api/profile/{username}`

Retrieves detailed data for a specific user profile.

## Description

This endpoint fetches the profile information for a given username from the database. It is the primary way to get all the necessary data to display a user's profile page on the frontend. The data is transformed to a frontend-friendly format before being returned.

## Path Parameters

| Parameter  | Type   | Description                        |
| :--------- | :----- | :--------------------------------- |
| `username` | string | The Instagram username to look up. |

## Execution Flow

1.  **Receive Request**: The endpoint receives an HTTP GET request with a `username` in the URL path.
2.  **Query Database**: It queries the `primary_profiles` table to find a record where the `username` column matches the one from the request.
3.  **Handle Not Found**: If no record is found, the endpoint returns a `404 Not Found` error.
4.  **Transform Data**: If a profile is found, the raw data from the database is passed to a transformation function (`_transform_profile_for_frontend`). This function formats the data into a frontend-friendly structure, which might involve renaming fields, calculating new values, or nesting related data.
5.  **Send Response**: The transformed profile data is returned in the response with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# In ViralSpotAPI class in backend_api.py

async def get_profile(self, username: str):
    """Get profile data"""
    try:
        logger.info(f"Getting profile: {username}")

        response = self.supabase.client.table('primary_profiles').select('*').eq('username', username).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile = response.data[0]
        transformed_profile = self._transform_profile_for_frontend(profile)

        logger.info(f"✅ Found profile: {username}")

        return transformed_profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting profile {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint definition
@app.get("/api/profile/{username}")
async def get_profile(
    username: str = Path(..., description="Instagram username"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get profile data"""
    result = await api_instance.get_profile(username)
    return APIResponse(success=True, data=result)
```

**Line-by-Line Explanation:**

1.  **`async def get_profile(self, username: str):`**: Defines an asynchronous method `get_profile` that takes a `username` string as input.
2.  **`self.supabase.client.table('primary_profiles').select('*').eq('username', username).execute()`**: This line uses the Supabase client to build a SQL query. It's equivalent to `SELECT * FROM primary_profiles WHERE username = :username`.
3.  **`if not response.data:`**: Checks if the database query returned any data.
4.  **`raise HTTPException(status_code=404, ...)`**: If no data is returned, it raises an HTTP exception, which FastAPI translates into a 404 Not Found response.
5.  **`profile = response.data[0]`**: Retrieves the first record from the database response.
6.  **`transformed_profile = self._transform_profile_for_frontend(profile)`**: Calls a helper method to format the database record into the desired frontend structure.
7.  **`return transformed_profile`**: Returns the final transformed data.
8.  **`@app.get(...)`**: The FastAPI decorator that registers the `get_profile` function as an HTTP GET endpoint.
9.  **`username: str = Path(...)`**: Defines `username` as a path parameter.
10. **`api_instance: ViralSpotAPI = Depends(get_api)`**: A dependency injection that provides an instance of the `ViralSpotAPI` class to the endpoint.
11. **`result = await api_instance.get_profile(username)`**: Calls the main logic method.
12. **`return APIResponse(success=True, data=result)`**: Wraps the result in a standardized API response format.

### Nest.js (Mongoose)

```typescript
// In your profile.controller.ts

import { Controller, Get, Param, NotFoundException } from "@nestjs/common";
import { ProfileService } from "./profile.service";

@Controller("api/profile")
export class ProfileController {
    constructor(private readonly profileService: ProfileService) {}

    @Get(":username")
    async getProfile(@Param("username") username: string) {
        const profile = await this.profileService.getProfileByUsername(
            username
        );
        if (!profile) {
            throw new NotFoundException("Profile not found");
        }
        return { success: true, data: profile };
    }
}

// In your profile.service.ts

import { Injectable } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import {
    PrimaryProfile,
    PrimaryProfileDocument,
} from "./schemas/primary-profile.schema";

@Injectable()
export class ProfileService {
    constructor(
        @InjectModel(PrimaryProfile.name)
        private primaryProfileModel: Model<PrimaryProfileDocument>
    ) {}

    async getProfileByUsername(username: string): Promise<any> {
        const profile = await this.primaryProfileModel
            .findOne({ username })
            .exec();
        if (!profile) {
            return null;
        }
        return this.transformProfileForFrontend(profile);
    }

    private transformProfileForFrontend(profile: PrimaryProfileDocument): any {
        // This transformation logic should mirror the Python `_transform_profile_for_frontend`
        return {
            username: profile.username,
            profile_name: profile.profile_name || "",
            followers: profile.followers || 0,
            profile_image_url: profile.profile_image_url, // Assuming you handle CDN URLs
            bio: profile.bio || "",
            is_verified: profile.is_verified || false,
            // ... and so on for all other fields
        };
    }
}
```

## Responses

### Success: 200 OK

Returns the profile data in a structured format.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "username": "exampleuser",
        "profile_name": "Example User",
        "bio": "This is an example bio.",
        "follower_count": 12345,
        "profile_image_url": "https://example.com/profile.jpg",
        "is_verified": false,
        "account_type": "Public",
        "recent_reels": [
            // ... array of reel objects
        ]
    }
}
```

### Error: 404 Not Found

Returned if the requested `username` does not exist in the database.

**Example Response:**

```json
{
    "detail": "Profile not found"
}
```

### Error: 500 Internal Server Error

Returned if an unexpected error occurs on the server while processing the request.

**Example Response:**

```json
{
    "detail": "Internal server error message"
}
```

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_profile(username: str)`
-   **Database Table:** `primary_profiles`

The backend function `_transform_profile_for_frontend` is used to process the raw data from the database before it is sent to the client. This ensures that the data is in a consistent and easy-to-use format.
