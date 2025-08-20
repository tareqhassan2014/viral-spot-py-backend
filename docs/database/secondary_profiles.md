# Table: `secondary_profiles`

Stores similar profiles that have been discovered but not yet fully scraped. This table holds basic information about profiles that have been identified as similar to a `primary_profile`.

## Schema

This table contains 36 columns.

| Column                      | Type                       | Description                                                                           |
| --------------------------- | -------------------------- | ------------------------------------------------------------------------------------- |
| `id`                        | `UUID`                     | Primary key, auto-generated.                                                          |
| `username`                  | `VARCHAR(255)`             | Unique username of the profile.                                                       |
| `full_name`                 | `VARCHAR(255)`             | Display name of the profile.                                                          |
| `biography`                 | `TEXT`                     | Biography of the profile.                                                             |
| `followers_count`           | `INTEGER`                  | Number of followers.                                                                  |
| `following_count`           | `INTEGER`                  | Number of accounts the profile is following.                                          |
| `media_count`               | `INTEGER`                  | Number of posts.                                                                      |
| `profile_pic_url`           | `TEXT`                     | URL of the profile image.                                                             |
| `profile_pic_path`          | `TEXT`                     | Path to the profile image in the Supabase storage bucket.                             |
| `is_verified`               | `BOOLEAN`                  | Whether the profile is verified.                                                      |
| `is_private`                | `BOOLEAN`                  | Whether the profile is private.                                                       |
| `business_email`            | `VARCHAR(255)`             | Business email if available.                                                          |
| `external_url`              | `TEXT`                     | A URL included in the profile's bio.                                                  |
| `category`                  | `VARCHAR(100)`             | Category assigned by the social media platform.                                       |
| `pk`                        | `VARCHAR(255)`             | Platform-specific primary key.                                                        |
| `social_context`            | `TEXT`                     | Social context information (e.g., "Followed by...").                                  |
| `estimated_account_type`    | `account_type` (ENUM)      | Estimated account type (`Influencer`, `Theme Page`, `Business Page`, `Personal`).     |
| `primary_category`          | `VARCHAR(100)`             | Primary content category, estimated by our system.                                    |
| `secondary_category`        | `VARCHAR(100)`             | Secondary content category, estimated by our system.                                  |
| `tertiary_category`         | `VARCHAR(100)`             | Tertiary content category, estimated by our system.                                   |
| `categorization_confidence` | `DECIMAL(3,2)`             | Confidence score for the profile categorization.                                      |
| `account_type_confidence`   | `DECIMAL(3,2)`             | Confidence score for the account type estimation.                                     |
| `estimated_language`        | `VARCHAR(10)`              | Estimated primary language of the profile.                                            |
| `click_count`               | `INTEGER`                  | Number of times this profile has been clicked on as a suggestion.                     |
| `search_count`              | `INTEGER`                  | Number of times this profile has appeared in search results.                          |
| `promotion_eligible`        | `BOOLEAN`                  | Whether the profile is eligible for promotion.                                        |
| `discovered_by`             | `VARCHAR(255)`             | Username of the `primary_profile` that discovered this one.                           |
| `discovery_reason`          | `VARCHAR(100)`             | The reason for the discovery (e.g., `similar_to`).                                    |
| `api_source`                | `VARCHAR(100)`             | The API or source that provided this profile data.                                    |
| `similarity_rank`           | `INTEGER`                  | The rank of similarity to the `discovered_by` profile.                                |
| `last_basic_scrape`         | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last basic information scrape.                                       |
| `last_full_scrape`          | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last complete data scrape.                                           |
| `analysis_timestamp`        | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last AI analysis.                                                    |
| `created_at`                | `TIMESTAMP WITH TIME ZONE` | Timestamp of when the record was created.                                             |
| `updated_at`                | `TIMESTAMP WITH TIME ZONE` | Timestamp of the last update.                                                         |
| `discovered_by_id`          | `UUID`                     | Foreign key referencing `primary_profiles(id)`. The profile that discovered this one. |

## Related API Endpoints

1.  **GET `/api/profile/{username}/similar`**: ([Details](../api/get_similar_profiles.md))
    -   This is the primary endpoint that queries the `secondary_profiles` table to find profiles similar to a given primary profile.
2.  **GET `/api/profile/{username}/secondary`**: ([Details](../api/get_secondary_profile.md))
    -   Fetches a single profile from this table, often used for loading states or previews.

## Nest.js Mongoose Schema

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Schema as MongooseSchema } from "mongoose";
import { PrimaryProfile } from "./primary-profile.schema";

export type SecondaryProfileDocument = SecondaryProfile & Document;

@Schema({ timestamps: true, collection: "secondary_profiles" })
export class SecondaryProfile {
    @Prop({ type: String, required: true, unique: true, index: true })
    username: string;

    @Prop(String)
    full_name: string;

    @Prop(String)
    biography: string;

    @Prop({ type: Number, default: 0, index: true })
    followers_count: number;

    @Prop({ type: Number, default: 0 })
    following_count: number;

    @Prop({ type: Number, default: 0 })
    media_count: number;

    @Prop(String)
    profile_pic_url: string;

    @Prop(String)
    profile_pic_path: string;

    @Prop({ type: Boolean, default: false })
    is_verified: boolean;

    @Prop({ type: Boolean, default: false })
    is_private: boolean;

    @Prop(String)
    business_email: string;

    @Prop(String)
    external_url: string;

    @Prop(String)
    category: string;

    @Prop(String)
    pk: string;

    @Prop(String)
    social_context: string;

    @Prop({
        type: String,
        enum: ["Influencer", "Theme Page", "Business Page", "Personal"],
        default: "Personal",
    })
    estimated_account_type: string;

    @Prop(String)
    primary_category: string;

    @Prop(String)
    secondary_category: string;

    @Prop(String)
    tertiary_category: string;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
    categorization_confidence: number;

    @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
    account_type_confidence: number;

    @Prop({ type: String, default: "en" })
    estimated_language: string;

    @Prop({ type: Number, default: 0 })
    click_count: number;

    @Prop({ type: Number, default: 0 })
    search_count: number;

    @Prop({ type: Boolean, default: false })
    promotion_eligible: boolean;

    @Prop({ type: String, index: true })
    discovered_by: string;

    @Prop(String)
    discovery_reason: string;

    @Prop(String)
    api_source: string;

    @Prop(Number)
    similarity_rank: number;

    @Prop(Date)
    last_basic_scrape: Date;

    @Prop(Date)
    last_full_scrape: Date;

    @Prop(Date)
    analysis_timestamp: Date;

    @Prop({ type: MongooseSchema.Types.ObjectId, ref: "PrimaryProfile" })
    discovered_by_id: PrimaryProfile;
}

export const SecondaryProfileSchema =
    SchemaFactory.createForClass(SecondaryProfile);
```
