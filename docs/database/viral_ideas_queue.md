# Table: `viral_ideas_queue`

Tracks form submissions and competitor selections for viral ideas analysis. This table serves as the central queue system for managing AI-powered viral content analysis jobs, storing user preferences and processing status.

## Schema

This table contains 20 columns.

| Column                  | Type                       | Description                                                                          |
| ----------------------- | -------------------------- | ------------------------------------------------------------------------------------ |
| `id`                    | `UUID`                     | Primary key, auto-generated.                                                         |
| `session_id`            | `VARCHAR(255)`             | Unique session identifier for tracking user requests.                                |
| `primary_username`      | `VARCHAR(255)`             | Username of the primary profile being analyzed.                                      |
| `content_strategy`      | `JSONB`                    | Form data from viral ideas flow containing content type, target audience, and goals. |
| `analysis_settings`     | `JSONB`                    | Additional settings and preferences for the analysis.                                |
| `status`                | `VARCHAR(50)`              | Current queue status (`pending`, `processing`, `completed`, `failed`, `paused`).     |
| `priority`              | `INTEGER`                  | Processing priority (1=highest, 10=lowest).                                          |
| `current_step`          | `VARCHAR(100)`             | Current processing step for progress tracking.                                       |
| `progress_percentage`   | `INTEGER`                  | Progress percentage (0-100) of the analysis.                                         |
| `error_message`         | `TEXT`                     | Error details if processing fails.                                                   |
| `auto_rerun_enabled`    | `BOOLEAN`                  | Whether to automatically re-run analysis periodically.                               |
| `rerun_frequency_hours` | `INTEGER`                  | How often to re-run analysis in hours (default: 24).                                 |
| `last_analysis_at`      | `TIMESTAMP WITH TIME ZONE` | Timestamp when analysis was last completed.                                          |
| `next_scheduled_run`    | `TIMESTAMP WITH TIME ZONE` | Timestamp for next scheduled automatic run.                                          |
| `total_runs`            | `INTEGER`                  | Total number of times this analysis has been executed.                               |
| `submitted_at`          | `TIMESTAMP WITH TIME ZONE` | Timestamp when the request was submitted.                                            |
| `started_processing_at` | `TIMESTAMP WITH TIME ZONE` | Timestamp when processing began.                                                     |
| `completed_at`          | `TIMESTAMP WITH TIME ZONE` | Timestamp when processing completed.                                                 |
| `created_at`            | `TIMESTAMP WITH TIME ZONE` | Timestamp when the record was created.                                               |
| `updated_at`            | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last update.                                                        |

## Related API Endpoints

1.  **POST `/api/viral-ideas/queue`**: ([Details](../api/create_viral_ideas_queue.md))
    -   Creates a new viral ideas analysis job and adds it to the queue.
2.  **GET `/api/viral-ideas/queue/{session_id}`**: ([Details](../api/get_viral_ideas_queue.md))
    -   Retrieves the status of a specific viral ideas analysis job from the queue.
3.  **GET `/api/viral-ideas/check-existing/{username}`**: ([Details](../api/check_existing_viral_analysis.md))
    -   Checks if there's already an existing analysis for a profile with duplicate prevention.
4.  **POST `/api/viral-ideas/queue/{queue_id}/start`**: ([Details](../api/start_viral_analysis.md))
    -   Signals a queued analysis job as ready for background worker processing.
5.  **POST `/api/viral-ideas/queue/{queue_id}/process`**: ([Details](../api/trigger_viral_analysis_processing.md))
    -   Immediately triggers the processing of a specific item in the queue.
6.  **POST `/api/viral-ideas/process-pending`**: ([Details](../api/process_pending_viral_ideas.md))
    -   Processes all pending items in the viral ideas queue.
7.  **GET `/api/viral-ideas/queue-status`**: ([Details](../api/get_viral_ideas_queue_status.md))
    -   Gets overall statistics for the viral ideas queue.
8.  **GET `/api/viral-analysis/{queue_id}/results`**: ([Details](../api/get_viral_analysis_results.md))
    -   Retrieves the final results of a viral analysis job.
9.  **GET `/api/viral-analysis/{queue_id}/content`**: ([Details](../api/get_viral_analysis_content.md))
    -   Retrieves the content that was analyzed as part of a job.

## Nest.js Mongoose Schema

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Schema as MongooseSchema } from "mongoose";

export type ViralIdeasQueueDocument = ViralIdeasQueue & Document;

@Schema({ timestamps: true, collection: "viral_ideas_queue" })
export class ViralIdeasQueue {
    @Prop({ type: String, required: true, unique: true, index: true })
    session_id: string;

    @Prop({ type: String, required: true, index: true })
    primary_username: string;

    @Prop({
        type: MongooseSchema.Types.Mixed,
        default: {},
        validate: {
            validator: function (v: any) {
                // Validate content_strategy structure
                if (!v || Object.keys(v).length === 0) return true;
                return v.contentType && v.targetAudience && v.goals;
            },
            message:
                "content_strategy must include contentType, targetAudience, and goals",
        },
    })
    content_strategy: {
        contentType?: string; // "What type of content do you create?"
        targetAudience?: string; // "Who is your target audience?"
        goals?: string; // "What are your main goals?"
    };

    @Prop({ type: MongooseSchema.Types.Mixed, default: {} })
    analysis_settings: Record<string, any>;

    @Prop({
        type: String,
        enum: ["pending", "processing", "completed", "failed", "paused"],
        default: "pending",
        index: true,
    })
    status: string;

    @Prop({ type: Number, default: 5, min: 1, max: 10 })
    priority: number;

    @Prop(String)
    current_step: string;

    @Prop({ type: Number, default: 0, min: 0, max: 100 })
    progress_percentage: number;

    @Prop(String)
    error_message: string;

    @Prop({ type: Boolean, default: true })
    auto_rerun_enabled: boolean;

    @Prop({ type: Number, default: 24, min: 1 })
    rerun_frequency_hours: number;

    @Prop(Date)
    last_analysis_at: Date;

    @Prop(Date)
    next_scheduled_run: Date;

    @Prop({ type: Number, default: 0 })
    total_runs: number;

    @Prop({ type: Date, default: Date.now, index: true })
    submitted_at: Date;

    @Prop(Date)
    started_processing_at: Date;

    @Prop(Date)
    completed_at: Date;
}

export const ViralIdeasQueueSchema =
    SchemaFactory.createForClass(ViralIdeasQueue);

// Performance indexes
ViralIdeasQueueSchema.index({ status: 1, priority: 1 });
ViralIdeasQueueSchema.index({ auto_rerun_enabled: 1, next_scheduled_run: 1 });
ViralIdeasQueueSchema.index({ primary_username: 1, status: 1 });
```
