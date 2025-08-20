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

  @Prop({ type: String, default: 'v2_json' })
  workflow_version: string;

  @Prop({
    type: String,
    enum: ['pending', 'transcribing', 'analyzing', 'completed', 'failed'],
    default: 'pending',
    index: true,
  })
  status: string;

  @Prop(String)
  error_message: string;

  @Prop(Date)
  started_at: Date;

  @Prop(Date)
  transcripts_completed_at: Date;

  @Prop(Date)
  analysis_completed_at: Date;
}

export const ViralAnalysisResultsSchema =
  SchemaFactory.createForClass(ViralAnalysisResults);

// Performance indexes
ViralAnalysisResultsSchema.index({ queue_id: 1, analysis_run: -1 });
ViralAnalysisResultsSchema.index({ status: 1, started_at: -1 });
ViralAnalysisResultsSchema.index({ workflow_version: 1 });
