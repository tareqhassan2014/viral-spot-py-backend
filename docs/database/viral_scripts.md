# Table: `viral_scripts`

Stores full scripts generated from user reel transcripts and AI analysis. This table contains complete, ready-to-use content scripts based on viral patterns discovered in the analysis, with detailed metadata about generation and structure.

## Schema

This table contains 17 columns.

| Column                   | Type                       | Description                                                        |
| ------------------------ | -------------------------- | ------------------------------------------------------------------ |
| `id`                     | `UUID`                     | Primary key, auto-generated.                                       |
| `analysis_id`            | `UUID`                     | Foreign key referencing `viral_analysis_results.id`.               |
| `script_title`           | `VARCHAR(255)`             | Title or name of the generated script.                             |
| `script_content`         | `TEXT`                     | Full script content based on user's reel transcripts.              |
| `script_type`            | `VARCHAR(50)`              | Type of script (`reel`, `story`, `post`, etc.).                    |
| `estimated_duration`     | `INTEGER`                  | Estimated duration in seconds for the script.                      |
| `target_audience`        | `VARCHAR(255)`             | Target demographic for this script.                                |
| `primary_hook`           | `TEXT`                     | Main hook or opening line for the script.                          |
| `call_to_action`         | `TEXT`                     | Call-to-action element for the script.                             |
| `source_reels`           | `JSONB`                    | Array of content_ids used as inspiration for this script.          |
| `script_structure`       | `JSONB`                    | Breakdown of script sections (intro, hook, body, CTA) with timing. |
| `generation_prompt`      | `TEXT`                     | AI prompt used to generate this script.                            |
| `ai_model`               | `VARCHAR(100)`             | AI model used for script generation.                               |
| `generation_temperature` | `NUMERIC`                  | Creativity setting used during AI generation (0-1).                |
| `status`                 | `VARCHAR(50)`              | Script status (`draft`, `reviewed`, `approved`, `published`).      |
| `created_at`             | `TIMESTAMP WITH TIME ZONE` | Timestamp when the script was generated.                           |
| `updated_at`             | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last update.                                      |

## Related API Endpoints

1.  **GET `/api/viral-analysis/{queue_id}/results`**: ([Details](../api/get_viral_analysis_results.md))
    -   Includes generated scripts in the complete analysis results.
2.  **POST `/api/viral-ideas/queue/{queue_id}/process`**: ([Details](../api/trigger_viral_analysis_processing.md))
    -   Creates script records during the AI processing pipeline.

## Nest.js Mongoose Schema

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Schema as MongooseSchema } from "mongoose";

export type ViralScriptsDocument = ViralScripts & Document;

@Schema({ timestamps: true, collection: "viral_scripts" })
export class ViralScripts {
    @Prop({
        type: MongooseSchema.Types.ObjectId,
        ref: "ViralAnalysisResults",
        required: true,
        index: true,
    })
    analysis_id: MongooseSchema.Types.ObjectId;

    @Prop({ type: String, required: true })
    script_title: string;

    @Prop({ type: String, required: true })
    script_content: string;

    @Prop({
        type: String,
        enum: ["reel", "story", "post", "youtube", "tiktok"],
        default: "reel",
    })
    script_type: string;

    @Prop({ type: Number, min: 0 })
    estimated_duration: number;

    @Prop(String)
    target_audience: string;

    @Prop(String)
    primary_hook: string;

    @Prop(String)
    call_to_action: string;

    @Prop({
        type: [String],
        default: [],
        validate: {
            validator: function (v: string[]) {
                // Ensure all content_ids are valid format
                return v.every((id) => typeof id === "string" && id.length > 0);
            },
            message: "source_reels must contain valid content_id strings",
        },
    })
    source_reels: string[];

    @Prop({
        type: MongooseSchema.Types.Mixed,
        default: {},
        validate: {
            validator: function (v: any) {
                // Basic structure validation for script breakdown
                if (!v || Object.keys(v).length === 0) return true;
                return typeof v === "object";
            },
            message: "script_structure must be a valid object",
        },
    })
    script_structure: {
        intro?: any;
        hook?: any;
        body?: any;
        cta?: any;
        timing?: any;
        voice_elements?: any;
    };

    @Prop(String)
    generation_prompt: string;

    @Prop({ type: String, default: "gpt-4o-mini" })
    ai_model: string;

    @Prop({
        type: MongooseSchema.Types.Decimal128,
        default: 0.8,
        min: 0,
        max: 1,
    })
    generation_temperature: number;

    @Prop({
        type: String,
        enum: ["draft", "reviewed", "approved", "published"],
        default: "draft",
        index: true,
    })
    status: string;
}

export const ViralScriptsSchema = SchemaFactory.createForClass(ViralScripts);

// Performance indexes
ViralScriptsSchema.index({ analysis_id: 1, script_type: 1 });
ViralScriptsSchema.index({ status: 1, createdAt: -1 });
ViralScriptsSchema.index({ script_type: 1, status: 1 });
```
