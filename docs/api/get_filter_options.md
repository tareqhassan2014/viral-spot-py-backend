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
