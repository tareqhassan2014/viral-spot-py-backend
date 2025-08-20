import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';

export type PrimaryProfileDocument = PrimaryProfile & Document;

@Schema({ timestamps: true, collection: 'primary_profiles' })
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
    enum: ['Influencer', 'Theme Page', 'Business Page', 'Personal'],
    default: 'Personal',
    index: true,
  })
  account_type: string;

  @Prop({ type: String, default: 'en' })
  language: string;

  @Prop({ type: String, default: 'entertainment' })
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
