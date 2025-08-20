# Table: `viral_ideas_competitors`

Stores competitor selections for each viral ideas analysis. This table tracks which competitor profiles are being analyzed alongside the primary profile, including selection method and processing status.

## Schema

This table contains 11 columns.

| Column                | Type                       | Description                                                         |
| --------------------- | -------------------------- | ------------------------------------------------------------------- |
| `id`                  | `UUID`                     | Primary key, auto-generated.                                        |
| `queue_id`            | `UUID`                     | Foreign key referencing `viral_ideas_queue.id`.                     |
| `competitor_username` | `VARCHAR(255)`             | Username of the competitor profile being analyzed.                  |
| `selection_method`    | `VARCHAR(50)`              | How the competitor was selected (`suggested`, `manual`, `api`).     |
| `is_active`           | `BOOLEAN`                  | Whether this competitor is still active in the analysis.            |
| `processing_status`   | `VARCHAR(50)`              | Processing status (`pending`, `processing`, `completed`, `failed`). |
| `added_at`            | `TIMESTAMP WITH TIME ZONE` | Timestamp when the competitor was added to the analysis.            |
| `removed_at`          | `TIMESTAMP WITH TIME ZONE` | Timestamp when the competitor was removed (if applicable).          |
| `processed_at`        | `TIMESTAMP WITH TIME ZONE` | Timestamp when processing completed for this competitor.            |
| `error_message`       | `TEXT`                     | Error details if competitor processing fails.                       |
| `created_at`          | `TIMESTAMP WITH TIME ZONE` | Timestamp when the record was created (automatic via timestamps).   |
| `updated_at`          | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last update (automatic via timestamps).            |

## Related API Endpoints

1.  **POST `/api/viral-ideas/queue`**: ([Details](../api/create_viral_ideas_queue.md))
    -   Creates competitor entries when creating a new viral analysis queue.
2.  **GET `/api/viral-ideas/queue/{session_id}`**: ([Details](../api/get_viral_ideas_queue.md))
    -   Includes competitor information in queue status responses.
3.  **POST `/api/viral-ideas/queue/{queue_id}/process`**: ([Details](../api/trigger_viral_analysis_processing.md))
    -   Updates competitor processing status during analysis.
4.  **POST `/api/profile/{primary_username}/add-competitor/{target_username}`**: ([Details](../api/add_manual_competitor.md))
    -   Manually adds competitors to existing analyses.

## Nest.js Mongoose Schema

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Schema as MongooseSchema } from "mongoose";

export type ViralIdeasCompetitorDocument = ViralIdeasCompetitor & Document;

@Schema({ timestamps: true, collection: "viral_ideas_competitors" })
export class ViralIdeasCompetitor {
    @Prop({
        type: MongooseSchema.Types.ObjectId,
        ref: "ViralIdeasQueue",
        required: true,
        index: true,
    })
    queue_id: MongooseSchema.Types.ObjectId;

    @Prop({ type: String, required: true, index: true })
    competitor_username: string;

    @Prop({
        type: String,
        enum: ["suggested", "manual", "api"],
        default: "suggested",
    })
    selection_method: string;

    @Prop({ type: Boolean, default: true, index: true })
    is_active: boolean;

    @Prop({
        type: String,
        enum: ["pending", "processing", "completed", "failed"],
        default: "pending",
        index: true,
    })
    processing_status: string;

    @Prop({ type: Date, default: Date.now })
    added_at: Date;

    @Prop(Date)
    removed_at: Date;

    @Prop(Date)
    processed_at: Date;

    @Prop(String)
    error_message: string;
}

export const ViralIdeasCompetitorSchema =
    SchemaFactory.createForClass(ViralIdeasCompetitor);

// Performance indexes
ViralIdeasCompetitorSchema.index({ queue_id: 1, is_active: 1 });
ViralIdeasCompetitorSchema.index({ competitor_username: 1 });
ViralIdeasCompetitorSchema.index(
    { queue_id: 1, competitor_username: 1 },
    { unique: true }
);
```
