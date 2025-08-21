import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';
import { PrimaryProfile } from './primary-profile.schema';

export type SecondaryProfileDocument = SecondaryProfile & Document;

@Schema({ timestamps: true, collection: 'secondary_profiles' })
export class SecondaryProfile {
  @Prop({
    type: String,
    required: true,
    unique: true,
    maxlength: 255,
  })
  username: string;

  @Prop({ type: String, maxlength: 255 })
  full_name: string;

  @Prop({ type: String })
  biography: string;

  @Prop({ type: Number, default: 0, index: true })
  followers_count: number;

  @Prop({ type: Number, default: 0 })
  following_count: number;

  @Prop({ type: Number, default: 0 })
  media_count: number;

  @Prop({ type: String })
  profile_pic_url: string;

  @Prop({ type: String })
  profile_pic_path: string;

  @Prop({ type: Boolean, default: false })
  is_verified: boolean;

  @Prop({ type: Boolean, default: false })
  is_private: boolean;

  @Prop({ type: String, maxlength: 255 })
  business_email: string;

  @Prop({ type: String })
  external_url: string;

  @Prop({ type: String, maxlength: 100 })
  category: string;

  @Prop({ type: String, maxlength: 255 })
  pk: string;

  @Prop({ type: String })
  social_context: string;

  @Prop({
    type: String,
    enum: ['Influencer', 'Theme Page', 'Business Page', 'Personal'],
    default: 'Personal',
  })
  estimated_account_type: string;

  @Prop({ type: String, maxlength: 100 })
  primary_category: string;

  @Prop({ type: String, maxlength: 100 })
  secondary_category: string;

  @Prop({ type: String, maxlength: 100 })
  tertiary_category: string;

  @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
  categorization_confidence: number;

  @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
  account_type_confidence: number;

  @Prop({ type: String, default: 'en', maxlength: 10 })
  estimated_language: string;

  @Prop({ type: Number, default: 0 })
  click_count: number;

  @Prop({ type: Number, default: 0 })
  search_count: number;

  @Prop({ type: Boolean, default: false })
  promotion_eligible: boolean;

  @Prop({ type: String, index: true, maxlength: 255 })
  discovered_by: string;

  @Prop({ type: String, maxlength: 100 })
  discovery_reason: string;

  @Prop({ type: String, maxlength: 100 })
  api_source: string;

  @Prop({ type: Number })
  similarity_rank: number;

  @Prop({ type: Date })
  last_basic_scrape: Date;

  @Prop({ type: Date })
  last_full_scrape: Date;

  @Prop({ type: Date })
  analysis_timestamp: Date;

  @Prop({ type: MongooseSchema.Types.ObjectId, ref: PrimaryProfile.name })
  discovered_by_id: PrimaryProfile;
}

export const SecondaryProfileSchema =
  SchemaFactory.createForClass(SecondaryProfile);
