import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';

export type ViralIdeasQueueDocument = ViralIdeasQueue & Document;

@Schema({ timestamps: true, collection: 'viral_ideas_queue' })
export class ViralIdeasQueue {
  @Prop({ type: String, required: true, unique: true, maxlength: 255 })
  session_id: string;

  @Prop({ type: String, required: true, index: true, maxlength: 255 })
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
    maxlength: 50,
  })
  status: string;

  @Prop({ type: Number, default: 5, min: 1, max: 10, index: true })
  priority: number;

  @Prop({ type: String, maxlength: 100 })
  current_step: string;

  @Prop({ type: Number, default: 0, min: 0, max: 100 })
  progress_percentage: number;

  @Prop({ type: String })
  error_message: string;

  @Prop({ type: Boolean, default: true })
  auto_rerun_enabled: boolean;

  @Prop({ type: Number, default: 24, min: 1 })
  rerun_frequency_hours: number;

  @Prop({ type: Date })
  last_analysis_at: Date;

  @Prop({ type: Date })
  next_scheduled_run: Date;

  @Prop({ type: Number, default: 0 })
  total_runs: number;

  @Prop({ type: Date, default: Date.now, index: -1 })
  submitted_at: Date;

  @Prop({ type: Date })
  started_processing_at: Date;

  @Prop({ type: Date })
  completed_at: Date;
}

export const ViralIdeasQueueSchema =
  SchemaFactory.createForClass(ViralIdeasQueue);

// Performance indexes (matching SQL schema)
ViralIdeasQueueSchema.index({ status: 1, priority: 1 }); // For queue processing
ViralIdeasQueueSchema.index({ auto_rerun_enabled: 1, next_scheduled_run: 1 }); // idx_viral_queue_auto_rerun
ViralIdeasQueueSchema.index({ primary_username: 1, status: 1 }); // For user-specific queries
