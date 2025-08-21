import { PrimaryProfile } from '@/profile/schemas/primary-profile.schema';
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';

export type ContentDocument = Content & Document;

@Schema({ timestamps: true, collection: 'content' })
export class Content {
  // ==========================================
  // CORE CONTENT FIELDS
  // ==========================================

  @Prop({ type: String, required: true, unique: true })
  content_id: string; // Unique identifier from social platform

  @Prop({ type: String, required: true, unique: true, index: true })
  shortcode: string; // Short URL code

  @Prop({
    type: String,
    enum: ['reel', 'post', 'story'],
    default: 'reel',
  })
  content_type: string; // Type of content (enum: 'reel', 'post', 'story')

  @Prop(String)
  url: string; // Direct URL to the content

  @Prop(String)
  description: string; // Caption or description of the content

  @Prop(String)
  thumbnail_url: string; // URL of the content's thumbnail image

  // ==========================================
  // MEDIA STORAGE PATHS
  // ==========================================

  @Prop(String)
  thumbnail_path: string; // Path to thumbnail in Supabase storage bucket

  @Prop(String)
  display_url_path: string; // Path to main display image in storage bucket

  @Prop(String)
  video_thumbnail_path: string; // Path to video thumbnail in storage bucket

  @Prop({ type: MongooseSchema.Types.Mixed })
  all_image_urls: any; // JSONB for carousel content - all image URLs

  // ==========================================
  // ENGAGEMENT METRICS
  // ==========================================

  @Prop({ type: Number, default: 0, index: true })
  view_count: number; // Number of views for the content

  @Prop({ type: Number, default: 0 })
  like_count: number; // Number of likes for the content

  @Prop({ type: Number, default: 0 })
  comment_count: number; // Number of comments on the content

  @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.0 })
  outlier_score: number; // Performance deviation score from profile's average

  // ==========================================
  // CONTENT CLASSIFICATION
  // ==========================================

  @Prop({ type: String, index: true })
  primary_category: string; // Primary category of the content

  @Prop(String)
  secondary_category: string; // Secondary category of the content

  @Prop(String)
  tertiary_category: string; // Tertiary category of the content

  @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.5 })
  categorization_confidence: number; // Confidence score for content categorization

  @Prop({ type: String })
  keyword_1: string; // First keyword extracted from content

  @Prop({ type: String })
  keyword_2: string; // Second keyword extracted from content

  @Prop({ type: String })
  keyword_3: string; // Third keyword extracted from content

  @Prop({ type: String })
  keyword_4: string; // Fourth keyword extracted from content

  @Prop({ type: String, default: 'en' })
  language: string; // Primary language of the content

  @Prop({ type: String, default: 'video' })
  content_style: string; // Style of the content (e.g., 'video', 'image')

  // ==========================================
  // RELATIONSHIPS & INDEXING
  // ==========================================

  @Prop({
    type: MongooseSchema.Types.ObjectId,
    ref: PrimaryProfile.name,
    index: true,
  })
  profile_id: MongooseSchema.Types.ObjectId; // Reference to PrimaryProfile

  @Prop({ type: String, required: true, index: true })
  username: string; // Username for quick profile lookups

  @Prop({ type: Date, index: true })
  date_posted: Date; // Date and time content was posted (with timezone support)
}

export const ContentSchema = SchemaFactory.createForClass(Content);

// ==========================================
// PERFORMANCE INDEXES FOR COMMON QUERY PATTERNS
// ==========================================

// Index for user content queries sorted by date
ContentSchema.index({ username: 1, date_posted: -1 });

// Index for content type filtering with view count sorting
ContentSchema.index({ content_type: 1, view_count: -1 });

// Index for category-based queries with outlier score sorting
ContentSchema.index({ primary_category: 1, outlier_score: -1 });

// Index for profile-based content type filtering
ContentSchema.index({ profile_id: 1, content_type: 1 });
