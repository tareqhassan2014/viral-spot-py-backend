# REST API Documentation

This document outlines the REST API endpoints available in the ViralSpot backend.

## Main API (`backend_api.py`)

### Profile Endpoints

-   **GET `/api/profile/{username}`**

    -   **Description:** Retrieves detailed data for a specific profile.
    -   **Usage:** Used to display profile pages on the frontend.

-   **GET `/api/profile/{username}/reels`**

    -   **Description:** Fetches all the reels associated with a specific profile.
    -   **Usage:** Populates the reels section of a profile's page.

-   **GET `/api/profile/{username}/similar`**

    -   **Description:** Gets a list of similar profiles. This is the standard endpoint for similarity checks.
    -   **Usage:** Suggests other profiles to the user.

-   **GET `/api/profile/{username}/similar-fast` ⚡ NEW**

    -   **Description:** A new, faster endpoint for retrieving similar profiles.
    -   **Usage:** An optimized alternative to the standard `/similar` endpoint.

-   **GET `/api/profile/{username}/secondary`**

    -   **Description:** Retrieves secondary (discovered) profiles associated with a primary profile.
    -   **Usage:** Can be used to show how the network of profiles is expanding.

-   **GET `/api/profile/{username}/status`**

    -   **Description:** Checks the processing status of a profile.
    -   **Usage:** Allows the frontend to poll for updates after requesting a profile to be processed.

-   **POST `/api/profile/{username}/request`**

    -   **Description:** Submits a request to scrape and analyze a new profile.
    -   **Usage:** The primary way for users to add new profiles to the system.

-   **POST `/api/profile/{primary_username}/add-competitor/{target_username}` ⚡ NEW**
    -   **Description:** Adds a `target_username` as a competitor to a `primary_username`.
    -   **Usage:** Part of a new competitor analysis feature.

### Content Endpoints

-   **GET `/api/reels`**

    -   **Description:** Retrieves a list of reels, with support for filtering and pagination.
    -   **Usage:** The main endpoint for browsing and discovering viral content.

-   **GET `/api/posts`**

    -   **Description:** Retrieves a list of posts, likely with filtering and pagination.
    -   **Usage:** For browsing content that is not in video format.

-   **GET `/api/content/competitor/{username}` ⚡ NEW**

    -   **Description:** Fetches content from a competitor's profile.
    -   **Usage:** Used in the competitor analysis feature to compare content strategies.

-   **GET `/api/content/user/{username}` ⚡ NEW**
    -   **Description:** Fetches content from a user's own profile.
    -   **Usage:** Allows users to analyze their own content through the ViralSpot pipeline.

### Viral Ideas & Analysis Endpoints

-   **POST `/api/viral-ideas/queue` ⚡ NEW**

    -   **Description:** Creates a new viral ideas analysis job and adds it to the queue.
    -   **Usage:** Kicks off the AI pipeline to find viral trends.

-   **GET `/api/viral-ideas/queue/{session_id}` ⚡ NEW**

    -   **Description:** Retrieves the status of a specific viral ideas analysis job from the queue.
    -   **Usage:** Polling for real-time updates on the analysis progress.

-   **POST `/api/viral-ideas/queue/{queue_id}/start` ⚡ NEW**

    -   **Description:** Starts a queued analysis job.
    -   **Usage:** Manually triggers the processing of a specific job.

-   **POST `/api/viral-ideas/queue/{queue_id}/process` ⚡ NEW**

    -   **Description:** Triggers the processing of a specific item in the queue.
    -   **Usage:** Internal or manual trigger for processing.

-   **GET `/api/viral-ideas/queue-status` ⚡ NEW**

    -   **Description:** Gets overall statistics for the viral ideas queue.
    -   **Usage:** A dashboard-like feature to monitor the health of the processing queue.

-   **POST `/api/viral-ideas/process-pending` ⚡ NEW**

    -   **Description:** Processes all pending items in the viral ideas queue.
    -   **Usage:** A batch operation to clear the queue.

-   **GET `/api/viral-analysis/{queue_id}/results` ⚡ NEW**

    -   **Description:** Retrieves the final results of a viral analysis job.
    -   **Usage:** Fetches the data to be displayed on the frontend once an analysis is complete.

-   **GET `/api/viral-analysis/{queue_id}/content` ⚡ NEW**
    -   **Description:** Retrieves the content that was analyzed as part of a job.
    -   **Usage:** To show the source content alongside the analysis results.

### Utility Endpoints

-   **GET `/api/filter-options`**

    -   **Description:** Retrieves the available options for filtering content (e.g., categories, languages).
    -   **Usage:** Populates the filter dropdowns on the frontend.

-   **POST `/api/reset-session`**

    -   **Description:** Resets the user's random session.
    -   **Usage:** For debugging or clearing session-specific data.

-   **GET `/api/debug/profile/{username}` 🐛 DEBUG**
    -   **Description:** A debug endpoint to get raw or extended data for a profile.
    -   **Usage:** For internal testing and development purposes.
