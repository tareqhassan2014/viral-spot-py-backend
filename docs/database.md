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

### 6. `viral_ideas_queue`

Tracks form submissions and competitor selections for viral ideas analysis. Central queue system for managing AI-powered viral content analysis jobs.

[**View Detailed Documentation**](./database/viral_ideas_queue.md)

### 7. `viral_ideas_competitors`

Stores competitor selections for each viral ideas analysis. Tracks which competitor profiles are being analyzed alongside the primary profile.

[**View Detailed Documentation**](./database/viral_ideas_competitors.md)

### 8. `viral_queue_summary` (View)

An optimized database view providing comprehensive queue information by joining viral_ideas_queue and viral_ideas_competitors tables.

[**View Detailed Documentation**](./database/viral_queue_summary.md)

### 9. `viral_analysis_results`

Stores the results of each viral ideas analysis run. Contains AI-generated analysis output including viral ideas, trending patterns, and hook analysis.

[**View Detailed Documentation**](./database/viral_analysis_results.md)

### 10. `viral_analysis_reels`

Tracks which specific reels were used in each viral analysis. Maintains records of both primary and competitor reels with performance metrics.

[**View Detailed Documentation**](./database/viral_analysis_reels.md)

### 11. `viral_scripts`

Stores full scripts generated from user reel transcripts and AI analysis. Contains complete, ready-to-use content scripts based on viral patterns.

[**View Detailed Documentation**](./database/viral_scripts.md)

## Relationships

### Core Profile System

-   **`primary_profiles` to `content`**: One-to-Many. A primary profile can have multiple pieces of content. (`content.profile_id` -> `primary_profiles.id`)
-   **`primary_profiles` to `secondary_profiles`**: One-to-Many. A primary profile can discover multiple secondary profiles. (`secondary_profiles.discovered_by_id` -> `primary_profiles.id`)
-   **`queue`**: Drives the processing of `primary_profiles`. An entry in the queue with a `username` will trigger a scrape and analysis for that profile.

### Viral Analysis System

-   **`viral_ideas_queue` to `viral_ideas_competitors`**: One-to-Many. Each viral analysis can have multiple competitor profiles selected for comparison. (`viral_ideas_competitors.queue_id` -> `viral_ideas_queue.id`)
-   **`viral_ideas_queue` to `viral_analysis_results`**: One-to-Many. Each queue entry can have multiple analysis runs over time. (`viral_analysis_results.queue_id` -> `viral_ideas_queue.id`)
-   **`viral_analysis_results` to `viral_analysis_reels`**: One-to-Many. Each analysis tracks multiple reels that were processed. (`viral_analysis_reels.analysis_id` -> `viral_analysis_results.id`)
-   **`viral_analysis_results` to `viral_scripts`**: One-to-Many. Each analysis can generate multiple scripts. (`viral_scripts.analysis_id` -> `viral_analysis_results.id`)
-   **`viral_analysis_reels` to `content`**: Many-to-One. Analysis reels link to existing content records. (`viral_analysis_reels.content_id` -> `content.content_id`)

### Cross-System Relationships

-   **`viral_ideas_queue` to `primary_profiles`**: Many-to-One. Multiple viral analyses can reference the same primary profile. (`viral_ideas_queue.primary_username` -> `primary_profiles.username`)
-   **`viral_queue_summary`**: Database view that joins `viral_ideas_queue` and `viral_ideas_competitors` for optimized API queries.
