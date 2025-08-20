# REST API Documentation

This document outlines the REST API endpoints available in the ViralSpot backend.

## Main API (`backend_api.py`)

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

    -   **Description:** A new, faster endpoint for retrieving similar profiles.
    -   **Usage:** An optimized alternative to the standard `/similar` endpoint.

5.  **GET `/api/profile/{username}/secondary`** ([Details](./api/get_secondary_profile.md))

    -   **Description:** Retrieves secondary (discovered) profiles associated with a primary profile.
    -   **Usage:** Can be used to show how the network of profiles is expanding.

6.  **GET `/api/profile/{username}/status`** ([Details](./api/check_profile_status.md))

    -   **Description:** Checks the processing status of a profile.
    -   **Usage:** Allows the frontend to poll for updates after requesting a profile to be processed.

7.  **POST `/api/profile/{username}/request`** ([Details](./api/request_profile_processing.md))

    -   **Description:** Submits a request to scrape and analyze a new profile.
    -   **Usage:** The primary way for users to add new profiles to the system.

8.  **POST `/api/profile/{primary_username}/add-competitor/{target_username}` ⚡ NEW** ([Details](./api/add_manual_competitor.md))
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

3.  **POST `/api/viral-ideas/queue/{queue_id}/start` ⚡ NEW** ([Details](./api/start_viral_analysis.md))

    -   **Description:** Starts a queued analysis job.
    -   **Usage:** Manually triggers the processing of a specific job.

4.  **POST `/api/viral-ideas/queue/{queue_id}/process` ⚡ NEW** ([Details](./api/trigger_viral_analysis_processing.md))

    -   **Description:** Triggers the processing of a specific item in the queue.
    -   **Usage:** Internal or manual trigger for processing.

5.  **GET `/api/viral-ideas/queue-status` ⚡ NEW** ([Details](./api/get_viral_ideas_queue_status.md))

    -   **Description:** Gets overall statistics for the viral ideas queue.
    -   **Usage:** A dashboard-like feature to monitor the health of the processing queue.

6.  **POST `/api/viral-ideas/process-pending` ⚡ NEW** ([Details](./api/process_pending_viral_ideas.md))

    -   **Description:** Processes all pending items in the viral ideas queue.
    -   **Usage:** A batch operation to clear the queue.

7.  **GET `/api/viral-analysis/{queue_id}/results` ⚡ NEW** ([Details](./api/get_viral_analysis_results.md))

    -   **Description:** Retrieves the final results of a viral analysis job.
    -   **Usage:** Fetches the data to be displayed on the frontend once an analysis is complete.

8.  **GET `/api/viral-analysis/{queue_id}/content` ⚡ NEW** ([Details](./api/get_viral_analysis_content.md))
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
