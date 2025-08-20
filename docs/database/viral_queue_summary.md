# View: `viral_queue_summary`

An optimized database view that provides comprehensive queue information by joining `viral_ideas_queue` and `viral_ideas_competitors` tables. This view eliminates the need for complex JOINs in application code and provides pre-aggregated competitor counts and form data.

## Schema

This view contains 19 columns.

| Column                     | Type                       | Description                                                                      |
| -------------------------- | -------------------------- | -------------------------------------------------------------------------------- |
| `id`                       | `UUID`                     | Primary key from viral_ideas_queue.                                              |
| `session_id`               | `VARCHAR(255)`             | Unique session identifier for tracking user requests.                            |
| `primary_username`         | `VARCHAR(255)`             | Username of the primary profile being analyzed.                                  |
| `status`                   | `VARCHAR(50)`              | Current queue status (`pending`, `processing`, `completed`, `failed`, `paused`). |
| `priority`                 | `INTEGER`                  | Processing priority (1=highest, 10=lowest).                                      |
| `progress_percentage`      | `INTEGER`                  | Progress percentage (0-100) of the analysis.                                     |
| `auto_rerun_enabled`       | `BOOLEAN`                  | Whether to automatically re-run analysis periodically.                           |
| `rerun_frequency_hours`    | `INTEGER`                  | How often to re-run analysis in hours.                                           |
| `last_analysis_at`         | `TIMESTAMP WITH TIME ZONE` | Timestamp when analysis was last completed.                                      |
| `next_scheduled_run`       | `TIMESTAMP WITH TIME ZONE` | Timestamp for next scheduled automatic run.                                      |
| `total_runs`               | `INTEGER`                  | Total number of times this analysis has been executed.                           |
| `submitted_at`             | `TIMESTAMP WITH TIME ZONE` | Timestamp when the request was submitted.                                        |
| `started_processing_at`    | `TIMESTAMP WITH TIME ZONE` | Timestamp when processing began.                                                 |
| `completed_at`             | `TIMESTAMP WITH TIME ZONE` | Timestamp when processing completed.                                             |
| `content_type`             | `TEXT`                     | Extracted content type from content_strategy JSONB.                              |
| `target_audience`          | `TEXT`                     | Extracted target audience from content_strategy JSONB.                           |
| `main_goals`               | `TEXT`                     | Extracted goals from content_strategy JSONB.                                     |
| `full_content_strategy`    | `JSONB`                    | Complete content_strategy object from the queue.                                 |
| `active_competitors_count` | `INTEGER`                  | Count of active competitors for this analysis.                                   |
| `total_competitors_count`  | `INTEGER`                  | Total count of all competitors (active and inactive).                            |

## Related API Endpoints

1.  **GET `/api/viral-ideas/queue/{session_id}`**: ([Details](../api/get_viral_ideas_queue.md))
    -   Primary consumer of this view for single-query efficiency.
2.  **GET `/api/viral-ideas/queue-status`**: ([Details](../api/get_viral_ideas_queue_status.md))
    -   Uses this view to fetch recent queue items with enhanced metadata.
3.  **POST `/api/viral-ideas/queue/{queue_id}/process`**: ([Details](../api/trigger_viral_analysis_processing.md))
    -   Queries this view for comprehensive job data assembly.
4.  **POST `/api/viral-ideas/process-pending`**: ([Details](../api/process_pending_viral_ideas.md))
    -   Uses this view to identify pending and stuck processing items.

## View Definition

```sql
-- View to get queue items with competitor count and form data
CREATE VIEW viral_queue_summary AS
SELECT
    q.id,
    q.session_id,
    q.primary_username,
    q.status,
    q.priority,
    q.progress_percentage,
    q.auto_rerun_enabled,
    q.rerun_frequency_hours,
    q.last_analysis_at,
    q.next_scheduled_run,
    q.total_runs,
    q.submitted_at,
    q.started_processing_at,
    q.completed_at,
    -- Form responses (easily accessible)
    extract_content_strategy_field(q.content_strategy, 'contentType') as content_type,
    extract_content_strategy_field(q.content_strategy, 'targetAudience') as target_audience,
    extract_content_strategy_field(q.content_strategy, 'goals') as main_goals,
    q.content_strategy as full_content_strategy,
    COUNT(c.id) FILTER (WHERE c.is_active = TRUE) as active_competitors_count,
    COUNT(c.id) as total_competitors_count
FROM viral_ideas_queue q
LEFT JOIN viral_ideas_competitors c ON q.id = c.queue_id
GROUP BY q.id, q.session_id, q.primary_username, q.status, q.priority, q.progress_percentage,
         q.auto_rerun_enabled, q.rerun_frequency_hours, q.last_analysis_at, q.next_scheduled_run,
         q.total_runs, q.submitted_at, q.started_processing_at, q.completed_at, q.content_strategy;
```

## Performance Benefits

-   **Single Query Efficiency**: Eliminates complex JOINs in application code
-   **Pre-aggregated Data**: Competitor counts calculated at view level
-   **Extracted Form Fields**: Content strategy fields readily accessible as columns
-   **Optimized for APIs**: Designed specifically for frequent API endpoint queries
