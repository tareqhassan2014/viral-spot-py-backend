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
# In ViralSpotAPI class in backend_api.py

async def get_filter_options(self):
    """Get available filter options from database"""
    try:
        # It executes multiple queries to get all distinct values
        categories_response = self.supabase.client.table('content').select(
            'primary_category, secondary_category, ...'
        ).execute()

        keywords_response = self.supabase.client.table('content').select(
            'keyword_1, keyword_2, ...'
        ).execute()

        usernames_response = self.supabase.client.table('primary_profiles').select(
            'username, profile_name, account_type'
        ).execute()

        # Then, it processes the results of these queries, using sets to get unique values
        primary_categories = set()
        for item in categories_response.data:
            primary_categories.add(item['primary_category'])

        # ... and so on for all other fields ...

        # Finally, it assembles the response object with sorted lists of unique values
        return { 'primary_categories': sorted(list(primary_categories)), ... }

    except Exception as e:
        # ... error handling ...
```

**Line-by-Line Explanation:**

The Python code fetches all values for the filterable columns from the database. It then uses Python's `set` data structure to efficiently find all the unique values, converts them to sorted lists, and returns them in the response.

### Nest.js (Mongoose)

```typescript
// In your utility.controller.ts (or a relevant controller)

@Get('/filter-options')
async getFilterOptions() {
  const result = await this.utilityService.getFilterOptions();
  return { success: true, data: result };
}

// In your utility.service.ts

async getFilterOptions(): Promise<any> {
  // Mongoose's `.distinct()` is much more efficient for this task.
  const primaryCategories = await this.contentModel.distinct('primary_category');
  const secondaryCategories = await this.contentModel.distinct('secondary_category');
  const languages = await this.contentModel.distinct('language');
  const contentStyles = await this.contentModel.distinct('content_style');

  const accountTypes = await this.primaryProfileModel.distinct('account_type');
  const usernames = await this.primaryProfileModel.find().select('username profile_name').exec();

  // Keywords are a bit different since they are in multiple fields
  const keywordPipeline = [
    { $project: { keywords: ['$keyword_1', '$keyword_2', '$keyword_3', '$keyword_4'] } },
    { $unwind: '$keywords' },
    { $group: { _id: '$keywords' } }
  ];
  const keywordsResult = await this.contentModel.aggregate(keywordPipeline);
  const keywords = keywordsResult.map(k => k._id).filter(Boolean);

  return {
    primary_categories: primaryCategories.sort(),
    secondary_categories: secondaryCategories.sort(),
    languages: languages.sort(),
    content_styles: contentStyles.sort(),
    account_types: accountTypes.sort(),
    usernames,
    keywords: keywords.sort(),
  };
}
```

## Responses

### Success: 200 OK

Returns an object containing lists of available options for each filter type.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "primary_categories": ["Art", "Business", "Education", "Entertainment"],
        "secondary_categories": [
            "Digital Art",
            "Entrepreneurship",
            "Programming",
            "Comedy"
        ],
        "tertiary_categories": [],
        "keywords": ["AI", "SaaS", "Tutorial", "Web Development"],
        "usernames": [
            { "username": "user1", "profile_name": "User One" },
            { "username": "user2", "profile_name": "User Two" }
        ],
        "content_types": ["reel", "post"],
        "languages": ["en", "es", "fr"],
        "content_styles": ["Talking Head", "Tutorial", "Vlog"],
        "account_types": ["Influencer", "Business Page", "Theme Page"]
    }
}
```

### Error: 500 Internal Server Error

Returned if there is a failure in retrieving the options from the database.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_filter_options()`
-   **Database Interaction:** The endpoint queries the `content` and `primary_profiles` tables to get all distinct values for the filterable fields. The results are then processed into sorted lists for the response.
