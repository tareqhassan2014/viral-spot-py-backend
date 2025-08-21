import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';

export type ViralAnalysisResultsDocument = ViralAnalysisResults & Document;

@Schema({ timestamps: true, collection: 'viral_analysis_results' })
export class ViralAnalysisResults {
  @Prop({
    type: MongooseSchema.Types.ObjectId,
    ref: 'ViralIdeasQueue',
    required: true,
    index: true,
  })
  queue_id: MongooseSchema.Types.ObjectId;

  @Prop({ type: Number, default: 1 })
  analysis_run: number;

  @Prop({
    type: String,
    enum: ['initial', 'recurring'],
    default: 'initial',
    maxlength: 50,
  })
  analysis_type: string;

  @Prop({ type: Number, default: 0 })
  total_reels_analyzed: number;

  @Prop({ type: Number, default: 0 })
  primary_reels_count: number;

  @Prop({ type: Number, default: 0 })
  competitor_reels_count: number;

  @Prop({ type: Number, default: 0 })
  transcripts_fetched: number;

  @Prop({
    type: String,
    enum: ['pending', 'transcribing', 'analyzing', 'completed', 'failed'],
    default: 'pending',
    index: true,
    maxlength: 50,
  })
  status: string;

  @Prop({ type: String, default: null })
  error_message: string;

  @Prop({ type: Date, default: Date.now })
  started_at: Date;

  @Prop({ type: Date, default: null })
  transcripts_completed_at: Date;

  @Prop({ type: Date, default: null })
  analysis_completed_at: Date;

  @Prop({
    type: MongooseSchema.Types.Mixed,
    default: {},
    validate: {
      validator: function (v: Record<string, any>): boolean {
        // Ensure workflow_version exists if analysis_data is populated
        if (v && Object.keys(v).length > 0) {
          return v.workflow_version !== undefined;
        }
        return true;
      },
      message: 'analysis_data must include workflow_version when populated',
    },
  })
  analysis_data: {
    workflow_version?: string;
    analysis_timestamp?: string;
    profile_analysis?: any;
    individual_reel_analyses?: any[];
    generated_hooks?: any[];
    complete_scripts?: any[];
    scripts_summary?: any[];
    analysis_summary?: any;
  };

  @Prop({ type: String, default: 'v2_json', maxlength: 50, index: true })
  workflow_version: string;
}

export const ViralAnalysisResultsSchema =
  SchemaFactory.createForClass(ViralAnalysisResults);

// Performance indexes (matching actual SQL schema)
ViralAnalysisResultsSchema.index({ queue_id: 1, analysis_run: -1 }); // idx_viral_analysis_results_queue
ViralAnalysisResultsSchema.index({ status: 1, started_at: -1 }); // idx_viral_analysis_results_status
ViralAnalysisResultsSchema.index({ updatedAt: 1 }); // idx_viral_analysis_results_updated_at (timestamps: true creates updatedAt)

// Note: MongoDB doesn't have direct GIN index equivalent, but these compound indexes help with JSONB queries
ViralAnalysisResultsSchema.index({ 'analysis_data.generated_hooks': 1 }); // Similar to idx_analysis_data_hooks
ViralAnalysisResultsSchema.index({ 'analysis_data.profile_analysis': 1 }); // Similar to idx_analysis_data_profile

// Unique constraint to match SQL UNIQUE(queue_id, analysis_run)
ViralAnalysisResultsSchema.index(
  { queue_id: 1, analysis_run: 1 },
  { unique: true },
);
