import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';

export type ViralIdeasQueueDocument = ViralIdeasQueue & Document;

@Schema({ timestamps: true, collection: 'viral_ideas_queue' })
export class ViralIdeasQueue {
  @Prop({ type: String, required: true, unique: true, index: true })
  session_id: string;

  @Prop({ type: String, required: true, index: true })
  primary_username: string;

  @Prop({
    type: MongooseSchema.Types.Mixed,
    default: {},
    validate: {
      validator: function (v: Record<string, any>): boolean {
        // Validate content_strategy structure
        if (!v || Object.keys(v).length === 0) return true;
        return !!(v.contentType && v.targetAudience && v.goals);
      },
      message:
        'content_strategy must include contentType, targetAudience, and goals',
    },
  })
  content_strategy: {
    contentType?: string; // "What type of content do you create?"
    targetAudience?: string; // "Who is your target audience?"
    goals?: string; // "What are your main goals?"
  };

  @Prop({ type: MongooseSchema.Types.Mixed, default: {} })
  analysis_settings: Record<string, any>;

  @Prop({
    type: String,
    enum: ['pending', 'processing', 'completed', 'failed', 'paused'],
    default: 'pending',
    index: true,
  })
  status: string;

  @Prop({ type: Number, default: 5, min: 1, max: 10 })
  priority: number;

  @Prop(String)
  current_step: string;

  @Prop({ type: Number, default: 0, min: 0, max: 100 })
  progress_percentage: number;

  @Prop(String)
  error_message: string;

  @Prop({ type: Boolean, default: true })
  auto_rerun_enabled: boolean;

  @Prop({ type: Number, default: 24, min: 1 })
  rerun_frequency_hours: number;

  @Prop(Date)
  last_analysis_at: Date;

  @Prop(Date)
  next_scheduled_run: Date;

  @Prop({ type: Number, default: 0 })
  total_runs: number;

  @Prop({ type: Date, default: Date.now, index: true })
  submitted_at: Date;

  @Prop(Date)
  started_processing_at: Date;

  @Prop(Date)
  completed_at: Date;
}

export const ViralIdeasQueueSchema =
  SchemaFactory.createForClass(ViralIdeasQueue);

// Performance indexes
ViralIdeasQueueSchema.index({ status: 1, priority: 1 });
ViralIdeasQueueSchema.index({ auto_rerun_enabled: 1, next_scheduled_run: 1 });
ViralIdeasQueueSchema.index({ primary_username: 1, status: 1 });
