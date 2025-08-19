# Background Processes Documentation

This document describes the background processes that power the ViralSpot backend.

## 1. Queue Processor (`queue_processor.py`)

The `QueueProcessor` is the backbone of the data ingestion pipeline. It manages a queue of Instagram profiles to be scraped and analyzed, ensuring that processing is done in an orderly and reliable manner.

### Key Features:

-   **Hybrid Queue Management:** Can operate with a local CSV file (`queue.csv`) or a Supabase table as the queue backend. This allows for flexibility and resilience.
-   **Priority Handling:** Supports `HIGH` and `LOW` priority tasks. High-priority items will pause the processing of low-priority ones, ensuring that urgent requests are handled promptly.
-   **Concurrency Control:** Manages the number of concurrent scraping tasks to avoid rate limiting and overloading the system.
-   **Error Handling & Retries:** Implements robust error handling and keeps track of processing attempts for each queue item.
-   **Graceful Shutdown:** Can be shut down gracefully, ensuring that in-progress tasks are not lost.

### Workflow:

1.  A new username is added to the queue (either via the API or the Network Crawler).
2.  The `QueueProcessor` picks up the next available item based on priority.
3.  It invokes the `InstagramDataPipeline` (from `PrimaryProfileFetch.py`) to scrape the profile data.
4.  The status of the queue item is updated to `COMPLETED` or `FAILED`.

## 2. Viral Ideas Processor (`viral_ideas_processor.py`)

This is the core AI component of the system, responsible for analyzing content and identifying viral trends. It is highly optimized for speed, using parallel processing to fetch and analyze data from multiple profiles at once.

### Key Features:

-   **Parallel Processing:** Uses `asyncio.gather()` to fetch data from the primary user and all their competitors simultaneously, drastically reducing processing time.
-   **Transcript Extraction:** Integrates with an external API to fetch transcripts from video content (reels).
-   **Smart Reel Selection:** Intelligently selects the top-performing reels for analysis and has a fallback mechanism to ensure enough transcripts are fetched.
-   **Dual Storage Strategy:** Stores the fetched data in both the main content tables (making it available to all users) and in dedicated viral analysis tables.
-   **Recurring Analysis:** Can run recurring analyses to discover newly posted content and track evolving trends.

### Workflow:

1.  A new viral ideas analysis job is created via the API.
2.  The `ViralIdeasProcessor` fetches the profile data for the primary user and their competitors in parallel.
3.  It identifies the top-performing reels and fetches their transcripts.
4.  The collected data is then passed to the AI pipeline (`viral_ideas_ai_pipeline.py`) for analysis.
5.  The results are stored in the database.

## 3. Network Crawler (`network_crawler.py`)

The `NetworkCrawler` is responsible for discovering new profiles to be added to the processing queue. It expands the network of known profiles by finding accounts that are similar to existing ones.

### Key Features:

-   **Intelligent Seed Selection:** Can automatically select "seed" profiles from the existing database of primary profiles to start the discovery process from.
-   **Multi-Round Discovery:** Performs discovery in multiple rounds, using different seed profiles in each round to explore different parts of the network.
-   **Deduplication:** Keeps track of profiles that are already in the queue or have been processed to avoid redundant work.
-   **Configurable:** The crawling process is highly configurable, with settings for the number of profiles to find, the number of rounds to run, and more.
-   **RapidAPI Integration:** Uses the RapidAPI service to find profiles similar to the seed profiles.

### Workflow:

1.  The crawler is started, either with a specific set of seed profiles or in automatic mode.
2.  It selects a seed profile and uses the RapidAPI to find similar accounts.
3.  It filters the results, removing duplicates and low-quality profiles.
4.  The selected profiles are added to the queue with `LOW` priority.
5.  The process repeats with a new seed profile until the target number of new profiles has been queued.
