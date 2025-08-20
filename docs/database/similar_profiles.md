# Table: `similar_profiles`

Stores a lightweight list of similar profiles for a given primary profile. This table is optimized for fast read operations, making it ideal for the high-performance `/similar-fast` endpoint.

## Schema

This table contains 12 columns.

| Column               | Type                       | Description                                                  |
| -------------------- | -------------------------- | ------------------------------------------------------------ |
| `id`                 | `UUID`                     | Primary key, auto-generated.                                 |
| `primary_username`   | `VARCHAR(255)`             | The main profile these are similar to.                       |
| `similar_username`   | `VARCHAR(255)`             | The username of the similar profile.                         |
| `similar_name`       | `VARCHAR(255)`             | The display name of the similar profile.                     |
| `profile_image_path` | `TEXT`                     | Path to the profile image in the Supabase storage bucket.    |
| `profile_image_url`  | `TEXT`                     | The CDN URL for the stored profile image.                    |
| `similarity_rank`    | `INTEGER`                  | The rank of similarity (1 is the most similar).              |
| `batch_id`           | `UUID`                     | An ID to group profiles that were fetched in the same batch. |
| `image_downloaded`   | `BOOLEAN`                  | A flag to track if the profile image has been downloaded.    |
| `fetch_failed`       | `BOOLEAN`                  | A flag to mark profiles that failed to be fetched.           |
| `created_at`         | `TIMESTAMP WITH TIME ZONE` | Timestamp of when the record was created.                    |
| `updated_at`         | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last update.                                |

## Related API Endpoints

1.  **GET `/api/profile/{username}/similar-fast`**: ([Details](../api/get_similar_profiles_fast.md))
    -   This is the primary endpoint that reads from this table to quickly fetch similar profiles.
2.  **POST `/api/profile/{primary_username}/add-competitor/{target_username}`**: ([Details](../api/add_manual_competitor.md))
    -   This endpoint writes to this table when a user manually adds a competitor.

## Nest.js Mongoose Schema

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document } from "mongoose";

export type SimilarProfileDocument = SimilarProfile & Document;

@Schema({ timestamps: true, collection: "similar_profiles" })
export class SimilarProfile {
    @Prop({ type: String, required: true, index: true })
    primary_username: string;

    @Prop({ type: String, required: true })
    similar_username: string;

    @Prop(String)
    similar_name: string;

    @Prop(String)
    profile_image_path: string;

    @Prop(String)
    profile_image_url: string;

    @Prop({ type: Number, default: 0 })
    similarity_rank: number;

    @Prop({ type: String, index: true })
    batch_id: string;

    @Prop({ type: Boolean, default: false })
    image_downloaded: boolean;

    @Prop({ type: Boolean, default: false })
    fetch_failed: boolean;
}

export const SimilarProfileSchema =
    SchemaFactory.createForClass(SimilarProfile);

// Compound index for the main lookup query
SimilarProfileSchema.index({ primary_username: 1, similarity_rank: 1 });
```
