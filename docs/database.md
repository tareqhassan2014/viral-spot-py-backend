# Database Schema Documentation

This document provides a detailed overview of the database schema used in the ViralSpot backend.

## Tables

### 1. `primary_profiles`

Stores the main profiles for which content has been fetched and analyzed.

| Column                                   | Type                       | Description                                                                |
| ---------------------------------------- | -------------------------- | -------------------------------------------------------------------------- |
| `id`                                     | `UUID`                     | Primary key, auto-generated.                                               |
| `username`                               | `VARCHAR(255)`             | Unique username of the profile.                                            |
| `profile_name`                           | `VARCHAR(255)`             | Display name of the profile.                                               |
| `bio`                                    | `TEXT`                     | Biography of the profile.                                                  |
| `followers`                              | `INTEGER`                  | Number of followers.                                                       |
| `posts_count`                            | `INTEGER`                  | Number of posts.                                                           |
| `is_verified`                            | `BOOLEAN`                  | Whether the profile is verified.                                           |
| `is_business_account`                    | `BOOLEAN`                  | Whether it's a business account.                                           |
| `profile_url`                            | `VARCHAR(500)`             | URL to the profile page.                                                   |
| `profile_image_url`                      | `TEXT`                     | URL of the profile image.                                                  |
| `profile_image_path`                     | `TEXT`                     | Path to the profile image in the Supabase storage bucket.                  |
| `hd_profile_image_path`                  | `TEXT`                     | Path to the high-definition profile image in the storage bucket.           |
| `account_type`                           | `account_type` (ENUM)      | Type of account (`Influencer`, `Theme Page`, `Business Page`, `Personal`). |
| `language`                               | `VARCHAR(10)`              | Primary language of the profile.                                           |
| `content_type`                           | `VARCHAR(50)`              | Main type of content the profile produces.                                 |
| `total_reels`                            | `INTEGER`                  | Total number of reels posted.                                              |
| `median_views`                           | `BIGINT`                   | Median views on the profile's content.                                     |
| `mean_views`                             | `DECIMAL(12,2)`            | Mean (average) views on the profile's content.                             |
| `std_views`                              | `DECIMAL(12,2)`            | Standard deviation of views.                                               |
| `total_views`                            | `BIGINT`                   | Total cumulative views on all content.                                     |
| `total_likes`                            | `BIGINT`                   | Total cumulative likes on all content.                                     |
| `total_comments`                         | `BIGINT`                   | Total cumulative comments on all content.                                  |
| `profile_primary_category`               | `VARCHAR(100)`             | Primary content category.                                                  |
| `profile_secondary_category`             | `VARCHAR(100)`             | Secondary content category.                                                |
| `profile_tertiary_category`              | `VARCHAR(100)`             | Tertiary content category.                                                 |
| `profile_categorization_confidence`      | `DECIMAL(3,2)`             | Confidence score for the profile categorization.                           |
| `account_type_confidence`                | `DECIMAL(3,2)`             | Confidence score for the account type estimation.                          |
| `similar_account1` - `similar_account20` | `VARCHAR(255)`             | Denormalized list of similar account usernames for performance.            |
| `last_full_scrape`                       | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last complete data scrape.                                |
| `analysis_timestamp`                     | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last AI analysis.                                         |
| `created_at`                             | `TIMESTAMP WITH TIME ZONE` | Timestamp of when the record was created.                                  |
| `updated_at`                             | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last update.                                              |

### 2. `secondary_profiles`

Stores similar profiles that have been discovered but not yet fully scraped.

| Column              | Type           | Description                                                                           |
| ------------------- | -------------- | ------------------------------------------------------------------------------------- |
| `id`                | `UUID`         | Primary key, auto-generated.                                                          |
| `username`          | `VARCHAR(255)` | Unique username of the profile.                                                       |
| ... (other columns) | ...            | ...                                                                                   |
| `discovered_by_id`  | `UUID`         | Foreign key referencing `primary_profiles(id)`. The profile that discovered this one. |

### 3. `content`

Stores individual pieces of content (reels, posts) from primary profiles.

| Column              | Type                  | Description                                                                   |
| ------------------- | --------------------- | ----------------------------------------------------------------------------- |
| `id`                | `UUID`                | Primary key, auto-generated.                                                  |
| `content_id`        | `VARCHAR(255)`        | Unique ID of the content from the social media platform.                      |
| `shortcode`         | `VARCHAR(255)`        | Short URL code for the content.                                               |
| `content_type`      | `content_type` (ENUM) | Type of content (`reel`, `post`, `story`).                                    |
| ... (other columns) | ...                   | ...                                                                           |
| `profile_id`        | `UUID`                | Foreign key referencing `primary_profiles(id)`. The profile that posted this. |

### 4. `queue`

A task queue for processing profiles.

| Column              | Type                  | Description                                                                  |
| ------------------- | --------------------- | ---------------------------------------------------------------------------- |
| `id`                | `UUID`                | Primary key, auto-generated.                                                 |
| `username`          | `VARCHAR(255)`        | The username to be processed.                                                |
| `status`            | `queue_status` (ENUM) | Current status of the task (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`). |
| ... (other columns) | ...                   | ...                                                                          |

### 5. `similar_profiles`

Stores a list of similar profiles for a given primary profile.

| Column              | Type           | Description                            |
| ------------------- | -------------- | -------------------------------------- |
| `id`                | `UUID`         | Primary key, auto-generated.           |
| `primary_username`  | `VARCHAR(255)` | The main profile these are similar to. |
| `similar_username`  | `VARCHAR(255)` | The username of the similar profile.   |
| ... (other columns) | ...            | ...                                    |

## Relationships

-   **`primary_profiles` to `content`**: One-to-Many. A primary profile can have multiple pieces of content. (`content.profile_id` -> `primary_profiles.id`)
-   **`primary_profiles` to `secondary_profiles`**: One-to-Many. A primary profile can discover multiple secondary profiles. (`secondary_profiles.discovered_by_id` -> `primary_profiles.id`)
-   **`queue`**: Drives the processing of `primary_profiles`. An entry in the queue with a `username` will trigger a scrape and analysis for that profile.
