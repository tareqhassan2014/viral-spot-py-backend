# GET `/api/filter-options`

Retrieves the available options for filtering content.

## Description

This is a utility endpoint designed to populate the filter dropdowns and selection menus on the frontend. It dynamically queries the database to find all unique values for the various filterable fields, such as categories, content types, languages, and keywords.

By using this endpoint, the frontend can ensure that its filter options are always in sync with the data that actually exists in the database, providing a better user experience.

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request.
2.  **Query for Distinct Values**: It executes several `SELECT DISTINCT` queries on the `content` and `primary_profiles` tables to get all the unique values for each filterable field (e.g., `primary_category`, `language`, `account_type`).
3.  **Assemble Response**: The results of these queries are assembled into a single JSON object, where each key is a filter type and the value is a sorted list of the unique options.
4.  **Send Response**: The JSON object with all the filter options is returned with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# Complete get_filter_options method in ViralSpotAPI class (lines 555-634)
async def get_filter_options(self):
    """Get available filter options from database"""
    try:
        logger.info("Getting filter options")

        # Get distinct categories and content metadata
        categories_response = self.supabase.client.table('content').select(
            'primary_category, secondary_category, tertiary_category, content_type, language, content_style'
        ).execute()

        # Get distinct keywords
        keywords_response = self.supabase.client.table('content').select(
            'keyword_1, keyword_2, keyword_3, keyword_4'
        ).execute()

        # Get distinct usernames and account types
        usernames_response = self.supabase.client.table('primary_profiles').select(
            'username, profile_name, account_type'
        ).execute()

        # Process categories and metadata
        primary_categories = set()
        secondary_categories = set()
        tertiary_categories = set()
        content_types = set()
        languages = set()
        content_styles = set()

        for item in categories_response.data:
            if item.get('primary_category'):
                primary_categories.add(item['primary_category'])
            if item.get('secondary_category'):
                secondary_categories.add(item['secondary_category'])
            if item.get('tertiary_category'):
                tertiary_categories.add(item['tertiary_category'])
            if item.get('content_type'):
                content_types.add(item['content_type'])
            if item.get('language'):
                languages.add(item['language'])
            if item.get('content_style'):
                content_styles.add(item['content_style'])

        # Process keywords
        keywords = set()
        for item in keywords_response.data:
            for i in range(1, 5):
                keyword = item.get(f'keyword_{i}')
                if keyword and keyword.strip():
                    keywords.add(keyword.strip())

        # Process usernames and account types
        usernames = []
        account_types = set()
        for item in usernames_response.data:
            usernames.append({
                'username': item['username'],
                'profile_name': item.get('profile_name', '')
            })
            if item.get('account_type'):
                account_types.add(item['account_type'])

        result = {
            'primary_categories': sorted(list(primary_categories)),
            'secondary_categories': sorted(list(secondary_categories)),
            'tertiary_categories': sorted(list(tertiary_categories)),
            'keywords': sorted(list(keywords)),
            'usernames': usernames,
            # New filter options
            'account_types': sorted(list(account_types)),
            'content_types': sorted(list(content_types)),
            'languages': sorted(list(languages)),
            'content_styles': sorted(list(content_styles))
        }

        logger.info(f"✅ Filter options: {len(result['primary_categories'])} primary categories, {len(result['keywords'])} keywords")

        return result

    except Exception as e:
        logger.error(f"❌ Error getting filter options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint definition (lines 1211-1215)
@app.get("/api/filter-options")
async def get_filter_options(api_instance: ViralSpotAPI = Depends(get_api)):
    """Get available filter options"""
    result = await api_instance.get_filter_options()
    return APIResponse(success=True, data=result)
```

**Line-by-Line Explanation:**

1.  **`async def get_filter_options(self):`**: Defines an asynchronous method that retrieves all available filter options from the database.

2.  **`logger.info("Getting filter options")`**: Logs the start of the filter options retrieval for monitoring and debugging.

3.  **Categories and Metadata Query**: The first query fetches all content metadata in a single request:

    ```sql
    SELECT primary_category, secondary_category, tertiary_category, content_type, language, content_style FROM content
    ```

    This is efficient as it gets all categorical data in one database round-trip.

4.  **Keywords Query**: A separate query specifically for keywords:

    ```sql
    SELECT keyword_1, keyword_2, keyword_3, keyword_4 FROM content
    ```

    Keywords are stored in separate columns, so they need special processing.

5.  **Profiles Query**: Fetches username and account type data:

    ```sql
    SELECT username, profile_name, account_type FROM primary_profiles
    ```

6.  **Set Initialization**: Creates empty sets for each filter category to automatically handle uniqueness:

    -   `primary_categories`, `secondary_categories`, `tertiary_categories`
    -   `content_types`, `languages`, `content_styles`

7.  **Categories Processing Loop**: Iterates through all content records and adds non-null values to the appropriate sets:

    -   Uses `item.get('field')` to safely handle missing fields
    -   Only adds values that exist (not None or empty)

8.  **Keywords Processing**: Special handling for the 4 keyword fields:

    -   Loops through `keyword_1` to `keyword_4` for each content item
    -   Strips whitespace and only adds non-empty keywords
    -   Uses a set to automatically deduplicate keywords across all fields

9.  **Usernames Processing**: Creates a list of username objects with profile names:

    -   Each username entry includes both `username` and `profile_name`
    -   Also collects unique `account_type` values in a separate set

10. **Result Assembly**: Creates the final response object with sorted lists:

    -   Converts all sets to sorted lists for consistent ordering
    -   Includes 8 different filter categories
    -   Usernames remain as objects (not sorted by username)

11. **Success Logging**: Logs the count of primary categories and keywords for monitoring.

12. **Error Handling**: Catches all exceptions and converts them to HTTP 500 errors with detailed messages.

### Key Implementation Features

**1. Efficient Database Queries**: Uses only 3 database queries to fetch all filter options, minimizing database round-trips.

**2. Automatic Deduplication**: Uses Python sets to automatically handle uniqueness without complex SQL DISTINCT operations.

**3. Null Safety**: Comprehensive null checking with `item.get()` and `if` conditions to handle missing data gracefully.

**4. Keyword Aggregation**: Smart processing of the 4 keyword fields into a single deduplicated list.

**5. Structured Username Data**: Returns usernames as objects with both username and display name for frontend flexibility.

**6. Consistent Sorting**: All filter options are alphabetically sorted for predictable frontend behavior.

**7. Comprehensive Logging**: Detailed logging for monitoring and debugging filter option retrieval.

### Nest.js (Mongoose)

```typescript
// In your utility.controller.ts (or content.controller.ts)
import { Controller, Get, Logger } from "@nestjs/common";
import { UtilityService } from "./utility.service";

@Controller("api")
export class UtilityController {
    private readonly logger = new Logger(UtilityController.name);

    constructor(private readonly utilityService: UtilityService) {}

    @Get("/filter-options")
    async getFilterOptions() {
        this.logger.log("Getting filter options");

        const result = await this.utilityService.getFilterOptions();

        this.logger.log(
            `✅ Filter options: ${result.primary_categories.length} primary categories, ${result.keywords.length} keywords`
        );
        return { success: true, data: result };
    }
}

// In your utility.service.ts
import { Injectable, Logger } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import { Content, ContentDocument } from "./schemas/content.schema";
import {
    PrimaryProfile,
    PrimaryProfileDocument,
} from "./schemas/primary-profile.schema";

@Injectable()
export class UtilityService {
    private readonly logger = new Logger(UtilityService.name);

    constructor(
        @InjectModel(Content.name) private contentModel: Model<ContentDocument>,
        @InjectModel(PrimaryProfile.name)
        private primaryProfileModel: Model<PrimaryProfileDocument>
    ) {}

    async getFilterOptions(): Promise<any> {
        try {
            // Parallel execution of all distinct queries for better performance
            const [
                primaryCategories,
                secondaryCategories,
                tertiaryCategories,
                contentTypes,
                languages,
                contentStyles,
                accountTypes,
                usernames,
                keywords,
            ] = await Promise.all([
                // Content metadata queries
                this.contentModel.distinct("primary_category").exec(),
                this.contentModel.distinct("secondary_category").exec(),
                this.contentModel.distinct("tertiary_category").exec(),
                this.contentModel.distinct("content_type").exec(),
                this.contentModel.distinct("language").exec(),
                this.contentModel.distinct("content_style").exec(),

                // Profile queries
                this.primaryProfileModel.distinct("account_type").exec(),
                this.primaryProfileModel
                    .find()
                    .select("username profile_name")
                    .lean()
                    .exec(),

                // Keywords aggregation query
                this.getUniqueKeywords(),
            ]);

            // Filter out null/undefined values and sort
            const result = {
                primary_categories: this.filterAndSort(primaryCategories),
                secondary_categories: this.filterAndSort(secondaryCategories),
                tertiary_categories: this.filterAndSort(tertiaryCategories),
                keywords: this.filterAndSort(keywords),
                usernames: usernames.map((user) => ({
                    username: user.username,
                    profile_name: user.profile_name || "",
                })),
                account_types: this.filterAndSort(accountTypes),
                content_types: this.filterAndSort(contentTypes),
                languages: this.filterAndSort(languages),
                content_styles: this.filterAndSort(contentStyles),
            };

            return result;
        } catch (error) {
            this.logger.error(
                `❌ Error getting filter options: ${error.message}`
            );
            throw error;
        }
    }

    private async getUniqueKeywords(): Promise<string[]> {
        // MongoDB aggregation pipeline to extract unique keywords from all 4 keyword fields
        const keywordPipeline = [
            {
                $project: {
                    keywords: [
                        "$keyword_1",
                        "$keyword_2",
                        "$keyword_3",
                        "$keyword_4",
                    ],
                },
            },
            {
                $unwind: "$keywords",
            },
            {
                $match: {
                    keywords: { $ne: null, $ne: "", $exists: true },
                },
            },
            {
                $group: {
                    _id: "$keywords",
                },
            },
            {
                $sort: { _id: 1 },
            },
        ];

        const keywordsResult = await this.contentModel
            .aggregate(keywordPipeline)
            .exec();
        return keywordsResult.map((k) => k._id).filter(Boolean);
    }

    private filterAndSort(array: any[]): string[] {
        // Filter out null, undefined, and empty strings, then sort
        return array
            .filter((item) => item && item.toString().trim())
            .map((item) => item.toString().trim())
            .sort((a, b) =>
                a.localeCompare(b, undefined, { sensitivity: "base" })
            );
    }

    // Alternative implementation using a single aggregation query (more efficient for large datasets)
    async getFilterOptionsOptimized(): Promise<any> {
        try {
            // Single aggregation pipeline to get all content metadata
            const contentMetadataPipeline = [
                {
                    $group: {
                        _id: null,
                        primary_categories: { $addToSet: "$primary_category" },
                        secondary_categories: {
                            $addToSet: "$secondary_category",
                        },
                        tertiary_categories: {
                            $addToSet: "$tertiary_category",
                        },
                        content_types: { $addToSet: "$content_type" },
                        languages: { $addToSet: "$language" },
                        content_styles: { $addToSet: "$content_style" },
                        keywords: {
                            $addToSet: {
                                $concatArrays: [
                                    [{ $ifNull: ["$keyword_1", null] }],
                                    [{ $ifNull: ["$keyword_2", null] }],
                                    [{ $ifNull: ["$keyword_3", null] }],
                                    [{ $ifNull: ["$keyword_4", null] }],
                                ],
                            },
                        },
                    },
                },
                {
                    $project: {
                        _id: 0,
                        primary_categories: 1,
                        secondary_categories: 1,
                        tertiary_categories: 1,
                        content_types: 1,
                        languages: 1,
                        content_styles: 1,
                        keywords: {
                            $reduce: {
                                input: "$keywords",
                                initialValue: [],
                                in: { $concatArrays: ["$$value", "$$this"] },
                            },
                        },
                    },
                },
            ];

            // Single aggregation pipeline for profile metadata
            const profileMetadataPipeline = [
                {
                    $group: {
                        _id: null,
                        account_types: { $addToSet: "$account_type" },
                        usernames: {
                            $push: {
                                username: "$username",
                                profile_name: {
                                    $ifNull: ["$profile_name", ""],
                                },
                            },
                        },
                    },
                },
                {
                    $project: {
                        _id: 0,
                        account_types: 1,
                        usernames: 1,
                    },
                },
            ];

            const [contentMetadata, profileMetadata] = await Promise.all([
                this.contentModel.aggregate(contentMetadataPipeline).exec(),
                this.primaryProfileModel
                    .aggregate(profileMetadataPipeline)
                    .exec(),
            ]);

            const content = contentMetadata[0] || {};
            const profile = profileMetadata[0] || {};

            return {
                primary_categories: this.filterAndSort(
                    content.primary_categories || []
                ),
                secondary_categories: this.filterAndSort(
                    content.secondary_categories || []
                ),
                tertiary_categories: this.filterAndSort(
                    content.tertiary_categories || []
                ),
                keywords: this.filterAndSort(content.keywords || []),
                usernames: profile.usernames || [],
                account_types: this.filterAndSort(profile.account_types || []),
                content_types: this.filterAndSort(content.content_types || []),
                languages: this.filterAndSort(content.languages || []),
                content_styles: this.filterAndSort(
                    content.content_styles || []
                ),
            };
        } catch (error) {
            this.logger.error(
                `❌ Error getting optimized filter options: ${error.message}`
            );
            throw error;
        }
    }
}
```

### Key Differences in Nest.js Implementation

1. **Parallel Query Execution**: Uses `Promise.all()` to execute all distinct queries simultaneously, significantly improving performance compared to sequential execution.

2. **MongoDB Aggregation for Keywords**: Implements a sophisticated aggregation pipeline to extract unique keywords from all 4 keyword fields efficiently.

3. **Null Filtering**: Comprehensive filtering of null, undefined, and empty values using a dedicated `filterAndSort()` helper method.

4. **Locale-Aware Sorting**: Uses `localeCompare()` for proper alphabetical sorting that handles special characters and case sensitivity.

5. **Optimized Alternative**: Provides an alternative implementation using fewer aggregation queries for better performance with large datasets.

6. **Error Handling**: Comprehensive error handling with detailed logging for debugging.

7. **Type Safety**: Full TypeScript support with proper typing throughout the implementation.

### Performance Considerations

**Standard Implementation:**

-   **9 parallel queries** for maximum simplicity and readability
-   **Easy to understand** and maintain
-   **Good for small to medium datasets**

**Optimized Implementation:**

-   **2 aggregation queries** for better performance
-   **Reduced database round-trips** for large datasets
-   **More complex** but significantly faster for production use

Both implementations provide identical results but with different performance characteristics depending on your dataset size and requirements.

## Responses

### Success: 200 OK

Returns an object containing lists of available options for each filter type, dynamically generated from the current database content.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "primary_categories": [
            "Art & Design",
            "Business & Finance",
            "Comedy & Entertainment",
            "Education & Learning",
            "Fashion & Beauty",
            "Fitness & Health",
            "Food & Cooking",
            "Gaming",
            "Lifestyle",
            "Music & Dance",
            "News & Politics",
            "Science & Technology",
            "Sports",
            "Travel & Adventure"
        ],
        "secondary_categories": [
            "Animation",
            "Cryptocurrency",
            "Digital Marketing",
            "DIY Projects",
            "Entrepreneurship",
            "Graphic Design",
            "Home Decor",
            "Investment Tips",
            "Makeup Tutorials",
            "Photography",
            "Programming",
            "Recipe Videos",
            "Stand-up Comedy",
            "Workout Routines"
        ],
        "tertiary_categories": [
            "Adobe Photoshop",
            "Bitcoin Trading",
            "Healthy Breakfast",
            "JavaScript Tutorials",
            "Social Media Marketing",
            "Travel Photography",
            "Vegan Recipes",
            "Web Development"
        ],
        "keywords": [
            "AI",
            "algorithm",
            "automation",
            "blockchain",
            "coding",
            "creativity",
            "entrepreneur",
            "fitness",
            "growth",
            "innovation",
            "inspiration",
            "lifestyle",
            "marketing",
            "motivation",
            "productivity",
            "SaaS",
            "startup",
            "success",
            "technology",
            "tutorial",
            "viral",
            "web development"
        ],
        "usernames": [
            {
                "username": "alex_codes",
                "profile_name": "Alex - Web Developer"
            },
            {
                "username": "beauty_guru_sarah",
                "profile_name": "Sarah's Beauty Tips"
            },
            { "username": "chef_marco", "profile_name": "Marco's Kitchen" },
            {
                "username": "fitness_coach_mike",
                "profile_name": "Mike Johnson Fitness"
            },
            {
                "username": "travel_with_emma",
                "profile_name": "Emma's Adventures"
            },
            {
                "username": "tech_reviewer_john",
                "profile_name": "John's Tech Reviews"
            }
        ],
        "content_types": ["post", "reel"],
        "languages": ["en", "es", "fr", "de", "it", "pt"],
        "content_styles": [
            "carousel",
            "image",
            "talking head",
            "tutorial",
            "video",
            "vlog"
        ],
        "account_types": [
            "Business Page",
            "Influencer",
            "Personal",
            "Theme Page"
        ]
    }
}
```

**Key Response Features:**

-   **Dynamic Content**: All filter options are generated from actual database content, ensuring they're always current and relevant
-   **Alphabetical Sorting**: All arrays are sorted alphabetically for consistent frontend display
-   **Comprehensive Coverage**: Includes 8 different filter categories covering all major filterable fields
-   **Structured Usernames**: Username objects include both the username and display name for flexible frontend usage
-   **Null Filtering**: All null, undefined, and empty values are automatically filtered out
-   **Real-World Categories**: Categories reflect actual content types found in social media platforms
-   **Multi-Language Support**: Language codes follow ISO standards for international content
-   **Content Type Distinction**: Clear separation between posts (images/carousels) and reels (videos)

### Response Field Descriptions:

-   **`primary_categories`**: Top-level content categories (14+ options)
-   **`secondary_categories`**: More specific subcategories (20+ options)
-   **`tertiary_categories`**: Highly specific niche categories (10+ options)
-   **`keywords`**: Popular hashtags and keywords extracted from content (50+ options)
-   **`usernames`**: Available profiles with display names for filtering
-   **`content_types`**: Media types (post, reel)
-   **`languages`**: Content languages using ISO codes
-   **`content_styles`**: Visual/format styles of content
-   **`account_types`**: Creator account classifications

### Error: 500 Internal Server Error

Returned if there is a failure in retrieving the options from the database.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_filter_options()`
-   **Database Interaction:** The endpoint queries the `content` and `primary_profiles` tables to get all distinct values for the filterable fields. The results are then processed into sorted lists for the response.
