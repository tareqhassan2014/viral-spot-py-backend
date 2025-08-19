# ViralSpot Backend Documentation

## 1. Project Overview

The ViralSpot backend is a Python-based system designed to identify and analyze viral content trends on social media platforms. It scrapes data from profiles, processes it through an AI pipeline, and exposes the results via a REST API. The system is built to be scalable, using a queue-based architecture to handle asynchronous processing of profiles and content.

## 2. System Architecture

The backend is composed of three main parts: REST APIs for client interaction, background processes for data fetching and analysis, and a PostgreSQL database for data storage, managed via Supabase.

-   **`main.py`**: The central entry point that starts all services.
-   **REST API (`backend_api.py`)**: A FastAPI server that exposes endpoints for the frontend.
-   **Background Processes**:
    -   **`network_crawler.py`**: Discovers new profiles and adds them to the queue.
    -   **`queue_processor.py`**: Processes profiles from the queue, scraping their data.
    -   **`viral_ideas_processor.py`**: Analyzes content for viral trends.
-   **Database**: A PostgreSQL database (managed by Supabase) that stores all data.

## 3. Core Components

### 3.1. REST APIs

The system exposes several REST APIs for frontend integration and data retrieval. These APIs provide access to profile data, content analysis, and similar profile suggestions.

-   **Main API (`backend_api.py`):** Provides core functionalities like fetching profile data and viral content analysis.
-   **Similar Profiles API (`simple_similar_profiles_api.py`):** A specialized API for retrieving lists of similar profiles.

[Detailed API Documentation](./docs/api.md)

### 3.2. Background Processes

Several long-running processes handle the data scraping, processing, and analysis tasks in the background.

-   **Network Crawler (`network_crawler.py`):** Scours social media for new profiles and content based on certain criteria.
-   **Queue Processor (`queue_processor.py`):** Manages a queue of profiles to be processed, ensuring orderly and reliable data fetching.
-   **Viral Ideas Processor (`viral_ideas_processor.py`):** The core AI component that analyzes content and profile data to identify viral trends.

[Detailed Processes Documentation](./docs/processes.md)

### 3.3. Database Schema

The database is the backbone of the system, storing all scraped data, analysis results, and queue states. It is defined in SQL schema files.

-   **Tables:** The schema consists of tables for `primary_profiles`, `secondary_profiles`, `content`, `queue`, and `similar_profiles`.
-   **Relationships:** `content` is linked to `primary_profiles`, and `secondary_profiles` can be discovered by `primary_profiles`. The `queue` table drives the processing workflow.

[Detailed Database Documentation](./docs/database.md)

## 4. Directory Structure

-   `docs/`: Contains all documentation files.
    -   `api.md`: Detailed documentation of the REST APIs.
    -   `database.md`: Detailed documentation of the database schema.
    -   `processes.md`: Detailed documentation of the background processes.
-   `schema/`: Contains all `.sql` files that define the database schema.
-   `test/`: Contains all test files for the project.
-   `backend_api.py`: Implements the main REST API endpoints using FastAPI.
-   `config.py`: Manages configuration variables for the application.
-   `main.py`: The main entry point for starting all backend services.
-   `network_crawler.py`: Discovers new profiles to add to the processing queue.
-   `queue_processor.py`: Manages the queue of profiles to be scraped.
-   `supabase_integration.py`: Handles all interactions with the Supabase PostgreSQL database.
-   `viral_ideas_ai_pipeline.py`: Contains the logic for the AI-powered content analysis.
-   `viral_ideas_processor.py`: The core AI component that analyzes content to identify viral trends.

## 5. Getting Started

### Prerequisites

-   Python 3.7+
-   An account with Supabase to host the PostgreSQL database.
-   A RapidAPI account and API key for the Instagram scraper.

### Setup

1.  **Clone the repository:**

    ```sh
    git clone <repository_url>
    cd backend
    ```

2.  **Install dependencies:**

    ```sh
    pip install -r requirements_backend.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the root of the project and add the following variables:

    ```
    SUPABASE_URL=<your_supabase_url>
    SUPABASE_SERVICE_ROLE_KEY=<your_supabase_service_role_key>
    RAPIDAPI_KEY=<your_rapidapi_key>
    ```

4.  **Set up the database:**
    Run the `.sql` files in the `schema/` directory on your Supabase instance to create the necessary tables and relationships.

### Running the Application

To start all the backend services, including the API server and the background processors, run the following command:

```sh
python main.py
```

This will start:

-   The FastAPI server on `http://localhost:8000`.
-   The `Queue Processor` to handle profile scraping.
-   The `Viral Ideas Processor` to handle content analysis.
