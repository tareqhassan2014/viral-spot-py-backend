import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';

export type ViralAnalysisReelsDocument = ViralAnalysisReels & Document;

@Schema({
  timestamps: { createdAt: 'selected_at', updatedAt: false },
  collection: 'viral_analysis_reels',
})
export class ViralAnalysisReels {
  @Prop({
    type: MongooseSchema.Types.ObjectId,
    ref: 'ViralAnalysisResults',
    required: true,
    index: true,
  })
  analysis_id: MongooseSchema.Types.ObjectId;

  @Prop({ type: String, required: true, index: true })
  content_id: string;

  @Prop({
    type: String,
    enum: ['primary', 'competitor'],
    required: true,
    index: true,
  })
  reel_type: string;

  @Prop({ type: String, required: true, index: true })
  username: string;

  @Prop(String)
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

  @Prop({ type: Boolean, default: false, index: true })
  transcript_completed: boolean;

  @Prop(String)
  transcript_error: string;

  @Prop(String)
  hook_text: string;

  @Prop({ type: [String], default: [] })
  power_words: string[];

  @Prop({ type: MongooseSchema.Types.Mixed, default: {} })
  analysis_metadata: Record<string, any>;

  @Prop({ type: Date, default: Date.now })
  selected_at: Date;

  @Prop(Date)
  transcript_fetched_at: Date;
}

export const ViralAnalysisReelsSchema =
  SchemaFactory.createForClass(ViralAnalysisReels);

// Performance indexes
ViralAnalysisReelsSchema.index({
  analysis_id: 1,
  reel_type: 1,
  rank_in_selection: 1,
});
ViralAnalysisReelsSchema.index(
  { analysis_id: 1, content_id: 1 },
  { unique: true },
);
ViralAnalysisReelsSchema.index({
  transcript_completed: 1,
  transcript_fetched_at: -1,
});
