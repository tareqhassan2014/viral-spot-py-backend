# Table: `primary_profiles`

Stores the main profiles for which content has been fetched and analyzed. This is a central table in the database, linking to content and discovered profiles.

## Schema

This table contains 51 columns.

| Column                                   | Type                       | Description                                                                |
| ---------------------------------------- | -------------------------- | -------------------------------------------------------------------------- |
| `id`                                     | `UUID`                     | Primary key, auto-generated.                                               |
| `username`                               | `VARCHAR(255)`             | Unique username of the profile.                                            |
| `profile_name`                           | `VARCHAR(255)`             | Display name of the profile.                                               |
| `bio`                                    | `TEXT`                     | Biography of the profile.                                                  |
| `followers`                              | `INTEGER`                  | Number of followers.                                                       |
| `posts_count`                            | `INTEGER`                  | Number of posts.                                                           |
| `is_verified`                            | `BOOLEAN`                  | Whether the profile is verified.                                           |
| `is_business_account`                    | `BOOLEAN`                  | Whether it's a business account.                                           |
| `profile_url`                            | `VARCHAR(500)`             | URL to the profile page.                                                   |
| `profile_image_url`                      | `TEXT`                     | URL of the profile image.                                                  |
| `profile_image_path`                     | `TEXT`                     | Path to the profile image in the Supabase storage bucket.                  |
| `hd_profile_image_path`                  | `TEXT`                     | Path to the high-definition profile image in the storage bucket.           |
| `account_type`                           | `account_type` (ENUM)      | Type of account (`Influencer`, `Theme Page`, `Business Page`, `Personal`). |
| `language`                               | `VARCHAR(10)`              | Primary language of the profile.                                           |
| `content_type`                           | `VARCHAR(50)`              | Main type of content the profile produces.                                 |
| `total_reels`                            | `INTEGER`                  | Total number of reels posted.                                              |
| `median_views`                           | `BIGINT`                   | Median views on the profile's content.                                     |
| `mean_views`                             | `DECIMAL(12,2)`            | Mean (average) views on the profile's content.                             |
| `std_views`                              | `DECIMAL(12,2)`            | Standard deviation of views.                                               |
| `total_views`                            | `BIGINT`                   | Total cumulative views on all content.                                     |
| `total_likes`                            | `BIGINT`                   | Total cumulative likes on all content.                                     |
| `total_comments`                         | `BIGINT`                   | Total cumulative comments on all content.                                  |
| `profile_primary_category`               | `VARCHAR(100)`             | Primary content category.                                                  |
| `profile_secondary_category`             | `VARCHAR(100)`             | Secondary content category.                                                |
| `profile_tertiary_category`              | `VARCHAR(100)`             | Tertiary content category.                                                 |
| `profile_categorization_confidence`      | `DECIMAL(3,2)`             | Confidence score for the profile categorization.                           |
| `account_type_confidence`                | `DECIMAL(3,2)`             | Confidence score for the account type estimation.                          |
| `similar_account1` - `similar_account20` | `VARCHAR(255)`             | Denormalized list of similar account usernames for performance.            |
| `last_full_scrape`                       | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last complete data scrape.                                |
| `analysis_timestamp`                     | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last AI analysis.                                         |
| `created_at`                             | `TIMESTAMP WITH TIME ZONE` | Timestamp of when the record was created.                                  |
| `updated_at`                             | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last update.                                              |

## Related API Endpoints

1.  **GET `/api/profile/{username}`**: ([Details](../api/get_profile.md))
    -   Fetches a single profile from this table to display on a profile page.
2.  **GET `/api/profile/{username}/reels`**: ([Details](../api/get_profile_reels.md))
    -   Uses this table in a join to provide profile information for the reels.
3.  **GET `/api/profile/{username}/similar`**: ([Details](../api/get_similar_profiles.md))
    -   Starts by querying this table to find the `id` of the primary profile.
4.  **POST `/api/profile/{username}/request`**: ([Details](../api/request_profile_processing.md))
    -   Checks this table to see if a profile already exists before adding it to the queue.
5.  **GET `/api/profile/{username}/status`**: ([Details](../api/check_profile_status.md))
    -   Checks for the existence of a profile in this table to determine if processing is complete.
6.  **GET `/api/reels`**: ([Details](../api/get_reels.md))
    -   Joins with this table to filter by account-level metrics like follower count and account type.
7.  **GET `/api/viral-analysis/{queue_id}/results`**: ([Details](../api/get_viral_analysis_results.md))
    -   Fetches data from this table to include in the final analysis results.

## Nest.js Mongoose Schema

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Schema as MongooseSchema } from "mongoose";

export type PrimaryProfileDocument = PrimaryProfile & Document;

@Schema({ timestamps: true, collection: "primary_profiles" })
export class PrimaryProfile {
    @Prop({ type: String, required: true, unique: true, index: true })
    username: string;

    @Prop(String)
    profile_name: string;

    @Prop(String)
    bio: string;

    @Prop({ type: Number, default: 0, index: true })
    followers: number;

    @Prop({ type: Number, default: 0 })
    posts_count: number;

    @Prop({ type: Boolean, default: false })
    is_verified: boolean;

    @Prop({ type: Boolean, default: false })
    is_business_account: boolean;

    @Prop(String)
    profile_url: string;

    @Prop(String)
    profile_image_url: string;

    @Prop(String)
    profile_image_path: string;

    @Prop(String)
    hd_profile_image_path: string;

    @Prop({
        type: String,
        enum: ["Influencer", "Theme Page", "Business Page", "Personal"],
        default: "Personal",
        index: true,
    })
    account_type: string;

    @Prop({ type: String, default: "en" })
    language: string;

    @Prop({ type: String, default: "entertainment" })
    content_type: string;

    @Prop({ type: Number, default: 0 })
    total_reels: number;

    @Prop({ type: Number, default: 0, index: true })
    median_views: number;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.0 })
    mean_views: number;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.0 })
    std_views: number;

    @Prop({ type: Number, default: 0 })
    total_views: number;

    @Prop({ type: Number, default: 0 })
    total_likes: number;

    @Prop({ type: Number, default: 0 })
    total_comments: number;

    @Prop(String)
    profile_primary_category: string;

    @Prop(String)
    profile_secondary_category: string;

    @Prop(String)
    profile_tertiary_category: string;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
    profile_categorization_confidence: number;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
    account_type_confidence: number;

    @Prop([String])
    similar_accounts: string[]; // Store similar_account1-20 in an array

    @Prop(Date)
    last_full_scrape: Date;

    @Prop(Date)
    analysis_timestamp: Date;
}

export const PrimaryProfileSchema =
    SchemaFactory.createForClass(PrimaryProfile);

// Compound indexes for performance
PrimaryProfileSchema.index({ followers: 1, median_views: -1 });
```
