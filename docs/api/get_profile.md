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
# Main get_profile method in ViralSpotAPI class (lines 637-658)
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

# FastAPI endpoint definition (lines 1217-1224)
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

2.  **`logger.info(f"Getting profile: {username}")`**: Logs the incoming request for debugging and monitoring purposes.

3.  **`self.supabase.client.table('primary_profiles').select('*').eq('username', username).execute()`**: This line uses the Supabase client to build a SQL query. It's equivalent to `SELECT * FROM primary_profiles WHERE username = :username`. The query retrieves all 70+ columns from the primary_profiles table.

4.  **`if not response.data:`**: Checks if the database query returned any data. This handles the case where the username doesn't exist in the database.

5.  **`raise HTTPException(status_code=404, detail="Profile not found")`**: If no data is returned, it raises an HTTP exception, which FastAPI translates into a 404 Not Found response.

6.  **`profile = response.data[0]`**: Retrieves the first record from the database response. Since username is unique, there should only be one result.

7.  **`transformed_profile = self._transform_profile_for_frontend(profile)`**: Calls a helper method to format the database record into the desired frontend structure. This method handles CDN URLs, field mapping, and data formatting.

8.  **`logger.info(f"✅ Found profile: {username}")`**: Logs successful profile retrieval for monitoring.

9.  **`return transformed_profile`**: Returns the final transformed data to the endpoint.

10. **Exception Handling**: The method has two levels of exception handling - it re-raises HTTPExceptions (like 404) and catches all other exceptions to return a 500 error.

11. **`@app.get("/api/profile/{username}")`**: The FastAPI decorator that registers the `get_profile` function as an HTTP GET endpoint with a path parameter.

12. **`username: str = Path(..., description="Instagram username")`**: Defines `username` as a required path parameter with validation and documentation.

13. **`api_instance: ViralSpotAPI = Depends(get_api)`**: A dependency injection that provides an instance of the `ViralSpotAPI` class to the endpoint.

14. **`return APIResponse(success=True, data=result)`**: Wraps the result in a standardized API response format with success flag.

### Profile Transformation Method

The `_transform_profile_for_frontend()` method (lines 468-491) handles the complex data transformation:

```python
def _transform_profile_for_frontend(self, profile_item: Dict) -> Dict:
    """Transform Supabase profile to frontend format"""
    # Get profile image URL - prioritize Supabase Storage CDN
    profile_image_url = None
    if profile_item.get('profile_image_path'):
        profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile_item['profile_image_path'])
    elif profile_item.get('profile_image_url'):
        profile_image_url = profile_item['profile_image_url']

    return {
        'username': profile_item['username'],
        'profile_name': profile_item.get('profile_name', ''),
        'followers': profile_item.get('followers', 0),
        'profile_image_url': profile_image_url,
        'profile_image_local': profile_image_url,  # Alias for compatibility
        'bio': profile_item.get('bio', ''),
        'is_verified': profile_item.get('is_verified', False),
        'is_business_account': profile_item.get('is_business_account', False),
        'reels_count': profile_item.get('total_reels', 0),
        'average_views': profile_item.get('mean_views', 0),
        'primary_category': profile_item.get('profile_primary_category'),
        'profile_type': 'primary',
        'url': f"https://www.instagram.com/{profile_item['username']}/"
    }
```

**Key Transformation Features:**

1. **CDN URL Handling**: Prioritizes Supabase Storage CDN URLs over external URLs for better performance and reliability.

2. **Field Mapping**: Maps database field names to frontend-expected field names (e.g., `total_reels` → `reels_count`).

3. **Default Values**: Provides sensible defaults for missing or null values to prevent frontend errors.

4. **URL Generation**: Automatically generates the Instagram profile URL.

5. **Type Identification**: Adds a `profile_type: 'primary'` field to distinguish from secondary profiles.

### Database Schema Context

The `primary_profiles` table contains 70+ columns including:

**Core Profile Data:**

-   `username`, `profile_name`, `bio`, `followers`, `posts_count`
-   `is_verified`, `is_business_account`, `account_type`
-   `profile_image_url`, `profile_image_path`, `hd_profile_image_path`

**Analytics & Metrics:**

-   `total_reels`, `median_views`, `mean_views`, `std_views`
-   `total_views`, `total_likes`, `total_comments`

**Categorization:**

-   `profile_primary_category`, `profile_secondary_category`, `profile_tertiary_category`
-   `profile_categorization_confidence`, `account_type_confidence`

**Similar Accounts (Denormalized):**

-   `similar_account1` through `similar_account20`

**Metadata:**

-   `language`, `content_type`, `last_full_scrape`, `analysis_timestamp`
-   `created_at`, `updated_at`

### Nest.js (Mongoose)

```typescript
// DTO for path parameter validation
import { IsString, IsNotEmpty, Matches } from "class-validator";

export class GetProfileParamsDto {
    @IsString()
    @IsNotEmpty()
    @Matches(/^[a-zA-Z0-9._]+$/, {
        message:
            "Username must contain only letters, numbers, dots, and underscores",
    })
    username: string;
}

// In your profile.controller.ts
import {
    Controller,
    Get,
    Param,
    NotFoundException,
    Logger,
} from "@nestjs/common";
import { ProfileService } from "./profile.service";
import { GetProfileParamsDto } from "./dto/get-profile-params.dto";

@Controller("api/profile")
export class ProfileController {
    private readonly logger = new Logger(ProfileController.name);

    constructor(private readonly profileService: ProfileService) {}

    @Get(":username")
    async getProfile(@Param() params: GetProfileParamsDto) {
        this.logger.log(`Getting profile: ${params.username}`);

        const profile = await this.profileService.getProfileByUsername(
            params.username
        );

        if (!profile) {
            this.logger.warn(`Profile not found: ${params.username}`);
            throw new NotFoundException("Profile not found");
        }

        this.logger.log(`✅ Found profile: ${params.username}`);
        return { success: true, data: profile };
    }
}

// In your profile.service.ts
import { Injectable, Logger } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import {
    PrimaryProfile,
    PrimaryProfileDocument,
} from "./schemas/primary-profile.schema";

@Injectable()
export class ProfileService {
    private readonly logger = new Logger(ProfileService.name);

    constructor(
        @InjectModel(PrimaryProfile.name)
        private primaryProfileModel: Model<PrimaryProfileDocument>
    ) {}

    async getProfileByUsername(username: string): Promise<any> {
        try {
            // Query MongoDB for the profile
            const profile = await this.primaryProfileModel
                .findOne({ username })
                .lean() // Use lean() for better performance when we don't need Mongoose document features
                .exec();

            if (!profile) {
                return null;
            }

            // Transform the profile data for frontend consumption
            return this.transformProfileForFrontend(profile);
        } catch (error) {
            this.logger.error(
                `❌ Error getting profile ${username}: ${error.message}`
            );
            throw error;
        }
    }

    private transformProfileForFrontend(profile: any): any {
        // Handle profile image URL - prioritize CDN URLs
        let profile_image_url = null;
        if (profile.profile_image_path) {
            // If using a CDN service like AWS CloudFront, Cloudinary, etc.
            profile_image_url = `${process.env.CDN_BASE_URL}/profile-images/${profile.profile_image_path}`;
        } else if (profile.profile_image_url) {
            profile_image_url = profile.profile_image_url;
        }

        // Transform to match the Python implementation exactly
        return {
            username: profile.username,
            profile_name: profile.profile_name || "",
            followers: profile.followers || 0,
            profile_image_url: profile_image_url,
            profile_image_local: profile_image_url, // Alias for compatibility
            bio: profile.bio || "",
            is_verified: profile.is_verified || false,
            is_business_account: profile.is_business_account || false,
            reels_count: profile.total_reels || 0,
            average_views: profile.mean_views || 0,
            primary_category: profile.profile_primary_category,
            profile_type: "primary",
            url: `https://www.instagram.com/${profile.username}/`,

            // Additional fields that might be useful for the frontend
            posts_count: profile.posts_count || 0,
            account_type: profile.account_type || "Personal",
            language: profile.language || "en",
            content_type: profile.content_type || "entertainment",

            // Analytics data
            median_views: profile.median_views || 0,
            total_views: profile.total_views || 0,
            total_likes: profile.total_likes || 0,
            total_comments: profile.total_comments || 0,

            // Categorization
            secondary_category: profile.profile_secondary_category,
            tertiary_category: profile.profile_tertiary_category,
            categorization_confidence:
                profile.profile_categorization_confidence || 0.5,

            // Similar accounts (first 10 for performance)
            similar_accounts: [
                profile.similar_account1,
                profile.similar_account2,
                profile.similar_account3,
                profile.similar_account4,
                profile.similar_account5,
                profile.similar_account6,
                profile.similar_account7,
                profile.similar_account8,
                profile.similar_account9,
                profile.similar_account10,
            ].filter((account) => account), // Remove null/undefined values

            // Timestamps
            last_full_scrape: profile.last_full_scrape,
            analysis_timestamp: profile.analysis_timestamp,
            created_at: profile.created_at,
            updated_at: profile.updated_at,
        };
    }

    // Additional helper method for getting profile statistics
    async getProfileStats(username: string): Promise<any> {
        const profile = await this.primaryProfileModel
            .findOne({ username })
            .select(
                "total_reels median_views mean_views total_views total_likes total_comments followers"
            )
            .lean()
            .exec();

        if (!profile) {
            return null;
        }

        // Calculate engagement rate
        const engagementRate =
            profile.followers > 0
                ? (
                      ((profile.total_likes + profile.total_comments) /
                          profile.total_views) *
                      100
                  ).toFixed(2)
                : 0;

        return {
            username,
            total_content: profile.total_reels || 0,
            avg_views: profile.mean_views || 0,
            median_views: profile.median_views || 0,
            total_engagement:
                (profile.total_likes || 0) + (profile.total_comments || 0),
            engagement_rate: parseFloat(engagementRate),
            followers: profile.followers || 0,
        };
    }
}

// Enhanced Mongoose Schema (in schemas/primary-profile.schema.ts)
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Schema as MongooseSchema } from "mongoose";

export type PrimaryProfileDocument = PrimaryProfile & Document;

@Schema({ timestamps: true, collection: "primary_profiles" })
export class PrimaryProfile {
    @Prop({ type: String, required: true, unique: true, index: true })
    username: string;

    @Prop({ type: String })
    profile_name: string;

    @Prop({ type: String })
    bio: string;

    @Prop({ type: Number, default: 0, index: true })
    followers: number;

    @Prop({ type: Number, default: 0 })
    posts_count: number;

    @Prop({ type: Boolean, default: false })
    is_verified: boolean;

    @Prop({ type: Boolean, default: false })
    is_business_account: boolean;

    @Prop({ type: String })
    profile_url: string;

    @Prop({ type: String })
    profile_image_url: string;

    @Prop({ type: String })
    profile_image_path: string;

    @Prop({ type: String })
    hd_profile_image_path: string;

    @Prop({
        type: String,
        enum: ["Influencer", "Theme Page", "Business Page", "Personal"],
        default: "Personal",
    })
    account_type: string;

    @Prop({ type: String, default: "en" })
    language: string;

    @Prop({ type: String, default: "entertainment" })
    content_type: string;

    // Metrics
    @Prop({ type: Number, default: 0, index: true })
    total_reels: number;

    @Prop({ type: Number, default: 0, index: true })
    median_views: number;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0 })
    mean_views: number;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0 })
    std_views: number;

    @Prop({ type: Number, default: 0 })
    total_views: number;

    @Prop({ type: Number, default: 0 })
    total_likes: number;

    @Prop({ type: Number, default: 0 })
    total_comments: number;

    // Categorization
    @Prop({ type: String, index: true })
    profile_primary_category: string;

    @Prop({ type: String })
    profile_secondary_category: string;

    @Prop({ type: String })
    profile_tertiary_category: string;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
    profile_categorization_confidence: number;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
    account_type_confidence: number;

    // Similar accounts (denormalized for performance)
    @Prop({ type: String })
    similar_account1: string;

    @Prop({ type: String })
    similar_account2: string;

    @Prop({ type: String })
    similar_account3: string;

    @Prop({ type: String })
    similar_account4: string;

    @Prop({ type: String })
    similar_account5: string;

    @Prop({ type: String })
    similar_account6: string;

    @Prop({ type: String })
    similar_account7: string;

    @Prop({ type: String })
    similar_account8: string;

    @Prop({ type: String })
    similar_account9: string;

    @Prop({ type: String })
    similar_account10: string;

    @Prop({ type: String })
    similar_account11: string;

    @Prop({ type: String })
    similar_account12: string;

    @Prop({ type: String })
    similar_account13: string;

    @Prop({ type: String })
    similar_account14: string;

    @Prop({ type: String })
    similar_account15: string;

    @Prop({ type: String })
    similar_account16: string;

    @Prop({ type: String })
    similar_account17: string;

    @Prop({ type: String })
    similar_account18: string;

    @Prop({ type: String })
    similar_account19: string;

    @Prop({ type: String })
    similar_account20: string;

    // Timestamps
    @Prop({ type: Date })
    last_full_scrape: Date;

    @Prop({ type: Date })
    analysis_timestamp: Date;
}

export const PrimaryProfileSchema =
    SchemaFactory.createForClass(PrimaryProfile);

// Compound indexes for performance
PrimaryProfileSchema.index({ followers: 1, median_views: -1 });
PrimaryProfileSchema.index({ profile_primary_category: 1, followers: -1 });
PrimaryProfileSchema.index({ account_type: 1, total_reels: -1 });
PrimaryProfileSchema.index({ created_at: -1 });
```

### Key Differences in Nest.js Implementation

1. **DTO Validation**: Uses class-validator decorators for comprehensive input validation of the username parameter.

2. **Logging**: Implements comprehensive logging using Nest.js Logger service, mirroring the Python implementation.

3. **Error Handling**: Proper exception handling with specific error types (NotFoundException).

4. **Performance Optimization**: Uses `.lean()` for better query performance when Mongoose document features aren't needed.

5. **CDN Integration**: Handles CDN URLs for profile images using environment variables.

6. **Complete Schema**: Full Mongoose schema definition with all 70+ fields from the PostgreSQL table.

7. **Additional Methods**: Includes helper methods like `getProfileStats()` for extended functionality.

8. **Type Safety**: Full TypeScript support with proper typing throughout the implementation.

9. **Indexing**: Proper MongoDB indexes for performance optimization on frequently queried fields.

## Responses

### Success: 200 OK

Returns the profile data in a structured format, transformed for frontend consumption.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "username": "exampleuser",
        "profile_name": "Example User",
        "bio": "This is an example bio about content creation and lifestyle.",
        "followers": 125430,
        "profile_image_url": "https://cdn.supabase.co/storage/v1/object/public/profile-images/exampleuser_profile.jpg",
        "profile_image_local": "https://cdn.supabase.co/storage/v1/object/public/profile-images/exampleuser_profile.jpg",
        "is_verified": true,
        "is_business_account": false,
        "reels_count": 247,
        "average_views": 45230.75,
        "primary_category": "Lifestyle",
        "profile_type": "primary",
        "url": "https://www.instagram.com/exampleuser/",
        "posts_count": 312,
        "account_type": "Influencer",
        "language": "en",
        "content_type": "lifestyle",
        "median_views": 38500,
        "total_views": 11181875,
        "total_likes": 892340,
        "total_comments": 45670,
        "secondary_category": "Fashion",
        "tertiary_category": "Travel",
        "categorization_confidence": 0.87,
        "similar_accounts": [
            "similar_creator1",
            "similar_creator2",
            "similar_creator3",
            "similar_creator4",
            "similar_creator5"
        ],
        "last_full_scrape": "2024-01-15T10:30:00Z",
        "analysis_timestamp": "2024-01-15T11:45:00Z",
        "created_at": "2023-08-20T14:22:00Z",
        "updated_at": "2024-01-15T11:45:00Z"
    }
}
```

**Key Response Fields:**

-   **Core Profile Data**: `username`, `profile_name`, `bio`, `followers`, `is_verified`
-   **Media & Content**: `reels_count`, `posts_count`, `average_views`, `median_views`
-   **Analytics**: `total_views`, `total_likes`, `total_comments`
-   **Categorization**: `primary_category`, `secondary_category`, `tertiary_category`
-   **Account Info**: `account_type`, `is_business_account`, `language`
-   **Similar Accounts**: Array of up to 10 similar usernames
-   **URLs**: `profile_image_url` (CDN optimized), `url` (Instagram link)
-   **Metadata**: `last_full_scrape`, `analysis_timestamp`, timestamps

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
