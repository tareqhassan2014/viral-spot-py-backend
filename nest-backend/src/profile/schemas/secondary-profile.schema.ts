import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';
import { PrimaryProfile } from './primary-profile.schema';

export type SecondaryProfileDocument = SecondaryProfile & Document;

@Schema({ timestamps: true, collection: 'secondary_profiles' })
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
    enum: ['Influencer', 'Theme Page', 'Business Page', 'Personal'],
    default: 'Personal',
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

  @Prop({ type: String, default: 'en' })
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

  @Prop({ type: MongooseSchema.Types.ObjectId, ref: 'PrimaryProfile' })
  discovered_by_id: PrimaryProfile;
}

export const SecondaryProfileSchema =
  SchemaFactory.createForClass(SecondaryProfile);
