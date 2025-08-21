import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';

export type PrimaryProfileDocument = PrimaryProfile &
  Document & {
    createdAt: Date;
    updatedAt: Date;
  };

@Schema({ timestamps: true, collection: 'primary_profiles' })
export class PrimaryProfile {
  @Prop({
    type: String,
    required: true,
    unique: true,
    maxlength: 255,
  })
  username: string;

  @Prop({ type: String, maxlength: 255 })
  profile_name: string;

  @Prop({ type: String })
  bio: string;

  @Prop({ type: Number, default: 0, index: true })
  followers: number;

  @Prop({ type: Number, default: 0 })
  posts_count: number;

  @Prop({ type: Boolean, default: false })
  is_verified: boolean;

  @Prop({ type: Boolean, default: false })
  is_business_account: boolean;

  @Prop({ type: String, maxlength: 500 })
  profile_url: string;

  @Prop({ type: String })
  profile_image_url: string;

  @Prop({ type: String })
  profile_image_path: string;

  @Prop({ type: String })
  hd_profile_image_path: string;

  @Prop({
    type: String,
    enum: ['Influencer', 'Theme Page', 'Business Page', 'Personal'],
    default: 'Personal',
    index: true,
  })
  account_type: string;

  @Prop({ type: String, default: 'en', maxlength: 10 })
  language: string;

  @Prop({ type: String, default: 'entertainment', maxlength: 50 })
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

  @Prop({ type: String, maxlength: 100 })
  profile_primary_category: string;

  @Prop({ type: String, maxlength: 100 })
  profile_secondary_category: string;

  @Prop({ type: String, maxlength: 100 })
  profile_tertiary_category: string;

  @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
  profile_categorization_confidence: number;

  @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
  account_type_confidence: number;

  // Similar accounts - using individual fields to match SQL schema structure
  @Prop({ type: String, maxlength: 255 })
  similar_account1: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account2: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account3: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account4: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account5: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account6: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account7: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account8: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account9: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account10: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account11: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account12: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account13: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account14: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account15: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account16: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account17: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account18: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account19: string;

  @Prop({ type: String, maxlength: 255 })
  similar_account20: string;

  @Prop({ type: Date })
  last_full_scrape: Date;

  @Prop({ type: Date })
  analysis_timestamp: Date;
}

export const PrimaryProfileSchema =
  SchemaFactory.createForClass(PrimaryProfile);

// Compound indexes for performance
PrimaryProfileSchema.index({ followers: 1, median_views: -1 });
