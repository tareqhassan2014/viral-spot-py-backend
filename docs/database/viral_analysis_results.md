# Table: `viral_analysis_results`

Stores the results of each viral ideas analysis run. This table contains the AI-generated analysis output, including viral ideas, trending patterns, and hook analysis from the N8N workflow processing.

## Schema

This table contains 16 columns.

| Column                     | Type                       | Description                                                                      |
| -------------------------- | -------------------------- | -------------------------------------------------------------------------------- |
| `id`                       | `UUID`                     | Primary key, auto-generated.                                                     |
| `queue_id`                 | `UUID`                     | Foreign key referencing `viral_ideas_queue.id`.                                  |
| `analysis_run`             | `INTEGER`                  | Sequential run number (1=initial, 2=first update, etc.).                         |
| `analysis_type`            | `VARCHAR(50)`              | Type of analysis (`initial` or `recurring`).                                     |
| `total_reels_analyzed`     | `INTEGER`                  | Total number of reels processed in this analysis.                                |
| `primary_reels_count`      | `INTEGER`                  | Number of primary profile reels analyzed.                                        |
| `competitor_reels_count`   | `INTEGER`                  | Number of competitor reels analyzed.                                             |
| `transcripts_fetched`      | `INTEGER`                  | Number of transcripts successfully obtained.                                     |
| `analysis_data`            | `JSONB`                    | Flexible analysis storage with AI results (hooks, patterns, profile analysis).   |
| `workflow_version`         | `VARCHAR(50)`              | Version of the AI workflow used for analysis.                                    |
| `status`                   | `VARCHAR(50)`              | Analysis status (`pending`, `transcribing`, `analyzing`, `completed`, `failed`). |
| `error_message`            | `TEXT`                     | Error details if analysis fails.                                                 |
| `started_at`               | `TIMESTAMP WITH TIME ZONE` | Timestamp when analysis processing began.                                        |
| `transcripts_completed_at` | `TIMESTAMP WITH TIME ZONE` | Timestamp when transcript fetching completed.                                    |
| `analysis_completed_at`    | `TIMESTAMP WITH TIME ZONE` | Timestamp when AI analysis completed.                                            |
| `created_at`               | `TIMESTAMP WITH TIME ZONE` | Timestamp when the record was created.                                           |

## Related API Endpoints

1.  **GET `/api/viral-analysis/{queue_id}/results`**: ([Details](../api/get_viral_analysis_results.md))
    -   Primary endpoint for retrieving completed analysis results.
2.  **POST `/api/viral-ideas/queue/{queue_id}/process`**: ([Details](../api/trigger_viral_analysis_processing.md))
    -   Creates and updates records in this table during processing.
3.  **POST `/api/viral-ideas/process-pending`**: ([Details](../api/process_pending_viral_ideas.md))
    -   Batch processes multiple analyses and stores results here.

## Nest.js Mongoose Schema

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Schema as MongooseSchema } from "mongoose";

export type ViralAnalysisResultsDocument = ViralAnalysisResults & Document;

@Schema({ timestamps: true, collection: "viral_analysis_results" })
export class ViralAnalysisResults {
    @Prop({
        type: MongooseSchema.Types.ObjectId,
        ref: "ViralIdeasQueue",
        required: true,
        index: true,
    })
    queue_id: MongooseSchema.Types.ObjectId;

    @Prop({ type: Number, default: 1 })
    analysis_run: number;

    @Prop({
        type: String,
        enum: ["initial", "recurring"],
        default: "initial",
    })
    analysis_type: string;

    @Prop({ type: Number, default: 0 })
    total_reels_analyzed: number;

    @Prop({ type: Number, default: 0 })
    primary_reels_count: number;

    @Prop({ type: Number, default: 0 })
    competitor_reels_count: number;

    @Prop({ type: Number, default: 0 })
    transcripts_fetched: number;

    @Prop({
        type: MongooseSchema.Types.Mixed,
        default: {},
        validate: {
            validator: function (v: any) {
                // Ensure workflow_version exists if analysis_data is populated
                if (v && Object.keys(v).length > 0) {
                    return v.workflow_version !== undefined;
                }
                return true;
            },
            message:
                "analysis_data must include workflow_version when populated",
        },
    })
    analysis_data: {
        workflow_version?: string;
        analysis_timestamp?: string;
        profile_analysis?: any;
        individual_reel_analyses?: any[];
        generated_hooks?: any[];
        complete_scripts?: any[];
        scripts_summary?: any[];
        analysis_summary?: any;
    };

    @Prop({ type: String, default: "v2_json" })
    workflow_version: string;

    @Prop({
        type: String,
        enum: ["pending", "transcribing", "analyzing", "completed", "failed"],
        default: "pending",
        index: true,
    })
    status: string;

    @Prop(String)
    error_message: string;

    @Prop(Date)
    started_at: Date;

    @Prop(Date)
    transcripts_completed_at: Date;

    @Prop(Date)
    analysis_completed_at: Date;
}

export const ViralAnalysisResultsSchema =
    SchemaFactory.createForClass(ViralAnalysisResults);

// Performance indexes
ViralAnalysisResultsSchema.index({ queue_id: 1, analysis_run: -1 });
ViralAnalysisResultsSchema.index({ status: 1, started_at: -1 });
ViralAnalysisResultsSchema.index({ workflow_version: 1 });
```
