# Table: `content`

Stores individual pieces of content (reels, posts) from primary profiles. This table is at the heart of the content analysis features.

## Schema

This table contains 27 columns.

| Column                      | Type                       | Description                                                                                           |
| --------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------- |
| `id`                        | `UUID`                     | Primary key, auto-generated.                                                                          |
| `content_id`                | `VARCHAR(255)`             | Unique ID of the content from the social media platform.                                              |
| `shortcode`                 | `VARCHAR(255)`             | Short URL code for the content.                                                                       |
| `content_type`              | `content_type` (ENUM)      | Type of content (`reel`, `post`, `story`).                                                            |
| `url`                       | `TEXT`                     | The direct URL to the content.                                                                        |
| `description`               | `TEXT`                     | The caption or description of the content.                                                            |
| `thumbnail_url`             | `TEXT`                     | URL of the content's thumbnail image.                                                                 |
| `thumbnail_path`            | `TEXT`                     | Path to the thumbnail in the Supabase storage bucket.                                                 |
| `display_url_path`          | `TEXT`                     | Path to the main display image in the storage bucket.                                                 |
| `video_thumbnail_path`      | `TEXT`                     | Path to the video thumbnail in the storage bucket.                                                    |
| `view_count`                | `BIGINT`                   | The number of views for the content.                                                                  |
| `like_count`                | `BIGINT`                   | The number of likes for the content.                                                                  |
| `comment_count`             | `BIGINT`                   | The number of comments on the content.                                                                |
| `outlier_score`             | `DECIMAL(10,4)`            | A calculated score indicating how much the content's performance deviates from the profile's average. |
| `date_posted`               | `TIMESTAMP WITH TIME ZONE` | The date and time the content was posted.                                                             |
| `username`                  | `VARCHAR(255)`             | The username of the profile that posted the content.                                                  |
| `language`                  | `VARCHAR(10)`              | The primary language of the content.                                                                  |
| `content_style`             | `VARCHAR(50)`              | The style of the content (e.g., `video`, `image`).                                                    |
| `primary_category`          | `VARCHAR(100)`             | The primary category of the content.                                                                  |
| `secondary_category`        | `VARCHAR(100)`             | The secondary category of the content.                                                                |
| `tertiary_category`         | `VARCHAR(100)`             | The tertiary category of the content.                                                                 |
| `categorization_confidence` | `DECIMAL(3,2)`             | The confidence score for the content categorization.                                                  |
| `keyword_1` - `keyword_4`   | `VARCHAR(100)`             | Keywords extracted from the content.                                                                  |
| `all_image_urls`            | `JSONB`                    | A JSON object containing all image URLs associated with the content (for carousels).                  |
| `created_at`                | `TIMESTAMP WITH TIME ZONE` | Timestamp of when the record was created.                                                             |
| `updated_at`                | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last update.                                                                         |
| `profile_id`                | `UUID`                     | Foreign key referencing `primary_profiles(id)`. The profile that posted this.                         |

## Related API Endpoints

1.  **GET `/api/reels`**: ([Details](../api/get_reels.md))
    -   The main endpoint for querying this table to find reels based on various filters.
2.  **GET `/api/posts`**: ([Details](../api/get_posts.md))
    -   Queries this table, specifically filtering for content where `content_type` is `post`.
3.  **GET `/api/profile/{username}/reels`**: ([Details](../api/get_profile_reels.md))
    -   Fetches all content from this table for a specific username.
4.  **GET `/api/content/competitor/{username}`**: ([Details](../api/get_competitor_content.md))
    -   Fetches content from this table for a specific competitor's username.
5.  **GET `/api/content/user/{username}`**: ([Details](../api/get_user_content.md))
    -   Fetches content from this table for the user's own profile.
6.  **GET `/api/viral-analysis/{queue_id}/content`**: ([Details](../api/get_viral_analysis_content.md))
    -   Retrieves the specific content items from this table that were used in an analysis.

## Nest.js Mongoose Schema

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Schema as MongooseSchema } from "mongoose";
import { PrimaryProfile } from "./primary-profile.schema";

export type ContentDocument = Content & Document;

@Schema({ timestamps: true, collection: "content" })
export class Content {
    @Prop({ type: String, required: true, unique: true })
    content_id: string;

    @Prop({ type: String, required: true, unique: true, index: true })
    shortcode: string;

    @Prop({
        type: String,
        enum: ["reel", "post", "story"],
        default: "reel",
    })
    content_type: string;

    @Prop(String)
    url: string;

    @Prop(String)
    description: string;

    @Prop(String)
    thumbnail_url: string;

    @Prop(String)
    thumbnail_path: string;

    @Prop(String)
    display_url_path: string;

    @Prop(String)
    video_thumbnail_path: string;

    @Prop({ type: Number, default: 0, index: true })
    view_count: number;

    @Prop({ type: Number, default: 0 })
    like_count: number;

    @Prop({ type: Number, default: 0 })
    comment_count: number;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.0 })
    outlier_score: number;

    @Prop({ type: Date, index: true })
    date_posted: Date;

    @Prop({ type: String, required: true, index: true })
    username: string;

    @Prop({ type: String, default: "en" })
    language: string;

    @Prop({ type: String, default: "video" })
    content_style: string;

    @Prop({ type: String, index: true })
    primary_category: string;

    @Prop(String)
    secondary_category: string;

    @Prop(String)
    tertiary_category: string;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
    categorization_confidence: number;

    @Prop([String])
    keywords: string[];

    @Prop({ type: MongooseSchema.Types.Mixed })
    all_image_urls: any;

    @Prop({
        type: MongooseSchema.Types.ObjectId,
        ref: "PrimaryProfile",
        index: true,
    })
    profile_id: PrimaryProfile;
}

export const ContentSchema = SchemaFactory.createForClass(Content);
```
