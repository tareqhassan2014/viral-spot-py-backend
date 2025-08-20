# REST API Documentation

This document outlines the REST API endpoints available in the ViralSpot backend.

## Main API (`backend_api.py`)

**Total Endpoints:** 27 active endpoints serving frontend, administrative, and debugging needs.

### Root & Health Endpoints

1.  **GET `/`**

    -   **Description:** Root endpoint providing API status and availability information.
    -   **Usage:** Basic API health check and service discovery.

2.  **GET `/health`**

    -   **Description:** Comprehensive health check endpoint with detailed service status.
    -   **Usage:** Monitoring API availability, Supabase connectivity, and service dependencies.

### Profile Endpoints

1.  **GET `/api/profile/{username}`** ([Details](./api/get_profile.md))

    -   **Description:** Retrieves detailed data for a specific profile.
    -   **Usage:** Used to display profile pages on the frontend.

2.  **GET `/api/profile/{username}/reels`** ([Details](./api/get_profile_reels.md))

    -   **Description:** Fetches all the reels associated with a specific profile.
    -   **Usage:** Populates the reels section of a profile's page.

3.  **GET `/api/profile/{username}/similar`** ([Details](./api/get_similar_profiles.md))

    -   **Description:** Gets a list of similar profiles. This is the standard endpoint for similarity checks.
    -   **Usage:** Suggests other profiles to the user.

4.  **GET `/api/profile/{username}/similar-fast` ⚡ NEW** ([Details](./api/get_similar_profiles_fast.md))

    -   **Description:** A new, faster endpoint for retrieving similar profiles with 24hr caching.
    -   **Usage:** An optimized alternative to the standard `/similar` endpoint with CDN-delivered images.

5.  **DELETE `/api/profile/{username}/similar-cache` ⚡ NEW** ([Details](./api/clear_similar_profiles_cache.md))

    -   **Description:** Clears cached similar profiles data for a specific username with advanced cache management.
    -   **Usage:** Cache management, data refresh, and performance optimization for similar profiles system.

6.  **GET `/api/profile/{username}/secondary`** ([Details](./api/get_secondary_profile.md))

    -   **Description:** Retrieves secondary (discovered) profiles associated with a primary profile.
    -   **Usage:** Can be used to show how the network of profiles is expanding.

7.  **GET `/api/profile/{username}/status`** ([Details](./api/check_profile_status.md))

    -   **Description:** Checks the processing status of a profile.
    -   **Usage:** Allows the frontend to poll for updates after requesting a profile to be processed.

8.  **POST `/api/profile/{username}/request`** ([Details](./api/request_profile_processing.md))

    -   **Description:** Submits a request to scrape and analyze a new profile.
    -   **Usage:** The primary way for users to add new profiles to the system.

9.  **POST `/api/profile/{primary_username}/add-competitor/{target_username}` ⚡ NEW** ([Details](./api/add_manual_competitor.md))

    -   **Description:** Adds a `target_username` as a competitor to a `primary_username`.
    -   **Usage:** Part of a new competitor analysis feature.

### Content Endpoints

1.  **GET `/api/reels`** ([Details](./api/get_reels.md))

    -   **Description:** Retrieves a list of reels, with support for filtering and pagination.
    -   **Usage:** The main endpoint for browsing and discovering viral content.

2.  **GET `/api/posts`** ([Details](./api/get_posts.md))

    -   **Description:** Retrieves a list of posts, likely with filtering and pagination.
    -   **Usage:** For browsing content that is not in video format.

3.  **GET `/api/content/competitor/{username}` ⚡ NEW** ([Details](./api/get_competitor_content.md))

    -   **Description:** Fetches content from a competitor's profile.
    -   **Usage:** Used in the competitor analysis feature to compare content strategies.

4.  **GET `/api/content/user/{username}` ⚡ NEW** ([Details](./api/get_user_content.md))
    -   **Description:** Fetches content from a user's own profile.
    -   **Usage:** Allows users to analyze their own content through the ViralSpot pipeline.

### Viral Ideas & Analysis Endpoints

1.  **POST `/api/viral-ideas/queue` ⚡ NEW** ([Details](./api/create_viral_ideas_queue.md))

    -   **Description:** Creates a new viral ideas analysis job and adds it to the queue.
    -   **Usage:** Kicks off the AI pipeline to find viral trends.

2.  **GET `/api/viral-ideas/queue/{session_id}` ⚡ NEW** ([Details](./api/get_viral_ideas_queue.md))

    -   **Description:** Retrieves the status of a specific viral ideas analysis job from the queue.
    -   **Usage:** Polling for real-time updates on the analysis progress.

3.  **GET `/api/viral-ideas/check-existing/{username}` ⚡ NEW** ([Details](./api/check_existing_viral_analysis.md))

    -   **Description:** Checks if there's already an existing analysis (completed or active) for a profile with intelligent duplicate prevention.
    -   **Usage:** Prevents duplicate analysis creation, enables immediate access to existing results, and optimizes resource utilization.

4.  **POST `/api/viral-ideas/queue/{queue_id}/start` ⚡ NEW** ([Details](./api/start_viral_analysis.md))

    -   **Description:** Signals a queued analysis job as ready for background worker processing.
    -   **Usage:** Queue signaling and worker coordination for viral analysis jobs.

5.  **POST `/api/viral-ideas/queue/{queue_id}/process` ⚡ NEW** ([Details](./api/trigger_viral_analysis_processing.md))

    -   **Description:** Immediately triggers the processing of a specific item in the queue.
    -   **Usage:** Administrative tool for immediate processing, debugging, and manual intervention.

6.  **POST `/api/viral-ideas/process-pending` ⚡ NEW** ([Details](./api/process_pending_viral_ideas.md))

    -   **Description:** Processes all pending items in the viral ideas queue.
    -   **Usage:** A batch operation to clear the queue and process multiple jobs.

7.  **GET `/api/viral-ideas/queue-status` ⚡ NEW** ([Details](./api/get_viral_ideas_queue_status.md))

    -   **Description:** Gets overall statistics for the viral ideas queue.
    -   **Usage:** A dashboard-like feature to monitor the health of the processing queue.

8.  **GET `/api/viral-analysis/{queue_id}/results` ⚡ NEW** ([Details](./api/get_viral_analysis_results.md))

    -   **Description:** Retrieves the final results of a viral analysis job.
    -   **Usage:** Fetches the data to be displayed on the frontend once an analysis is complete.

9.  **GET `/api/viral-analysis/{queue_id}/content` ⚡ NEW** ([Details](./api/get_viral_analysis_content.md))

    -   **Description:** Retrieves the content that was analyzed as part of a job.
    -   **Usage:** To show the source content alongside the analysis results.

### Utility Endpoints

1.  **GET `/api/filter-options`** ([Details](./api/get_filter_options.md))

    -   **Description:** Retrieves the available options for filtering content (e.g., categories, languages).
    -   **Usage:** Populates the filter dropdowns on the frontend.

2.  **POST `/api/reset-session`** ([Details](./api/reset_session.md))

    -   **Description:** Resets the user's random session.
    -   **Usage:** For debugging or clearing session-specific data.

3.  **GET `/api/debug/profile/{username}` 🐛 DEBUG** ([Details](./api/debug_profile_fetch.md))
    -   **Description:** A debug endpoint to get raw or extended data for a profile.
    -   **Usage:** For internal testing and development purposes.

## Related Database Tables

The API endpoints interact with the following database tables and views:

### Core Profile System

-   **`primary_profiles`**: ([Details](./database/primary_profiles.md)) - Main profiles data used by profile endpoints
-   **`secondary_profiles`**: ([Details](./database/secondary_profiles.md)) - Similar profiles discovered during analysis
-   **`content`**: ([Details](./database/content.md)) - Individual reels and posts content
-   **`queue`**: ([Details](./database/queue.md)) - Task queue for profile processing
-   **`similar_profiles`**: ([Details](./database/similar_profiles.md)) - Similar profile relationships

### Viral Analysis System

-   **`viral_ideas_queue`**: ([Details](./database/viral_ideas_queue.md)) - Central queue for viral analysis jobs
-   **`viral_ideas_competitors`**: ([Details](./database/viral_ideas_competitors.md)) - Competitor selections for each analysis
-   **`viral_queue_summary`**: ([Details](./database/viral_queue_summary.md)) - Optimized view for queue data with competitor counts
-   **`viral_analysis_results`**: ([Details](./database/viral_analysis_results.md)) - AI analysis results and output
-   **`viral_analysis_reels`**: ([Details](./database/viral_analysis_reels.md)) - Specific reels used in each analysis
-   **`viral_scripts`**: ([Details](./database/viral_scripts.md)) - Generated scripts from analysis
