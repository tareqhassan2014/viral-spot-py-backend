# Database Schema Documentation

This document provides a detailed overview of the database schema used in the ViralSpot backend.

## Tables

### 1. `primary_profiles`

Stores the main profiles for which content has been fetched and analyzed.

[**View Detailed Documentation**](./database/primary_profiles.md)

### 2. `secondary_profiles`

Stores similar profiles that have been discovered but not yet fully scraped.

[**View Detailed Documentation**](./database/secondary_profiles.md)

### 3. `content`

Stores individual pieces of content (reels, posts) from primary profiles.

[**View Detailed Documentation**](./database/content.md)

### 4. `queue`

A task queue for processing profiles.

[**View Detailed Documentation**](./database/queue.md)

### 5. `similar_profiles`

Stores a list of similar profiles for a given primary profile.

[**View Detailed Documentation**](./database/similar_profiles.md)

## Relationships

-   **`primary_profiles` to `content`**: One-to-Many. A primary profile can have multiple pieces of content. (`content.profile_id` -> `primary_profiles.id`)
-   **`primary_profiles` to `secondary_profiles`**: One-to-Many. A primary profile can discover multiple secondary profiles. (`secondary_profiles.discovered_by_id` -> `primary_profiles.id`)
-   **`queue`**: Drives the processing of `primary_profiles`. An entry in the queue with a `username` will trigger a scrape and analysis for that profile.
