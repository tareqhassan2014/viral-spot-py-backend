# Table: `viral_analysis_reels`

Tracks which specific reels were used in each viral analysis. This table maintains a record of both primary and competitor reels selected for analysis, including their performance metrics at the time of analysis and transcript processing status.

## Schema

This table contains 19 columns.

| Column                      | Type                       | Description                                                                      |
| --------------------------- | -------------------------- | -------------------------------------------------------------------------------- |
| `id`                        | `UUID`                     | Primary key, auto-generated.                                                     |
| `analysis_id`               | `UUID`                     | Foreign key referencing `viral_analysis_results.id`.                             |
| `content_id`                | `VARCHAR(255)`             | Links to `content.content_id` for the reel data.                                 |
| `reel_type`                 | `VARCHAR(20)`              | Type of reel (`primary` or `competitor`).                                        |
| `username`                  | `VARCHAR(255)`             | Username of the profile this reel belongs to.                                    |
| `selection_reason`          | `VARCHAR(100)`             | Why this reel was selected (`top_performer_last_month`, `newly_trending`, etc.). |
| `rank_in_selection`         | `INTEGER`                  | Ranking within its category (1-3 for primary, 1-5 for competitors).              |
| `view_count_at_analysis`    | `BIGINT`                   | View count when the reel was analyzed.                                           |
| `like_count_at_analysis`    | `BIGINT`                   | Like count when the reel was analyzed.                                           |
| `comment_count_at_analysis` | `BIGINT`                   | Comment count when the reel was analyzed.                                        |
| `outlier_score_at_analysis` | `NUMERIC`                  | Outlier score calculated at time of analysis.                                    |
| `transcript_requested`      | `BOOLEAN`                  | Whether transcript was requested for this reel.                                  |
| `transcript_completed`      | `BOOLEAN`                  | Whether transcript processing completed successfully.                            |
| `transcript_error`          | `TEXT`                     | Error message if transcript processing failed.                                   |
| `hook_text`                 | `TEXT`                     | The actual hook (first sentence) extracted from the reel.                        |
| `power_words`               | `JSONB`                    | Array of power words identified in the hook.                                     |
| `analysis_metadata`         | `JSONB`                    | Flexible metadata storage for additional analysis data.                          |
| `selected_at`               | `TIMESTAMP WITH TIME ZONE` | Timestamp when the reel was selected for analysis.                               |
| `transcript_fetched_at`     | `TIMESTAMP WITH TIME ZONE` | Timestamp when transcript was successfully fetched.                              |

## Related API Endpoints

1.  **GET `/api/viral-analysis/{queue_id}/content`**: ([Details](../api/get_viral_analysis_content.md))
    -   Retrieves the content that was analyzed, sourced from this table.
2.  **POST `/api/viral-ideas/queue/{queue_id}/process`**: ([Details](../api/trigger_viral_analysis_processing.md))
    -   Creates records in this table when selecting reels for analysis.
3.  **GET `/api/viral-analysis/{queue_id}/results`**: ([Details](../api/get_viral_analysis_results.md))
    -   May include reel-level analysis data from this table.

## Nest.js Mongoose Schema

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Schema as MongooseSchema } from "mongoose";

export type ViralAnalysisReelsDocument = ViralAnalysisReels & Document;

@Schema({
    timestamps: { createdAt: "selected_at", updatedAt: false },
    collection: "viral_analysis_reels",
})
export class ViralAnalysisReels {
    @Prop({
        type: MongooseSchema.Types.ObjectId,
        ref: "ViralAnalysisResults",
        required: true,
        index: true,
    })
    analysis_id: MongooseSchema.Types.ObjectId;

    @Prop({ type: String, required: true, index: true })
    content_id: string;

    @Prop({
        type: String,
        enum: ["primary", "competitor"],
        required: true,
        index: true,
    })
    reel_type: string;

    @Prop({ type: String, required: true, index: true })
    username: string;

    @Prop(String)
    selection_reason: string;

    @Prop({ type: Number, default: 0, min: 0 })
    rank_in_selection: number;

    @Prop({ type: Number, default: 0 })
    view_count_at_analysis: number;

    @Prop({ type: Number, default: 0 })
    like_count_at_analysis: number;

    @Prop({ type: Number, default: 0 })
    comment_count_at_analysis: number;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.0 })
    outlier_score_at_analysis: number;

    @Prop({ type: Boolean, default: false })
    transcript_requested: boolean;

    @Prop({ type: Boolean, default: false, index: true })
    transcript_completed: boolean;

    @Prop(String)
    transcript_error: string;

    @Prop(String)
    hook_text: string;

    @Prop({ type: [String], default: [] })
    power_words: string[];

    @Prop({ type: MongooseSchema.Types.Mixed, default: {} })
    analysis_metadata: Record<string, any>;

    @Prop({ type: Date, default: Date.now })
    selected_at: Date;

    @Prop(Date)
    transcript_fetched_at: Date;
}

export const ViralAnalysisReelsSchema =
    SchemaFactory.createForClass(ViralAnalysisReels);

// Performance indexes
ViralAnalysisReelsSchema.index({
    analysis_id: 1,
    reel_type: 1,
    rank_in_selection: 1,
});
ViralAnalysisReelsSchema.index(
    { analysis_id: 1, content_id: 1 },
    { unique: true }
);
ViralAnalysisReelsSchema.index({
    transcript_completed: 1,
    transcript_fetched_at: -1,
});
```
