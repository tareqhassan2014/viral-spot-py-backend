import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';
import { ViralAnalysisResults } from './viral-analysis-results.schema';

export type ViralAnalysisReelsDocument = ViralAnalysisReels & Document;

@Schema({
  timestamps: { createdAt: 'selected_at', updatedAt: false },
  collection: 'viral_analysis_reels',
})
export class ViralAnalysisReels {
  @Prop({
    type: MongooseSchema.Types.ObjectId,
    ref: ViralAnalysisResults.name,
    required: true,
    index: true,
  })
  analysis_id: MongooseSchema.Types.ObjectId;

  @Prop({ type: String, required: true, maxlength: 255 })
  content_id: string;

  @Prop({
    type: String,
    enum: ['primary', 'competitor'],
    required: true,
    maxlength: 20,
  })
  reel_type: string;

  @Prop({ type: String, required: true, maxlength: 255 })
  username: string;

  @Prop({ type: String, maxlength: 100, default: null })
  selection_reason: string;

  @Prop({ type: Number, default: 0, min: 0 })
  rank_in_selection: number;

  @Prop({ type: Number, default: 0 })
  view_count_at_analysis: number;

  @Prop({ type: Number, default: 0 })
  like_count_at_analysis: number;

  @Prop({ type: Number, default: 0 })
  comment_count_at_analysis: number;

  @Prop({ type: MongooseSchema.Types.Decimal128, default: 0.0 })
  outlier_score_at_analysis: number;

  @Prop({ type: Boolean, default: false })
  transcript_requested: boolean;

  @Prop({ type: Boolean, default: false })
  transcript_completed: boolean;

  @Prop({ type: String, default: null })
  transcript_error: string;

  @Prop({ type: String, default: null })
  hook_text: string;

  @Prop({ type: MongooseSchema.Types.Mixed, default: null })
  power_words: any; // JSONB equivalent

  @Prop({ type: MongooseSchema.Types.Mixed, default: {} })
  analysis_metadata: Record<string, any>;

  @Prop({ type: Date, default: Date.now })
  selected_at: Date;

  @Prop(Date)
  transcript_fetched_at: Date;
}

export const ViralAnalysisReelsSchema =
  SchemaFactory.createForClass(ViralAnalysisReels);

// Performance indexes (matching actual SQL schema)
ViralAnalysisReelsSchema.index({
  analysis_id: 1,
  reel_type: 1,
  rank_in_selection: 1,
}); // idx_viral_analysis_reels_analysis

ViralAnalysisReelsSchema.index(
  { analysis_id: 1, content_id: 1 },
  { unique: true }, // viral_analysis_reels_unique_per_analysis
);

// Conditional index equivalent - MongoDB doesn't support WHERE clauses in indexes,
// but this compound index will be efficient for queries filtering by transcript_completed = true
ViralAnalysisReelsSchema.index({
  transcript_completed: 1,
  transcript_fetched_at: -1,
}); // idx_viral_analysis_reels_transcript

// MongoDB equivalent of GIN index for JSONB field
ViralAnalysisReelsSchema.index({ analysis_metadata: 1 }); // idx_viral_analysis_reels_analysis_metadata_gin
