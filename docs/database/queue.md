# Table: `queue`

A task queue for processing profiles. This table manages the pipeline of scraping and analyzing new profiles.

## Schema

This table contains 12 columns.

| Column          | Type                       | Description                                                                  |
| --------------- | -------------------------- | ---------------------------------------------------------------------------- |
| `id`            | `UUID`                     | Primary key, auto-generated.                                                 |
| `username`      | `VARCHAR(255)`             | The username to be processed.                                                |
| `source`        | `VARCHAR(100)`             | The source of the request (e.g., `manual`, `frontend`).                      |
| `priority`      | `queue_priority` (ENUM)    | The priority of the task (`HIGH`, `LOW`).                                    |
| `status`        | `queue_status` (ENUM)      | Current status of the task (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`). |
| `attempts`      | `INTEGER`                  | The number of times this task has been attempted.                            |
| `last_attempt`  | `TIMESTAMP WITH TIME ZONE` | The timestamp of the last attempt.                                           |
| `error_message` | `TEXT`                     | Any error message if the task failed.                                        |
| `request_id`    | `VARCHAR(50)`              | A unique ID for the request, to prevent duplicate processing.                |
| `timestamp`     | `TIMESTAMP WITH TIME ZONE` | The timestamp of when the task was created.                                  |
| `created_at`    | `TIMESTAMP WITH TIME ZONE` | Timestamp of when the record was created.                                    |
| `updated_at`    | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last update.                                                |

## Related API Endpoints

1.  **POST `/api/profile/{username}/request`**: ([Details](../api/request_profile_processing.md))
    -   This is the main endpoint that adds new entries to this table.
2.  **GET `/api/profile/{username}/status`**: ([Details](../api/check_profile_status.md))
    -   Queries this table to check the current status of a processing job.

## Nest.js Mongoose Schema

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document } from "mongoose";

export type QueueDocument = Queue & Document;

@Schema({ timestamps: true, collection: "queue" })
export class Queue {
    @Prop({ type: String, required: true, index: true })
    username: string;

    @Prop({ type: String, default: "manual" })
    source: string;

    @Prop({
        type: String,
        enum: ["HIGH", "LOW"],
        default: "LOW",
        index: true,
    })
    priority: string;

    @Prop({
        type: String,
        enum: ["PENDING", "PROCESSING", "COMPLETED", "FAILED", "PAUSED"],
        default: "PENDING",
        index: true,
    })
    status: string;

    @Prop({ type: Number, default: 0 })
    attempts: number;

    @Prop(Date)
    last_attempt: Date;

    @Prop(String)
    error_message: string;

    @Prop({ type: String, unique: true, sparse: true })
    request_id: string;
}

export const QueueSchema = SchemaFactory.createForClass(Queue);
```
