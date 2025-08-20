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
# Complete get_secondary_profile method in ViralSpotAPI class (lines 660-719)
async def get_secondary_profile(self, username: str):
    """Get secondary profile data for loading state"""
    try:
        logger.info(f"Getting secondary profile: {username}")

        response = self.supabase.client.table('secondary_profiles').select('''
            username,
            full_name,
            biography,
            followers_count,
            profile_pic_url,
            profile_pic_path,
            is_verified,
            primary_category,
            secondary_category,
            tertiary_category,
            estimated_account_type,
            created_at
        ''').eq('username', username).execute()

        if not response.data:
            return None

        profile = response.data[0]

        # Get the best available profile image URL
        profile_image_url = None
        profile_image_local = None

        if profile.get('profile_pic_path'):
            # Convert Supabase storage path to public URL
            profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_pic_path'])
            profile_image_local = profile_image_url  # Use the same URL for both fields
        elif profile.get('profile_pic_url'):
            # Fallback to original Instagram URL
            profile_image_url = profile['profile_pic_url']
            profile_image_local = profile_image_url

        # Transform to match frontend interface
        transformed_profile = {
            'username': profile.get('username', username),
            'profile_name': profile.get('full_name', username),
            'bio': profile.get('biography', ''),
            'followers': profile.get('followers_count', 0),
            'profile_image_url': profile_image_url,
            'profile_image_local': profile_image_local,
            'is_verified': profile.get('is_verified', False),
            'primary_category': profile.get('primary_category'),
            'account_type': profile.get('estimated_account_type', 'Personal'),
            'url': f"https://instagram.com/{username}",
            'reels_count': 0,  # Unknown for secondary profiles
            'average_views': 0,  # Unknown for secondary profiles
            'is_secondary': True,  # Flag to indicate this is secondary data
            'created_at': profile.get('created_at')
        }

        logger.info(f"✅ Found secondary profile: {username} with image URL: {profile_image_url}")

        return transformed_profile

    except Exception as e:
        logger.error(f"❌ Error getting secondary profile {username}: {e}")
        return None

# FastAPI endpoint definition (lines 1248-1258)
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

1.  **`async def get_secondary_profile(self, username: str):`**: Defines an asynchronous method to retrieve secondary profile data, typically used for loading states or profile previews.

2.  **`logger.info(f"Getting secondary profile: {username}")`**: Logs the start of the secondary profile retrieval for monitoring and debugging.

3.  **Comprehensive Field Selection**: The query selects 12 specific fields from the `secondary_profiles` table:

    -   **Basic Info**: `username`, `full_name`, `biography`
    -   **Metrics**: `followers_count`
    -   **Images**: `profile_pic_url`, `profile_pic_path`
    -   **Verification**: `is_verified`
    -   **Categories**: `primary_category`, `secondary_category`, `tertiary_category`
    -   **Classification**: `estimated_account_type`
    -   **Metadata**: `created_at`

4.  **`.eq('username', username)`**: Filters the secondary profiles table to find the specific username requested.

5.  **`if not response.data: return None`**: Returns `None` if no secondary profile is found, which the endpoint handler converts to a 404 error.

6.  **`profile = response.data[0]`**: Extracts the first (and should be only) matching profile record.

7.  **Smart Image URL Handling**: Implements a fallback strategy for profile images:

    -   **Primary**: Uses Supabase Storage CDN URL if `profile_pic_path` exists
    -   **Fallback**: Uses original Instagram URL if `profile_pic_url` exists
    -   **Consistent Fields**: Sets both `profile_image_url` and `profile_image_local` for frontend compatibility

8.  **Supabase Storage Integration**:

    ```python
    profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_pic_path'])
    ```

    Converts internal storage paths to public CDN URLs for optimized image delivery.

9.  **Frontend-Compatible Transformation**: Creates a response object that matches the primary profile interface:

    -   Maps `full_name` to `profile_name`
    -   Maps `followers_count` to `followers`
    -   Maps `biography` to `bio`
    -   Maps `estimated_account_type` to `account_type`
    -   Adds computed fields like `url` and secondary-specific flags

10. **Secondary Profile Indicators**: Adds fields that distinguish secondary profiles:

    -   `reels_count: 0` (unknown for secondary profiles)
    -   `average_views: 0` (unknown for secondary profiles)
    -   `is_secondary: True` (flag for frontend logic)

11. **Success Logging**: Logs successful retrieval with image URL information for monitoring.

12. **Error Handling**: Comprehensive exception handling with detailed logging and graceful `None` return.

### Key Implementation Features

**1. Loading State Optimization**: Designed specifically for providing quick profile previews while full profile data is being processed.

**2. Dual Image Source Support**: Handles both Supabase Storage CDN URLs and original Instagram URLs with intelligent fallback.

**3. Frontend Interface Compatibility**: Response structure matches primary profiles for seamless frontend integration.

**4. Category Information**: Includes content categorization data for profile classification and filtering.

**5. Secondary Profile Distinction**: Clear indicators that this is preliminary/discovered data, not complete profile information.

**6. Comprehensive Logging**: Detailed logging for monitoring secondary profile usage and debugging issues.

**7. Graceful Degradation**: Returns `None` instead of throwing exceptions, allowing the endpoint to handle 404 responses appropriately.

### Nest.js (Mongoose)

```typescript
// In your profile.controller.ts
import {
    Controller,
    Get,
    Param,
    Logger,
    NotFoundException,
} from "@nestjs/common";
import { ProfileService } from "./profile.service";

@Controller("api/profile")
export class ProfileController {
    private readonly logger = new Logger(ProfileController.name);

    constructor(private readonly profileService: ProfileService) {}

    @Get(":username/secondary")
    async getSecondaryProfile(@Param("username") username: string) {
        this.logger.log(`Getting secondary profile: ${username}`);

        const profile = await this.profileService.getSecondaryProfile(username);
        if (!profile) {
            throw new NotFoundException("Secondary profile not found");
        }

        this.logger.log(`✅ Found secondary profile: ${username}`);
        return { success: true, data: profile };
    }
}

// In your profile.service.ts
import { Injectable, Logger } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import {
    SecondaryProfile,
    SecondaryProfileDocument,
} from "./schemas/secondary-profile.schema";

@Injectable()
export class ProfileService {
    private readonly logger = new Logger(ProfileService.name);

    constructor(
        @InjectModel(SecondaryProfile.name)
        private secondaryProfileModel: Model<SecondaryProfileDocument>
    ) {}

    async getSecondaryProfile(username: string): Promise<any> {
        try {
            const profile = await this.secondaryProfileModel
                .findOne({ username })
                .lean()
                .exec();

            if (!profile) {
                return null;
            }

            return this.transformSecondaryProfile(profile);
        } catch (error) {
            this.logger.error(
                `❌ Error getting secondary profile ${username}: ${error.message}`
            );
            return null;
        }
    }

    private transformSecondaryProfile(profile: any): any {
        // Smart image URL handling with fallback strategy
        let profile_image_url = null;
        let profile_image_local = null;

        if (profile.profile_pic_path) {
            // Convert to Supabase Storage CDN URL
            profile_image_url = `https://cdn.supabase.co/storage/v1/object/public/profile-images/${profile.profile_pic_path}`;
            profile_image_local = profile_image_url;
        } else if (profile.profile_pic_url) {
            // Fallback to original Instagram URL
            profile_image_url = profile.profile_pic_url;
            profile_image_local = profile_image_url;
        }

        // Transform to match frontend interface (same as primary profiles)
        return {
            username: profile.username || "",
            profile_name: profile.full_name || profile.username || "",
            bio: profile.biography || "",
            followers: profile.followers_count || 0,
            profile_image_url: profile_image_url,
            profile_image_local: profile_image_local,
            is_verified: profile.is_verified || false,
            primary_category: profile.primary_category,
            secondary_category: profile.secondary_category,
            tertiary_category: profile.tertiary_category,
            account_type: profile.estimated_account_type || "Personal",
            url: `https://instagram.com/${profile.username}`,

            // Secondary profile specific fields
            reels_count: 0, // Unknown for secondary profiles
            average_views: 0, // Unknown for secondary profiles
            is_secondary: true, // Flag to indicate this is secondary data
            created_at: profile.created_at,
        };
    }
}

// Secondary Profile Mongoose Schema
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document } from "mongoose";

export type SecondaryProfileDocument = SecondaryProfile & Document;

@Schema({ timestamps: true, collection: "secondary_profiles" })
export class SecondaryProfile {
    @Prop({ required: true, unique: true, index: true })
    username: string;

    @Prop()
    full_name?: string;

    @Prop()
    biography?: string;

    @Prop({ type: Number, default: 0 })
    followers_count: number;

    @Prop()
    profile_pic_url?: string;

    @Prop()
    profile_pic_path?: string;

    @Prop({ type: Boolean, default: false })
    is_verified: boolean;

    @Prop()
    primary_category?: string;

    @Prop()
    secondary_category?: string;

    @Prop()
    tertiary_category?: string;

    @Prop({ default: "Personal" })
    estimated_account_type: string;

    @Prop({ type: Date })
    created_at?: Date;

    // Additional fields for secondary profile discovery
    @Prop()
    discovered_from?: string; // Username that led to this discovery

    @Prop({ type: Date })
    last_updated?: Date;

    @Prop({ type: Boolean, default: false })
    promoted_to_primary: boolean; // Flag if this became a primary profile
}

export const SecondaryProfileSchema =
    SchemaFactory.createForClass(SecondaryProfile);

// Create indexes for efficient querying
SecondaryProfileSchema.index({ username: 1 });
SecondaryProfileSchema.index({ primary_category: 1 });
SecondaryProfileSchema.index({ estimated_account_type: 1 });
SecondaryProfileSchema.index({ created_at: -1 });
SecondaryProfileSchema.index({ discovered_from: 1 });
```

### Key Differences in Nest.js Implementation

1. **Comprehensive Schema Definition**: Complete Mongoose schema for secondary profiles with proper indexing and field types.

2. **Smart Image URL Handling**: Implements the same dual-source image strategy as the Python implementation:

    - **Primary**: Supabase Storage CDN URLs for optimized delivery
    - **Fallback**: Original Instagram URLs when CDN paths aren't available

3. **Frontend Interface Compatibility**: Transformation method ensures the response structure matches primary profiles for seamless frontend integration.

4. **Secondary Profile Indicators**: Includes specific fields that distinguish secondary profiles:

    - `is_secondary: true` flag for frontend logic
    - `reels_count: 0` and `average_views: 0` (unknown metrics)
    - Discovery metadata for tracking profile relationships

5. **Performance Optimization**: Uses `lean()` queries for better performance when transforming data.

6. **Comprehensive Indexing**: Strategic database indexes on key fields:

    - `username` (unique, primary lookup)
    - `primary_category` (filtering)
    - `estimated_account_type` (classification)
    - `created_at` (temporal queries)
    - `discovered_from` (relationship tracking)

7. **Discovery Tracking**: Additional fields for tracking how secondary profiles were discovered and their lifecycle:

    - `discovered_from`: Source username that led to discovery
    - `promoted_to_primary`: Flag for profiles that became primary
    - `last_updated`: Timestamp for data freshness

8. **Error Handling**: Comprehensive exception handling with detailed logging, matching the Python implementation's approach.

## Responses

### Success: 200 OK

Returns a transformed secondary profile object with comprehensive information for loading states and profile previews.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "username": "discovered_creator",
        "profile_name": "Creative Designer",
        "bio": "🎨 Digital artist & UI/UX designer | Creating beautiful interfaces | Available for freelance work",
        "followers": 45600,
        "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/discovered_creator_profile.jpg",
        "profile_image_local": "https://cdn.supabase.co/storage/v1/object/public/profile-images/discovered_creator_profile.jpg",
        "is_verified": false,
        "primary_category": "Art & Design",
        "secondary_category": "Digital Art",
        "tertiary_category": "UI/UX Design",
        "account_type": "Business Page",
        "url": "https://instagram.com/discovered_creator",
        "reels_count": 0,
        "average_views": 0,
        "is_secondary": true,
        "created_at": "2024-01-12T08:30:00Z"
    }
}
```

**Key Response Features:**

-   **Frontend Interface Compatibility**: Response structure matches primary profiles for seamless integration
-   **Loading State Optimization**: Provides essential profile information quickly while full data is processed
-   **CDN Image URLs**: Optimized Supabase Storage URLs for fast image loading
-   **Category Information**: Content classification data for profile understanding
-   **Secondary Profile Indicators**: Clear flags (`is_secondary: true`, zero metrics) distinguishing from primary profiles
-   **Complete Profile Data**: All essential fields needed for profile previews and loading states

### Response Field Details:

-   **`username`**: Instagram username (unique identifier)
-   **`profile_name`**: Display name or full name from Instagram
-   **`bio`**: Profile biography/description text
-   **`followers`**: Follower count at time of discovery
-   **`profile_image_url`**: CDN-optimized profile image URL
-   **`profile_image_local`**: Same as profile_image_url for frontend compatibility
-   **`is_verified`**: Instagram verification status
-   **`primary_category`**: Top-level content category classification
-   **`secondary_category`**: More specific content subcategory
-   **`tertiary_category`**: Highly specific niche classification
-   **`account_type`**: Estimated account type (Personal, Business Page, Influencer, etc.)
-   **`url`**: Direct Instagram profile URL
-   **`reels_count`**: Always 0 (unknown for secondary profiles)
-   **`average_views`**: Always 0 (unknown for secondary profiles)
-   **`is_secondary`**: Always true (flag for frontend logic)
-   **`created_at`**: Timestamp when profile was discovered

### Use Cases:

1. **Loading States**: Display profile information while full profile data is being fetched
2. **Profile Previews**: Show discovered profiles before they become primary profiles
3. **Quick Profile Cards**: Display basic profile information in lists or grids
4. **Profile Discovery**: Show profiles found through analysis of primary profiles
5. **Competitor Research**: Preview competitor profiles before detailed analysis

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
