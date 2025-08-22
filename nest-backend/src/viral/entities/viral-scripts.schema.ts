import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';
import { ViralAnalysisResults } from './viral-analysis-results.schema';

export type ViralScriptsDocument = ViralScripts & Document;

@Schema({ timestamps: true, collection: 'viral_scripts' })
export class ViralScripts {
  @Prop({
    type: MongooseSchema.Types.ObjectId,
    ref: ViralAnalysisResults.name,
    required: true,
    index: true,
  })
  analysis_id: MongooseSchema.Types.ObjectId;

  @Prop({ type: String, required: true })
  script_title: string;

  @Prop({ type: String, required: true })
  script_content: string;

  @Prop({
    type: String,
    enum: ['reel', 'story', 'post', 'youtube', 'tiktok'],
    default: 'reel',
  })
  script_type: string;

  @Prop({ type: Number, min: 0 })
  estimated_duration: number;

  @Prop(String)
  target_audience: string;

  @Prop(String)
  primary_hook: string;

  @Prop(String)
  call_to_action: string;

  @Prop({
    type: [String],
    default: [],
    validate: {
      validator: function (v: string[]) {
        // Ensure all content_ids are valid format
        return v.every((id) => typeof id === 'string' && id.length > 0);
      },
      message: 'source_reels must contain valid content_id strings',
    },
  })
  source_reels: string[];

  @Prop({
    type: MongooseSchema.Types.Mixed,
    default: {},
    validate: {
      validator: function (v: any) {
        // Basic structure validation for script breakdown
        if (!v || Object.keys(v).length === 0) return true;
        return typeof v === 'object';
      },
      message: 'script_structure must be a valid object',
    },
  })
  script_structure: {
    intro?: any;
    hook?: any;
    body?: any;
    cta?: any;
    timing?: any;
    voice_elements?: any;
  };

  @Prop(String)
  generation_prompt: string;

  @Prop({ type: String, default: 'gpt-4o-mini' })
  ai_model: string;

  @Prop({
    type: MongooseSchema.Types.Decimal128,
    default: 0.8,
    min: 0,
    max: 1,
  })
  generation_temperature: number;

  @Prop({
    type: String,
    enum: ['draft', 'reviewed', 'approved', 'published'],
    default: 'draft',
    index: true,
  })
  status: string;

  createdAt: string;
  updatedAt: string;
}

export const ViralScriptsSchema = SchemaFactory.createForClass(ViralScripts);

// Performance indexes
ViralScriptsSchema.index({ analysis_id: 1, script_type: 1 });
ViralScriptsSchema.index({ status: 1, createdAt: -1 });
ViralScriptsSchema.index({ script_type: 1, status: 1 });
